"""Tests unitaires des extracteurs texte/email/pdf."""

from pathlib import Path

from src.extractors.email_extractor import extract_text_from_raw_email
from src.extractors.text_extractor import clean_text, extract_text_from_file, regex_extract_fields


class TestTextExtractor:
	def test_clean_text_normalise_espaces_et_lignes(self):
		raw = "Nom:   Dupont\n\n\nPrenom:\t Jean   \n"
		cleaned = clean_text(raw)
		assert "\n\n\n" not in cleaned
		assert "  " not in cleaned
		assert "Nom: Dupont" in cleaned

	def test_extract_text_from_file_inexistant(self):
		text = extract_text_from_file("fichier_inexistant_123456.txt")
		assert text == ""

	def test_extract_text_from_file_ok(self, tmp_path: Path):
		file_path = tmp_path / "sample.txt"
		file_path.write_text("Bonjour\nNom: Dupont", encoding="utf-8")
		text = extract_text_from_file(file_path)
		assert "Bonjour" in text
		assert "Nom: Dupont" in text

	def test_regex_extract_fields_principaux(self):
		text = (
			"Nom: Dupont\n"
			"Prénom: Jean\n"
			"Email: jean.dupont@example.com\n"
			"Téléphone: 06 11 22 33 44\n"
			"Date: 15/03/2026\n"
			"Montant: 1 250,50 EUR\n"
			"N° Dossier: REF-2026-001\n"
			"Société: ACME\n"
		)
		fields = regex_extract_fields(text)
		assert fields["nom"] == "Dupont"
		assert fields["prenom"] == "Jean"
		assert fields["email"] is not None
		assert fields["telephone"] is not None
		assert fields["date"] is not None
		assert fields["montant"] is not None
		assert fields["numero_dossier"] == "REF-2026-001"
		assert fields["societe"] == "ACME"


class TestEmailExtractor:
	def test_extract_text_from_raw_email_supprime_lignes_vides(self):
		raw = "From: a@test.com\n\n\nBody line 1\n\nBody line 2\n"
		text = extract_text_from_raw_email(raw)
		assert "\n\n" not in text
		assert "From: a@test.com" in text
		assert "Body line 2" in text
