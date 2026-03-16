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


## Session 3 — Pipeline RAG, Groq et normalisation

**Objectif :** Orchestrer le pipeline complet, intégrer Groq et normaliser les formats

**Prompt utilisé :**
> "Crée pipeline.py qui orchestre : lecture → nettoyage → regex → Groq → fusion → normalisation → validation → sauvegarde. Comment éviter que le regex envoie une mauvaise valeur à Groq et fausse l'extraction ?"

**Ce qui a été fait :**
- `pipeline.py` : orchestration des 8 étapes
- `retriever.py` : construction du prompt Groq avec stratégie de préfill sélectif
- `normalizer.py` : normalisation dates → ISO 8601, montants → float, téléphones → E.164
- `database.py` : architecture SQLite avec fonctions CRUD

**Problème majeur — prompt poisoning :**
Le regex détectait `"Dossier"` et l'envoyait à Groq en préfill → Groq faisait confiance et retournait `"Dossier"` au lieu de `"REF-2025-00312"`. C'est exactement le piège que vous avez mentionné sur la combinaison regex + LLM.

**Solution :** Séparation stricte des responsabilités — seuls les champs fiables à 100% sont préfillés à Groq, les champs complexes sont laissés entièrement à Groq sans préfill.

**Problème 2 :** Groq retournait `null` pour les emails invalides car il "savait" que c'était invalide.

**Solution :** Instruction explicite dans le prompt : extraire toujours la valeur brute même si invalide, c'est le normalizer qui valide.

**Problème 3 :** Montant `"1200 EUR"` non détecté — le regex attendait max 3 chiffres.

**Solution :** Remplacé `\d{1,3}` par `\d+` pour accepter n'importe quelle longueur.

**Ce qui a marché :** `temperature=0.0` rend Groq complètement déterministe — essentiel pour l'extraction structurée.

**Ce qui a échoué :** Vouloir que Groq fasse la validation en plus de l'extraction — il faut séparer les deux rôles.

**Apprentissage :** Le LLM extrait, le code valide — chaque composant a un rôle précis et ne doit pas empiéter sur l'autre. La combinaison regex + LLM est puissante mais dangereuse si mal orchestrée.

---

## Session 4 — Interface Streamlit et validation d'exécution

**Objectif :** Finaliser l'interface utilisateur et vérifier que l'application démarre correctement

**Prompt utilisé :**
> "Je veux une interface Streamlit claire en 3 zones : source document, résultats extraits, historique, avec un style cohérent et des logs lisibles."

**Ce qui a été fait :**
- Finalisation de `app.py` avec un dashboard en 3 zones
- Intégration des entrées multi-sources : PDF, email collé, texte libre
- Affichage des statuts champs (valide, invalide, absent) + export JSON/CSV
- Affichage de l'historique SQLite dans l'interface

**Problème 1 :** Erreur `ModuleNotFoundError: No module named 'pdfplumber'` au lancement.
**Solution :** Installation de `pdfplumber` dans l'environnement virtuel actif.

**Problème 2 :** `streamlit` absent dans le venv pendant les essais de relance.
**Solution :** Installation du package puis relance avec l'interpréteur complet du venv.

**Problème 3 :** Port déjà utilisé sur certains runs.
**Solution :** Test sur port alternatif (`8503`) pour confirmer que l'app démarre bien.

**Ce qui a marché :** L'application démarre et sert bien l'interface.
**Ce qui a échoué :** Lancement direct sans vérifier toutes les dépendances du venv avant run.

**Apprentissage :** Toujours lancer l'app avec l'interpréteur du venv explicite pour éviter les confusions d'environnement.

---

## Session 5  — OCR Intelligent et Robustesse des Données Scannées
**Objectif :** Ajouter une fonctionnalité "wow" de soutenance sans casser la base existante.

**Prompt utilisé :**
> "Ajoute le support OCR image, puis un mode dossier multi-documents avec consolidation, score et gestion des conflits."

**Ce qui a été fait :**
- Ajout de `src/extractors/image_extractor.py` (OCR via `pytesseract` + Tesseract)
- Intégration OCR dans `pipeline.py` (`source_type = image`)
- Ajout d'un onglet **Image** dans l'interface `app.py`
- Ajout d'un onglet **Dossier** (upload multiple)
- Consolidation multi-documents par champ
- Score de cohérence global + score par profil
- Détection automatique de plusieurs profils dans un batch :
	- priorité au `numero_dossier`
	- fallback sur `nom/prenom`
- Export JSON rapport global + rapport profil

**Problème 1 :** OCR renvoyait parfois vide car le binaire Tesseract n'était pas détecté dans certains contextes Python.
**Solution :** Configuration automatique du chemin Windows standard de `tesseract.exe` dans l'extracteur image.

**Problème 2 :** Le téléphone était mal lu sur OCR (ex: `O`/`0`, `I`/`1`, zéro initial manquant).
**Solution :**
- fallback regex dédié sur la ligne téléphone,
- mapping des confusions OCR,
- normalisation tolérante aux formats FR bruités (9/10 chiffres).

**Problème 3 :** Le mode dossier mélangeait deux personnes différentes dans un seul résultat consolidé.
**Solution :** Regroupement en profils séparés avant consolidation, avec sélection de profil à inspecter.

**Problème 4 :** Artefacts visuels (carrés blancs) dans la carte résultats après analyse dossier.
**Solution :** Passage à un rendu tableau compact dans le mode dossier.

**Ce qui a marché :**
- séparation correcte des profils,
- extraction OCR exploitable sur images nettes,
- score/cohérence très démonstratifs pour une soutenance.

**Ce qui a échoué :**
- première version de consolidation trop "agressive" (fusion inter-profils),
- première version UI dossier avec composants qui réservaient trop d'espace.

**Apprentissage :** Une feature impressionnante n'est pas juste visuelle : il faut aussi traçabilité, score, et gestion des conflits.

---

## Session 6 — Complétion des tests et stabilisation

**Objectif :** Compléter la suite de tests sans modifier la logique applicative existante

**Prompt utilisé :**
> "Complète les tests sans changer le code source, car pour l'instant tout marche."

**Ce qui a été fait :**
- Complétion de `tests/test_extractor.py` (nettoyage, extraction fichier texte, regex, email brut)
- Correction de `tests/test_pipeline.py` pour l'aligner avec les fonctions réellement présentes (`_smart_merge`, `_empty_result`, `process_document`)
- Ajout de `tests/test_normalizer.py` (dates, montants, téléphones, emails, agrégation des erreurs)
- Exécution de la suite via `pytest`

**Problème :** Un test supposait une priorité IA sur des champs où l'implémentation actuelle applique la priorité regex.
**Solution :** Ajustement du test pour refléter le comportement réel, sans modifier le code métier.

**Résultat :** `22 passed` (suite complète valide).

**Ce qui a marché :** Approche "adapter les tests au comportement actuel" pour sécuriser sans régression fonctionnelle.
**Ce qui a échoué :** Hypothèse initiale des tests non alignée avec la stratégie de merge réellement codée.

**Apprentissage :** Les tests doivent décrire le comportement observé du système, pas l'intention supposée.

---

## Session 7 — Finalisation GitHub et clôture

**Objectif :** Pousser les derniers éléments et vérifier la synchronisation complète avec le dépôt distant

**Prompt utilisé :**
> "aid emoi a identifier les fichier qui restnet a pusher et puis donns moi les commandes qu'il faut ."

**Ce qui a été fait :**
- Push du commit tests (`test: tests unitaires extracteurs, pipeline et normalizer`)
- Push final du dernier changement restant (`chore: update local extraction database`)
- Vérification finale : branche `main` à jour avec `origin/main`, working tree clean

**Point d'attention :** `data/extractions.db` a été versionné et poussé.
**Recommandation pour la suite :** Ajouter ce fichier au `.gitignore` si la base doit rester strictement locale (et le retirer du suivi Git ensuite).

**Apprentissage :** Avant chaque commit, vérifier `git status` pour éviter de pousser des artefacts locaux non essentiels.





**État global du projet :** MVP fonctionnel, testé et synchronisé sur GitHub.