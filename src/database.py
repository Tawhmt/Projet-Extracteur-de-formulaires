"""
database.py - Architecture BDD SQLite
Gère la création, l'insertion et la consultation des extractions
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

import config

logger = logging.getLogger(__name__)

DB_PATH = config.BASE_DIR / "data" / "extractions.db"


def get_connection() -> sqlite3.Connection:
    """Retourne une connexion SQLite avec support des types natifs."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # accès aux colonnes par nom
    return conn


def init_db() -> None:
    """
    Crée la base de données et les tables si elles n'existent pas.
    À appeler au démarrage de l'application.
    """
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS extractions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                source_fichier  TEXT,
                nom             TEXT,
                prenom          TEXT,
                email           TEXT,
                telephone       TEXT,
                date            TEXT,
                adresse         TEXT,
                montant         REAL,
                numero_dossier  TEXT,
                societe         TEXT,
                statut          TEXT    NOT NULL DEFAULT 'partial',
                champs_manquants TEXT,
                validation_ok   INTEGER DEFAULT 1,
                created_at      TEXT    NOT NULL
            )
        """)
        conn.commit()
    logger.info(f"Base de données initialisée : {DB_PATH}")


def insert_extraction(result: dict) -> int:
    """
    Insère une extraction dans la BDD.

    Args:
        result : dict retourné par validate_and_store (avec 'fields')

    Returns:
        id de la ligne insérée
    """
    fields  = result.get("fields", {})
    missing = result.get("missing_fields", [])

    # Montant en float pour SQLite
    montant_raw = fields.get("montant")
    try:
        montant_val = float(montant_raw) if montant_raw else None
    except (ValueError, TypeError):
        montant_val = None

    with get_connection() as conn:
        cursor = conn.execute(
            """
            INSERT INTO extractions (
                source_fichier, nom, prenom, email, telephone,
                date, adresse, montant, numero_dossier, societe,
                statut, champs_manquants, validation_ok, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(result.get("source", "")),
                fields.get("nom"),
                fields.get("prenom"),
                fields.get("email"),
                fields.get("telephone"),
                fields.get("date"),
                fields.get("adresse"),
                montant_val,
                fields.get("numero_dossier"),
                fields.get("societe"),
                result.get("status", "partial"),
                ", ".join(missing) if missing else None,
                1 if result.get("validation_ok", True) else 0,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        row_id = cursor.lastrowid

    logger.info(f"Extraction sauvegardée en BDD (id={row_id})")
    return row_id


def get_all_extractions(limit: int = 100) -> list[dict]:
    """Retourne toutes les extractions triées par date décroissante."""
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM extractions ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_extraction_by_id(extraction_id: int) -> dict | None:
    """Retourne une extraction par son id."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM extractions WHERE id = ?", (extraction_id,)
        ).fetchone()
    return dict(row) if row else None


def get_stats() -> dict:
    """Retourne des statistiques globales sur les extractions."""
    with get_connection() as conn:
        total = conn.execute("SELECT COUNT(*) FROM extractions").fetchone()[0]
        success = conn.execute(
            "SELECT COUNT(*) FROM extractions WHERE statut = 'success'"
        ).fetchone()[0]
        partial = conn.execute(
            "SELECT COUNT(*) FROM extractions WHERE statut = 'partial'"
        ).fetchone()[0]
        errors = conn.execute(
            "SELECT COUNT(*) FROM extractions WHERE statut = 'error'"
        ).fetchone()[0]

    return {
        "total": total,
        "success": success,
        "partial": partial,
        "errors": errors,
        "taux_completion": round((success / total * 100) if total else 0, 1),
    }


def delete_extraction(extraction_id: int) -> bool:
    """Supprime une extraction par son id."""
    with get_connection() as conn:
        conn.execute("DELETE FROM extractions WHERE id = ?", (extraction_id,))
        conn.commit()
    logger.info(f"Extraction supprimée (id={extraction_id})")
    return True