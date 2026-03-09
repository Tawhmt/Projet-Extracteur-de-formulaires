"""
text_extractor.py - Extraction et nettoyage de textes mal formatés

Deux types de regex :
1. REGEX_PATTERNS     : patterns universels (email, tel, date, montant, ref)
2. FORM_LABEL_PATTERNS: patterns "Label : Valeur" pour les formulaires structurés
"""

import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


# ── 1. Patterns universels (fonctionnent sur tout type de texte) ──────────────
REGEX_PATTERNS = {
    # Capture un vrai email OU une valeur brute après "email :" (même invalide)
    "email": re.compile(
        r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
        r"|(?:email|mail|courriel|e-mail)\s*(?:est|:)\s*([\w._%+\-]+(?:@[\w.\-]+)?)",
        re.IGNORECASE
    ),
    "telephone": re.compile(
        r"(?:\+33|0033|0)\s*[1-9](?:[\s.\-]?\d{2}){4}"
    ),
    "date": re.compile(
        r"\b(?:\d{1,2}[\/\-\.]\d{1,2}[\/\-\.]\d{2,4}"
        r"|\d{4}[\/\-\.]\d{1,2}[\/\-\.]\d{1,2}"
        r"|(?:\d{1,2}\s+)?(?:janvier|février|mars|avril|mai|juin"
        r"|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})\b",
        re.IGNORECASE,
    ),
    "montant": re.compile(
        r"\b\d+(?:[.\s,]\d{3})*(?:[.,]\d{1,2})?\s*(?:€|EUR|euros?)\b"
        r"|\b(?:€|EUR)\s*\d+(?:[.,]\d{1,2})?\b"
        r"|(?:montant|somme|prix|total)\s*(?:demandé|total|:)?\s*:?\s*([\d\s.,]+(?:€|EUR|euros?))",
        re.IGNORECASE,
    ),
    "numero_dossier": re.compile(
        r"(?:n[°o]\s*dossier|dossier\s*n[°o]?|ref|réf|référence)[.\s:#-]*"
        r"([A-Z]{2,}-[A-Z0-9]{2,}(?:-[A-Z0-9]+)*)",
        re.IGNORECASE,
    ),
}

# ── 2. Patterns "Label : Valeur" pour formulaires structurés ─────────────────
# Fiables à 100% sur les formulaires PDF/texte avec structure claire
FORM_LABEL_PATTERNS = {
    "nom": re.compile(
        r"^(?:nom|last\s*name|name)\s*:\s*(.+)$",
        re.MULTILINE | re.IGNORECASE
    ),
    "prenom": re.compile(
        r"^(?:pr[eé]nom|first\s*name|given\s*name)\s*:\s*(.+)$",
        re.MULTILINE | re.IGNORECASE
    ),
    # Formulations libres : "je m'appelle Jean Dupont"
    "nom_libre": re.compile(
        r"(?:je\s+m['\'']appelle|je\s+suis|my\s+name\s+is)\s+([A-ZÀ-Ÿa-zà-ÿ]+(?:\s+[A-ZÀ-Ÿa-zà-ÿ]+)?)",
        re.IGNORECASE
    ),
    "adresse": re.compile(
        r"^(?:adresse|address|domicile)\s*:\s*(.+)$",
        re.MULTILINE | re.IGNORECASE
    ),
    "societe": re.compile(
        r"^(?:soci[eé]t[eé]|entreprise|company|organisation|employeur)\s*:\s*(.+)$",
        re.MULTILINE | re.IGNORECASE
    ),
}


def extract_text_from_file(filepath: str | Path) -> str:
    """Lit un fichier texte brut (.txt, .csv, etc.)"""
    filepath = Path(filepath)
    if not filepath.exists():
        logger.error(f"Fichier introuvable : {filepath}")
        return ""
    try:
        text = filepath.read_text(encoding="utf-8", errors="ignore")
        logger.info(f"Fichier texte lu : {filepath.name} ({len(text)} caractères)")
        return text
    except Exception as e:
        logger.error(f"Erreur lecture {filepath.name} : {e}")
        return ""


def clean_text(text: str) -> str:
    """Nettoie un texte mal formaté."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    return text.strip()


def regex_extract_fields(text: str) -> dict:
    """
    Extrait tous les champs par regex :
    - D'abord les patterns universels
    - Ensuite les patterns formulaire (Label : Valeur) qui complètent

    Returns:
        dict avec tous les champs trouvés (None si absent)
    """
    results = {}

    # ── Patterns universels ───────────────────────────────────────────────────
    for field, pattern in REGEX_PATTERNS.items():
        match = pattern.search(text)
        if match:
            value = match.group(1) if match.lastindex else match.group(0)
            results[field] = value.strip()
        else:
            results[field] = None

    # ── Patterns formulaire (Label : Valeur) ──────────────────────────────────
    for field, pattern in FORM_LABEL_PATTERNS.items():
        # Ignorer le pattern spécial nom_libre ici
        if field == "nom_libre":
            continue
        match = pattern.search(text)
        if match:
            value = match.group(1).strip()
            if value and len(value) < 200:
                results[field] = value
                logger.debug(f"[form regex] {field} → {value}")
        if field not in results:
            results[field] = None

    # ── Formulations libres : "je m'appelle Jean Dupont" ─────────────────────
    if not results.get("nom") and not results.get("prenom"):
        m = FORM_LABEL_PATTERNS["nom_libre"].search(text)
        if m:
            full_name = m.group(1).strip().split()
            if len(full_name) >= 2:
                results["prenom"] = full_name[0]
                results["nom"]    = full_name[-1]
            elif len(full_name) == 1:
                results["prenom"] = full_name[0]
            logger.debug(f"[form regex] nom_libre → {m.group(1)}")

    found = sum(1 for v in results.values() if v)
    logger.info(f"[regex total] {found}/{len(results)} champs détectés")
    return results