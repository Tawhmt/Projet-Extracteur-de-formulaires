"""
test_extractor.py - Tests unitaires des extracteurs texte/email
"""

from src.extractors.email_extractor import extract_text_from_raw_email
from src.extractors.text_extractor import clean_text, regex_extract_fields


class TestTextExtractor:
	def test_clean_text_normalise_espaces_et_lignes(self):
		raw = "Nom:  Dupont   \n\n\nEmail:\tjean.dupont@test.fr  \n"
		cleaned = clean_text(raw)
		assert cleaned == "Nom: Dupont\n\nEmail: jean.dupont@test.fr"

	def test_regex_extract_fields_detecte_email_tel_et_reference(self):
		text = (
			"Nom: Dupont\n"
			"Prenom: Jean\n"
			"Email: jean.dupont@test.fr\n"
			"Telephone: 06 12 34 56 78\n"
			"Ref: REF-2025-003\n"
		)
		result = regex_extract_fields(text)

		assert result["email"] == "jean.dupont@test.fr"
		assert result["telephone"] == "06 12 34 56 78"
		assert result["numero_dossier"] == "REF-2025-003"
		assert result["nom"] == "Dupont"
		assert result["prenom"] == "Jean"

	def test_regex_extract_fields_parse_nom_libre(self):
		text = "Bonjour, je m'appelle Jean Dupont."
		result = regex_extract_fields(text)
		assert result["prenom"] == "Jean"
		assert result["nom"] == "Dupont"


class TestEmailExtractor:
	def test_extract_text_from_raw_email_supprime_lignes_vides(self):
		raw = "\nFrom: a@b.com\n\nObjet\n\nCorps du message\n"
		cleaned = extract_text_from_raw_email(raw)
		assert cleaned == "From: a@b.com\nObjet\nCorps du message"
