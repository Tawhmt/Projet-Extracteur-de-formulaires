# 📓 Journal de Développement: Extracteur de Formulaires

---

## Session 1 — Cadrage du projet et structure

**Objectif :** Définir le problème, choisir la stack technique et créer la structure du projet

**Prompt utilisé :**
> "Je veux créer un projet Python qui extrait automatiquement des données depuis des formulaires variés (PDF, emails mal formatés). La stack : pdfplumber, Groq, Streamlit, SQLite, json. Génère une structure de dossiers professionnelle pour GitHub avec src/, tests/, data/."

**Ce qui a été fait :**
- Rédaction du document de cadrage (problème, stack, scope négatif, difficultés anticipées)
- Définition de l'architecture : pipeline en 8 étapes, séparation extractors/rag
- Création de la structure des dossiers
- Choix de la stratégie regex + Groq : chaque outil là où il est le plus fiable

**Problème :** Python 3.14 incompatible avec `venv` — erreur au moment de créer l'environnement virtuel.  
**Solution :** Utilisé `virtualenv` à la place via le chemin complet `C:\Users\Asus\AppData\Roaming\Python\Python314\Scripts\virtualenv.exe`.

**Ce qui a marché :** La discussion avec l'IA pour définir la stack — elle a bien justifié pourquoi SQLite plutôt que MySQL pour un projet local, et pourquoi séparer regex et LLM.

**Ce qui a échoué :** Premier essai avec `venv` natif — pas compatible Python 3.14, perdu du temps avant de trouver la solution.

**Décision architecture — double stockage JSON + SQLite :**  
Comme vous a mentionné qu'il faut avoir une vraie BDD, j'ai pensé à un double stockage :
- **JSON dans `data/processed/`** → trace brute de chaque extraction, indépendante de la BDD. Si la BDD est corrompue ou supprimée, les données sont toujours là.
- **SQLite dans `extractions.db`** → permet de requêter, filtrer, comparer et afficher l'historique dans Streamlit.

**Apprentissage :** Toujours vérifier la compatibilité Python avant de commencer. L'architecture se réfléchit avant de coder — un bon schéma évite de tout refactoriser plus tard.

---

## Session 2 — Extracteurs PDF, Email et Regex

**Objectif :** Implémenter la lecture des documents et l'extraction des champs par regex

**Prompt utilisé :**
> "Crée pdf_extractor.py avec pdfplumber en priorité et PyPDF2 en fallback. Puis text_extractor.py avec deux types de regex : patterns universels (email, téléphone, date, montant) et patterns Label:Valeur (Nom : Martin) pour les formulaires structurés."

**Ce qui a été fait :**
- `pdf_extractor.py` : lecture PDF avec pdfplumber + fallback PyPDF2
- `email_extractor.py` : parsing des fichiers .eml
- `text_extractor.py` : nettoyage du texte + deux types de regex

**Problème 1 :** Le regex `numero_dossier` capturait le mot `"Dossier"` au lieu du code `"REF-2025-00312"`. (exemple) 
**Solution :** Refonte du pattern pour exiger un code avec tiret : `[A-Z]{2,}-[A-Z0-9]{2,}`.

**Problème 2 :** Les champs `nom`, `prénom`, `adresse`, `société` non détectés sur texte libre.  
**Solution :** Ajout d'un deuxième type de regex — patterns `Label : Valeur` qui ciblent les formulaires structurés. Pour le texte libre, le LLM prendra le relais au prochain commit.

**Ce qui a marché :** `pdfplumber` extrait parfaitement les tableaux et formulaires PDF.  
**Ce qui a échoué :** Vouloir tout détecter par regex — impossible sur le texte libre, il faut accepter les limites et passer la main à l'IA.

**Apprentissage :** Les regex sont fiables uniquement sur des formats prévisibles. La séparation en deux types de patterns (universels vs Label:Valeur) permet de couvrir les deux cas sans mélanger les responsabilités.