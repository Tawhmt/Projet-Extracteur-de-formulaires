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
├── app.py                  → Interface Streamlit (PDF / Email / Texte / Image / Dossier)
├── config.py               → Paramètres centralisés
├── README.md               → Documentation
├── journal.md              → Journal de développement
├── requirements.txt        → Dépendances Python
├── .env / .env.example     → Variables d'environnement
│
├── fichiers/               → Jeux de test (documents exemple)
├── docs/                   → Documentation additionnelle
├── notebooks/              → Expérimentations
│
├── data/
│   ├── uploads/            → Fichiers entrants
│   ├── processed/          → Résultats JSON extraits
│   └── extractions.db      → Base SQLite locale
│
├── src/
│   ├── cli.py              → CLI moderne (`python -m src.cli`)
│   ├── main.py             → Entrypoint CLI historique (compatibilité)
│   ├── mcp_server.py       → Serveur MCP (outils d'extraction)
│   ├── database.py         → Persistance SQLite
│   ├── normalizer.py       → Normalisation/validation des champs
│   ├── extractors/
│   │   ├── pdf_extractor.py
│   │   ├── email_extractor.py
│   │   ├── text_extractor.py
│   │   └── image_extractor.py   → OCR image (Tesseract)
│   └── rag/
│       ├── pipeline.py
│       ├── retriever.py
│       └── vectorstore.py
│
└── tests/                  → Tests unitaires (extracteurs, pipeline, normalizer)
```

---

##  Pipeline d'extraction 

```
Document Input (PDF / Email / Texte / Image  OCR / Dossier /)
        ↓
1. Détection du type de source (`auto`, `pdf`, `email`, `text`, `image`)
        ↓
2. Parsing adapté à la source
   ├── PDF        → `pdf_extractor.py`
   ├── Email      → `email_extractor.py`
   ├── Texte      → `text_extractor.py`
   └── Image OCR  → `image_extractor.py` (Tesseract)
        ↓
3. Nettoyage du texte
        ↓
4. Extraction regex
   ├── Patterns universels : email, telephone, date, montant
   └── Patterns Label:Valeur : nom, prenom, adresse, societe, numero_dossier
        ↓
5. Extraction IA (Groq LLaMA 3)
        ↓
6. Fusion intelligente
   ├── Regex prioritaire sur champs fiables
   └── IA prioritaire sur champs complexes
        ↓
7. Normalisation + validation JSON Schema
        ↓
8. Stockage
   ├── JSON dans `data/processed/`
   └── SQLite dans `data/extractions.db`

Mode Dossier (multi-documents)
        ↓
9. Consolidation inter-documents
   ├── regroupement par `numero_dossier` (ou fallback nom/prenom)
   ├── score de coherence
   ├── detection de conflits
   └── export rapports JSON (global + profils)
```

---

---

## Mise à jour fonctionnelle 

Le projet inclut maintenant des fonctionnalités supplémentaires au MVP initial :

- OCR image (PNG/JPG/JPEG/BMP/TIF/TIFF) via Tesseract + `pytesseract`
- Support des documents scannés via l'onglet **Image** dans l'interface
- Mode **Dossier** (analyse multi-documents)
- Consolidation intelligente par champ avec score de cohérence
- Détection automatique de plusieurs profils/dossiers dans un même batch
- Rapport exportable JSON (global + profil)
- CLI dédiée pour exécuter le pipeline en terminal (`src.cli`)
- Serveur MCP pour exposer les outils d'extraction à un client compatible

---
## Ce que je ne ferai pas (scope négatif)
- Pas de correction automatique des champs manquants ou douteux
- Pas de règles métier complexes (IBAN, validation de dates avancées)

---

## Quelques difficultés anticipées

- Certains documents peuvent être mal formatés ou contenir des informations incomplètes
- L'extraction exacte des champs peut être difficile si le texte est ambigu
- Vérification de la cohérence des données pour tous les types de formulaires
- Gestion des fichiers multiples et suivi des documents traités

---

## Installation rapide

### Prerequis Python

- Version recommandee: Python 3.12
- Version supportee: Python 3.11 ou 3.12
- Python 3.14 peut echouer sur certaines dependances (notamment numpy/streamlit)

### Demarrage express (Windows PowerShell)

Copier-coller ce bloc pour un lancement propre:

```powershell
git clone https://github.com/Tawhmt/Projet-Extracteur-de-formulaires.git
cd Projet-Extracteur-de-formulaires
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m pytest -q
python -m streamlit run app.py
```

### 1) Cloner et créer l'environnement

```powershell
git clone https://github.com/Tawhmt/Projet-Extracteur-de-formulaires.git
cd Projet-Extracteur-de-formulaires
py -3.12 -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Installer les dépendances Python

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Le fichier `requirements.txt` contient toutes les bibliotheques Python necessaires.

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
python -m streamlit run app.py
```

Acces local par defaut: `http://localhost:8501`.

### 6) Utiliser la CLI

La CLI permet d'executer le pipeline sans interface Streamlit.

```powershell
# Extraction depuis un fichier
python -m src.cli extract --file fichiers\formulaire_test.pdf --type auto --pretty

# Extraction depuis un texte brut
python -m src.cli extract --text "Nom: Jean Dupont, email: jean@test.fr"

# Lancer les tests via la CLI
python -m src.cli test --pytest-args "-q"
```

Compatibilite ancienne commande:

```powershell
python -m src.main extract --file fichiers\formulaire_test.pdf
```

### 7) Lancer le serveur MCP

Ce projet expose un serveur MCP (Model Context Protocol) pour permettre a un client
MCP d'appeler des outils d'extraction.

```powershell
python -m src.mcp_server
```

Outils exposes:
- `healthcheck`
- `extract_from_text(text)`
- `extract_from_file(file_path, source_type="auto")`

Exemple de configuration client MCP (stdio):

```json
{
        "mcpServers": {
                "extracteur-formulaires": {
                        "command": "C:/Users/Asus/Extracteur-Formulaires/venv/Scripts/python.exe",
                        "args": ["-m", "src.mcp_server"],
                        "cwd": "C:/Users/Asus/Extracteur-Formulaires"
                }
        }
}
```

### 8) Verification finale 

```powershell
python -m pytest -q
python -m src.cli version
python -m src.cli extract --text "Nom: Jean Dupont, email: jean@test.fr" --type text --pretty
```

Si ces commandes passent, le projet est correctement configure.

---


## Tests

Pour tester rapidement l'application, vous trouverez des formulaires PDF d'exemple dans le dossier `fichiers/`.

```powershell
python -m pytest -q
```

Si `py -3.12` n'est pas disponible, installer Python 3.12 puis recreer l'environnement virtuel.

Statut actuel : suite de tests passante.

---



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

## Limites connues

- Python 3.14 : warning de compatibilité côté dépendance Groq/Pydantic v1
- Streamlit : warning d'accessibilité si labels vides (`label_visibility="collapsed"`)
- OCR dépend de la qualité du scan/photo (netteté, contraste, orientation)
- Certains champs OCR peuvent nécessiter des fallbacks regex supplémentaires selon les formats

---

## Depannage rapide

### Erreur `No module named streamlit` ou `No module named pytest`

L'environnement virtuel n'est pas actif ou les dependances ne sont pas installees:

```powershell
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### Erreur `py -3.12` introuvable

Verifier les versions detectees:

```powershell
py -0p
```

Installer Python 3.12 puis recreer l'environnement virtuel.

### Erreur `destination path ... already exists`

Le dossier du projet est deja clone. Utiliser simplement:

```powershell
cd Projet-Extracteur-de-formulaires
```

### Erreur d'activation du venv

Commande correcte:

```powershell
.\venv\Scripts\Activate.ps1
```

Si la policy PowerShell bloque les scripts:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

### Warning Streamlit sur labels vides

Ce warning n'empeche pas l'execution de l'application.

---

## Notes Git

- `data/extractions.db` est ignoré via `.gitignore` (base locale)
- Les dossiers `data/uploads/` et `data/processed/` sont également ignorés