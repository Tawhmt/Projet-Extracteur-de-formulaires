"""
pdf_extractor.py - Extraction de texte depuis des fichiers PDF
Utilise pdfplumber (prioritaire) avec fallback sur PyPDF2
"""

import logging
from pathlib import Path

import pdfplumber
import PyPDF2

logger = logging.getLogger(__name__)


def extract_text_from_pdf(filepath: str | Path) -> str:
    """
    Extrait tout le texte d'un PDF page par page.

    Args:
        filepath: chemin vers le fichier PDF

    Returns:
        Texte brut extrait (str), ou chaîne vide en cas d'échec
    """
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"Fichier introuvable : {filepath}")
        return ""

    if filepath.suffix.lower() != ".pdf":
        logger.warning(f"Extension inattendue pour un PDF : {filepath.suffix}")

    # ── Tentative 1 : pdfplumber (meilleur pour les tableaux / formulaires) ──
    try:
        text = _extract_with_pdfplumber(filepath)
        if text.strip():
            logger.info(f"[pdfplumber] Extraction réussie : {filepath.name}")
            return text
    except Exception as e:
        logger.warning(f"[pdfplumber] Échec ({e}), tentative avec PyPDF2...")

    # ── Tentative 2 : PyPDF2 (fallback) ──────────────────────────────────────
    try:
        text = _extract_with_pypdf2(filepath)
        if text.strip():
            logger.info(f"[PyPDF2] Extraction réussie : {filepath.name}")
            return text
    except Exception as e:
        logger.error(f"[PyPDF2] Échec également : {e}")

    logger.error(f"Impossible d'extraire le texte de : {filepath.name}")
    return ""


def _extract_with_pdfplumber(filepath: Path) -> str:
    """Extraction page par page avec pdfplumber."""
    pages_text = []
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"--- Page {i + 1} ---\n{page_text}")
    return "\n\n".join(pages_text)


def _extract_with_pypdf2(filepath: Path) -> str:
    """Extraction page par page avec PyPDF2."""
    pages_text = []
    with open(filepath, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages_text.append(f"--- Page {i + 1} ---\n{page_text}")
    return "\n\n".join(pages_text)