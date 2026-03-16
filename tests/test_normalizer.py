"""Tests unitaires du module normalizer."""

from src.normalizer import (
    normalize_adresse,
    normalize_all,
    normalize_date,
    normalize_email,
    normalize_montant,
    normalize_telephone,
)


class TestNormalizeDate:
    def test_format_europeen(self):
        assert normalize_date("15/03/2026") == "2026-03-15"

    def test_format_mois_fr(self):
        assert normalize_date("15 mars 2026") == "2026-03-15"

    def test_invalide(self):
        assert normalize_date("99/99/2026").startswith("ERREUR")


class TestNormalizeMontant:
    def test_montant_fr(self):
        assert normalize_montant("1 250,50 EUR") == "1250.50"

    def test_montant_negatif(self):
        assert normalize_montant("-100 EUR").startswith("ERREUR")


class TestNormalizeTelephone:
    def test_format_local(self):
        assert normalize_telephone("06 11 22 33 44") == "+33611223344"

    def test_invalide(self):
        assert normalize_telephone("123").startswith("ERREUR")


class TestNormalizeEmail:
    def test_email_ok(self):
        assert normalize_email(" Jean.Dupont@Example.com ") == "jean.dupont@example.com"

    def test_email_invalide(self):
        assert normalize_email("jean.dupontexample.com").startswith("ERREUR")


class TestNormalizeAdresse:
    def test_adresse_nettoyee(self):
        assert normalize_adresse("  10   rue   de la paix  ") == "10 rue de la paix"


class TestNormalizeAll:
    def test_agrege_erreurs(self):
        fields = {
            "date": "99/99/2026",
            "montant": "abc",
            "telephone": "000",
            "email": "bad-mail",
            "adresse": "  10   rue   de la paix  ",
        }
        result = normalize_all(fields)

        assert result["date"] is None
        assert result["montant"] is None
        assert result["telephone"] is None
        assert result["email"] is None
        assert result["adresse"] == "10 rue de la paix"
        assert set(result["_errors"].keys()) == {"date", "montant", "telephone", "email"}
