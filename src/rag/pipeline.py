"""
pipeline.py - Pipeline principal d'extraction

Stratégie regex + Groq :
─────────────────────────────────────────────────────────────
│ Champ          │ Regex  │ Groq   │ Priorité finale        │
│────────────────│────────│────────│────────────────────────│
│ email          │  ✅    │   ✅   │ Regex (plus précis)    │
│ telephone      │  ✅    │   ✅   │ Regex (plus précis)    │
│ montant        │  ✅    │   ✅   │ Regex (plus précis)    │
│ date           │  ✅    │   ✅   │ Regex (plus précis)    │
│ nom            │  ❌    │   ✅   │ Groq uniquement        │
│ prenom         │  ❌    │   ✅   │ Groq uniquement        │
│ adresse        │  ❌    │   ✅   │ Groq uniquement        │
│ societe        │  ❌    │   ✅   │ Groq uniquement        │
│ numero_dossier │  ✅*   │   ✅   │ Groq prioritaire       │
─────────────────────────────────────────────────────────────
* regex numero_dossier utilisé seulement si Groq échoue
"""

import json
import logging
from pathlib import Path

from groq import Groq

import config
from src.extractors.pdf_extractor import extract_text_from_pdf
from src.extractors.email_extractor import extract_text_from_email, extract_text_from_raw_email
from src.extractors.text_extractor import clean_text, regex_extract_fields, extract_text_from_file
from src.extractors.image_extractor import extract_text_from_image
from src.rag.retriever import build_prompt, REGEX_RELIABLE_FIELDS
from src.rag.vectorstore import validate_and_store
from src.normalizer import normalize_all
from src.database import insert_extraction

logger = logging.getLogger(__name__)

_client = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        if not config.GROQ_API_KEY:
            raise ValueError("GROQ_API_KEY manquante dans le fichier .env !")
        _client = Groq(api_key=config.GROQ_API_KEY)
    return _client


def process_document(source, source_type: str = "auto") -> dict:
    """Pipeline complet : lit → nettoie → regex → Groq → fusionne → normalise → BDD"""

    # 1. Lecture
    raw_text = _load_source(source, source_type)
    if not raw_text.strip():
        return _empty_result("Document vide ou illisible")

    # 2. Nettoyage
    clean = clean_text(raw_text)
    logger.info(f"Texte nettoyé : {len(clean)} caractères")

    # 3. Pré-extraction regex (email, tel, montant, date uniquement)
    regex_fields = regex_extract_fields(clean)
    logger.info(f"Regex → {[k for k,v in regex_fields.items() if v]}")

    # 4. Extraction Groq (tous les champs)
    ai_fields = _extract_with_groq(clean, regex_fields)
    logger.info(f"Groq  → {[k for k,v in ai_fields.items() if v]}")

    # 5. Fusion intelligente
    merged = _smart_merge(regex_fields, ai_fields)
    logger.info(f"Fusionné → {[k for k,v in merged.items() if v]}")

    # 6. Normalisation
    normalized = normalize_all(merged)

    # 7. Validation JSON Schema
    result = validate_and_store(normalized, source)

    # 8. Sauvegarde BDD
    try:
        row_id = insert_extraction(result)
        result["db_id"] = row_id
    except Exception as e:
        logger.error(f"Erreur BDD : {e}")

    return result


def _smart_merge(regex_fields: dict, ai_fields: dict) -> dict:
    """
    Fusion intelligente selon la fiabilité de chaque source :
    - Champs fiables (email, tel, montant, date) : regex prioritaire sur Groq
    - Champs complexes (nom, prénom, adresse, etc.) : Groq uniquement
    - numero_dossier : Groq prioritaire, regex en fallback
    """
    merged = {}

    for key in config.FIELDS_TO_EXTRACT:
        regex_val = regex_fields.get(key)
        ai_val = ai_fields.get(key)

        if key in REGEX_RELIABLE_FIELDS:
            # Regex est plus fiable → regex prioritaire
            merged[key] = regex_val if regex_val else ai_val

        elif key == "numero_dossier":
            # Groq prioritaire car regex capture parfois le mot "Dossier"
            # Fallback sur regex seulement si Groq retourne null
            merged[key] = ai_val if ai_val else regex_val

        else:
            # Champs complexes (nom, prenom, adresse, societe) → Groq uniquement
            merged[key] = ai_val

    return merged


def _load_source(source, source_type: str) -> str:
    source_str = str(source)
    if source_type == "text" or (
        source_type == "auto" and not Path(source_str).exists()
    ):
        return extract_text_from_raw_email(source_str)

    path = Path(source_str)
    ext = path.suffix.lower()

    if source_type == "pdf" or ext == ".pdf":
        return extract_text_from_pdf(path)
    elif source_type == "image" or ext in (".png", ".jpg", ".jpeg", ".bmp", ".tif", ".tiff"):
        return extract_text_from_image(path)
    elif source_type == "email" or ext in (".eml", ".msg"):
        return extract_text_from_email(path)
    else:
        return extract_text_from_file(path)


def _extract_with_groq(text: str, regex_prefill: dict) -> dict:
    prompt = build_prompt(text, regex_prefill, config.FIELDS_TO_EXTRACT)
    try:
        client = get_groq_client()
        response = client.chat.completions.create(
            model=config.GROQ_MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Tu es un assistant spécialisé en extraction de données structurées. "
                        "Tu réponds UNIQUEMENT en JSON valide, sans texte autour, sans backticks."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            max_tokens=800,
        )
        raw_json = response.choices[0].message.content.strip()
        raw_json = raw_json.strip("```json").strip("```").strip()
        fields = json.loads(raw_json)
        return fields
    except json.JSONDecodeError as e:
        logger.error(f"[Groq] Réponse non-JSON : {e}")
        return {}
    except Exception as e:
        logger.error(f"[Groq] Erreur API : {e}")
        return {}


def _empty_result(reason: str) -> dict:
    return {
        "fields": {f: None for f in config.FIELDS_TO_EXTRACT},
        "missing_fields": config.FIELDS_TO_EXTRACT,
        "status": "error",
        "message": reason,
    }