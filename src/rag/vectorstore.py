"""
vectorstore.py - Validation JSON Schema et sauvegarde des résultats
(Dans ce projet, joue le rôle de couche de persistance et de validation)
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from jsonschema import validate, ValidationError

import config

logger = logging.getLogger(__name__)

# ── JSON Schema des champs extraits ───────────────────────────────────────────
EXTRACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "nom":             {"type": ["string", "null"]},
        "prenom":          {"type": ["string", "null"]},
        "email":           {"type": ["string", "null"], "format": "email"},
        "telephone":       {"type": ["string", "null"]},
        "date":            {"type": ["string", "null"]},
        "adresse":         {"type": ["string", "null"]},
        "montant":         {"type": ["string", "null"]},
        "numero_dossier":  {"type": ["string", "null"]},
        "societe":         {"type": ["string", "null"]},
    },
    "additionalProperties": True,
}


def validate_and_store(fields: dict, source) -> dict:
    """
    Valide les champs extraits contre le JSON Schema,
    log les champs manquants, et sauvegarde le résultat.

    Args:
        fields : dict des champs extraits
        source : fichier ou texte d'origine (pour le nom du fichier de sortie)

    Returns:
        dict enrichi avec statut, champs manquants et chemin de sauvegarde
    """
    # ── Validation JSON Schema ────────────────────────────────────────────────
    is_valid = True
    validation_errors = []
    try:
        validate(instance=fields, schema=EXTRACTION_SCHEMA)
        logger.info("Validation JSON Schema : OK")
    except ValidationError as e:
        is_valid = False
        validation_errors.append(str(e.message))
        logger.warning(f"Validation JSON Schema : ÉCHEC — {e.message}")

    # ── Champs manquants / douteux ────────────────────────────────────────────
    missing = [k for k, v in fields.items() if v is None]
    if missing:
        logger.warning(f"Champs manquants ou non trouvés : {', '.join(missing)}")
    else:
        logger.info("Tous les champs ont été extraits avec succès.")

    # ── Construction du résultat final ────────────────────────────────────────
    result = {
        "fields":            fields,
        "missing_fields":    missing,
        "validation_ok":     is_valid,
        "validation_errors": validation_errors,
        "status":            "success" if not missing else "partial",
        "extracted_at":      datetime.now().isoformat(),
        "source":            str(source),
    }

    # ── Sauvegarde dans data/processed/ ──────────────────────────────────────
    _save_result(result, source)

    return result


def _save_result(result: dict, source) -> None:
    """Sauvegarde le résultat JSON dans le dossier processed."""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        source_name = Path(str(source)).stem if Path(str(source)).exists() else "texte_brut"
        filename = f"{source_name}_{timestamp}.json"
        output_path = config.PROCESSED_DIR / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)

        logger.info(f"Résultat sauvegardé : {output_path}")
    except Exception as e:
        logger.error(f"Erreur sauvegarde : {e}")