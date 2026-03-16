# Extracteur de Formulaires

##  Le problème que je résous

Quand on reçoit des formulaires (PDF, emails, textes mal formatés), il faut souvent copier-coller les infos dans un système. C'est long, répétitif et ça génère des erreurs.  
Mon projet va automatiser cette extraction pour **gagner du temps** et **éviter les oublis ou erreurs**.

---

## Choix techniques et justifications

| Technologie | Justification |
|---|---|
| **Python** | Facile à utiliser pour manipuler des fichiers et du texte |
| **PyPDF2 / pdfplumber** | Pour lire le contenu des PDFs textuels |
| **Regex + Groq (LLaMA 3)** | Regex pour les patterns fiables, IA pour les champs complexes |
| **JSON / JSON Schema** | Pour stocker les données de façon structurée et valide |
| **SQLite** | Base de données locale, zéro configuration |
| **Logs simples** | Pour signaler les champs manquants ou douteux |
| **Streamlit** | Pour créer une interface et la visualisation |

---

## Architecture du projet

```
Extracteur-Formulaires/
│
├── 🎨 Interface (app.py)
│   └── Streamlit → Upload + Visualisation
│
├── 🧠 Pipeline (src/rag/)
│   ├── pipeline.py    → Orchestration des 8 étapes
│   ├── retriever.py   → Construction des prompts Groq
│   └── vectorstore.py → Validation JSON Schema + sauvegarde
│
├── 🔧 Extracteurs (src/extractors/)
│   ├── pdf_extractor.py   → Parsing PDFs (pdfplumber + PyPDF2)
│   ├── email_extractor.py → Parsing emails .eml
│   └── text_extractor.py  → Nettoyage + regex universels + Label:Valeur
│
├── 💾 Persistance (src/)
│   ├── database.py    → Architecture BDD SQLite
│   └── normalizer.py  → Normalisation et validation des formats
│
├── 📁 Données
│   ├── uploads/       → Fichiers input
│   ├── processed/     → Résultats JSON extraits
│   └── extractions.db → Base de données SQLite
│
├── 🧪 Tests
│   └── tests/
│
├── README.md          → Présentation du projet
├── JOURNAL.md         → Journal de développement
├── config.py          → Paramètres centralisés
├── requirements.txt   → Dépendances pip
└── .env.example       → Template variables d'environnement
```

---

##  Pipeline d'extraction (8 étapes)

```
Document Input (PDF / Email / Texte)
        ↓
1. Détection du type (PDF / Email / Texte)
        ↓
2. Parsing format spécifique
        ↓
3. Nettoyage du texte (espaces, lignes vides, caractères parasites)
        ↓
4. Extraction Regex
   ├── Patterns universels  : email, téléphone, date, montant
   └── Patterns Label:Valeur: nom, prénom, adresse, société
        ↓
5. Extraction IA (Groq LLaMA 3) → champs complexes + texte libre
        ↓
6. Fusion intelligente
   ├── Regex prioritaire sur champs fiables
   └── Groq prioritaire sur champs complexes
        ↓
7. Normalisation + Validation JSON Schema
   ├── Dates    → YYYY-MM-DD
   ├── Montants → float (2500.00)
   ├── Tél      → +33XXXXXXXXX
   └── Valide / Invalide /  Absent
        ↓
8. Stockage double
   ├── JSON dans data/processed/  (traçabilité)
   └── SQLite extractions.db      (exploitation)
```

---

## Ce que je ne ferai pas (scope négatif)
- Pas de correction automatique des champs manquants ou douteux
- Pas de règles métier complexes (IBAN, validation de dates avancées)

---

##  Difficultés anticipées

- Certains documents peuvent être mal formatés ou contenir des informations incomplètes
- L'extraction exacte des champs peut être difficile si le texte est ambigu
- Vérification de la cohérence des données pour tous les types de formulaires
- Gestion des fichiers multiples et suivi des documents traités

### Amélioration appliquées 

- Ajout de l'extraction OCR image (PNG/JPG/JPEG/BMP/TIF/TIFF) via Tesseract + `pytesseract`
- Ajout d'un extracteur dédié OCR image et intégration au pipeline principal
- Ajout de l'onglet **Image** dans l'interface Streamlit
- Renforcement de la robustesse OCR (fallback langues, prétraitement, chemin auto de `tesseract.exe`)
- Amélioration de l'extraction `telephone`/`montant` pour les textes OCR bruités
- Ajout du mode **Dossier** (analyse multi-documents)
- Consolidation multi-sources avec score de cohérence + détection de conflits
- Détection automatique de plusieurs profils/dossiers dans un même batch
- Export des rapports JSON (profil + global)
- Finitions UI du mode Dossier (tableaux compacts, suppression des blocs visuels vides)
- Ajout/complétion des tests unitaires (extracteurs, pipeline, normalizer)
- Base SQLite locale retirée du suivi Git et ignorée via `.gitignore`

---

## Mise à jour fonctionnelle (version actuelle)

Le projet inclut maintenant des fonctionnalités supplémentaires au MVP initial :

- OCR image (PNG/JPG/JPEG/BMP/TIF/TIFF) via Tesseract + `pytesseract`
- Support des documents scannés via l'onglet **Image** dans l'interface
- Mode **Dossier** (analyse multi-documents)
- Consolidation intelligente par champ avec score de cohérence
- Détection automatique de plusieurs profils/dossiers dans un même batch
- Rapport exportable JSON (global + profil)

---

## Installation rapide

### 1) Cloner et créer l'environnement

```powershell
git clone https://github.com/Tawhmt/Projet-Extracteur-de-formulaires.git
cd Projet-Extracteur-de-formulaires
python -m venv venv
venv\Scripts\Activate.ps1
```

### 2) Installer les dépendances Python

```powershell
pip install -r requirements.txt
```

### 3) Installer OCR (Windows)

- Installer Tesseract OCR (build UB Mannheim)
- Vérifier dans PowerShell :

```powershell
tesseract --version
```

### 4) Configurer les variables d'environnement

```powershell
copy .env.example .env
```

Renseigner la clé `GROQ_API_KEY` dans `.env`.

### 5) Lancer l'application

```powershell
venv\Scripts\python.exe -m streamlit run app.py
```

---

## Mode Dossier (feature "wow")

L'onglet **Dossier** permet de charger plusieurs fichiers hétérogènes d'un coup.

Le système :

1. analyse chaque document séparément,
2. regroupe automatiquement les résultats par `numero_dossier` (ou `nom/prenom` en fallback),
3. calcule un score global,
4. calcule un score par profil,
5. signale les conflits de valeurs,
6. exporte les rapports JSON.

---

## Limites connues

- Python 3.14 : warning de compatibilité côté dépendance Groq/Pydantic v1
- Streamlit : warning d'accessibilité si labels vides (`label_visibility="collapsed"`)
- OCR dépend de la qualité du scan/photo (netteté, contraste, orientation)
- Certains champs OCR peuvent nécessiter des fallbacks regex supplémentaires selon les formats

---

## Tests

Pour tester rapidement l'application, vous trouverez des formulaires PDF d'exemple dans le dossier `fichiers/`.

```powershell
venv\Scripts\python.exe -m pytest -q
```

Statut actuel : suite de tests passante.

---

## Notes Git

- `data/extractions.db` est ignoré via `.gitignore` (base locale)
- Les dossiers `data/uploads/` et `data/processed/` sont également ignorés


