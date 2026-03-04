"""
config.py - Paramètres centralisés du projet
"""

import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# ── Chemins ──────────────────────────────────────────────
BASE_DIR      = Path(__file__).parent
DATA_DIR      = BASE_DIR / "data"
UPLOADS_DIR   = DATA_DIR / "uploads"
PROCESSED_DIR = DATA_DIR / "processed"

# Création automatique des dossiers si absents
UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

# ── Groq ─────────────────────────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = os.getenv("GROQ_MODEL", "llama3-8b-8192")

# ── Extraction ───────────────────────────────────────────
# Champs à extraire automatiquement depuis les documents
FIELDS_TO_EXTRACT = [
    "nom",
    "prenom",
    "email",
    "telephone",
    "date",
    "adresse",
    "montant",
    "numero_dossier",
    "societe",
]

# ── Logs ─────────────────────────────────────────────────
LOG_LEVEL  = "INFO"
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s - %(message)s"