"""Serveur MCP pour l'extracteur de formulaires.

Demarrage:
    python -m src.mcp_server

Ce serveur expose des outils MCP que des clients (VS Code/Copilot Desktop/Claude)
peuvent appeler pour lancer l'extraction.
"""

from pathlib import Path

from src.rag.pipeline import process_document

try:
    from mcp.server.fastmcp import FastMCP
except Exception as exc:  # pragma: no cover
    raise RuntimeError(
        "La dependance 'mcp' est requise. Installe-la avec: pip install mcp"
    ) from exc


mcp = FastMCP("extracteur-formulaires")


@mcp.tool()
def healthcheck() -> dict:
    """Retourne l'etat du serveur MCP."""
    return {"status": "ok", "server": "extracteur-formulaires"}


@mcp.tool()
def extract_from_text(text: str) -> dict:
    """Extrait les champs d'un texte brut."""
    return process_document(source=text, source_type="text")


@mcp.tool()
def extract_from_file(file_path: str, source_type: str = "auto") -> dict:
    """Extrait les champs d'un fichier local (pdf, eml, txt, image)."""
    path = Path(file_path)
    if not path.exists():
        return {
            "status": "error",
            "message": f"Fichier introuvable: {file_path}",
            "fields": {},
            "missing_fields": [],
        }
    return process_document(source=str(path), source_type=source_type)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
