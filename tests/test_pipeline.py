"""
test_pipeline.py - Tests d'intégration du pipeline
"""

from src.rag.pipeline import _smart_merge, _empty_result


class TestSmartMerge:
    def test_regex_prioritaire_sur_champ_fiable(self):
        regex = {"email": "regex@test.fr", "nom": None}
        ai    = {"email": "ia@test.fr",    "nom": "Dupont"}
        result = _smart_merge(regex, ai)
        assert result["email"] == "regex@test.fr"
        assert result["nom"]   == "Dupont"

    def test_regex_comble_si_ia_vide_champ_fiable(self):
        regex = {"email": "regex@test.fr"}
        ai    = {"email": None}
        result = _smart_merge(regex, ai)
        assert result["email"] == "regex@test.fr"

    def test_groq_prioritaire_pour_numero_dossier(self):
        regex = {"numero_dossier": "REF-REGEX-001"}
        ai    = {"numero_dossier": "REF-AI-999"}
        result = _smart_merge(regex, ai)
        assert result["numero_dossier"] == "REF-AI-999"

    def test_tous_vides_retourne_none(self):
        result = _smart_merge({"email": None}, {"email": None})
        assert result["email"] is None


class TestEmptyResult:
    def test_structure_resultat_vide(self):
        result = _empty_result("test error")
        assert result["status"] == "error"
        assert result["message"] == "test error"
        assert "missing_fields" in result
        assert "fields" in result