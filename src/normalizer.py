"""
normalizer.py - Normalisation ET validation des champs extraits
- Dates     → YYYY-MM-DD (ISO 8601)
- Montants  → float string (ex: "2500.00")
- Téléphone → +33XXXXXXXXX (E.164)
- Email     → minuscules + validation format
Retourne des erreurs explicites si le format est invalide.
"""

import logging
import re

logger = logging.getLogger(__name__)

MOIS_FR = {
    "janvier": "01", "février": "02", "fevrier": "02",
    "mars": "03",    "avril": "04",   "mai": "05",
    "juin": "06",    "juillet": "07", "août": "08",
    "aout": "08",    "septembre": "09","octobre": "10",
    "novembre": "11","décembre": "12", "decembre": "12",
}


def normalize_all(fields: dict) -> dict:
    """
    Applique toutes les normalisations + validations.
    Si un champ est invalide, sa valeur devient un message d'erreur explicite.
    """
    normalized = dict(fields)
    errors = {}

    if fields.get("date"):
        result = normalize_date(fields["date"])
        if result.startswith("ERREUR"):
            errors["date"] = result
            normalized["date"] = None
        else:
            normalized["date"] = result

    if fields.get("montant"):
        result = normalize_montant(fields["montant"])
        if result.startswith("ERREUR"):
            errors["montant"] = result
            normalized["montant"] = None
        else:
            normalized["montant"] = result

    if fields.get("telephone"):
        result = normalize_telephone(fields["telephone"])
        if result.startswith("ERREUR"):
            errors["telephone"] = result
            normalized["telephone"] = None
        else:
            normalized["telephone"] = result

    if fields.get("email"):
        result = normalize_email(fields["email"])
        if result.startswith("ERREUR"):
            errors["email"] = result
            normalized["email"] = None
        else:
            normalized["email"] = result

    if fields.get("adresse"):
        normalized["adresse"] = normalize_adresse(fields["adresse"])

    # On attache les erreurs au dict pour les afficher dans l'interface
    normalized["_errors"] = errors
    if errors:
        logger.warning(f"[normalizer] Erreurs de format : {errors}")

    return normalized


def normalize_date(raw: str) -> str:
    """
    Convertit une date en ISO 8601 : YYYY-MM-DD
    Retourne 'ERREUR: ...' si le format n'est pas reconnu.
    """
    if not raw:
        return "ERREUR: date vide"

    raw = raw.strip()

    # Déjà au bon format ISO
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw):
        return raw

    # AAAA/MM/JJ ou AAAA.MM.JJ
    m = re.match(r"^(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})$", raw)
    if m:
        a, mo, j = m.group(1), m.group(2), m.group(3)
        if not _date_valide(int(j), int(mo), int(a)):
            return f"ERREUR: date invalide '{raw}' (jour/mois hors limites)"
        return f"{a}-{mo.zfill(2)}-{j.zfill(2)}"

    # JJ/MM/AAAA ou JJ/MM/AA (format européen)
    m = re.match(r"^(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{2,4})$", raw)
    if m:
        j, mo, a = m.group(1), m.group(2), m.group(3)
        if len(a) == 2:
            a = "20" + a if int(a) <= 30 else "19" + a
        if not _date_valide(int(j), int(mo), int(a)):
            return f"ERREUR: date invalide '{raw}' (jour/mois hors limites)"
        return f"{a}-{mo.zfill(2)}-{j.zfill(2)}"

    # "15 mars 1985"
    m = re.match(r"^(\d{1,2})\s+([a-zéûôîàâùèê]+)\s+(\d{2,4})$", raw.lower())
    if m:
        j, mois_str, a = m.group(1), m.group(2), m.group(3)
        mo = MOIS_FR.get(mois_str)
        if not mo:
            return f"ERREUR: mois inconnu '{mois_str}' dans '{raw}'"
        if len(a) == 2:
            a = "20" + a if int(a) <= 30 else "19" + a
        return f"{a}-{mo}-{j.zfill(2)}"

    # "mars 2024"
    m = re.match(r"^([a-zéûôîàâùèê]+)\s+(\d{4})$", raw.lower())
    if m:
        mois_str, a = m.group(1), m.group(2)
        mo = MOIS_FR.get(mois_str)
        if not mo:
            return f"ERREUR: mois inconnu '{mois_str}' dans '{raw}'"
        return f"{a}-{mo}-01"

    return f"ERREUR: format de date non reconnu '{raw}' (attendu: JJ/MM/AAAA ou AAAA-MM-JJ)"


def normalize_montant(raw: str) -> str:
    """
    Convertit un montant en float string : "2500.00"
    Retourne 'ERREUR: ...' si invalide.
    """
    if not raw:
        return "ERREUR: montant vide"

    cleaned = re.sub(r"[€EUReur\s]", "", raw, flags=re.IGNORECASE)

    # "2.500,50" → point = séparateur milliers, virgule = décimale
    if re.match(r"^\d{1,3}(\.\d{3})*(,\d+)?$", cleaned):
        cleaned = cleaned.replace(".", "").replace(",", ".")
    # "2,500.50" → virgule = séparateur milliers, point = décimale
    elif re.match(r"^\d{1,3}(,\d{3})*(\.\d+)?$", cleaned):
        cleaned = cleaned.replace(",", "")
    # "2500,50" → virgule = décimale simple
    elif "," in cleaned and "." not in cleaned:
        cleaned = cleaned.replace(",", ".")

    try:
        value = float(cleaned)
        if value < 0:
            return f"ERREUR: montant négatif non autorisé '{raw}'"
        return f"{value:.2f}"
    except ValueError:
        return f"ERREUR: format de montant non reconnu '{raw}' (attendu: 1500.00 ou 1 500,00 EUR)"


def normalize_telephone(raw: str) -> str:
    """
    Convertit un numéro français au format E.164 : +33XXXXXXXXX
    Retourne 'ERREUR: ...' si invalide.
    """
    if not raw:
        return "ERREUR: téléphone vide"

    # Corrige quelques confusions OCR fréquentes avant normalisation.
    raw = raw.strip().replace("O", "0").replace("o", "0")
    digits = re.sub(r"[^\d\+]", "", raw)

    if digits.startswith("+33") and len(digits) == 12:
        return digits
    if digits.startswith("0033"):
        digits = "+33" + digits[4:]
        if len(digits) == 12:
            return digits
    if digits.startswith("0") and len(digits) == 10:
        return "+33" + digits[1:]
    if digits.isdigit() and len(digits) == 9:
        return "+33" + digits

    return f"ERREUR: format de téléphone non reconnu '{raw}' (attendu: 06 XX XX XX XX ou +33XXXXXXXXX)"


def normalize_email(raw: str) -> str:
    """
    Normalise et valide un email.
    Retourne 'ERREUR: ...' si le format est invalide.
    """
    if not raw:
        return "ERREUR: email vide"

    cleaned = raw.strip().lower()

    if not re.match(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$", cleaned):
        return f"ERREUR: format email invalide '{raw}' (attendu: nom@domaine.fr)"

    return cleaned


def normalize_adresse(raw: str) -> str:
    """Nettoie une adresse (espaces multiples, casse)."""
    if not raw:
        return raw
    cleaned = re.sub(r"\s+", " ", raw.strip())
    return cleaned[0].upper() + cleaned[1:] if cleaned else cleaned


def _date_valide(jour: int, mois: int, annee: int) -> bool:
    """Vérifie que jour/mois/année sont dans des plages cohérentes."""
    if not (1 <= mois <= 12):
        return False
    if not (1 <= jour <= 31):
        return False
    if not (1900 <= annee <= 2100):
        return False
    return True