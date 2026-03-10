"""
retriever.py - Construction du prompt envoyé à Groq

Stratégie de combinaison regex + Groq :
- Regex est fiable pour : email, telephone, montant, date
- Groq gère : nom, prenom, adresse, societe, numero_dossier
- On ne préfill Groq QUE avec les champs regex fiables (pas les champs complexes)
"""
import json

# Champs où regex est fiable → on les communique à Groq pour confirmation
REGEX_RELIABLE_FIELDS = {"email", "telephone", "montant", "date", "nom", "prenom", "adresse", "societe"}

# Champs où Groq est meilleur → on NE préfill PAS pour éviter de polluer
GROQ_ONLY_FIELDS = {"nom", "prenom", "adresse", "societe", "numero_dossier"}


def build_prompt(text: str, regex_prefill: dict, fields: list[str]) -> str:
    """
    Construit le prompt d'extraction structurée pour Groq.
    Ne préfill que les champs regex fiables pour éviter d'empoisonner Groq.
    """
    # Seulement les champs fiables dans le préfill
    prefill_lines = []
    for field, value in regex_prefill.items():
        if value and field in REGEX_RELIABLE_FIELDS:
            prefill_lines.append(f"  - {field}: {value}")

    prefill_section = ""
    if prefill_lines:
        prefill_section = (
            "\nChamps déjà détectés avec certitude (confirme uniquement) :\n"
            + "\n".join(prefill_lines) + "\n"
        )

    fields_template = {f: None for f in fields}

    prompt = f"""Tu es un expert en extraction de données depuis des formulaires.

Le document contient des lignes "Label : Valeur". Extrais chaque valeur.

Correspondances label → champ JSON :
- "Nom"                          → "nom"        (juste le nom de famille)
- "Prénom" / "Prenom"            → "prenom"      (juste le prénom)
- "Email" / "Mail"               → "email"
- "Téléphone" / "Tel"            → "telephone"
- "Date de naissance" / "Date"   → "date"
- "Adresse"                      → "adresse"     (rue + code postal + ville)
- "Montant" / "Montant demandé"  → "montant"     (valeur numérique avec devise)
- "N° Dossier" / "Ref" / "Réf"  → "numero_dossier" (le CODE uniquement, ex: REF-2025-00312)
- "Société" / "Entreprise"       → "societe"
{prefill_section}
Document à analyser :
---
{text[:4000]}
---

Règles strictes :
1. Pour "numero_dossier" : retourne UNIQUEMENT le code de référence (ex: REF-2025-00312), jamais le mot "Dossier"
2. Pour "nom" et "prenom" : cherche aussi les formulations comme "je m\'appelle X", "c\'est X", "name is X"
3. Extrais TOUJOURS la valeur brute même si elle semble invalide :
   - Si tu vois "mon email est marcdupontgmail" → retourne "marcdupontgmail" dans "email"
   - Si tu vois "montant : 1200 EUR" → retourne "1200 EUR" dans "montant"
   - Ne filtre JAMAIS une valeur parce qu\'elle semble mal formatée
   → c\'est le système de validation qui jugera, pas toi
4. Si un champ est vraiment absent du texte → null
5. Réponds UNIQUEMENT avec le JSON ci-dessous, sans texte autour, sans backticks

{json.dumps(fields_template, ensure_ascii=False, indent=2)}
"""
    return prompt