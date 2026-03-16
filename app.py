import streamlit as st
import json
import pandas as pd
from pathlib import Path
import tempfile
import os
import sys
import time

sys.path.insert(0, str(Path(__file__).parent))
import config
from src.rag.pipeline import process_document
from src.database import get_all_extractions, get_stats, delete_extraction, init_db

st.set_page_config(
    page_title="Extracteur · Formulaires",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,wght@0,300;0,400;0,500;1,300&family=Playfair+Display:wght@400;500&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
    background-color: #f5f0eb !important;
    color: #3a3a4a !important;
    font-family: 'DM Sans', sans-serif !important;
}

.block-container { padding: 0 24px 24px !important; max-width: 100% !important; }
#MainMenu, footer, header { visibility: hidden; }

/* ── TOP BANNER ── */
.top-banner {
    background: linear-gradient(135deg, #b8d8e8 0%, #d4e8f0 40%, #f5c9b0 80%, #f0b8a0 100%);
    padding: 28px 36px 22px;
    margin: 0 -24px 28px;
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    position: relative;
    overflow: hidden;
}
.top-banner::before {
    content: '';
    position: absolute;
    top: -40px; right: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,255,255,0.3) 0%, transparent 70%);
    border-radius: 50%;
}
.top-banner::after {
    content: '';
    position: absolute;
    bottom: -60px; left: 30%;
    width: 300px; height: 120px;
    background: radial-gradient(ellipse, rgba(255,255,255,0.2) 0%, transparent 70%);
}
.banner-title {
    font-family: 'Playfair Display', serif;
    font-size: 2.4rem;
    color: #2a3a4a;
    font-weight: 500;
    letter-spacing: -0.5px;
    line-height: 1;
}
.banner-sub {
    font-family: 'DM Sans', sans-serif;
    font-size: 0.78rem;
    color: #4a5a6a;
    font-weight: 300;
    letter-spacing: 2px;
    text-transform: uppercase;
    margin-top: 6px;
}
.banner-stats {
    display: flex;
    gap: 20px;
    align-items: center;
}
.stat-pill {
    background: rgba(255,255,255,0.55);
    backdrop-filter: blur(8px);
    border: 1px solid rgba(255,255,255,0.7);
    padding: 8px 18px;
    border-radius: 50px;
    font-size: 0.75rem;
    color: #2a3a4a;
    font-weight: 500;
    white-space: nowrap;
}
.stat-pill b { font-size: 1.1rem; display: block; text-align: center; }

/* ── CARDS ── */
.card {
    background: #fffdf9;
    border: 1px solid #e8ddd0;
    border-radius: 16px;
    padding: 22px 22px 18px;
    box-shadow: 0 2px 16px rgba(100,120,140,0.07);
}
.card-title {
    font-family: 'Playfair Display', serif;
    font-size: 1.05rem;
    color: #2a3a4a;
    margin-bottom: 14px;
    padding-bottom: 10px;
    border-bottom: 1.5px solid #e8ddd0;
    display: flex;
    align-items: center;
    gap: 8px;
}

/* ── FIELD ROWS ── */
.field-row {
    display: flex;
    align-items: flex-start;
    gap: 10px;
    padding: 7px 10px;
    border-radius: 8px;
    margin: 3px 0;
    font-size: 0.78rem;
    transition: background 0.15s;
}
.field-row:hover { background: #f0ede8; }
.field-ok   { background: #eef7f0; }
.field-err  { background: #fdf0ee; }
.field-null { opacity: 0.5; }
.field-icon { font-size: 0.9rem; min-width: 16px; }
.field-name { min-width: 120px; font-weight: 500; color: #5a6a7a; font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.8px; }
.field-val  { color: #2a3a4a; word-break: break-all; }
.field-inv  { color: #c0604a; font-size: 0.71rem; font-style: italic; }
.field-missing { color: #aab0ba; font-style: italic; }

/* ── BUTTONS ── */
[data-testid="stButton"] button {
    background: linear-gradient(135deg, #b8d8e8, #c8e0ee) !important;
    border: none !important;
    color: #2a3a4a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    border-radius: 50px !important;
    padding: 8px 24px !important;
    letter-spacing: 0.5px !important;
    box-shadow: 0 2px 8px rgba(100,160,200,0.25) !important;
    transition: all 0.2s !important;
    width: 100% !important;
}
[data-testid="stButton"] button:hover {
    background: linear-gradient(135deg, #f5c9b0, #f0b8a0) !important;
    box-shadow: 0 4px 16px rgba(200,120,100,0.3) !important;
    transform: translateY(-1px) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    border: 2px dashed #c8d8e8 !important;
    border-radius: 12px !important;
    background: #f8fbfd !important;
}
[data-testid="stFileUploader"] * { font-family: 'DM Sans', sans-serif !important; color: #5a7a9a !important; }

/* ── TEXT AREA ── */
textarea {
    background: #f8fbfd !important;
    border: 1.5px solid #d0e0ea !important;
    border-radius: 10px !important;
    color: #2a3a4a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.8rem !important;
}
textarea:focus {
    border-color: #90c0d8 !important;
    box-shadow: 0 0 0 3px rgba(144,192,216,0.2) !important;
}

/* ── DOWNLOAD BUTTONS ── */
[data-testid="stDownloadButton"] button {
    background: #f5f0eb !important;
    border: 1.5px solid #ddd0c8 !important;
    color: #5a6a7a !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.74rem !important;
    border-radius: 50px !important;
    padding: 5px 16px !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: #e8f0f5 !important;
    border-color: #90c0d8 !important;
    color: #2a5a7a !important;
}

/* ── TABS ── */
[data-testid="stTabs"] { gap: 4px !important; }
[data-testid="stTabs"] button {
    background: transparent !important;
    border: 1.5px solid #d8dde8 !important;
    border-radius: 50px !important;
    color: #8a9aaa !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.75rem !important;
    font-weight: 500 !important;
    padding: 4px 16px !important;
    transition: all 0.2s !important;
}
[data-testid="stTabs"] button:hover {
    background: #eef5fa !important;
    border-color: #90c0d8 !important;
    color: #2a5a7a !important;
}
[data-testid="stTabs"] button[aria-selected="true"] {
    background: linear-gradient(135deg, #b8d8e8, #c8e8f0) !important;
    border-color: transparent !important;
    color: #2a3a4a !important;
}
[data-testid="stTabsContent"] { padding-top: 14px !important; }

/* ── DATAFRAME ── */
[data-testid="stDataFrame"],
[data-testid="stDataFrame"] *,
[data-testid="stDataFrame"] td,
[data-testid="stDataFrame"] th,
[data-testid="stDataFrame"] tr,
[data-testid="stDataFrame"] div,
[data-testid="stDataFrame"] span,
[data-testid="stDataFrame"] p,
.dvn-scroller * {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.75rem !important;
    color: #3a3a4a !important;
    background: #fffdf9 !important;
    border-color: #e8ddd0 !important;
}

/* ── SELECTBOX ── */
[data-testid="stSelectbox"] * {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    color: #3a3a4a !important;
}

/* ── LOGS ── */
.log-area {
    background: #f8f5f0;
    border: 1px solid #e8ddd0;
    border-radius: 12px;
    padding: 14px 16px;
    height: 160px;
    overflow-y: auto;
    font-family: 'DM Sans', monospace;
    font-size: 0.73rem;
}
.log-entry {
    padding: 3px 0;
    border-bottom: 1px solid #f0e8e0;
    display: flex;
    gap: 10px;
    align-items: baseline;
}
.log-ts   { color: #c0b0a0; min-width: 60px; font-size: 0.68rem; }
.log-ok   { color: #5aaa7a; font-weight: 500; }
.log-err  { color: #c06050; font-weight: 500; }
.log-warn { color: #d09050; font-weight: 500; }
.log-info { color: #7a9ab8; font-weight: 500; }
.log-msg  { color: #5a6a7a; }

/* ── EMPTY STATE ── */
.empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 200px;
    color: #c0b8b0;
    font-family: 'Playfair Display', serif;
    font-size: 1rem;
    font-style: italic;
    gap: 10px;
}
.empty-icon { font-size: 2.5rem; opacity: 0.4; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #f5f0eb; border-radius: 10px; }
::-webkit-scrollbar-thumb { background: #d0c8c0; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #90c0d8; }

/* ── SPINNER ── */
[data-testid="stSpinner"] * { color: #7ab0c8 !important; }
</style>
""", unsafe_allow_html=True)

# ── Init ──────────────────────────────────────────────────────────────────────
init_db()
if "logs" not in st.session_state:
    st.session_state.logs = [
        ("INFO", "Système initialisé"),
        ("INFO", f"Modèle actif : {config.GROQ_MODEL}"),
        ("INFO", f"{len(config.FIELDS_TO_EXTRACT)} champs configurés"),
        ("INFO", "En attente d'un document…"),
    ]
if "last_result" not in st.session_state:
    st.session_state.last_result = None

def add_log(level, msg):
    ts = time.strftime("%H:%M")
    st.session_state.logs.append((level, msg, ts))
    if len(st.session_state.logs) > 40:
        st.session_state.logs = st.session_state.logs[-40:]

# ─────────────────────────────────────────────────────────────────────────────
# ZONE 1 — BANNER
# ─────────────────────────────────────────────────────────────────────────────
try:
    stats = get_stats()
    total_ext = stats.get("total", 0)
    taux = stats.get("taux_completion", 0)
    complete = stats.get("success", 0)
except:
    total_ext, taux, complete = 0, 0, 0

result = st.session_state.last_result
last_label = "—"
if result:
    fields = result.get("fields", result)
    errors = result.get("_errors", {})
    found = sum(1 for f in config.FIELDS_TO_EXTRACT if fields.get(f) and f not in errors)
    last_label = f"{found} / {len(config.FIELDS_TO_EXTRACT)}"

st.markdown(f"""
<div class="top-banner">
    <div>
        <div class="banner-title">Extracteur de Formulaires</div>
        <div class="banner-sub">PDF · Email · Texte libre — propulsé par Groq LLaMA 3</div>
    </div>
    <div class="banner-stats">
        <div class="stat-pill">
            <b>{total_ext}</b>extractions
        </div>
        <div class="stat-pill">
            <b>{taux:.0f}%</b>complétion
        </div>
        <div class="stat-pill">
            <b>{last_label}</b>dernière
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# ZONE 2 — 3 CARTES
# ─────────────────────────────────────────────────────────────────────────────
col1, col2, col3 = st.columns([1, 1, 1], gap="medium")

# ── Carte 1 : Input ───────────────────────────────────────────────────────────
with col1:
    st.markdown('<div class="card"><div class="card-title">🗂 Source du document</div>', unsafe_allow_html=True)

    tab_pdf, tab_email, tab_text = st.tabs(["PDF", "Email", "Texte"])

    with tab_pdf:
        uploaded = st.file_uploader("", type=["pdf"], label_visibility="collapsed")
        if st.button("Extraire les données →", key="go_pdf"):
            if uploaded:
                with st.spinner("Analyse en cours…"):
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                        tmp.write(uploaded.read())
                        tmp_path = tmp.name
                    try:
                        add_log("INFO", f"Lecture PDF : {uploaded.name}")
                        result = process_document(tmp_path, "pdf")
                        st.session_state.last_result = result
                        fields = result.get("fields", result)
                        found = sum(1 for f in config.FIELDS_TO_EXTRACT if fields.get(f))
                        add_log("OK", f"{found}/{len(config.FIELDS_TO_EXTRACT)} champs extraits")
                    except Exception as e:
                        add_log("ERR", str(e))
                    finally:
                        os.unlink(tmp_path)
                st.rerun()
            else:
                add_log("WARN", "Aucun fichier sélectionné")

    with tab_email:
        email_text = st.text_area("", height=130, placeholder="Coller le contenu de l'email ici…", label_visibility="collapsed", key="email_inp")
        if st.button("Extraire les données →", key="go_email"):
            if email_text.strip():
                with st.spinner("Analyse en cours…"):
                    try:
                        add_log("INFO", "Lecture email…")
                        result = process_document(email_text, "text")
                        st.session_state.last_result = result
                        add_log("OK", "Extraction email terminée")
                    except Exception as e:
                        add_log("ERR", str(e))
                st.rerun()
            else:
                add_log("WARN", "Aucun contenu email")

    with tab_text:
        free_text = st.text_area("", height=130, placeholder="Nom : Dupont\nPrénom : Jean…", label_visibility="collapsed", key="text_inp")
        if st.button("Extraire les données →", key="go_text"):
            if free_text.strip():
                with st.spinner("Analyse en cours…"):
                    try:
                        add_log("INFO", "Lecture texte libre…")
                        result = process_document(free_text, "text")
                        st.session_state.last_result = result
                        add_log("OK", "Extraction texte terminée")
                    except Exception as e:
                        add_log("ERR", str(e))
                st.rerun()
            else:
                add_log("WARN", "Aucun contenu texte")

    st.markdown('</div>', unsafe_allow_html=True)


# ── Carte 2 : Résultats ───────────────────────────────────────────────────────
with col2:
    st.markdown('<div class="card"><div class="card-title">✦ Champs extraits</div>', unsafe_allow_html=True)

    result = st.session_state.last_result
    if result:
        fields = result.get("fields", result)
        errors = result.get("_errors", {})
        found  = sum(1 for f in config.FIELDS_TO_EXTRACT if fields.get(f) and f not in errors)
        inv    = len(errors)
        miss   = len(config.FIELDS_TO_EXTRACT) - found - inv

        st.markdown(f"""
        <div style="display:flex;gap:10px;margin-bottom:12px;flex-wrap:wrap;">
            <span style="background:#eef7f0;color:#3a8a5a;border-radius:50px;
                         padding:3px 12px;font-size:0.72rem;font-weight:500;">
                ✓ {found} valides
            </span>
            <span style="background:#fdf0ee;color:#c06050;border-radius:50px;
                         padding:3px 12px;font-size:0.72rem;font-weight:500;">
                ✗ {inv} invalides
            </span>
            <span style="background:#f5f2ee;color:#9a9080;border-radius:50px;
                         padding:3px 12px;font-size:0.72rem;font-weight:500;">
                ○ {miss} absents
            </span>
        </div>
        """, unsafe_allow_html=True)

        for field in config.FIELDS_TO_EXTRACT:
            val = fields.get(field)
            if field in errors:
                row_cls = "field-row field-err"
                icon = "✗"
                val_html = f'<span class="field-inv">{errors[field].replace("ERREUR: ","")}</span>'
            elif val:
                row_cls = "field-row field-ok"
                icon = "✓"
                val_html = f'<span class="field-val">{val}</span>'
            else:
                row_cls = "field-row field-null"
                icon = "○"
                val_html = '<span class="field-missing">non trouvé</span>'

            st.markdown(f"""
            <div class="{row_cls}">
                <span class="field-icon">{icon}</span>
                <span class="field-name">{field}</span>
                {val_html}
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br/>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.download_button("⬇ JSON", data=json.dumps(fields, ensure_ascii=False, indent=2),
                               file_name="extraction.json", mime="application/json")
        with c2:
            st.download_button("⬇ CSV", data=pd.DataFrame([fields]).to_csv(index=False),
                               file_name="extraction.csv", mime="text/csv")
    else:
        st.markdown("""
        <div class="empty-state">
            <span class="empty-icon">🌊</span>
            <span>En attente d'un document…</span>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ── Carte 3 : Historique ──────────────────────────────────────────────────────
with col3:
    st.markdown('<div class="card"><div class="card-title">📋 Historique</div>', unsafe_allow_html=True)

    try:
        rows = get_all_extractions()
        if rows:
            df = pd.DataFrame(rows)
            cols_ok = [c for c in ["id","source_fichier","nom","email","statut","created_at"] if c in df.columns]
            df_show = df[cols_ok].copy() if cols_ok else df.copy()

            # Table HTML pour contrôler les couleurs
            headers_html = "".join([
                f'<th style="padding:5px 10px;font-size:0.68rem;color:#8a9aaa;font-weight:500;text-align:left;border-bottom:2px solid #e8ddd0;letter-spacing:0.8px;">{c.upper()}</th>'
                for c in df_show.columns
            ])
            rows_html = ""
            for _, row in df_show.head(8).iterrows():
                cells = "".join([
                    f'<td style="padding:5px 10px;border-bottom:1px solid #f0e8e0;font-size:0.72rem;color:#3a3a4a;max-width:100px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{str(v) if v else "—"}</td>'
                    for v in row.values
                ])
                rows_html += f"<tr>{cells}</tr>"

            st.markdown(
                f'<div style="overflow-x:auto;margin-bottom:12px;"><table style="width:100%;border-collapse:collapse;background:#fffdf9;"><thead><tr>{headers_html}</tr></thead><tbody>{rows_html}</tbody></table></div>',
                unsafe_allow_html=True
            )

            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇ Tout exporter", data=df.to_csv(index=False),
                                   file_name="historique.csv", mime="text/csv")
            with c2:
                if "id" in df.columns:
                    options = {
                        f"#{r['id']} — {r.get('nom','?')} {r.get('prenom','')}".strip(): r['id']
                        for _, r in df.iterrows()
                    }
                    chosen = st.selectbox("Supprimer :", list(options.keys()))
                    if st.button("🗑 Supprimer", key="btn_del"):
                        delete_extraction(options[chosen])
                        add_log("WARN", f"Supprimé : {chosen}")
                        st.rerun()
        else:
            st.markdown('<div class="empty-state"><span class="empty-icon">🌿</span><span>Aucune extraction enregistrée</span></div>', unsafe_allow_html=True)
    except Exception as e:
        st.markdown(f'<div style="color:#c06050;font-size:0.78rem;padding:10px;">Erreur BDD : {e}</div>', unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# ZONE 3 — LOGS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown('<div style="margin-top:16px;">', unsafe_allow_html=True)
st.markdown("""
<div style="font-family:'Playfair Display',serif;font-size:0.9rem;
            color:#8a9aaa;margin-bottom:8px;letter-spacing:1px;">
    Journal d'activité
</div>
""", unsafe_allow_html=True)

level_map = {
    "OK":   ("log-ok",   "✓"),
    "ERR":  ("log-err",  "✗"),
    "WARN": ("log-warn", "⚠"),
    "INFO": ("log-info", "·"),
}
log_html = ""
for entry in reversed(st.session_state.logs[-20:]):
    level = entry[0]; msg = entry[1]
    ts = entry[2] if len(entry) > 2 else ""
    cls, icon = level_map.get(level, ("log-info", "·"))
    log_html += f'<div class="log-entry"><span class="log-ts">{ts}</span><span class="{cls}">{icon} {level}</span><span class="log-msg">{msg}</span></div>'

st.markdown(f'<div class="log-area">{log_html}</div></div>', unsafe_allow_html=True)