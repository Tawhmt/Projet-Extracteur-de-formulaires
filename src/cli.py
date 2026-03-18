"""CLI principale du projet.

Usage rapide:
    python -m src.cli extract --file fichiers/formulaire.pdf
    python -m src.cli extract --text "Nom: Dupont, email: test@example.com"
    python -m src.cli test
"""

import argparse
import json
import sys
from pathlib import Path

from src.rag.pipeline import process_document


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="extracteur-formulaires",
        description="CLI - Extracteur de formulaires",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    extract_parser = subparsers.add_parser(
        "extract", help="Lancer une extraction depuis un fichier ou du texte brut"
    )
    source_group = extract_parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument("--file", help="Chemin vers un fichier (pdf, eml, txt, image)")
    source_group.add_argument("--text", help="Texte brut a extraire")
    extract_parser.add_argument(
        "--type",
        choices=["auto", "pdf", "email", "text", "image"],
        default="auto",
        help="Type de document (defaut: auto)",
    )
    extract_parser.add_argument(
        "--pretty",
        action="store_true",
        help="Affiche le JSON avec indentation",
    )

    test_parser = subparsers.add_parser("test", help="Lancer les tests pytest")
    test_parser.add_argument(
        "--pytest-args",
        default="-q",
        help="Arguments transmis a pytest (defaut: -q)",
    )

    subparsers.add_parser("version", help="Afficher la version de la CLI")
    return parser


def _handle_extract(args: argparse.Namespace) -> int:
    source = args.file if args.file else args.text
    result = process_document(source=source, source_type=args.type)
    indent = 2 if args.pretty else None
    print(json.dumps(result, ensure_ascii=False, indent=indent))
    return 0 if result.get("status") == "ok" else 1


def _handle_test(args: argparse.Namespace) -> int:
    import shlex
    import pytest

    pytest_args = shlex.split(args.pytest_args)
    return pytest.main(pytest_args)


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "extract":
        if args.file and not Path(args.file).exists():
            print(f"Erreur: fichier introuvable -> {args.file}", file=sys.stderr)
            return 2
        return _handle_extract(args)

    if args.command == "test":
        return _handle_test(args)

    if args.command == "version":
        print("extracteur-formulaires-cli 1.0.0")
        return 0

    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
