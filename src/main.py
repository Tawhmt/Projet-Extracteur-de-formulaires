"""Entrypoint CLI historique.

Conserve la compatibilite avec `python -m src.main` en deleguant
vers la nouvelle CLI `python -m src.cli`.
"""

from src.cli import main


if __name__ == "__main__":
    raise SystemExit(main())