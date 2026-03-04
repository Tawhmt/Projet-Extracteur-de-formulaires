*****Projet 13 — Extracteur de Formulaires*****

***Le problème que je résous
Quand on reçoit des formulaires (PDF, emails, textes mal formatés), il faut souvent copier-coller les infos dans un système. C'est long, répétitif et ça génère des erreurs.
Mon projet va automatiser cette extraction pour gagner du temps et éviter les oublis ou erreurs.

***Choix techniques et justifications

*Python : facile à utiliser pour manipuler des fichiers et du texte. 
*PyPDF2 / pdfplumber : pour lire le contenu des PDFs textuels. 
*Regex + Groq (LLaMA 3) : Regex pour les patterns fiables, IA pour les champs complexes
*JSON / JSON Schema : pour stocker les données de façon structurée et valide, facile à 
réutiliser. 
*SQLite : Base de données locale, zéro configuration
*Logs simples : pour signaler les champs manquants ou douteux. 
*Streamlit : pour crée une interface et la visualisation  

***Ce que je ne ferai pas (scope négatif)

Pas de traitement des images ou PDFs scannés pour le MVP
Pas de correction automatique des champs manquants ou douteux
Pas de règles métier complexes (IBAN, validation de dates avancées)


***Difficultés anticipées

Certains documents peuvent être mal formatés ou contenir des informations incomplètes
L'extraction exacte des champs peut être difficile si le texte est ambigu
Vérification de la cohérence des données pour tous les types de formulaires
Gestion des fichiers multiples et suivi des documents traités

***Architecture du projet

Structure des dossiers
Projet13-Extracteur-Formulaires/
│
├── app.py                        ← Interface Streamlit
├── config.py                     ← Paramètres centralisés
├── requirements.txt              ← Dépendances pip
├── .env.example                  ← Template variables d'environnement
├── .gitignore                    ← Exclut .env, data/, __pycache__...
├── README.md                     ← Présentation du projet
├── JOURNAL.md                    ← Journal de développement
│
├── src/
│   ├── main.py                   ← Point d'entrée CLI
│   ├── normalizer.py             ← Normalisation et validation des formats
│   ├── database.py               ← Architecture BDD SQLite
│   │
│   ├── extractors/
│   │   ├── pdf_extractor.py      ← Lecture PDFs (pdfplumber + PyPDF2)
│   │   ├── email_extractor.py    ← Parsing emails .eml
│   │   └── text_extractor.py    ← Nettoyage + regex universels + Label:Valeur
│   │
│   └── rag/
│       ├── pipeline.py           ← Orchestrateur principal
│       ├── retriever.py          ← Construction des prompts Groq
│       └── vectorstore.py        ← Validation JSON Schema + sauvegarde
│
├── data/
│   ├── uploads/                  ← Documents à traiter
│   ├── processed/                ← Résultats JSON extraits
│   └── extractions.db            ← Base de données SQLite
│
└── tests/
    ├── test_extractor.py
    ├── test_pipeline.py
    └── test_normalizer.py

*Pipeline de traitement

Document entrant (PDF / Email / Texte)
            │
            ▼
    ┌─────────────────┐
    │  1. Lecture     │  pdfplumber → PyPDF2 (fallback)
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  2. Nettoyage   │  Suppression espaces, lignes vides, caractères parasites
    └────────┬────────┘
             │
             ▼
    ┌──────────────────────────────────────────┐
    │  3. Extraction Regex                     │
    │                                          │
    │  Patterns universels   Patterns Label:V  │
    │  email, tel, date  +   nom, prénom,      │
    │  montant, ref          adresse, société  │
    └────────┬─────────────────────────────────┘
             │
             ▼
    ┌─────────────────┐
    │  4. Groq LLaMA3 │  Champs complexes + texte libre
    └────────┬────────┘  (ne reçoit que les champs regex fiables en préfill)
             │
             ▼
    ┌─────────────────┐
    │  5. Fusion      │  Regex prioritaire sur champs fiables
    │  intelligente   │  Groq prioritaire sur champs complexes
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  6. Normalisa-  │  Dates → YYYY-MM-DD
    │  tion           │  Montants → float
    │                 │  Téléphones → +33XXXXXXXXX
    │                 │  Emails → minuscules
    └────────┬────────┘
             │
             ▼
    ┌─────────────────┐
    │  7. Validation  │  JSON Schema + messages d'erreur explicites
    └────────┬────────┘  ✅ Valide / 🔴 Invalide / ❌ Absent
             │
             ▼
    ┌─────────────────┐
    │  8. Sauvegarde  │  JSON dans data/processed/
    │  double         │  + entrée SQLite extractions.db
    └─────────────────┘