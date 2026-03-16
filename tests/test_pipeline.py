"""Tests unitaires du pipeline RAG."""

from unittest.mock import patch

import config
from src.rag.pipeline import _empty_result, _smart_merge, process_document


class TestSmartMerge:
    def test_regex_prioritaire_sur_champs_fiables(self):
        regex = {
            "email": "regex@test.fr",
            "telephone": "0611223344",
            "montant": "1200 EUR",
            "date": "01/03/2026",
        }
        ai = {
            "email": "ia@test.fr",
            "telephone": "+33699887766",
            "montant": "999 EUR",
            "date": "2026-03-01",
        }

        result = _smart_merge(regex, ai)

        assert result["email"] == "regex@test.fr"
        assert result["telephone"] == "0611223344"
        assert result["montant"] == "1200 EUR"
        assert result["date"] == "01/03/2026"

    def test_numero_dossier_ia_prioritaire(self):
        regex = {"numero_dossier": "REF-REGEX-001"}
        ai = {"numero_dossier": "REF-IA-999"}

        result = _smart_merge(regex, ai)
        assert result["numero_dossier"] == "REF-IA-999"

    def test_nom_prenom_societe_regex_prioritaire_comme_impl(self):
        regex = {"nom": "RegexNom", "prenom": "RegexPrenom", "societe": "RegexCorp"}
        ai = {"nom": "Dupont", "prenom": "Jean", "societe": "Acme"}

        result = _smart_merge(regex, ai)
        assert result["nom"] == "RegexNom"
        assert result["prenom"] == "RegexPrenom"
        assert result["societe"] == "RegexCorp"


class TestEmptyResult:
    def test_structure_resultat_vide(self):
        result = _empty_result("test error")
        assert result["status"] == "error"
        assert result["message"] == "test error"
        assert "missing_fields" in result
        assert "fields" in result
        assert set(result["fields"].keys()) == set(config.FIELDS_TO_EXTRACT)


class TestProcessDocument:
    @patch("src.rag.pipeline._load_source", return_value="")
    def test_document_vide_retourne_erreur(self, _mock_load_source):
        result = process_document("dummy", "text")
        assert result["status"] == "error"
        assert "vide" in result["message"].lower()

    @patch("src.rag.pipeline.insert_extraction", return_value=42)
    @patch("src.rag.pipeline.validate_and_store", return_value={"status": "ok", "fields": {}})
    @patch("src.rag.pipeline.normalize_all", side_effect=lambda x: x)
    @patch("src.rag.pipeline._extract_with_groq", return_value={"nom": "Dupont"})
    @patch("src.rag.pipeline.regex_extract_fields", return_value={"email": "x@test.fr"})
    @patch("src.rag.pipeline.clean_text", side_effect=lambda x: x)
    @patch("src.rag.pipeline._load_source", return_value="texte brut")
    def test_pipeline_happy_path(
        self,
        _mock_load_source,
        _mock_clean,
        _mock_regex,
        _mock_ai,
        _mock_norm,
        _mock_validate,
        _mock_insert,
    ):
        result = process_document("dummy", "text")
        assert result["status"] == "ok"
        assert result["db_id"] == 42