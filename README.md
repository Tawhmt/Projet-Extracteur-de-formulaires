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

- Pas de traitement des images ou PDFs scannés pour le MVP
- Pas de correction automatique des champs manquants ou douteux
- Pas de règles métier complexes (IBAN, validation de dates avancées)

---

##  Difficultés anticipées

- Certains documents peuvent être mal formatés ou contenir des informations incomplètes
- L'extraction exacte des champs peut être difficile si le texte est ambigu
- Vérification de la cohérence des données pour tous les types de formulaires
- Gestion des fichiers multiples et suivi des documents traitésgit add README.md JOURNAL.md
git commit -m "docs: maj session 2"
git push


