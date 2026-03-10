"""
main.py - Point d'entrée en ligne de commande
Usage : python -m src.main --file data/uploads/mon_formulaire.pdf
        python -m src.main --text "Jean Dupont, jean@test.fr, 500€..."
"""

import argparse
import json
import logging
import sys

import config
from src.rag.pipeline import process_document

# ── Configuration des logs ────────────────────────────────────────────────────
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format=config.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("extraction.log", encoding="utf-8"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Extracteur de formulaires — Projet 13"
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--file", help="Chemin vers un fichier PDF, .eml ou .txt")
    group.add_argument("--text", help="Texte brut à analyser directement")

    parser.add_argument(
        "--type",
        choices=["auto", "pdf", "email", "text"],
        default="auto",
        help="Type de document (défaut: auto-détection)",
    )

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("  EXTRACTEUR DE FORMULAIRES — Projet 13")
    print("=" * 60)

    source = args.file if args.file else args.text
    result = process_document(source=source, source_type=args.type)

    # ── Affichage des résultats ───────────────────────────────────────────────
    print(f"\n📄 Statut : {result.get('status', 'inconnu').upper()}")
    print("\n📋 Champs extraits :")
    for field, value in result.get("fields", {}).items():
        icon = "✅" if value else "❌"
        print(f"  {icon} {field:<20} : {value or '(non trouvé)'}")

    if result.get("missing_fields"):
        print(f"\n⚠️  Champs manquants : {', '.join(result['missing_fields'])}")

    if not result.get("validation_ok", True):
        print(f"\n🔴 Erreurs de validation : {result.get('validation_errors')}")

    print(f"\n💾 Résultat JSON complet :")
    print(json.dumps(result["fields"], ensure_ascii=False, indent=2))
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()