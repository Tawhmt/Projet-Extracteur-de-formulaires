"""image_extractor.py - Extraction OCR depuis des images."""

import logging
from pathlib import Path
import os

from PIL import Image
import pytesseract

logger = logging.getLogger(__name__)


def _configure_tesseract_path() -> None:
    """Configure le chemin de tesseract.exe sous Windows si nécessaire."""
    if os.name != "nt":
        return

    configured = pytesseract.pytesseract.tesseract_cmd or ""
    if configured and Path(configured).exists():
        return

    common_paths = [
        Path("C:/Program Files/Tesseract-OCR/tesseract.exe"),
        Path("C:/Program Files (x86)/Tesseract-OCR/tesseract.exe"),
    ]
    for candidate in common_paths:
        if candidate.exists():
            pytesseract.pytesseract.tesseract_cmd = str(candidate)
            return


def extract_text_from_image(filepath: str | Path) -> str:
    """Extrait le texte brut depuis une image via Tesseract OCR."""
    filepath = Path(filepath)

    if not filepath.exists():
        logger.error(f"Image introuvable : {filepath}")
        return ""

    _configure_tesseract_path()

    try:
        with Image.open(filepath) as img:
            # Prétraitement léger pour améliorer l'OCR sur photos de formulaires
            preprocessed = img.convert("L")

            text = _ocr_with_fallback(preprocessed)
            if not text.strip():
                # Fallback sur image d'origine si le prétraitement dégrade le rendu
                text = _ocr_with_fallback(img)

        logger.info(f"OCR image réussi : {filepath.name} ({len(text)} caractères)")
        return text or ""
    except Exception as e:
        logger.error(f"Erreur OCR image {filepath.name} : {e}")
        return ""


def _ocr_with_fallback(img: Image.Image) -> str:
    """Essaie plusieurs combinaisons de langues pour éviter l'échec total de Tesseract."""
    languages = ["fra+eng", "eng+fra", "fra", "eng", None]

    for lang in languages:
        try:
            if lang:
                text = pytesseract.image_to_string(img, lang=lang)
            else:
                text = pytesseract.image_to_string(img)
            if text and text.strip():
                return text
        except Exception as e:
            logger.warning(f"OCR fallback échoué (lang={lang}): {e}")

    return ""
