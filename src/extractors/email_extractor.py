"""
email_extractor.py - Extraction de texte depuis des fichiers email (.eml, .txt)
"""

import email
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_text_from_email(filepath: str | Path) -> str:
    """
    Extrait le contenu textuel d'un fichier email .eml

    Args:
        filepath: chemin vers le fichier .eml

    Returns:
        Texte brut de l'email (entêtes + corps)
    """
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"Fichier email introuvable : {filepath}")
        return ""

    try:
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            msg = email.message_from_file(f)

        parts = []

        # ── Entêtes utiles ────────────────────────────────────────────────────
        for header in ["From", "To", "Subject", "Date"]:
            value = msg.get(header)
            if value:
                parts.append(f"{header}: {value}")

        parts.append("")  # ligne vide de séparation

        # ── Corps du message ──────────────────────────────────────────────────
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    body = part.get_payload(decode=True)
                    if body:
                        parts.append(body.decode("utf-8", errors="ignore"))
        else:
            body = msg.get_payload(decode=True)
            if body:
                parts.append(body.decode("utf-8", errors="ignore"))

        result = "\n".join(parts)
        logger.info(f"Email extrait : {filepath.name} ({len(result)} caractères)")
        return result

    except Exception as e:
        logger.error(f"Erreur extraction email {filepath.name} : {e}")
        return ""


def extract_text_from_raw_email(raw_text: str) -> str:
    """
    Traite un email déjà copié-collé sous forme de texte brut.

    Args:
        raw_text: contenu email en texte brut

    Returns:
        Texte nettoyé
    """
    lines = raw_text.splitlines()
    cleaned = [line.strip() for line in lines if line.strip()]
    return "\n".join(cleaned)