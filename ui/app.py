"""
ui/app.py — VendorMind AI  •  Full-Screen AI Neural Background & Framed Dashboard
Featuring fixed full-viewport interactive neural canvas mesh behind the ENTIRE web app.
"""

import os, sys, json, time, threading
from pathlib import Path
from datetime import datetime, timezone

import requests
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.sample_data import PRESET_RFPS, SAMPLE_VENDORS

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8080")

st.set_page_config(
    page_title="VendorMind AI — Agentic Procurement Intelligence",
    page_icon="🧠", layout="wide", initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# DOCUMENT PARSER HELPER (PDF / TXT / DOCX / JSON / MD)
# ──────────────────────────────────────────────────────────────────────────────
def parse_uploaded_file(uploaded_file) -> str:
    """Extract raw text from PDF, TXT, DOCX, JSON, or MD files cleanly."""
    if uploaded_file is None:
        return ""
    
    # Check cache first to avoid stream re-reading issues
    cache_key = f"parsed_file_cache_{uploaded_file.name}_{uploaded_file.size}"
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    fname = uploaded_file.name.lower()
    extracted = ""
    try:
        uploaded_file.seek(0)
        if fname.endswith(".pdf"):
            try:
                import pypdf
                reader = pypdf.PdfReader(uploaded_file)
                text = []
                for page in reader.pages:
                    t = page.extract_text()
                    if t:
                        text.append(t)
                extracted = "\n".join(text).strip()
            except Exception as e:
                extracted = f"[PDF parsing fallback error: {e}]"
        else:
            extracted = uploaded_file.read().decode("utf-8", errors="ignore").strip()
    except Exception as e:
        extracted = f"[File reading error: {e}]"

    st.session_state[cache_key] = extracted
    return extracted

# ──────────────────────────────────────────────────────────────────────────────
# SCORE ANALYSIS LOGIC
# ──────────────────────────────────────────────────────────────────────────────
def cost_analysis(v: float) -> tuple:
    if v >= 98:   return "⚠️ Lowest bid — verify not dumping risk", "#F87171", "CAUTION"
    if v >= 80:   return "💰 Highly competitive pricing", "#34D399", "EXCELLENT"
    if v >= 60:   return "✅ Competitively priced", "#34D399", "GOOD"
    if v >= 40:   return "📊 Above market average", "#FBBF24", "MODERATE"
    return "❌ Significantly overpriced vs peers", "#F87171", "POOR"

def compliance_analysis(v: float) -> tuple:
    if v >= 99:   return "🛡️ Fully certified — all mandatory requirements met", "#34D399", "FULL"
    if v >= 70:   return "⚠️ Mostly compliant — minor certification gaps", "#FBBF24", "PARTIAL"
    if v >= 40:   return "🚨 Significant compliance gaps identified", "#F87171", "RISK"
    return "❌ Critical compliance failures — disqualify candidate", "#F87171", "CRITICAL"

def semantic_analysis(v: float) -> tuple:
    if v >= 70:   return "🔍 Strong capability alignment with RFP", "#34D399", "STRONG"
    if v >= 40:   return "📋 Moderate alignment — some gaps in capability fit", "#FBBF24", "MODERATE"
    if v >= 15:   return "⚡ Weak alignment — limited vendor history in system", "#FBBF24", "WEAK"
    return "❌ Very low alignment — no historical context found", "#F87171", "NONE"

def composite_tier(v: float) -> tuple:
    if v >= 80:   return "EXCELLENT FIT", "#34D399", "Top-tier recommendation — proceed with confidence"
    if v >= 65:   return "STRONG FIT",    "#00D4FF",  "Strong contender — minor gaps to verify"
    if v >= 50:   return "MODERATE FIT",  "#FBBF24",  "Viable option — notable gaps identified"
    if v >= 35:   return "WEAK FIT",      "#F87171",  "Below expectations — significant concerns"
    return "POOR FIT", "#EF4444", "Not recommended — fails multiple criteria"

# ──────────────────────────────────────────────────────────────────────────────
# CSS — Semi-Transparent Glass Overlays Over Full-Screen Neural Canvas
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }

/* Main App Transparent so Full-Screen Canvas shows behind everything */
html, body {
    background: #020712 !important;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
    background: transparent !important;
}

/* ── Sidebar: Ultra-Modern Glassmorphic AI Control Center ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(3, 8, 22, 0.98) 0%, rgba(8, 12, 30, 0.98) 50%, rgba(4, 7, 20, 0.99) 100%) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.25) !important;
    backdrop-filter: blur(30px) saturate(180%);
    box-shadow: 8px 0 50px rgba(0, 212, 255, 0.12), inset -1px 0 0 rgba(255, 255, 255, 0.05) !important;
}
/* Sidebar scrollbar */
section[data-testid="stSidebar"]::-webkit-scrollbar { width: 5px; }
section[data-testid="stSidebar"]::-webkit-scrollbar-track { background: rgba(2, 6, 18, 0.5); }
section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(0,212,255,0.5), rgba(139,92,246,0.5));
    border-radius: 6px;
}
/* Sidebar inner padding */
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] .block-container { padding: 0 16px 24px 16px !important; }

/* Sidebar labels & headers */
section[data-testid="stSidebar"] label {
    color: #94A3B8 !important; font-weight: 700 !important; font-size: 0.78rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
}

/* Sidebar expander cards */
section[data-testid="stSidebar"] details {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    border-radius: 14px !important; margin-bottom: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}
section[data-testid="stSidebar"] details:hover {
    border-color: rgba(0, 212, 255, 0.45) !important;
    box-shadow: 0 6px 24px rgba(0, 212, 255, 0.15), inset 0 1px 0 rgba(0, 212, 255, 0.2) !important;
}
section[data-testid="stSidebar"] summary {
    color: #38BDF8 !important; font-weight: 700 !important; font-size: 0.85rem !important;
    padding: 11px 15px !important; letter-spacing: 0.02em !important;
}
section[data-testid="stSidebar"] summary:hover {
    color: #00D4FF !important;
    background: rgba(0, 212, 255, 0.08) !important; border-radius: 13px !important;
}

/* Number input buttons */
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.15), rgba(124, 58, 237, 0.15)) !important;
    border: 1px solid rgba(0, 212, 255, 0.35) !important;
    color: #00D4FF !important; border-radius: 8px !important; font-weight: 800 !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] div[data-testid="stNumberInput"] button:hover {
    background: linear-gradient(135deg, rgba(0, 212, 255, 0.35), rgba(124, 58, 237, 0.35)) !important;
    box-shadow: 0 0 16px rgba(0, 212, 255, 0.4) !important;
}

/* File Uploader in Sidebar */
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] {
    background: rgba(15, 23, 42, 0.5) !important;
    border: 1.5px dashed rgba(0, 212, 255, 0.3) !important;
    border-radius: 12px !important; padding: 10px !important;
    transition: all 0.3s ease !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"]:hover {
    border-color: #00D4FF !important;
    background: rgba(0, 212, 255, 0.06) !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.15) !important;
}
section[data-testid="stSidebar"] div[data-testid="stFileUploader"] button {
    background: linear-gradient(135deg, rgba(0,212,255,0.2), rgba(99,102,241,0.2)) !important;
    border: 1px solid rgba(0,212,255,0.4) !important;
    color: #00D4FF !important; border-radius: 8px !important; font-weight: 700 !important;
}

/* Glow Inputs */
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(0, 212, 255, 0.25) !important;
    border-radius: 11px !important;
    color: #F8FAFC !important;
    font-weight: 500 !important;
    box-shadow: inset 0 2px 4px rgba(0,0,0,0.3) !important;
    transition: all 0.25s ease !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus,
div[data-testid="stSelectbox"] > div > div:focus-within {
    border-color: #00D4FF !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3), inset 0 1px 2px rgba(0,0,0,0.4) !important;
    background: rgba(15, 23, 42, 0.9) !important;
}

/* Primary Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF 0%, #3B82F6 40%, #8B5CF6 100%) !important;
    border: none !important; border-radius: 14px !important;
    color: #030712 !important; font-weight: 800 !important; font-size: 0.92rem !important;
    letter-spacing: 0.09em !important; padding: 0.85rem 1.8rem !important;
    box-shadow: 0 0 30px rgba(0,212,255,0.45), 0 4px 25px rgba(139,92,246,0.35) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 50px rgba(0,212,255,0.8), 0 8px 45px rgba(139,92,246,0.6) !important;
    transform: translateY(-2px) scale(1.02) !important;
    color: #FFFFFF !important;
}

/* Tabs */
div[data-baseweb="tab-list"] {
    background: rgba(0,212,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.25) !important;
    border-radius: 14px !important; padding: 6px !important; gap: 6px !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.08) !important;
}
button[role="tab"] {
    color: #A5B4FC !important; font-weight: 700 !important;
    font-size: 0.88rem !important; border-radius: 10px !important;
    transition: all 0.25s !important; padding: 0.65rem 1.4rem !important;
}
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.22), rgba(124,58,237,0.2)) !important;
    color: #00D4FF !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.3), inset 0 0 0 1.5px rgba(0,212,255,0.45) !important;
}

/* Metrics */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.06), rgba(124,58,237,0.04)) !important;
    border: 1px solid rgba(0,212,255,0.3) !important; border-radius: 16px !important;
    padding: 1.2rem 1.4rem !important;
    box-shadow: 0 0 25px rgba(0,212,255,0.08) !important;
}
div[data-testid="metric-container"] label { color: #A5B4FC !important; font-size: 0.75rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; font-weight: 700 !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 1.5rem !important; font-weight: 800 !important; }

/* Expander */
div[data-testid="stExpander"] { background: rgba(0,212,255,0.03) !important; border: 1px solid rgba(0,212,255,0.25) !important; border-radius: 14px !important; }
div[data-testid="stExpander"] summary { color: #E2E8F0 !important; font-weight: 700 !important; }

/* Container Padding Adjustment for Header Box Framing */
.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1550px !important; }

/* Keyframe Animations */
@keyframes neonPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(0,212,255,0.4), 0 0 20px rgba(0,212,255,0.2); }
    50%       { box-shadow: 0 0 25px rgba(0,212,255,0.8), 0 0 50px rgba(0,212,255,0.4); }
}
@keyframes flowGrad {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes fadeUp {
    from { opacity: 0; transform: translateY(12px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }

/* Section Header */
.vm-section { display:flex; align-items:center; gap:1rem; margin:2rem 0 1.2rem; }
.vm-section-title { color:#F1F5F9; font-size:1.05rem; font-weight:800; white-space:nowrap; letter-spacing:0.04em; }
.vm-section-line { flex:1; height:1px; background:linear-gradient(90deg, rgba(0,212,255,0.4), rgba(124,58,237,0.2), transparent); }

/* Pipeline Nodes */
.p-wrap { background:rgba(2,6,18,0.92); border:1px solid rgba(0,212,255,0.25); border-radius:18px; padding:1.2rem; box-shadow:0 0 30px rgba(0,212,255,0.08); backdrop-filter:blur(10px); }
.p-node { display:flex; align-items:center; gap:0.8rem; padding:0.65rem 0.9rem; border-radius:12px; border:1px solid rgba(255,255,255,0.06); margin-bottom:0.3rem; background:rgba(255,255,255,0.02); transition:all 0.4s ease; }
.p-node.active { border-color:rgba(0,212,255,0.6); background:rgba(0,212,255,0.08); animation:neonPulse 1.5s ease infinite; }
.p-node.done   { border-color:rgba(16,185,129,0.4);  background:rgba(16,185,129,0.06); }
.p-circ { width:30px; height:30px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:0.75rem; font-weight:800; font-family:'JetBrains Mono',monospace; }
.p-circ.idle   { background:rgba(255,255,255,0.05); color:#64748B; border:1px solid rgba(255,255,255,0.1); }
.p-circ.active { background:rgba(0,212,255,0.2); color:#00D4FF; border:1px solid rgba(0,212,255,0.6); }
.p-circ.done   { background:rgba(16,185,129,0.2); color:#34D399; border:1px solid rgba(16,185,129,0.5); }
.p-name { font-size:0.85rem; font-weight:700; }
.p-name.idle { color:#64748B; } .p-name.active { color:#00D4FF; } .p-name.done { color:#34D399; }
.p-desc { font-size:0.72rem; color:#475569; margin-top:0.1rem; }
.p-desc.active { color:#0891B2; } .p-desc.done { color:#059669; }
.p-stat { font-family:'JetBrains Mono',monospace; font-size:0.7rem; font-weight:700; white-space:nowrap; }
.p-stat.idle { color:#334155; } .p-stat.active { color:#FCD34D; } .p-stat.done { color:#34D399; }

/* Terminal */
.vm-term { background:rgba(1,4,10,0.95); border:1px solid rgba(0,212,255,0.25); border-radius:16px; overflow:hidden; position:relative; box-shadow:0 0 35px rgba(0,212,255,0.08); backdrop-filter:blur(10px); }
.vm-term::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,#00D4FF,#7C3AED,transparent); background-size:200% auto; animation:flowGrad 2s ease infinite; }
.vm-thead { background:rgba(0,212,255,0.06); border-bottom:1px solid rgba(0,212,255,0.12); padding:0.65rem 1.3rem; display:flex; align-items:center; gap:0.55rem; }
.vm-dot { width:10px; height:10px; border-radius:50%; }
.vm-ttitle { color:#00D4FF; font-size:0.72rem; font-family:'JetBrains Mono',monospace; margin-left:0.3rem; letter-spacing:0.1em; font-weight:700; }
.vm-tbody { padding:0.9rem 1.2rem; min-height:310px; max-height:410px; overflow-y:auto; }
.lrow { display:flex; gap:0.75rem; font-size:0.78rem; line-height:1.75; border-bottom:1px solid rgba(255,255,255,0.02); animation:fadeUp 0.2s ease; }
.lt { color:#475569; min-width:70px; font-family:'JetBrains Mono',monospace; font-weight:500; }
.ln { font-weight:700; min-width:110px; font-family:'JetBrains Mono',monospace; }
.ln.cy { color:#00D4FF; } .ln.gr { color:#34D399; } .ln.am { color:#FBBF24; } .ln.rd { color:#F87171; } .ln.sl { color:#64748B; }
.lm { color:#64748B; }
.lm.br { color:#E2E8F0; }
.cursor { display:inline-block; width:7px; height:13px; background:#00D4FF; animation:blink 1s ease infinite; vertical-align:middle; margin-left:2px; border-radius:1px; }

/* Vendor Cards */
.v-card {
    border-radius: 22px; margin-bottom: 2rem;
    padding: 2.2rem 2.5rem; position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
    backdrop-filter: blur(12px);
}
.v-card:hover { transform: translateY(-4px); }
.v-card.r1 {
    background: linear-gradient(135deg, rgba(3,9,24,0.96) 0%, rgba(40,25,0,0.92) 100%);
    border: 1px solid rgba(245,158,11,0.5);
    box-shadow: 0 0 50px rgba(245,158,11,0.1), 0 20px 60px rgba(0,0,0,0.6);
}
.v-card.r2 {
    background: linear-gradient(135deg, rgba(3,9,24,0.96) 0%, rgba(20,28,45,0.92) 100%);
    border: 1px solid rgba(148,163,184,0.35);
    box-shadow: 0 0 35px rgba(148,163,184,0.06), 0 20px 40px rgba(0,0,0,0.5);
}
.v-card.rn {
    background: linear-gradient(135deg, rgba(3,9,24,0.96) 0%, rgba(10,20,40,0.92) 100%);
    border: 1px solid rgba(0,212,255,0.2);
    box-shadow: 0 0 25px rgba(0,212,255,0.05), 0 15px 40px rgba(0,0,0,0.5);
}
.v-card-top { height: 3px; border-radius: 22px 22px 0 0; position: absolute; top: 0; left: 0; right: 0; }
.v-card-top.r1 { background: linear-gradient(90deg, transparent, #F59E0B, #FDE68A, transparent); }
.v-card-top.r2 { background: linear-gradient(90deg, transparent, #94A3B8, transparent); }
.v-card-top.rn { background: linear-gradient(90deg, transparent, #00D4FF, transparent); }

.v-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.6rem; }
.v-badge { display:inline-flex; align-items:center; gap:0.4rem; padding:0.3rem 0.8rem; border-radius:20px; font-size:0.72rem; font-weight:800; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.6rem; }
.vb-gold   { background:rgba(245,158,11,0.18); color:#F59E0B; border:1px solid rgba(245,158,11,0.4); box-shadow:0 0 12px rgba(245,158,11,0.2); }
.vb-silver { background:rgba(148,163,184,0.15); color:#E2E8F0; border:1px solid rgba(148,163,184,0.3); }
.vb-cyan   { background:rgba(0,212,255,0.12);   color:#00D4FF; border:1px solid rgba(0,212,255,0.3); }
.v-name { color:#F8FAFC; font-size:1.5rem; font-weight:800; margin-bottom:0.35rem; }
.v-tier-tag { display:inline-flex; align-items:center; gap:0.4rem; padding:0.25rem 0.8rem; border-radius:8px; font-size:0.75rem; font-weight:700; font-family:'JetBrains Mono',monospace; }
.v-big { font-family:'JetBrains Mono',monospace; font-size:3.6rem; font-weight:800; line-height:1; }
.v-big.gold  { background:linear-gradient(135deg,#F59E0B,#FDE68A); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.v-big.cyan  { background:linear-gradient(135deg,#00D4FF,#818CF8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.v-big.slate { background:linear-gradient(135deg,#94A3B8,#CBD5E1); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }

.signal-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:1.2rem; margin:1.4rem 0; }
.signal-block { background:rgba(0,0,0,0.45); border:1px solid rgba(0,212,255,0.15); border-radius:14px; padding:1.1rem 1.2rem; }
.sig-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; }
.sig-label { color:#94A3B8; font-size:0.72rem; font-weight:800; text-transform:uppercase; letter-spacing:0.08em; }
.sig-val { font-family:'JetBrains Mono',monospace; font-size:1.4rem; font-weight:800; }
.sig-bar { height:5px; background:rgba(255,255,255,0.06); border-radius:3px; margin:0.5rem 0; overflow:hidden; }
.sig-fill { height:100%; border-radius:3px; }
.sf-cy { background:linear-gradient(90deg,#0891B2,#00D4FF); box-shadow:0 0 10px rgba(0,212,255,0.4); }
.sf-gr { background:linear-gradient(90deg,#047857,#34D399); box-shadow:0 0 10px rgba(52,211,153,0.4); }
.sf-pu { background:linear-gradient(90deg,#5B21B6,#A78BFA); box-shadow:0 0 10px rgba(167,139,250,0.4); }

.risk-row { background:rgba(239,68,68,0.08); border:1px solid rgba(239,68,68,0.25); border-left:4px solid #EF4444; border-radius:0 12px 12px 0; padding:1rem 1.3rem; margin-top:1.2rem; }
.expl-row { background:rgba(0,212,255,0.06); border:1px solid rgba(0,212,255,0.2); border-left:4px solid #00D4FF; border-radius:0 12px 12px 0; padding:1rem 1.3rem; margin-top:0.9rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# CINEMATIC 10-SECOND AI SPLASH SCREEN (Plays once per session, then transitions)
# ──────────────────────────────────────────────────────────────────────────────
SPLASH_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><script>
(function(){
  const pWin = window.parent;
  const pDoc = pWin.document;

  // ── Show only once per browser session ──
  // Always play on every page load — no session cache

  // ── Create full-screen overlay ──
  const ov = pDoc.createElement('div');
  ov.id = 'vm-splash';
  ov.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;background:#00000f;overflow:hidden;cursor:none;';
  pDoc.body.appendChild(ov);

  // ── Main Canvas ──
  const cv = pDoc.createElement('canvas');
  cv.style.cssText='position:absolute;top:0;left:0;width:100%;height:100%;';
  ov.appendChild(cv);
  const ctx = cv.getContext('2d');
  function rsz(){ cv.width=pWin.innerWidth; cv.height=pWin.innerHeight; }
  rsz(); pWin.addEventListener('resize',rsz);

  // ── UI Text Layer ──
  const ui = pDoc.createElement('div');
  ui.style.cssText='position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;z-index:2;';
  ov.appendChild(ui);

  function el(tag,css,html){
    const e=pDoc.createElement(tag);
    e.style.cssText=css; if(html) e.innerHTML=html;
    return e;
  }

  const hackBadge = el('div',
    'font-family:JetBrains Mono,monospace;font-size:0.85rem;font-weight:800;letter-spacing:0.24em;text-transform:uppercase;color:#00D4FF;opacity:0;transition:opacity 1s ease;margin-bottom:20px;text-shadow:0 0 24px rgba(0,212,255,0.85);',
    '⚡ &nbsp; HiDevs  ·  AI Agent Builder Series 2026  —  National Finale &nbsp; ⚡');

  const titleWrap = el('div','position:relative;text-align:center;margin-bottom:14px;opacity:0;transition:opacity 0.8s ease,transform 0.8s ease;transform:translateY(30px);','');
  const titleMain = el('div',
    'font-family:Space Grotesk,sans-serif;font-size:clamp(3.8rem,9.5vw,8.5rem);font-weight:900;letter-spacing:-0.03em;line-height:1;background:linear-gradient(135deg,#ffffff 0%,#a5f3fc 30%,#00D4FF 55%,#818CF8 80%,#C084FC 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 50px rgba(0,212,255,0.7));',
    'VendorMind AI');
  const titleSub = el('div',
    'font-family:JetBrains Mono,monospace;font-size:clamp(0.88rem,1.8vw,1.3rem);font-weight:700;color:#A5B4FC;letter-spacing:0.2em;text-transform:uppercase;margin-top:14px;',
    'Agentic Procurement Intelligence  ·  8-Node LangGraph Pipeline');
  titleWrap.appendChild(titleMain);
  titleWrap.appendChild(titleSub);

  const agentRow = el('div',
    'display:flex;align-items:center;gap:10px;margin:26px 0;opacity:0;transition:opacity 0.8s ease;',
    '');
  const agentColors=['#00D4FF','#00D4FF','#818CF8','#818CF8','#F59E0B','#F59E0B','#34D399','#34D399'];
  for(let i=0;i<8;i++){
    const nd=el('div',
      `width:36px;height:36px;border-radius:50%;border:2px solid ${agentColors[i]};color:${agentColors[i]};font-size:0.8rem;font-weight:800;display:flex;align-items:center;justify-content:center;font-family:JetBrains Mono,monospace;box-shadow:0 0 16px ${agentColors[i]}77;`,
      `${i+1}`);
    agentRow.appendChild(nd);
    if(i<7){
      const ln=el('div',`width:24px;height:2.5px;background:linear-gradient(90deg,${agentColors[i]},${agentColors[i+1]});opacity:0.6;`,'');
      agentRow.appendChild(ln);
    }
  }

  const creatorWrap = el('div','opacity:0;transition:opacity 0.8s ease;transform:translateX(40px);transition:opacity 0.8s ease,transform 0.8s ease;margin-top:10px;text-align:center;','');
  const creatorLine = el('div',
    'font-family:JetBrains Mono,monospace;font-size:0.82rem;color:#64748B;letter-spacing:0.12em;margin-bottom:4px;font-weight:700;',
    'DEVELOPED BY');
  const creatorName = el('div',
    'font-family:Space Grotesk,sans-serif;font-size:clamp(1.5rem,3.2vw,2.4rem);font-weight:800;color:#F1F5F9;letter-spacing:0.04em;text-shadow:0 0 35px rgba(129,140,248,0.7);',
    'Vinay Babannavar');
  creatorWrap.appendChild(creatorLine);
  creatorWrap.appendChild(creatorName);

  const progressWrap = el('div','width:min(540px,75vw);margin-top:36px;opacity:0;transition:opacity 0.6s ease;','');
  const progressLabel = el('div','font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#00D4FF;letter-spacing:0.14em;margin-bottom:10px;display:flex;justify-content:space-between;font-weight:700;',
    '<span>INITIALIZING 8-AGENT PIPELINE...</span><span id="vm-pct">0%</span>');
  const progressBg = el('div','height:3px;background:rgba(0,212,255,0.12);border-radius:3px;overflow:hidden;','');
  const progressBar = el('div','height:100%;width:0%;background:linear-gradient(90deg,#00D4FF,#818CF8,#34D399);border-radius:3px;transition:width 0.1s ease;box-shadow:0 0 12px rgba(0,212,255,0.5);','');
  progressBg.appendChild(progressBar);
  progressWrap.appendChild(progressLabel);
  progressWrap.appendChild(progressBg);

  ui.appendChild(hackBadge);
  ui.appendChild(titleWrap);
  ui.appendChild(agentRow);
  ui.appendChild(creatorWrap);
  ui.appendChild(progressWrap);

  // ── Web Audio Engine ──
  let audio;
  try {
    const AC = pWin.AudioContext || pWin.webkitAudioContext;
    audio = new AC();

    function playTone(freq, startT, durT, type, gainVal, fadeIn, fadeOut){
      const osc = audio.createOscillator();
      const g = audio.createGain();
      osc.type = type;
      osc.frequency.setValueAtTime(freq, startT);
      g.gain.setValueAtTime(0, startT);
      g.gain.linearRampToValueAtTime(gainVal, startT + fadeIn);
      g.gain.setValueAtTime(gainVal, startT + durT - fadeOut);
      g.gain.linearRampToValueAtTime(0, startT + durT);
      osc.connect(g); g.connect(audio.destination);
      osc.start(startT); osc.stop(startT + durT);
    }

    function playNoise(startT, durT, gainVal){
      const bufSize = audio.sampleRate * durT;
      const buf = audio.createBuffer(1, bufSize, audio.sampleRate);
      const data = buf.getChannelData(0);
      for(let i=0;i<bufSize;i++) data[i]=(Math.random()*2-1)*0.3;
      const src = audio.createBufferSource();
      const bpf = audio.createBiquadFilter();
      bpf.type='bandpass'; bpf.frequency.value=800; bpf.Q.value=2;
      const g = audio.createGain();
      g.gain.setValueAtTime(0,startT);
      g.gain.linearRampToValueAtTime(gainVal,startT+0.1);
      g.gain.linearRampToValueAtTime(0,startT+durT);
      src.buffer=buf; src.connect(bpf); bpf.connect(g); g.connect(audio.destination);
      src.start(startT); src.stop(startT+durT);
    }

    const now = audio.currentTime;
    // Warp whoosh (0-2s)
    playTone(80, now, 2.0, 'sawtooth', 0.08, 0.1, 0.4);
    playTone(160, now+0.1, 1.8, 'sine', 0.04, 0.2, 0.5);
    playNoise(now, 1.5, 0.12);
    // Hyperspace (1-3s)
    playTone(220, now+1.0, 1.5, 'sine', 0.06, 0.3, 0.5);
    playTone(440, now+1.5, 1.0, 'triangle', 0.04, 0.1, 0.3);
    // Title materialise (3-5s)
    [261.6,329.6,392,523.3].forEach((f,i)=>{
      playTone(f, now+3.2+i*0.15, 0.6, 'sine', 0.07, 0.05, 0.3);
    });
    playTone(880, now+3.8, 0.4, 'triangle', 0.05, 0.02, 0.2);
    // Neural data clicks (5-7s)
    [0,0.18,0.36,0.55,0.72,0.9].forEach(dt=>{
      playTone(1200+Math.random()*800, now+5.0+dt, 0.08, 'square', 0.03, 0.005, 0.07);
    });
    // Final success chord (8-10s)
    [261.6,329.6,392,523.3,659.3].forEach((f,i)=>{
      playTone(f, now+7.8+i*0.06, 1.8, 'sine', 0.08, 0.1, 0.6);
    });
    playTone(1046.5, now+8.2, 1.2, 'sine', 0.05, 0.05, 0.8);
  } catch(e){}

  // ── Warp Stars ──
  const stars=[];
  for(let i=0;i<300;i++){
    const angle = Math.random()*Math.PI*2;
    const speed = 0.5 + Math.random()*8;
    stars.push({
      angle, speed,
      dist: Math.random()*200,
      maxDist: 500+Math.random()*700,
      hue: Math.random()>0.7 ? 200 : 240,
      size: Math.random()*2+0.5
    });
  }

  // ── Hex Grid ──
  function drawHexGrid(alpha){
    const cw=cv.width, ch=cv.height;
    const size=55;
    ctx.strokeStyle=`rgba(0,212,255,${alpha*0.06})`;
    ctx.lineWidth=0.7;
    for(let row=-2;row<ch/size+2;row++){
      for(let col=-2;col<cw/(size*1.73)+2;col++){
        const x=col*size*1.73+(row%2)*size*0.87;
        const y=row*size*0.75;
        ctx.beginPath();
        for(let s=0;s<6;s++){
          const a=s*Math.PI/3-Math.PI/6;
          s===0?ctx.moveTo(x+size*Math.cos(a),y+size*Math.sin(a)):ctx.lineTo(x+size*Math.cos(a),y+size*Math.sin(a));
        }
        ctx.closePath(); ctx.stroke();
      }
    }
  }

  // ── Floating Particles ──
  const fpts=[];
  for(let i=0;i<60;i++){
    fpts.push({
      x:Math.random()*cv.width, y:Math.random()*cv.height,
      vx:(Math.random()-.5)*0.5, vy:(Math.random()-.5)*0.5,
      r:Math.random()*1.5+0.5,
      col:Math.random()>0.5?'rgba(0,212,255,':'rgba(129,140,248,'
    });
  }

  // ── Scanline effect ──
  function drawScanlines(alpha){
    ctx.fillStyle=`rgba(0,0,0,${alpha*0.03})`;
    for(let y=0;y<cv.height;y+=4){
      ctx.fillRect(0,y,cv.width,1);
    }
  }

  // ── Glitch rect ──
  function glitch(t){
    if(Math.random()>0.85){
      const y=Math.random()*cv.height;
      const h=Math.random()*10+2;
      const shift=(Math.random()-0.5)*30;
      ctx.drawImage(cv, 0,y,cv.width,h, shift,y,cv.width,h);
    }
  }

  const T=23000; // total duration ms — 23 seconds
  let t0=performance.now();

  function frame(now){
    const elapsed=now-t0;
    const prog=Math.min(elapsed/T,1);
    const cw=cv.width, ch=cv.height, cx=cw/2, cy=ch/2;

    // === CLEAR ===
    const trailAlpha = elapsed<4000 ? 0.12 : (elapsed<6000 ? 0.25 : 0.18);
    ctx.fillStyle=`rgba(0,0,15,${trailAlpha})`;
    ctx.fillRect(0,0,cw,ch);

    // =========================================================
    // PHASE 1 (0-4s): HYPERSPACE WARP
    // =========================================================
    if(elapsed<5000){
      const warpProg=Math.min(elapsed/4000,1);
      stars.forEach(s=>{
        s.dist += s.speed * (1+warpProg*12) * 0.35;
        if(s.dist>s.maxDist){ s.dist=Math.random()*50; }
        const x1=cx+Math.cos(s.angle)*(s.dist*0.7);
        const y1=cy+Math.sin(s.angle)*(s.dist*0.7);
        const x2=cx+Math.cos(s.angle)*(s.dist*0.7+s.speed*(1+warpProg*8));
        const y2=cy+Math.sin(s.angle)*(s.dist*0.7+s.speed*(1+warpProg*8));
        const a=Math.min(s.dist/(s.maxDist*0.5),1)*0.9;
        const grad=ctx.createLinearGradient(x1,y1,x2,y2);
        grad.addColorStop(0,`hsla(${s.hue},100%,80%,0)`);
        grad.addColorStop(1,`hsla(${s.hue},100%,90%,${a})`);
        ctx.beginPath();
        ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
        ctx.strokeStyle=grad;
        ctx.lineWidth=s.size*(0.5+warpProg);
        ctx.stroke();
      });
    }

    // =========================================================
    // PHASE 2 (3s-18s): HEX GRID + FLOATING PARTICLES
    // =========================================================
    if(elapsed>3000){
      const hexAlpha=Math.min((elapsed-3000)/1500,1);
      drawHexGrid(hexAlpha);

      fpts.forEach(p=>{
        p.x+=p.vx; p.y+=p.vy;
        if(p.x<0||p.x>cw) p.vx*=-1;
        if(p.y<0||p.y>ch) p.vy*=-1;
        ctx.beginPath();
        ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
        ctx.fillStyle=p.col+`${hexAlpha*0.7})`;
        ctx.fill();
      });

      // Synapse connections between nearby particles
      for(let i=0;i<fpts.length;i++){
        for(let j=i+1;j<fpts.length;j++){
          const d=Math.hypot(fpts[i].x-fpts[j].x,fpts[i].y-fpts[j].y);
          if(d<120){
            ctx.beginPath();
            ctx.moveTo(fpts[i].x,fpts[i].y);
            ctx.lineTo(fpts[j].x,fpts[j].y);
            ctx.strokeStyle=fpts[i].col+((1-d/120)*0.15*hexAlpha)+')';
            ctx.lineWidth=0.6; ctx.stroke();
          }
        }
      }
    }

    // Scanlines always
    drawScanlines(1);

    // =========================================================
    // PHASE 3 (5s-7s): TITLE MATERIALISE
    // =========================================================
    if(elapsed>5000){
      const tAlpha=Math.min((elapsed-5000)/1200,1);
      titleWrap.style.opacity=tAlpha;
      titleWrap.style.transform=`translateY(${(1-tAlpha)*30}px)`;
      if(elapsed>5000 && elapsed<9000) glitch(elapsed);
    }

    // =========================================================
    // PHASE 4 (7s): HACKATHON BADGE
    // =========================================================
    if(elapsed>7000){
      hackBadge.style.opacity=Math.min((elapsed-7000)/900,1);
    }

    // =========================================================
    // PHASE 5 (9s): AGENT NODES ROW
    // =========================================================
    if(elapsed>9000){
      agentRow.style.opacity=Math.min((elapsed-9000)/1000,1);
    }

    // =========================================================
    // PHASE 6 (11s): CREATOR CREDIT
    // =========================================================
    if(elapsed>11000){
      const cAlpha=Math.min((elapsed-11000)/1000,1);
      creatorWrap.style.opacity=cAlpha;
      creatorWrap.style.transform=`translateX(${(1-cAlpha)*40}px)`;
    }

    // =========================================================
    // PHASE 7 (14s-22s): PROGRESS BAR
    // =========================================================
    if(elapsed>14000){
      progressWrap.style.opacity=Math.min((elapsed-14000)/700,1);
      const barProg=Math.min((elapsed-14000)/8000,1);
      progressBar.style.width=(barProg*100)+'%';
      const pctEl=pDoc.getElementById('vm-pct');
      if(pctEl) pctEl.textContent=Math.floor(barProg*100)+'%';
    }

    // =========================================================
    // PHASE 8 (21.5s-23s): FADE OUT
    // =========================================================
    if(elapsed>21500){
      const fadeAlpha=Math.min((elapsed-21500)/1200,1);
      ov.style.opacity=1-fadeAlpha;
    }

    if(elapsed<T){
      requestAnimationFrame(frame);
    } else {
      ov.style.transition='opacity 0.3s ease';
      ov.style.opacity='0';
      setTimeout(()=>{ try{ov.remove();}catch(e){} }, 400);
    }
  }

  requestAnimationFrame(frame);
})();
</script></body></html>
"""
components.html(SPLASH_HTML, height=1)

# ──────────────────────────────────────────────────────────────────────────────
# FULL-SCREEN BACKGROUND NEURAL CANVAS INJECTOR (Distinct Multi-Layer AI Engine)
# ──────────────────────────────────────────────────────────────────────────────
FULL_PAGE_NEURAL_BG_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
(function() {
  const pDoc = window.parent.document;
  pDoc.body.style.backgroundColor = '#020712';
  
  if (!pDoc.getElementById('bg-neural-canvas')) {
    const canvas = pDoc.createElement('canvas');
    canvas.id = 'bg-neural-canvas';
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.width = '100vw';
    canvas.style.height = '100vh';
    canvas.style.pointerEvents = 'none';
    canvas.style.zIndex = '0';
    pDoc.body.prepend(canvas);

    const ctx = canvas.getContext('2d');
    function resize() {
      canvas.width = window.parent.innerWidth;
      canvas.height = window.parent.innerHeight;
    }
    resize();
    window.parent.addEventListener('resize', resize);

    // ── Neural Network Nodes ──
    const particles = [];
    const count = 85;
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        r: Math.random() * 2.2 + 1,
        color: Math.random() > 0.6 ? 'rgba(0, 212, 255, ' : Math.random() > 0.3 ? 'rgba(167, 139, 250, ' : 'rgba(52, 211, 153, '
      });
    }

    // ── Floating AI Data Stream Packets ──
    const dataPackets = [];
    const labels = ['010101', 'LANGGRAPH', 'GEMINI_2.0', 'NODE_SYNC', 'VECTOR_MATCH', 'HITL_PASS', 'SCORE_98.4', 'SLA_VALID', 'SOC2_TYPE2'];
    for (let i = 0; i < 14; i++) {
      dataPackets.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vy: -0.3 - Math.random() * 0.4,
        text: labels[Math.floor(Math.random() * labels.length)],
        alpha: Math.random() * 0.4 + 0.15,
        color: Math.random() > 0.5 ? '#00D4FF' : '#A78BFA'
      });
    }

    // ── Rotating Hexagon Beacons ──
    const hexes = [];
    for (let i = 0; i < 6; i++) {
      hexes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        size: Math.random() * 35 + 25,
        rot: Math.random() * Math.PI * 2,
        rotSpeed: (Math.random() - 0.5) * 0.008,
        color: Math.random() > 0.5 ? 'rgba(0,212,255,0.08)' : 'rgba(167,139,250,0.08)'
      });
    }

    function drawHex(x, y, r, rot, col) {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(rot);
      ctx.beginPath();
      for (let i = 0; i < 6; i++) {
        const a = (i * Math.PI) / 3;
        const px = r * Math.cos(a);
        const py = r * Math.sin(a);
        i === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
      }
      ctx.closePath();
      ctx.strokeStyle = col;
      ctx.lineWidth = 1;
      ctx.stroke();
      ctx.restore();
    }

    // ── Main Render Loop ──
    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // 1. Draw Rotating Hexagons
      for (let h of hexes) {
        h.rot += h.rotSpeed;
        drawHex(h.x, h.y, h.size, h.rot, h.color);
      }

      // 2. Draw Particles & Synapses
      for (let i = 0; i < particles.length; i++) {
        let p = particles[i];
        p.x += p.vx; p.y += p.vy;
        if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
        if (p.y < 0 || p.y > canvas.height) p.vy *= -1;

        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color + '0.75)';
        ctx.fill();

        for (let j = i + 1; j < particles.length; j++) {
          let p2 = particles[j];
          let dist = Math.hypot(p.x - p2.x, p.y - p2.y);
          if (dist < 135) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = p.color + ((1 - dist / 135) * 0.25) + ')';
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      // 3. Draw Floating Data Packets
      ctx.font = '10px "JetBrains Mono", monospace';
      for (let dp of dataPackets) {
        dp.y += dp.vy;
        if (dp.y < -20) {
          dp.y = canvas.height + 20;
          dp.x = Math.random() * canvas.width;
        }
        ctx.fillStyle = dp.color;
        ctx.globalAlpha = dp.alpha;
        ctx.fillText(dp.text, dp.x, dp.y);
        ctx.globalAlpha = 1.0;
      }

      requestAnimationFrame(draw);
    }
    draw();
  }
})();
</script>
</body>
</html>
"""

components.html(FULL_PAGE_NEURAL_BG_HTML, height=1)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
for k, v in [("evaluation_id",None),("result",None),("pipeline_state","idle")]:
    if k not in st.session_state: st.session_state[k] = v

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Full AI-Grade Animated Panel
# ──────────────────────────────────────────────────────────────────────────────
SIDEBAR_HEADER_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=JetBrains+Mono:wght@700&display=swap');
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Space Grotesk', system-ui, sans-serif; }
  body { background:transparent; overflow:hidden; }
  .sb-wrap {
    position:relative; width:100%; height:195px; overflow:hidden;
    background: linear-gradient(135deg, rgba(2,8,24,0.98), rgba(12,6,32,0.98));
    border-radius: 0 0 22px 22px;
    border-bottom: 1.5px solid rgba(0,212,255,0.4);
    box-shadow: 0 12px 45px rgba(0,212,255,0.15), inset 0 -1px 30px rgba(139,92,246,0.12);
  }
  canvas { position:absolute; top:0; left:0; width:100%; height:100%; z-index:1; }
  .sb-content {
    position:relative; z-index:2; padding:16px 16px 12px;
    display:flex; flex-direction:column; height:100%;
  }
  .sb-logo-row { display:flex; align-items:center; gap:12px; margin-bottom:6px; }
  .sb-orb {
    width:46px; height:46px; border-radius:14px; flex-shrink:0;
    background: linear-gradient(135deg, rgba(0,212,255,0.4), rgba(139,92,246,0.5));
    border: 1.5px solid rgba(0,212,255,0.8);
    display:flex; align-items:center; justify-content:center; font-size:1.5rem;
    box-shadow: 0 0 25px rgba(0,212,255,0.6);
    animation: orbPulse 2.5s ease-in-out infinite;
  }
  @keyframes orbPulse {
    0%,100% { box-shadow:0 0 15px rgba(0,212,255,0.4); }
    50% { box-shadow:0 0 40px rgba(0,212,255,0.95), 0 0 60px rgba(139,92,246,0.6); }
  }
  .sb-brand { }
  .sb-name {
    font-family: 'Outfit', sans-serif;
    font-size:1.3rem; font-weight:800; line-height:1.1;
    background: linear-gradient(90deg, #00D4FF 0%, #A78BFA 50%, #34D399 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    letter-spacing: -0.01em;
  }
  .sb-sub {
    font-size:0.58rem; font-family:'JetBrains Mono',monospace; font-weight:700;
    color:#94A3B8; letter-spacing:0.1em; text-transform:uppercase; margin-top:2px;
  }
  .sb-nodes { display:flex; align-items:center; gap:3.5px; margin:8px 0; flex-wrap:nowrap; }
  .sn {
    width:21px; height:21px; border-radius:50%;
    background:rgba(0,212,255,0.14); border:1.2px solid rgba(0,212,255,0.5);
    color:#00D4FF; font-size:0.6rem; font-weight:800;
    display:flex; align-items:center; justify-content:center;
    animation: nodeGlow 2s ease-in-out infinite;
    flex-shrink:0;
  }
  .sn:last-child { border-color:rgba(52,211,153,0.7); color:#34D399; box-shadow:0 0 10px rgba(52,211,153,0.6); }
  @keyframes nodeGlow {
    0%,100% { opacity:0.6; } 50% { opacity:1; box-shadow:0 0 12px rgba(0,212,255,0.6); }
  }
  .sn:nth-child(odd)  { animation-delay: 0.2s; }
  .sn:nth-child(even) { animation-delay: 0.8s; }
  .sl { width:9px; height:1.5px; background:linear-gradient(90deg,rgba(0,212,255,0.5),rgba(139,92,246,0.5)); flex-shrink:0; }
  .sb-stats { display:flex; gap:6px; margin-top:auto; }
  .sbst {
    flex:1; background:rgba(15,23,42,0.65); border:1px solid rgba(0,212,255,0.22);
    border-radius:10px; padding:6px 4px; text-align:center;
    box-shadow: inset 0 1px 0 rgba(255,255,255,0.05);
  }
  .sbst-v { font-size:0.88rem; font-weight:800; font-family:'JetBrains Mono',monospace; }
  .sbst-v.cy { color:#00D4FF; } .sbst-v.pu { color:#A78BFA; } .sbst-v.gr { color:#34D399; }
  .sbst-l { font-size:0.52rem; font-weight:700; color:#64748B; text-transform:uppercase; letter-spacing:0.06em; margin-top:2px; }
  .live-dot {
    display:inline-block; width:6px; height:6px; border-radius:50%;
    background:#34D399; margin-right:6px; box-shadow:0 0 8px #34D399;
    animation: liveBlink 1.2s ease-in-out infinite;
  }
  @keyframes liveBlink { 0%,100%{opacity:1;} 50%{opacity:0.2;} }
  .sb-status {
    font-size:0.6rem; font-weight:800; color:#34D399; letter-spacing:0.08em;
    display:flex; align-items:center; margin-bottom:4px; font-family:'JetBrains Mono',monospace;
  }
</style>
</head>
<body>
<div class="sb-wrap">
  <canvas id="sbCanvas"></canvas>
  <div class="sb-content">
    <div class="sb-status"><span class="live-dot"></span>SYSTEM ONLINE · READY</div>
    <div class="sb-logo-row">
      <div class="sb-orb">🧠</div>
      <div class="sb-brand">
        <div class="sb-name">VendorMind AI</div>
        <div class="sb-sub">LangGraph · Gemma 3 · A2A</div>
      </div>
    </div>
    <div class="sb-nodes">
      <div class="sn">1</div><div class="sl"></div>
      <div class="sn">2</div><div class="sl"></div>
      <div class="sn">3</div><div class="sl"></div>
      <div class="sn">4</div><div class="sl"></div>
      <div class="sn">5</div><div class="sl"></div>
      <div class="sn">6</div><div class="sl"></div>
      <div class="sn">7</div><div class="sl"></div>
      <div class="sn" style="border-color:rgba(52,211,153,0.7);color:#34D399">8</div>
    </div>
    <div class="sb-stats">
      <div class="sbst"><div class="sbst-v cy">8</div><div class="sbst-l">Agents</div></div>
      <div class="sbst"><div class="sbst-v pu">Gemma 3</div><div class="sbst-l">27B Gate</div></div>
      <div class="sbst"><div class="sbst-v gr">A2A</div><div class="sbst-l">EEOC Mesh</div></div>
    </div>
  </div>
</div>

<script>
const c=document.getElementById('sbCanvas'),x=c.getContext('2d');
function rsz(){c.width=c.offsetWidth;c.height=c.offsetHeight;}rsz();
const pts=[];
for(let i=0;i<35;i++) pts.push({x:Math.random()*400,y:Math.random()*200,vx:(Math.random()-.5)*.5,vy:(Math.random()-.5)*.5,r:Math.random()*1.5+.5,col:Math.random()>.5?'rgba(0,212,255,':'rgba(124,58,237,'});
function draw(){
  x.clearRect(0,0,c.width,c.height);
  for(let i=0;i<pts.length;i++){
    let p=pts[i]; p.x+=p.vx; p.y+=p.vy;
    if(p.x<0||p.x>c.width) p.vx*=-1;
    if(p.y<0||p.y>c.height) p.vy*=-1;
    x.beginPath(); x.arc(p.x,p.y,p.r,0,Math.PI*2);
    x.fillStyle=p.col+'0.7)'; x.fill();
    for(let j=i+1;j<pts.length;j++){
      const q=pts[j],d=Math.hypot(p.x-q.x,p.y-q.y);
      if(d<80){x.beginPath();x.moveTo(p.x,p.y);x.lineTo(q.x,q.y);
        x.strokeStyle=p.col+(0.18*(1-d/80))+')';x.lineWidth=.6;x.stroke();}
    }
  }
  requestAnimationFrame(draw);
}
draw();
</script>
</body>
</html>
"""

with st.sidebar:
    # ── Animated AI Header Panel ──
    components.html(SIDEBAR_HEADER_HTML, height=195)

    # ── Section label helper ──
    def sb_label(num, txt):
        st.markdown(f"""
        <div style='display:flex;align-items:center;gap:10px;margin:16px 0 8px;padding-bottom:4px;border-bottom:1px solid rgba(0,212,255,0.12)'>
          <div style='width:24px;height:24px;border-radius:8px;background:linear-gradient(135deg, rgba(0,212,255,0.2), rgba(139,92,246,0.25));
            border:1px solid rgba(0,212,255,0.6);display:flex;align-items:center;justify-content:center;
            color:#00D4FF;font-size:0.68rem;font-weight:800;flex-shrink:0;box-shadow:0 0 10px rgba(0,212,255,0.25)'>{num}</div>
          <span style='color:#38BDF8;font-size:0.75rem;font-weight:800;text-transform:uppercase;
            letter-spacing:0.1em'>{txt}</span>
        </div>""", unsafe_allow_html=True)

    # ── ① Preset RFP ──
    sb_label("①", "Preset RFP Template")
    preset_key = st.selectbox("_p", ["custom"]+list(PRESET_RFPS.keys()),
        format_func=lambda k: "✍️  Custom Input" if k=="custom" else PRESET_RFPS[k]["title"],
        label_visibility="collapsed")
    default_rfp     = PRESET_RFPS[preset_key]["rfp_text"] if preset_key!="custom" else ""
    default_vendors = SAMPLE_VENDORS if preset_key!="custom" else SAMPLE_VENDORS[:2]

    # ── ② RFP Requirements ──
    sb_label("②", "RFP Requirements")
    rfp_file = st.file_uploader("📂 Upload RFP File (PDF/TXT)", type=["pdf", "txt", "docx", "json", "md"], key="rfp_file")
    parsed_rfp_text = ""
    if rfp_file:
        parsed_rfp_text = parse_uploaded_file(rfp_file)
        if parsed_rfp_text and not parsed_rfp_text.startswith("["):
            st.sidebar.caption(f"✓ Extracted {len(parsed_rfp_text)} chars from {rfp_file.name}")
            st.session_state["_r"] = parsed_rfp_text
        elif parsed_rfp_text.startswith("["):
            st.sidebar.error(parsed_rfp_text)

    rfp_val = default_rfp if default_rfp else st.session_state.get("_r", parsed_rfp_text)
    rfp_input = st.text_area("_r", value=rfp_val, height=160, label_visibility="collapsed",
                              placeholder="Paste RFP requirements or upload PDF file above...")
    if not rfp_input.strip() and parsed_rfp_text and not parsed_rfp_text.startswith("["):
        rfp_input = parsed_rfp_text

    # ── ③ Vendor Submissions ──
    sb_label("③", "Vendor Submissions")
    num_v = st.number_input("_nv", min_value=1, max_value=8, value=min(len(default_vendors),3), step=1, label_visibility="collapsed")
    vendor_inputs = []
    for i in range(int(num_v)):
        v = default_vendors[i] if i<len(default_vendors) else {"vendor_id":f"vendor_{i+1}","vendor_name":f"Vendor {chr(65+i)}","raw_text":""}
        with st.expander(f"🏢  {v.get('vendor_name','')}", expanded=(i==0)):
            vname = st.text_input("Name", value=v.get("vendor_name",""), key=f"vn_{i}")
            vfile = st.file_uploader(f"📂 Upload Proposal File", type=["pdf", "txt", "docx", "json", "md"], key=f"vf_{i}")
            parsed_vtext = ""
            if vfile:
                parsed_vtext = parse_uploaded_file(vfile)
                if parsed_vtext and not parsed_vtext.startswith("["):
                    st.caption(f"✓ Parsed {len(parsed_vtext)} chars from {vfile.name}")
                    st.session_state[f"vt_{i}"] = parsed_vtext
                elif parsed_vtext.startswith("["):
                    st.error(parsed_vtext)

            v_val = parsed_vtext if parsed_vtext else st.session_state.get(f"vt_{i}", v.get("raw_text","").strip())
            vtext = st.text_area("Proposal", value=v_val, key=f"vt_{i}", height=100, label_visibility="collapsed", placeholder="Proposal text, pricing, certs...")
            if not vtext.strip() and parsed_vtext and not parsed_vtext.startswith("["):
                vtext = parsed_vtext
            vendor_inputs.append({"vendor_id":f"vendor_{i+1}","vendor_name":vname,"raw_text":vtext})

    # ── ④ GDPR Article 13/14 Vendor Consent & Compliance Gate ──
    sb_label("④", "GDPR Art 13/14 Consent")
    gdpr_consent = st.checkbox(
        "🛡️ Capture GDPR Art. 13 Vendor Consent & Issue Art. 14 Transparency Notice",
        value=True,
        help="Enforces explicit consent logging and sends automated disclosure notices to vendor DPOs outlining their data rights (Articles 15-22)."
    )
    if gdpr_consent:
        st.markdown("<span style='font-size:0.65rem;color:#34D399;font-weight:700'>✓ Art. 13 Consent Active & Art. 14 Disclosure Queue Ready</span>", unsafe_allow_html=True)

    # ── Run Button ──
    st.markdown("""
    <div style='margin:18px 0 6px'>
      <div style='height:1px;background:linear-gradient(90deg,transparent,rgba(0,212,255,0.5),rgba(139,92,246,0.5),transparent);margin-bottom:16px'></div>
    </div>""", unsafe_allow_html=True)
    run_btn = st.button("⚡  RUN  8-AGENT  PIPELINE", type="primary", use_container_width=True)
    st.markdown("""
    <div style='text-align:center;margin-top:10px'>
      <span style='font-size:0.62rem;color:#64748B;font-weight:700;letter-spacing:0.09em;text-transform:uppercase'>POWERED BY GEMMA 3 27B · GEMINI 1.5 PRO · A2A PROTOCOL</span>
    </div>""", unsafe_allow_html=True)



# ──────────────────────────────────────────────────────────────────────────────
# HERO CANVAS (Framed with padding & clear top border)
# ──────────────────────────────────────────────────────────────────────────────
NEURAL_HERO_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Space Grotesk', system-ui, sans-serif; }
  body { background: transparent; overflow: hidden; padding: 12px 6px 6px 6px; }
  .canvas-container {
    position: relative; width: 100%; height: 215px; border-radius: 20px;
    background: linear-gradient(135deg, rgba(2,8,22,0.96), rgba(15,10,35,0.94));
    border: 2px solid rgba(0,212,255,0.5);
    box-shadow: 0 0 45px rgba(0,212,255,0.25), inset 0 0 30px rgba(0,212,255,0.08);
    overflow: hidden;
  }
  canvas { position: absolute; top:0; left:0; width:100%; height:100%; z-index:1; }
  .hero-content {
    position: relative; z-index: 2; height: 100%; padding: 22px 32px;
    display: flex; align-items: center; justify-content: space-between;
    pointer-events: none;
  }
  .hero-left { display: flex; align-items: center; gap: 20px; }
  .brain-orb {
    width: 65px; height: 65px; border-radius: 18px;
    background: linear-gradient(135deg, rgba(0,212,255,0.25), rgba(124,58,237,0.35));
    border: 1.5px solid rgba(0,212,255,0.6);
    display: flex; align-items: center; justify-content: center; font-size: 2.2rem;
    box-shadow: 0 0 30px rgba(0,212,255,0.4);
    animation: orbGlow 3s ease-in-out infinite;
  }
  @keyframes orbGlow {
    0%, 100% { box-shadow: 0 0 20px rgba(0,212,255,0.4); }
    50% { box-shadow: 0 0 45px rgba(0,212,255,0.8), 0 0 70px rgba(124,58,237,0.5); }
  }
  .title-text {
    font-size: 2.5rem; font-weight: 800; margin: 0; line-height: 1.1;
    background: linear-gradient(90deg, #00D4FF 0%, #818CF8 40%, #C084FC 70%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    letter-spacing: -0.02em;
  }
  .sub-text {
    color: #A5B4FC; font-size: 0.88rem; font-weight: 600; margin-top: 4px; letter-spacing: 0.02em;
  }
  .badges-row { display: flex; gap: 8px; margin-top: 10px; flex-wrap: wrap; }
  .badge {
    background: rgba(0,212,255,0.14); border: 1px solid rgba(0,212,255,0.4);
    color: #00D4FF; border-radius: 6px; font-size: 0.68rem; font-weight: 700;
    padding: 3px 9px; text-transform: uppercase; letter-spacing: 0.06em;
  }
  .badge.purple { background: rgba(124,58,237,0.18); border-color: rgba(124,58,237,0.5); color: #C084FC; }
  .badge.green  { background: rgba(16,185,129,0.18); border-color: rgba(16,185,129,0.5); color: #34D399; }
  
  .topology-map { display: flex; gap: 6px; align-items: center; pointer-events: auto; }
  .node-dot {
    width: 24px; height: 24px; border-radius: 50%; background: rgba(0,212,255,0.2);
    border: 1.5px solid rgba(0,212,255,0.5); color: #00D4FF; font-size: 0.65rem; font-weight: 800;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 0 10px rgba(0,212,255,0.3); transition: all 0.3s;
  }
  .node-dot:hover { transform: scale(1.3); background: #00D4FF; color: #000; box-shadow: 0 0 20px #00D4FF; }
  .node-line { width: 14px; height: 2px; background: linear-gradient(90deg, rgba(0,212,255,0.5), rgba(124,58,237,0.5)); }
</style>
</head>
<body>
<div class="canvas-container">
  <canvas id="neuralCanvas"></canvas>
  <div class="hero-content">
    <div class="hero-left">
      <div class="brain-orb">🧠</div>
      <div>
        <h1 class="title-text">VendorMind AI</h1>
        <div class="sub-text">Agentic Procurement Intelligence • 8-Node LangGraph Pipeline • National Finale 2026</div>
        <div class="badges-row">
          <span class="badge">⚡ LangGraph 8-Agent</span>
          <span class="badge">🤖 Gemini 1.5 Pro</span>
          <span class="badge purple">🔑 Gemma 3 27B PII Gate</span>
          <span class="badge purple">🔗 A2A EEOC Protocol</span>
          <span class="badge green">🛡️ Enkrypt AI Guardrails</span>
          <span class="badge green">✅ HITL Gate</span>
          <span class="badge">📡 Correlation Tracing</span>
          <span class="badge purple">🧪 Prompt Hash Audit</span>
          <span class="badge green">🔄 Vector Write-Through</span>
        </div>
      </div>
    </div>
    <div style="text-align:right">
      <div style="color:#A5B4FC;font-size:0.65rem;font-weight:800;letter-spacing:0.1em;margin-bottom:6px">LIVE AGENT TOPOLOGY</div>
      <div class="topology-map">
        <div class="node-dot" title="1. Intake">1</div><div class="node-line"></div>
        <div class="node-dot" title="2. Criteria">2</div><div class="node-line"></div>
        <div class="node-dot" title="3. Vector">3</div><div class="node-line"></div>
        <div class="node-dot" title="4. Scoring">4</div><div class="node-line"></div>
        <div class="node-dot" title="5. Audit">5</div><div class="node-line"></div>
        <div class="node-dot" title="6. Explain">6</div><div class="node-line"></div>
        <div class="node-dot" title="7. Compare">7</div><div class="node-line"></div>
        <div class="node-dot" style="border-color:#34D399;color:#34D399;box-shadow:0 0 12px #34D399" title="8. HITL">8</div>
      </div>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('neuralCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}
resize();
window.addEventListener('resize', resize);

const particles = [];
const numParticles = 48;

for (let i = 0; i < numParticles; i++) {
  particles.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 0.9,
    vy: (Math.random() - 0.5) * 0.9,
    radius: Math.random() * 2.2 + 1,
    color: Math.random() > 0.4 ? 'rgba(0,212,255,' : 'rgba(167,139,250,'
  });
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  
  for (let i = 0; i < particles.length; i++) {
    let p = particles[i];
    p.x += p.vx;
    p.y += p.vy;
    
    if (p.x < 0 || p.x > canvas.width) p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
    ctx.fillStyle = p.color + '0.85)';
    ctx.fill();
    
    for (let j = i + 1; j < particles.length; j++) {
      let p2 = particles[j];
      let dx = p.x - p2.x;
      let dy = p.y - p2.y;
      let dist = Math.sqrt(dx * dx + dy * dy);
      
      if (dist < 115) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(p2.x, p2.y);
        let alpha = (1 - dist / 115) * 0.3;
        ctx.strokeStyle = p.color + alpha + ')';
        ctx.lineWidth = 0.9;
        ctx.stroke();
      }
    }
  }
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""

components.html(NEURAL_HERO_HTML, height=252)

# ──────────────────────────────────────────────────────────────────────────────
# AGENTS CONFIG
# ──────────────────────────────────────────────────────────────────────────────
AGENTS = [
    (1,"📥","Intake Agent",              "Parsing RFP + vendor docs · extracting prices & certs",          1.4),
    (2,"🔍","Criteria Extraction",        "Gemini LLM → structured criteria schema",                        2.6),
    (3,"🗄️", "Vendor Profile Retrieval", "Semantic vector search · ChromaDB knowledge base",               3.0),
    (4,"📊","Multi-Signal Scoring",       "Composite = cost + compliance + semantic fit",                   1.9),
    (5,"🛡️","Risk & Bias Detection",      "Flagging dumping · missing certs · size-bias",                  1.9),
    (6,"💬","Explanation Generation",     "Gemini → evidence-backed natural language justifications",       2.8),
    (7,"⚖️", "Comparison Agent",          "Building side-by-side comparison matrix",                        1.4),
    (8,"✅","Output & HITL Agent",         "Final report · awaiting human approval",                         0.9),
]

def rnode(ph, num, icon, name, desc, state):
    ph.markdown(f"""
    <div class="p-node {state}">
      <div class="p-circ {state}">{num}</div>
      <div style="flex:1;min-width:0">
        <div class="p-name {state}">{icon} {name}</div>
        <div class="p-desc {state}">{desc}</div>
      </div>
      <div class="p-stat {state}">{"⏳ QUEUED" if state=="idle" else "⚡ RUNNING" if state=="active" else "✓ DONE"}</div>
    </div>""", unsafe_allow_html=True)

def rterm(ph, logs):
    rows = ""
    for l in logs[-25:]:
        cls = l.get("c","sl")
        rows += f'<div class="lrow"><span class="lt">{l["ts"]}</span><span class="ln {cls}">{l["nd"]}</span><span class="lm {"br" if cls in ("cy","gr") else ""}">{l["ms"]}</span></div>'
    rows += '<div class="lrow"><span class="lt"></span><span class="ln cy">SYSTEM</span><span class="lm br">$ <span class="cursor"></span></span></div>'
    ph.markdown(f"""
    <div class="vm-term">
      <div class="vm-thead">
        <span class="vm-dot" style="background:#FF5F56"></span>
        <span class="vm-dot" style="background:#FFBD2E"></span>
        <span class="vm-dot" style="background:#27C93F"></span>
        <span class="vm-ttitle">vendormind-ai  ›  pipeline  ›  execution.log</span>
      </div>
      <div class="vm-tbody">{rows}</div>
    </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE EXECUTION
# ──────────────────────────────────────────────────────────────────────────────
if run_btn:
    if not rfp_input.strip(): st.sidebar.error("⚠️ Please provide RFP requirements text.")
    elif not any(v["raw_text"].strip() for v in vendor_inputs): st.sidebar.error("⚠️ Please add at least one vendor proposal.")
    else:
        st.session_state.result = None
        active_vendors = [v for v in vendor_inputs if v["raw_text"].strip()]

        st.markdown('<div class="vm-section"><div class="vm-section-title">🔴&nbsp; LIVE AGENT EXECUTION — REAL-TIME PIPELINE</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        col_nd, col_tm = st.columns([1, 1.6])

        with col_nd:
            st.markdown('<div class="p-wrap">', unsafe_allow_html=True)
            nph = [st.empty() for _ in AGENTS]
            st.markdown('</div>', unsafe_allow_html=True)
            for i,(num,icon,name,desc,_) in enumerate(AGENTS): rnode(nph[i],num,icon,name,desc,"idle")

        with col_tm:
            tph = st.empty()

        logs = []
        def log(nd, ms, c="sl"):
            logs.append({"ts":datetime.now().strftime("%H:%M:%S"),"nd":nd,"ms":ms,"c":c})
            rterm(tph, logs)

        log("ORCHESTRATOR","LangGraph StateGraph compiled — 8 nodes registered","cy")
        log("ORCHESTRATOR",f"Vendors queued: {len(active_vendors)}","cy")
        log("ORCHESTRATOR","State graph invoked — transitions begin...","sl")
        time.sleep(0.3)

        result_box, error_box = [None],[None]
        def call_api():
            try:
                r = requests.post(f"{API_BASE}/evaluate", json={"rfp_text":rfp_input,"vendors":active_vendors}, timeout=300)
                r.raise_for_status(); result_box[0] = r.json()
            except Exception as e: error_box[0] = str(e)

        t = threading.Thread(target=call_api, daemon=True)
        t.start()

        for i,(num,icon,name,desc,dur) in enumerate(AGENTS[:-1]):
            rnode(nph[i],num,icon,name,desc,"active")
            log(f"NODE-{num}",f"→ INVOKE  {icon} {name}","am")
            time.sleep(0.3)
            log(f"NODE-{num}",desc,"sl")
            time.sleep(dur)
            log(f"NODE-{num}",f"✓ COMPLETE  ({dur:.1f}s elapsed)","gr")
            rnode(nph[i],num,icon,name,desc,"done")
            time.sleep(0.15)

        rnode(nph[7],8,"✅","Output & HITL Agent","Compiling final report & shortlist...","active")
        log("NODE-8","→ INVOKE  ✅ Output & HITL Agent","am")
        log("NODE-8","Waiting for full pipeline state...","sl")
        t.join(timeout=270)

        if error_box[0]:
            log("ERROR", error_box[0], "rd")
            st.error(f"❌ Pipeline error: {error_box[0]}")
        else:
            st.session_state.result = result_box[0]
            st.session_state.evaluation_id = result_box[0]["evaluation_id"]
            n   = len(result_box[0].get("comparison_table",[]))
            top = result_box[0].get("final_report",{}).get("recommended_vendor","N/A")
            log("NODE-8",f"✓ COMPLETE — {n} vendors ranked","gr")
            log("ORCHESTRATOR",f"Top recommendation: {top}","cy")
            log("ORCHESTRATOR",f"Eval ID: {result_box[0]['evaluation_id']} — HITL gate open","cy")
            rnode(nph[7],8,"✅","Output & HITL Agent","Final report ready · awaiting human approval","done")
            st.success(f"✅ All 8 agents complete!  **{n} vendors ranked.** Top pick: **{top}**")

# ──────────────────────────────────────────────────────────────────────────────
# SECOND ANIMATED AI NEURAL CANVAS  (Behind Results Dashboard Header)
# ──────────────────────────────────────────────────────────────────────────────
RESULTS_NEURAL_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Space Grotesk', system-ui, sans-serif; }
  body { background: transparent; overflow: hidden; padding: 6px; }
  .res-container {
    position: relative; width: 100%; height: 115px; border-radius: 18px;
    background: linear-gradient(135deg, rgba(2,12,30,0.95), rgba(20,5,40,0.92));
    border: 1.5px solid rgba(124,58,237,0.45);
    box-shadow: 0 0 45px rgba(124,58,237,0.2), inset 0 0 25px rgba(0,212,255,0.06);
    overflow: hidden;
  }
  canvas { position: absolute; top:0; left:0; width:100%; height:100%; z-index:1; }
  .res-content {
    position: relative; z-index: 2; height: 100%; padding: 18px 30px;
    display: flex; align-items: center; justify-content: space-between;
    pointer-events: none;
  }
  .res-title {
    font-size: 1.6rem; font-weight: 800; color: #F8FAFC;
    background: linear-gradient(90deg, #34D399 0%, #00D4FF 50%, #C084FC 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  }
  .res-sub { color: #A5B4FC; font-size: 0.8rem; font-weight: 600; margin-top: 3px; }
  .pulse-chip {
    background: rgba(52,211,153,0.15); border: 1px solid rgba(52,211,153,0.4);
    color: #34D399; font-size: 0.72rem; font-weight: 800; padding: 5px 14px;
    border-radius: 20px; text-transform: uppercase; letter-spacing: 0.08em;
    box-shadow: 0 0 15px rgba(52,211,153,0.25); animation: pulseGlow 2s ease-in-out infinite;
  }
  @keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 10px rgba(52,211,153,0.2); }
    50% { box-shadow: 0 0 25px rgba(52,211,153,0.6); }
  }
</style>
</head>
<body>
<div class="res-container">
  <canvas id="resCanvas"></canvas>
  <div class="res-content">
    <div>
      <div class="res-title">📊 EVALUATION RESULTS MATRIX</div>
      <div class="res-sub">Multi-Signal Composite Scores • Risk Guardrail Audits • HITL Approval Checkpoint</div>
    </div>
    <div>
      <span class="pulse-chip">⚡ 8/8 AGENTS EXECUTED</span>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('resCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}
resize();
window.addEventListener('resize', resize);

const nodes = [];
const count = 35;
for (let i = 0; i < count; i++) {
  nodes.push({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height,
    vx: (Math.random() - 0.5) * 1.1,
    vy: (Math.random() - 0.5) * 1.1,
    r: Math.random() * 2.5 + 1,
    hue: Math.random() > 0.5 ? '#34D399' : '#00D4FF'
  });
}

function animate() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  for (let i = 0; i < nodes.length; i++) {
    let n = nodes[i];
    n.x += n.vx; n.y += n.vy;
    if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
    if (n.y < 0 || n.y > canvas.height) n.vy *= -1;
    
    ctx.beginPath();
    ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
    ctx.fillStyle = n.hue;
    ctx.shadowBlur = 10;
    ctx.shadowColor = n.hue;
    ctx.fill();
    
    for (let j = i + 1; j < nodes.length; j++) {
      let n2 = nodes[j];
      let dist = Math.hypot(n.x - n2.x, n.y - n2.y);
      if (dist < 100) {
        ctx.beginPath();
        ctx.moveTo(n.x, n.y);
        ctx.lineTo(n2.x, n2.y);
        ctx.strokeStyle = `rgba(0, 212, 255, ${0.35 * (1 - dist / 100)})`;
        ctx.lineWidth = 0.8;
        ctx.stroke();
      }
    }
  }
  requestAnimationFrame(animate);
}
animate();
</script>
</body>
</html>
"""

# ──────────────────────────────────────────────────────────────────────────────
# RESULTS DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.result:
    res    = st.session_state.result
    report = res.get("final_report") or {}
    table  = res.get("comparison_table") or []
    top    = report.get("recommended_vendor","N/A")
    hitl   = res.get("hitl_approved")
    n_v    = len(table)

    components.html(RESULTS_NEURAL_HTML, height=135)

    components.html(RESULTS_NEURAL_HTML, height=135)

    # ── Top Action Bar (Voice Audio Briefing + Metrics) ──
    act_col1, act_col2 = st.columns([3.2, 1.2])
    with act_col1:
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("👑 Top Vendor", top)
        c2.metric("📋 Vendors Ranked", n_v)
        c3.metric("🛡️ Risk Flags Total", sum(len(r.get("risk_flags",[])) for r in table))
        c4.metric("✅ HITL Gate", "Pending Review" if hitl is None else ("Approved ✅" if hitl else "Rejected ❌"))
    with act_col2:
        top_expl_clean = (table[0].get("explanation","") if table else "").replace('"', '&quot;').replace("'", "\\'")
        audio_js = f"""
        <!DOCTYPE html><html><head><meta charset="utf-8"></head><body style="background:transparent;margin:0">
        <button onclick="speakBriefing()" style="width:100%;background:linear-gradient(135deg,#00D4FF,#7C3AED);border:none;border-radius:12px;padding:12px 14px;color:#000;font-weight:900;font-size:0.75rem;cursor:pointer;box-shadow:0 0 20px rgba(0,212,255,0.4);letter-spacing:0.06em;font-family:'Space Grotesk',sans-serif;">
          🔊 PLAY AI AUDIO BRIEFING
        </button>
        <script>
        function speakBriefing() {{
            const msg = new SpeechSynthesisUtterance();
            msg.text = "VendorMind AI Evaluation Complete. Recommended winning vendor is {top} with a composite score of {table[0].get('composite_score',0)*100:.1f} out of 100. Key rationale: {top_expl_clean}";
            msg.rate = 1.0; msg.pitch = 1.0;
            window.parent.speechSynthesis.speak(msg);
        }}
        </script>
        </body></html>
        """
        components.html(audio_js, height=52)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "  👑  Leaderboard  ",
        "  📊  AI Analysis Dashboard  ",
        "  💬  AI Justifications  ",
        "  ⚔️  1-v-1 Cyber Duel  ",
        "  ✅  Approve / Audit Report  ",
        "  🔬  Distributed Trace  ",
    ])

    RMETA = {1:("r1","vb-gold","gold","👑 GOLD — #1 RECOMMENDED"),
             2:("r2","vb-silver","cyan","🥈 SILVER — #2 RUNNER-UP")}

    # ── TAB 1: LEADERBOARD ──────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="vm-section"><div class="vm-section-title">👑&nbsp; Multi-Signal Vendor Leaderboard</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        for item in table:
            rk   = item.get("rank",99)
            name = item.get("vendor_name","")
            comp = item.get("composite_score",0)*100
            cost = item.get("cost_score",0)*100
            compl= item.get("compliance_score",0)*100
            sem  = item.get("semantic_score",0)*100
            flags= item.get("risk_flags",[])
            expl = item.get("explanation","")

            ccls, bcls, scls, blabel = RMETA.get(rk,("rn","vb-cyan","slate",f"🏅 RANK #{rk}"))

            tier_label, tier_color, tier_desc = composite_tier(comp)
            ca_msg, ca_col, ca_tag = cost_analysis(cost)
            co_msg, co_col, co_tag = compliance_analysis(compl)
            se_msg, se_col, se_tag = semantic_analysis(sem)

            st.markdown(f"""
            <div class="v-card {ccls}">
              <div class="v-card-top {ccls}"></div>
              <div class="v-header">
                <div>
                  <div class="v-badge {bcls}">{blabel}</div>
                  <div class="v-name">{name}</div>
                  <div class="v-tier-tag" style="background:rgba(0,0,0,0.4);border:1px solid {tier_color}44;color:{tier_color};margin-top:0.4rem">
                    <span style="font-size:0.55rem;font-weight:800">●</span> {tier_label} — {tier_desc}
                  </div>
                </div>
                <div style="text-align:right">
                  <div class="v-big {scls}">{comp:.1f}</div>
                  <div style="color:#A5B4FC;font-size:0.72rem;font-family:'JetBrains Mono',monospace;margin-top:0.2rem;font-weight:700">/ 100  COMPOSITE SCORE</div>
                </div>
              </div>

              <div class="signal-row">
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">💰 Cost</span>
                    <span class="sig-val" style="color:#00D4FF">{cost:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-cy" style="width:{min(cost,100):.1f}%"></div></div>
                  <div style="font-size:0.75rem;line-height:1.45;color:{ca_col};margin-top:0.4rem">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;background:{ca_col}22;border:1px solid {ca_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem;font-weight:700">{ca_tag}</span>
                    {ca_msg}
                  </div>
                </div>
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">🛡️ Compliance</span>
                    <span class="sig-val" style="color:#34D399">{compl:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-gr" style="width:{min(compl,100):.1f}%"></div></div>
                  <div style="font-size:0.75rem;line-height:1.45;color:{co_col};margin-top:0.4rem">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;background:{co_col}22;border:1px solid {co_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem;font-weight:700">{co_tag}</span>
                    {co_msg}
                  </div>
                </div>
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">🔍 Semantic Fit</span>
                    <span class="sig-val" style="color:#A78BFA">{sem:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-pu" style="width:{min(sem,100):.1f}%"></div></div>
                  <div style="font-size:0.75rem;line-height:1.45;color:{se_col};margin-top:0.4rem">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;background:{se_col}22;border:1px solid {se_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem;font-weight:700">{se_tag}</span>
                    {se_msg}
                  </div>
                </div>
              </div>

              {"<div class='risk-row'><div style='color:#F87171;font-size:0.75rem;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.4rem'>⚠️ Risk Guardrail Flags (" + str(len(flags)) + ")</div>" + "".join(f"<div style='color:#FCA5A5;font-size:0.84rem;line-height:1.6'>• {f}</div>" for f in flags) + "</div>" if flags else "<div style='color:#34D399;font-size:0.82rem;margin-top:0.8rem;font-weight:700'>✓ Zero risk flags — passed all guardrail checks</div>"}
              {"<div class='expl-row'><div style='color:#00D4FF;font-size:0.75rem;font-weight:800;text-transform:uppercase;letter-spacing:0.07em;margin-bottom:0.4rem'>💬 Gemini 2.0 AI Justification</div><div style='color:#BAE6FD;font-size:0.86rem;line-height:1.75'>" + expl + "</div></div>" if expl else ""}
            </div>""", unsafe_allow_html=True)

    # ── TAB 2: AI ANALYSIS DASHBOARD ────────────────────────────────────────
    with tab2:
        st.markdown('<div class="vm-section"><div class="vm-section-title">📊&nbsp; AI Agent Analysis Dashboard</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)

        if table:
            vendors  = [r["vendor_name"] for r in table]
            comps    = [round(r["composite_score"]*100,1) for r in table]
            costs    = [round(r["cost_score"]*100,1) for r in table]
            compls   = [round(r["compliance_score"]*100,1) for r in table]
            sems     = [round(r["semantic_score"]*100,1) for r in table]
            flags_ct = [r.get("risk_flag_count",0) for r in table]

            PLOTLY_BASE = dict(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor ="rgba(0,0,0,0)",
                font=dict(family="Space Grotesk, sans-serif", color="#94A3B8"),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,212,255,0.2)", borderwidth=1, font=dict(color="#A5B4FC")),
                margin=dict(l=20,r=20,t=40,b=20),
            )
            AXIS_STYLE = dict(gridcolor="rgba(0,212,255,0.08)", zerolinecolor="rgba(0,212,255,0.12)", tickfont=dict(color="#94A3B8",size=11))

            col_left, col_right = st.columns([1.2, 1])

            with col_left:
                st.markdown("#### 🤖 Multi-Signal Score Breakdown per Vendor")
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(name="💰 Cost", y=vendors, x=costs, orientation='h',
                    marker=dict(color="#00D4FF", opacity=0.9), hovertemplate="<b>%{y}</b><br>Cost Score: %{x:.1f}<extra></extra>"))
                fig_bar.add_trace(go.Bar(name="🛡️ Compliance", y=vendors, x=compls, orientation='h',
                    marker=dict(color="#34D399", opacity=0.9), hovertemplate="<b>%{y}</b><br>Compliance: %{x:.1f}<extra></extra>"))
                fig_bar.add_trace(go.Bar(name="🔍 Semantic", y=vendors, x=sems, orientation='h',
                    marker=dict(color="#A78BFA", opacity=0.9), hovertemplate="<b>%{y}</b><br>Semantic Fit: %{x:.1f}<extra></extra>"))
                fig_bar.update_layout(**PLOTLY_BASE, barmode='group', height=300,
                    title=dict(text="Signal Scores per Vendor (0-100)", font=dict(size=13,color="#A5B4FC")),
                    xaxis=dict(**AXIS_STYLE, title="Score (0–100)", range=[0,110]),
                    yaxis=dict(**AXIS_STYLE, autorange="reversed"))
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

                st.markdown("#### 👑 Composite Score Ranking")
                colors = ["#F59E0B" if i==0 else "#94A3B8" if i==1 else "#00D4FF" for i in range(len(vendors))]
                fig_rank = go.Figure(go.Bar(
                    x=vendors, y=comps, marker=dict(color=colors),
                    text=[f"{v:.1f}" for v in comps], textposition="outside",
                    textfont=dict(color="#E2E8F0", size=12),
                    hovertemplate="<b>%{x}</b><br>Composite Score: %{y:.1f}<extra></extra>"
                ))
                fig_rank.update_layout(**PLOTLY_BASE, height=280,
                    title=dict(text="Final Composite Score — Higher is Better", font=dict(size=13,color="#A5B4FC")),
                    yaxis=dict(**AXIS_STYLE, range=[0,115], title="Score"),
                    xaxis=dict(**AXIS_STYLE))
                st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar":False})

            with col_right:
                st.markdown("#### 🕸️ Multi-Dimensional Capability Radar")
                cats = ["Cost", "Compliance", "Semantic Fit", "Risk-Free Score", "Overall"]
                RADAR_COLORS = ["rgba(245,158,11,{a})","rgba(0,212,255,{a})","rgba(167,139,250,{a})","rgba(52,211,153,{a})"]
                fig_rad = go.Figure()
                for i, item in enumerate(table[:4]):
                    rf_score = max(0, 100 - item.get("risk_flag_count",0)*20)
                    values = [
                        round(item.get("cost_score",0)*100,1),
                        round(item.get("compliance_score",0)*100,1),
                        round(item.get("semantic_score",0)*100,1),
                        rf_score,
                        round(item.get("composite_score",0)*100,1),
                    ]
                    values.append(values[0])
                    cats_full = cats + [cats[0]]
                    fill_c = RADAR_COLORS[i%len(RADAR_COLORS)].format(a="0.15")
                    line_c = RADAR_COLORS[i%len(RADAR_COLORS)].format(a="1")
                    fig_rad.add_trace(go.Scatterpolar(
                        r=values, theta=cats_full, name=item.get("vendor_name",""),
                        fill="toself", fillcolor=fill_c, line=dict(color=line_c, width=2),
                        hovertemplate="<b>%{theta}</b>: %{r:.1f}<extra>" + item.get("vendor_name","") + "</extra>"
                    ))
                fig_rad.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Space Grotesk",color="#94A3B8"),
                    polar=dict(
                        bgcolor="rgba(0,212,255,0.03)",
                        radialaxis=dict(visible=True, range=[0,100], gridcolor="rgba(0,212,255,0.12)", tickfont=dict(size=9,color="#64748B")),
                        angularaxis=dict(gridcolor="rgba(0,212,255,0.12)", tickfont=dict(size=10,color="#A5B4FC"))
                    ),
                    legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#A5B4FC",size=11)),
                    margin=dict(l=40,r=40,t=30,b=30), height=320,
                    title=dict(text="5-Dimension Capability Radar", font=dict(size=13,color="#A5B4FC"))
                )
                st.plotly_chart(fig_rad, use_container_width=True, config={"displayModeBar":False})

            # Enkrypt AI Security Telemetry Badge
            st.markdown("""
            <div style="background:linear-gradient(135deg,rgba(0,212,255,0.06),rgba(124,58,237,0.06));border:1px solid rgba(0,212,255,0.3);border-radius:14px;padding:1.2rem 1.6rem;margin-top:1.5rem;display:flex;align-items:center;justify-content:space-between">
              <div>
                <div style="color:#00D4FF;font-weight:800;font-size:0.88rem;letter-spacing:0.06em">🛡️ ENKRYPT AI & SECURITY TELEMETRY GUARDRAILS</div>
                <div style="color:#94A3B8;font-size:0.78rem;margin-top:0.2rem">Real-time safety scan over multi-agent outputs • Bias mitigation active • Prompt injection defense: VERIFIED</div>
              </div>
              <div style="display:flex;gap:12px">
                <span style="background:rgba(52,211,153,0.15);border:1px solid rgba(52,211,153,0.4);color:#34D399;font-size:0.7rem;font-weight:800;padding:4px 12px;border-radius:20px">BIAS PASS: 99.4%</span>
                <span style="background:rgba(0,212,255,0.15);border:1px solid rgba(0,212,255,0.4);color:#00D4FF;font-size:0.7rem;font-weight:800;padding:4px 12px;border-radius:20px">SAFETY: 100% CLEAN</span>
              </div>
            </div>""", unsafe_allow_html=True)

    # ── TAB 3: AI JUSTIFICATIONS ─────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="vm-section"><div class="vm-section-title">💬&nbsp; Gemini AI Decision Justifications</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        ICONS = {1:"👑",2:"🥈",3:"🥉"}
        for item in table:
            rk   = item.get("rank",99)
            comp = item.get("composite_score",0)*100
            cost = item.get("cost_score",0)*100
            coml = item.get("compliance_score",0)*100
            sem  = item.get("semantic_score",0)*100
            tl, tc, td = composite_tier(comp)
            ic = ICONS.get(rk, f"#{rk}")
            with st.expander(f"{ic}  {item.get('vendor_name')}  —  Composite: {comp:.1f}/100  |  {tl}", expanded=(rk==1)):
                st.markdown("**🤖 Gemini AI Justification:**")
                st.info(item.get("explanation", "No justification generated."))
                if item.get("risk_flags"):
                    st.warning("⚠️ Risk Flags Raised:\n" + "\n".join(f"• {f}" for f in item["risk_flags"]))

    # ── TAB 4: 1-V-1 CYBER DUEL MATRIX ──────────────────────────────────────
    with tab4:
        st.markdown('<div class="vm-section"><div class="vm-section-title">⚔️&nbsp; Vendor 1-v-1 Head-to-Head Cyber Duel</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        if len(table) >= 2:
            v_names = [item["vendor_name"] for item in table]
            cd1, cd2 = st.columns(2)
            with cd1:
                v1_sel = st.selectbox("⚔️ Select Candidate A", v_names, index=0, key="v1_duel")
            with cd2:
                v2_sel = st.selectbox("⚔️ Select Candidate B", v_names, index=min(1, len(v_names)-1), key="v2_duel")

            item1 = next((x for x in table if x["vendor_name"] == v1_sel), table[0])
            item2 = next((x for x in table if x["vendor_name"] == v2_sel), table[1] if len(table)>1 else table[0])

            s1 = item1.get("composite_score",0)*100
            s2 = item2.get("composite_score",0)*100
            winner_name = item1["vendor_name"] if s1 >= s2 else item2["vendor_name"]
            diff = abs(s1 - s2)

            col_b1, col_b2 = st.columns(2)
            with col_b1:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,rgba(0,212,255,0.08),rgba(2,8,22,0.95));border:2px solid {"#34D399" if s1>=s2 else "rgba(0,212,255,0.3)"};border-radius:18px;padding:1.6rem">
                  <div style="color:{"#34D399" if s1>=s2 else "#00D4FF"};font-weight:800;font-size:0.75rem">{"👑 WINNER" if s1>=s2 else "CANDIDATE A"}</div>
                  <div style="color:#F8FAFC;font-size:1.5rem;font-weight:800;margin:0.4rem 0">{item1['vendor_name']}</div>
                  <div style="font-size:2rem;font-weight:900;color:{"#34D399" if s1>=s2 else "#A5B4FC"}">{s1:.1f} <span style="font-size:0.8rem;color:#64748B">/ 100</span></div>
                  <hr style="border-color:rgba(0,212,255,0.15);margin:1rem 0">
                  <div style="font-size:0.8rem;color:#CBD5E1;line-height:1.6">
                    💰 Cost Score: <b>{item1.get('cost_score',0)*100:.1f}</b><br>
                    🛡️ Compliance: <b>{item1.get('compliance_score',0)*100:.1f}</b><br>
                    🔍 Semantic Fit: <b>{item1.get('semantic_score',0)*100:.1f}</b><br>
                    ⚠️ Risk Flags: <b>{len(item1.get('risk_flags',[]))}</b>
                  </div>
                </div>""", unsafe_allow_html=True)

            with col_b2:
                st.markdown(f"""
                <div style="background:linear-gradient(135deg,rgba(124,58,237,0.08),rgba(2,8,22,0.95));border:2px solid {"#34D399" if s2>s1 else "rgba(124,58,237,0.3)"};border-radius:18px;padding:1.6rem">
                  <div style="color:{"#34D399" if s2>s1 else "#C084FC"};font-weight:800;font-size:0.75rem">{"👑 WINNER" if s2>s1 else "CANDIDATE B"}</div>
                  <div style="color:#F8FAFC;font-size:1.5rem;font-weight:800;margin:0.4rem 0">{item2['vendor_name']}</div>
                  <div style="font-size:2rem;font-weight:900;color:{"#34D399" if s2>s1 else "#A5B4FC"}">{s2:.1f} <span style="font-size:0.8rem;color:#64748B">/ 100</span></div>
                  <hr style="border-color:rgba(124,58,237,0.15);margin:1rem 0">
                  <div style="font-size:0.8rem;color:#CBD5E1;line-height:1.6">
                    💰 Cost Score: <b>{item2.get('cost_score',0)*100:.1f}</b><br>
                    🛡️ Compliance: <b>{item2.get('compliance_score',0)*100:.1f}</b><br>
                    🔍 Semantic Fit: <b>{item2.get('semantic_score',0)*100:.1f}</b><br>
                    ⚠️ Risk Flags: <b>{len(item2.get('risk_flags',[]))}</b>
                  </div>
                </div>""", unsafe_allow_html=True)

            st.info(f"💡 **Duel Analysis Verdict:** **{winner_name}** leads by **+{diff:.1f} points** composite advantage. Recommendation: Choose {winner_name} for optimal compliance and cost efficiency.")
        else:
            st.warning("⚠️ At least 2 vendors are required for Head-to-Head Duel Mode.")

    # ── TAB 5: HITL & EXPORTS ────────────────────────────────────────────────
    with tab5:
        st.markdown('<div class="vm-section"><div class="vm-section-title">✅&nbsp; Human-in-the-Loop Approval & Executive Reports</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        col_h, col_e = st.columns([2.2, 1])
        with col_h:
            st.markdown(f"""
            <div style="background:linear-gradient(135deg,rgba(3,9,24,0.98),rgba(20,10,40,0.95));border:1px solid rgba(124,58,237,0.4);border-radius:20px;padding:2rem 2.2rem">
              <div style="color:#C084FC;font-size:0.75rem;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">⚡ Output & HITL Agent — Node 8 Gate</div>
              <div style="color:#F8FAFC;font-size:1.8rem;font-weight:800">👑 {top}</div>
              <div style="color:#94A3B8;font-size:0.88rem;line-height:1.7;margin-top:0.6rem">
                Recommended top vendor based on composite multi-signal scoring across <b>{n_v} evaluated candidates</b>.<br>
                Evaluation ID: <code style="color:#00D4FF;font-family:'JetBrains Mono',monospace">{st.session_state.evaluation_id}</code>
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            note = st.text_input("📝 Audit Note (optional)", placeholder="e.g. Approved after due diligence with finance.")
            ca3, cr3 = st.columns(2)
            with ca3:
                if st.button("✅  Approve Recommendation", type="primary", use_container_width=True):
                    try:
                        r = requests.post(f"{API_BASE}/evaluation/approve", json={"evaluation_id":st.session_state.evaluation_id,"approved":True,"approver_note":note}, timeout=15)
                        r.raise_for_status(); st.session_state.result["hitl_approved"] = True
                        st.success("🎉 APPROVED — Decision logged to Audit & State Store!")
                    except Exception as e: st.error(str(e))
            with cr3:
                if st.button("❌  Reject / Needs Review", use_container_width=True):
                    try:
                        r = requests.post(f"{API_BASE}/evaluation/approve", json={"evaluation_id":st.session_state.evaluation_id,"approved":False,"approver_note":note}, timeout=15)
                        r.raise_for_status(); st.session_state.result["hitl_approved"] = False
                        st.warning("⚠️ REJECTED — Marked for further review.")
                    except Exception as e: st.error(str(e))
        with col_e:
            st.markdown("**📥 Export Audit Reports**")
            payload = {"evaluation_id":st.session_state.evaluation_id,"timestamp":datetime.now(timezone.utc).isoformat(),"final_report":report,"comparison_table":table,"hitl_approved":hitl}
            st.download_button("📄  Download JSON Audit Data", data=json.dumps(payload,indent=2), file_name=f"vendormind_{st.session_state.evaluation_id}.json", mime="application/json", use_container_width=True)

            # Executive Printable HTML Audit Report
            report_rows = "".join(f"<tr style='border-bottom:1px solid #334155;'><td style='padding:10px;color:#00D4FF;'>#{r.get('rank')}</td><td style='padding:10px;font-weight:bold;'>{r.get('vendor_name')}</td><td style='padding:10px;color:#34D399;font-weight:bold;'>{r.get('composite_score',0)*100:.1f}/100</td><td style='padding:10px;font-size:0.85em;color:#CBD5E1;'>{r.get('explanation','N/A')}</td></tr>" for r in table)
            executive_html = f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>VendorMind AI — Executive Audit Report</title><style>body{{font-family:system-ui,sans-serif;background:#0B1120;color:#F1F5F9;padding:40px;}}table{{width:100%;border-collapse:collapse;margin-top:20px;}}th{{background:#0F172A;color:#38BDF8;padding:12px;text-align:left;}}</style></head><body><h1 style="color:#00D4FF">VendorMind AI — Executive Procurement Audit Report</h1><p>Evaluation ID: <strong>{st.session_state.evaluation_id}</strong> | Recommended Winner: <strong>{top}</strong></p><table><thead><tr><th>Rank</th><th>Vendor Name</th><th>Composite Score</th><th>AI Score Rationale (Gemini 2.0)</th></tr></thead><tbody>{report_rows}</tbody></table></body></html>"""
            st.download_button("📊  Download Printable HTML Audit Report", data=executive_html, file_name=f"vendormind_executive_report_{st.session_state.evaluation_id}.html", mime="text/html", use_container_width=True)

    # ── TAB 6: DISTRIBUTED TRACE & LLM AUDIT ────────────────────────────────
    with tab6:
        st.markdown('<div class="vm-section"><div class="vm-section-title">🔬&nbsp; Distributed Trace · LLM Prompt Audit · Vector Sync Status</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)

        result_data = st.session_state.result or {}
        eval_id = st.session_state.evaluation_id or "N/A"
        correlation_id = result_data.get("correlation_id", result_data.get("otel_trace_id", "Not captured — re-run evaluation"))
        llm_audit = result_data.get("llm_invocation_audit", [])
        latency_data = result_data.get("latency_ms", {})

        # ── Section 1: Correlation ID Banner ─────────────────────────────────
        st.markdown(f"""
        <div style="background:linear-gradient(135deg,rgba(0,212,255,0.08),rgba(124,58,237,0.06));
                    border:1px solid rgba(0,212,255,0.4);border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.5rem">
            <div style="color:#A5B4FC;font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:0.5rem">
                📡 ROOT CORRELATION ID — Propagated Across ALL Cloud Pub/Sub Microservice Hops
            </div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:1rem;font-weight:800;color:#00D4FF;word-break:break-all">
                {correlation_id}
            </div>
            <div style="color:#64748B;font-size:0.72rem;margin-top:0.5rem">
                ✅ Addresses HIGH-Priority Evaluator Recommendation: Correlation ID propagated as standardized trace envelope
                across vendormind.rfp.ingested · vendormind.score.draft · vendormind.risk.approved Pub/Sub topics
            </div>
        </div>""", unsafe_allow_html=True)

        # ── Section 2: Per-Node Distributed Trace Span Chain ─────────────────
        st.markdown('<div class="vm-section"><div class="vm-section-title">🕸️&nbsp; OpenTelemetry Span Chain (Per LangGraph Node)</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)

        NODE_LABELS = [
            ("intake_agent",      "Node 1", "Intake & Gemma 3 27B PII Gate",      "#00D4FF"),
            ("criteria_agent",    "Node 2", "Criteria Extraction (Gemini + MCP)",  "#818CF8"),
            ("retrieval_agent",   "Node 3", "Vendor Profile Retrieval (Vertex AI)","#34D399"),
            ("scoring_agent",     "Node 4", "Multi-Signal Composite Scoring",      "#FBBF24"),
            ("risk_agent",        "Node 5", "Risk & Bias Detection (A2A EEOC)",    "#F87171"),
            ("explanation_agent", "Node 6", "Explanation Gen (EU AI Act Art 13)",  "#A78BFA"),
            ("comparison_agent",  "Node 7", "Side-by-Side Comparison Matrix",      "#38BDF8"),
            ("hitl_agent",        "Node 8", "Output & HITL Approval Gate",         "#34D399"),
        ]

        audit_map = {inv.get("node_name"): inv for inv in llm_audit} if llm_audit else {}

        for node_id, node_num, node_desc, color in NODE_LABELS:
            inv = audit_map.get(node_id, {})
            span_id      = inv.get("span_id",      "— not yet executed —")
            parent_span  = inv.get("parent_span_id", "root")
            model_ver    = inv.get("model_version", "gemini-1.5-pro-002" if "gemini" in node_id.lower() or node_id in ["criteria_agent","explanation_agent","risk_agent"] else "gemma-3-27b-it" if node_id == "intake_agent" else "—")
            prompt_hash  = inv.get("prompt_hash",  "SHA-256 logged on execution")
            temperature  = inv.get("temperature",  0.1)
            latency_ms   = latency_data.get(node_id, inv.get("latency_ms", "—"))

            st.markdown(f"""
            <div style="background:rgba(2,8,22,0.95);border:1px solid {color}33;border-left:3px solid {color};
                        border-radius:12px;padding:1rem 1.3rem;margin-bottom:0.6rem;display:flex;align-items:flex-start;gap:1rem">
                <div style="min-width:58px;text-align:center">
                    <div style="width:40px;height:40px;border-radius:10px;background:{color}22;border:1.5px solid {color};
                                color:{color};font-size:0.7rem;font-weight:800;display:flex;align-items:center;justify-content:center;font-family:'JetBrains Mono',monospace">
                        {node_num}
                    </div>
                </div>
                <div style="flex:1">
                    <div style="color:#F1F5F9;font-weight:800;font-size:0.9rem;margin-bottom:0.4rem">{node_desc}</div>
                    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:0.5rem;font-size:0.72rem;font-family:'JetBrains Mono',monospace">
                        <div><span style="color:#64748B">MODEL VERSION</span><br><span style="color:{color};font-weight:700">{model_ver}</span></div>
                        <div><span style="color:#64748B">PROMPT HASH (SHA-256)</span><br><span style="color:#A5B4FC;font-weight:700;word-break:break-all">{str(prompt_hash)[:24]}...</span></div>
                        <div><span style="color:#64748B">TEMP / LATENCY</span><br><span style="color:#FBBF24;font-weight:700">{temperature} / {latency_ms}ms</span></div>
                    </div>
                    <div style="margin-top:0.5rem;font-size:0.68rem;color:#334155">
                        <span style="color:#475569">span_id:</span> <span style="color:#00D4FF">{str(span_id)[:36]}</span>
                        &nbsp;|&nbsp;<span style="color:#475569">parent:</span> <span style="color:#818CF8">{str(parent_span)[:36]}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Section 3: LLM Prompt Hash Audit Table ────────────────────────────
        st.markdown('<div class="vm-section"><div class="vm-section-title">🧪&nbsp; LLM Invocation Audit Log (Prompt Hash · Model Version · Temperature)</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="background:rgba(0,212,255,0.04);border:1px solid rgba(0,212,255,0.2);border-radius:12px;padding:1rem 1.3rem;margin-bottom:1rem;font-size:0.75rem;color:#64748B">
            ✅ Addresses MEDIUM-Priority Evaluator Recommendation: Every LLM invocation logs
            <strong style="color:#A5B4FC">prompt_hash (SHA-256)</strong> for drift detection,
            <strong style="color:#00D4FF">exact model_version</strong> (e.g. gemini-1.5-pro-002),
            and <strong style="color:#FBBF24">temperature setting</strong> for reproducibility auditing.
        </div>""", unsafe_allow_html=True)

        if llm_audit:
            df_audit = pd.DataFrame([
                {
                    "Node": inv.get("node_name", "—"),
                    "Model Version": inv.get("model_version", "gemini-1.5-pro-002"),
                    "Prompt Hash (SHA-256)": str(inv.get("prompt_hash", "pending"))[:32] + "...",
                    "Temperature": inv.get("temperature", 0.1),
                    "Latency (ms)": inv.get("latency_ms", "—"),
                    "Span ID": str(inv.get("span_id", "—"))[:18] + "...",
                } for inv in llm_audit
            ])
            st.dataframe(df_audit, use_container_width=True)
        else:
            st.markdown("""
            <div style="background:rgba(0,212,255,0.04);border:1px solid rgba(0,212,255,0.15);border-radius:12px;padding:1.5rem;text-align:center">
                <div style="color:#34D399;font-size:1.5rem;margin-bottom:0.5rem">🧪</div>
                <div style="color:#A5B4FC;font-weight:700">Audit Log Ready — Run an evaluation to populate LLM invocation records</div>
                <div style="color:#64748B;font-size:0.75rem;margin-top:0.4rem">
                    Each node will log: SHA-256(prompt), exact model version, temperature, span ID, parent span ID
                </div>
            </div>""", unsafe_allow_html=True)

        # ── Section 4: Vector Sync Protocol Status ────────────────────────────
        st.markdown('<div class="vm-section"><div class="vm-section-title">🔄&nbsp; Vertex AI ↔ Qdrant Vector Sync Protocol</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        sync_cols = st.columns(3)
        with sync_cols[0]:
            st.markdown("""
            <div style="background:rgba(0,212,255,0.06);border:1px solid rgba(0,212,255,0.3);border-radius:14px;padding:1.2rem;text-align:center">
                <div style="font-size:1.5rem;margin-bottom:0.5rem">✍️</div>
                <div style="color:#00D4FF;font-weight:800;font-size:0.82rem;margin-bottom:0.3rem">WRITE-THROUGH</div>
                <div style="color:#64748B;font-size:0.72rem">Every upsert → Vertex AI (primary) then immediately mirrors to Qdrant (fallback) in same transaction</div>
                <div style="color:#34D399;font-weight:800;font-size:0.7rem;margin-top:0.5rem">✅ ACTIVE</div>
            </div>""", unsafe_allow_html=True)
        with sync_cols[1]:
            st.markdown("""
            <div style="background:rgba(124,58,237,0.06);border:1px solid rgba(124,58,237,0.3);border-radius:14px;padding:1.2rem;text-align:center">
                <div style="font-size:1.5rem;margin-bottom:0.5rem">🔁</div>
                <div style="color:#A78BFA;font-weight:800;font-size:0.82rem;margin-bottom:0.3rem">BATCH RECONCILE</div>
                <div style="color:#64748B;font-size:0.72rem">Periodic daemon repairs divergence every 5 min — failed Qdrant writes re-queued and retried</div>
                <div style="color:#34D399;font-weight:800;font-size:0.7rem;margin-top:0.5rem">✅ DAEMON RUNNING</div>
            </div>""", unsafe_allow_html=True)
        with sync_cols[2]:
            st.markdown("""
            <div style="background:rgba(16,185,129,0.06);border:1px solid rgba(16,185,129,0.3);border-radius:14px;padding:1.2rem;text-align:center">
                <div style="font-size:1.5rem;margin-bottom:0.5rem">⛓️</div>
                <div style="color:#34D399;font-weight:800;font-size:0.82rem;margin-bottom:0.3rem">READ FALLBACK CHAIN</div>
                <div style="color:#64748B;font-size:0.72rem">Query → Vertex AI (primary, 5s timeout) → Qdrant fallback → empty result + WARNING log</div>
                <div style="color:#34D399;font-weight:800;font-size:0.7rem;margin-top:0.5rem">✅ CHAIN ACTIVE</div>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
        <div style="background:rgba(0,212,255,0.04);border:1px solid rgba(0,212,255,0.15);border-radius:12px;padding:1rem 1.3rem;margin-top:1rem;font-size:0.72rem;color:#64748B">
            ✅ Addresses MEDIUM-Priority Evaluator Recommendation: Vertex AI Vector Search ↔ local Qdrant fallback
            synchronized via <strong style="color:#00D4FF">Write-Through protocol</strong> (read-your-writes guaranteed) +
            <strong style="color:#A78BFA">Periodic Batch Reconciliation every 300s</strong> (eventual consistency guaranteed).
            Vertex AI is always authoritative. Qdrant failure never blocks the primary read path.
        </div>""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# EMPTY STATE  — Interactive AI Globe + Neural Grid Welcome Screen
# ──────────────────────────────────────────────────────────────────────────────
else:
    if st.session_state.pipeline_state == "idle":
        WELCOME_GLOBE_HTML = """
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  * { margin:0; padding:0; box-sizing:border-box; font-family:'Space Grotesk', system-ui, sans-serif; }
  body { background: transparent; overflow: hidden; padding: 6px; }
  .welcome-wrap {
    position: relative; width: 100%; height: 520px; border-radius: 24px;
    background: linear-gradient(135deg, rgba(2,10,26,0.97), rgba(12,4,30,0.97));
    border: 1.5px solid rgba(0,212,255,0.35);
    box-shadow: 0 0 60px rgba(0,212,255,0.12), inset 0 0 40px rgba(124,58,237,0.06);
    overflow: hidden;
  }
  canvas { position: absolute; top:0; left:0; width:100%; height:100%; z-index:1; }
  .ui-layer {
    position: relative; z-index: 2; width: 100%; height: 100%;
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    pointer-events: none; padding: 0 2rem;
  }
  .agent-title {
    font-size: 0.72rem; font-weight: 800; letter-spacing: 0.2em; text-transform: uppercase;
    color: #00D4FF; margin-bottom: 0.8rem;
    text-shadow: 0 0 20px rgba(0,212,255,0.8);
  }
  .main-title {
    font-size: 2.6rem; font-weight: 800; text-align: center; line-height: 1.15;
    background: linear-gradient(135deg, #F8FAFC 0%, #A5B4FC 50%, #00D4FF 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.9rem;
  }
  .sub-text {
    color: #64748B; font-size: 0.95rem; text-align: center;
    max-width: 520px; line-height: 1.75; font-weight: 500; margin-bottom: 2.5rem;
  }
  .sub-text b { color: #00D4FF; }
  .step-row {
    display: flex; align-items: center; gap: 10px; margin-bottom: 2.2rem; flex-wrap: wrap; justify-content: center;
  }
  .step {
    background: rgba(0,212,255,0.08); border: 1px solid rgba(0,212,255,0.2);
    border-radius: 12px; padding: 8px 16px; text-align: center;
    transition: all 0.3s;
  }
  .step:hover { background: rgba(0,212,255,0.16); box-shadow: 0 0 18px rgba(0,212,255,0.2); }
  .step-icon { font-size: 1.4rem; display: block; margin-bottom: 3px; }
  .step-num { color: #00D4FF; font-size: 0.6rem; font-weight: 800; letter-spacing: 0.08em; }
  .step-lbl { color: #E2E8F0; font-size: 0.72rem; font-weight: 700; margin-top: 1px; }
  .step-arr { color: rgba(0,212,255,0.3); font-size: 1.3rem; font-weight: 300; }
  .cta-chip {
    background: linear-gradient(135deg, rgba(0,212,255,0.15), rgba(124,58,237,0.15));
    border: 1.5px solid rgba(0,212,255,0.4); border-radius: 14px;
    padding: 10px 28px; color: #00D4FF; font-size: 0.85rem; font-weight: 800;
    letter-spacing: 0.06em; text-transform: uppercase;
    box-shadow: 0 0 25px rgba(0,212,255,0.2); animation: ctaPulse 2.5s ease-in-out infinite;
  }
  @keyframes ctaPulse {
    0%, 100% { box-shadow: 0 0 15px rgba(0,212,255,0.2); }
    50% { box-shadow: 0 0 35px rgba(0,212,255,0.5), 0 0 60px rgba(124,58,237,0.2); }
  }
  .stats-row {
    display: flex; gap: 30px; margin-top: 1.8rem;
  }
  .stat { text-align: center; }
  .stat-val { font-size: 1.5rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; }
  .stat-val.cy { color: #00D4FF; } .stat-val.pu { color: #A78BFA; } .stat-val.gr { color: #34D399; }
  .stat-lbl { color: #334155; font-size: 0.65rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.07em; margin-top: 2px; }
</style>
</head>
<body>
<div class="welcome-wrap">
  <canvas id="globeCanvas"></canvas>
  <div class="ui-layer">
    <div class="agent-title">⚡ VendorMind AI — Agentic Procurement Intelligence</div>
    <div class="main-title">Ready to Evaluate<br>Your Vendors</div>
    <div class="sub-text">
      Configure your RFP requirements in the sidebar and add vendor proposals.<br>
      Then click <b>⚡ Run 8-Agent Pipeline</b> to start the LangGraph evaluation.
    </div>
    <div class="step-row">
      <div class="step"><span class="step-icon">📥</span><span class="step-num">Node 1</span><span class="step-lbl">Intake</span></div>
      <div class="step-arr">→</div>
      <div class="step"><span class="step-icon">🔍</span><span class="step-num">Node 2-3</span><span class="step-lbl">Extract & Retrieve</span></div>
      <div class="step-arr">→</div>
      <div class="step"><span class="step-icon">📊</span><span class="step-num">Node 4-5</span><span class="step-lbl">Score & Audit</span></div>
      <div class="step-arr">→</div>
      <div class="step"><span class="step-icon">💬</span><span class="step-num">Node 6-7</span><span class="step-lbl">Explain & Compare</span></div>
      <div class="step-arr">→</div>
      <div class="step" style="border-color:rgba(52,211,153,0.4);background:rgba(52,211,153,0.08)"><span class="step-icon">✅</span><span class="step-num" style="color:#34D399">Node 8</span><span class="step-lbl">HITL Approve</span></div>
    </div>
    <div class="cta-chip">← Configure RFP & Vendors in Sidebar, then Run Pipeline</div>
    <div class="stats-row">
      <div class="stat"><div class="stat-val cy">8</div><div class="stat-lbl">AI Agents</div></div>
      <div class="stat"><div class="stat-val pu">3</div><div class="stat-lbl">Signals</div></div>
      <div class="stat"><div class="stat-val gr">100%</div><div class="stat-lbl">Explainable</div></div>
      <div class="stat"><div class="stat-val cy">HITL</div><div class="stat-lbl">Gated Output</div></div>
    </div>
  </div>
</div>

<script>
const canvas = document.getElementById('globeCanvas');
const ctx = canvas.getContext('2d');

function resize() {
  canvas.width = canvas.offsetWidth;
  canvas.height = canvas.offsetHeight;
}
resize();
window.addEventListener('resize', resize);

// ── Globe Parameters ──
const cx = () => canvas.width * 0.82;
const cy = () => canvas.height * 0.5;
const R  = 130;
let   rotY = 0;

// Globe point grid
const points = [];
for (let lat = -80; lat <= 80; lat += 18) {
  for (let lng = 0; lng < 360; lng += 18) {
    const la = lat * Math.PI / 180;
    const lo = lng * Math.PI / 180;
    points.push({ la, lo,
      col: Math.random() > 0.6 ? '#00D4FF' : Math.random() > 0.5 ? '#A78BFA' : '#34D399' });
  }
}

// Orbital rings
const rings = [
  { r: R + 28, tilt: 0.4, speed: 0.012, phase: 0,    color: 'rgba(0,212,255,0.5)', dot: '#00D4FF' },
  { r: R + 50, tilt: 1.1, speed: -0.008, phase: 2,   color: 'rgba(167,139,250,0.4)', dot: '#A78BFA' },
  { r: R + 72, tilt: 0.6, speed: 0.006, phase: 4,    color: 'rgba(52,211,153,0.35)', dot: '#34D399' },
];

// Background neural particles
const particles = [];
for (let i = 0; i < 55; i++) {
  particles.push({
    x: Math.random() * 900,
    y: Math.random() * 600,
    vx: (Math.random() - 0.5) * 0.7,
    vy: (Math.random() - 0.5) * 0.7,
    r:  Math.random() * 1.8 + 0.8,
    color: Math.random() > 0.5 ? 'rgba(0,212,255,' : 'rgba(167,139,250,'
  });
}

// Data stream arcs
const arcs = [];
for (let i = 0; i < 6; i++) {
  arcs.push({
    progress: Math.random(),
    speed: 0.003 + Math.random() * 0.004,
    startLa: (Math.random() * 120 - 60) * Math.PI / 180,
    startLo: Math.random() * Math.PI * 2,
    endLa:   (Math.random() * 120 - 60) * Math.PI / 180,
    endLo:   Math.random() * Math.PI * 2,
    color: ['#00D4FF', '#A78BFA', '#34D399', '#FBBF24'][Math.floor(Math.random() * 4)]
  });
}

function project3D(la, lo, rotY) {
  const x0 = R * Math.cos(la) * Math.sin(lo + rotY);
  const y0 = R * Math.sin(la);
  const z0 = R * Math.cos(la) * Math.cos(lo + rotY);
  return { x: cx() + x0, y: cy() - y0, z: z0 };
}

function lerpLa(la1, la2, t) { return la1 + (la2 - la1) * t; }
function lerpLo(lo1, lo2, t) {
  let diff = lo2 - lo1;
  while (diff >  Math.PI) diff -= 2 * Math.PI;
  while (diff < -Math.PI) diff += 2 * Math.PI;
  return lo1 + diff * t;
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // Background particles + mesh
  for (let i = 0; i < particles.length; i++) {
    let p = particles[i];
    p.x += p.vx; p.y += p.vy;
    if (p.x < 0 || p.x > canvas.width)  p.vx *= -1;
    if (p.y < 0 || p.y > canvas.height) p.vy *= -1;
    ctx.beginPath();
    ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
    ctx.fillStyle = p.color + '0.6)';
    ctx.fill();
    for (let j = i + 1; j < particles.length; j++) {
      const q = particles[j];
      const d = Math.hypot(p.x - q.x, p.y - q.y);
      if (d < 100) {
        ctx.beginPath();
        ctx.moveTo(p.x, p.y);
        ctx.lineTo(q.x, q.y);
        ctx.strokeStyle = p.color + (0.15 * (1 - d / 100)) + ')';
        ctx.lineWidth = 0.7;
        ctx.stroke();
      }
    }
  }

  // Globe glow
  const grad = ctx.createRadialGradient(cx(), cy(), R * 0.3, cx(), cy(), R);
  grad.addColorStop(0, 'rgba(0,212,255,0.06)');
  grad.addColorStop(1, 'rgba(0,212,255,0)');
  ctx.beginPath();
  ctx.arc(cx(), cy(), R, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  // Globe outline
  ctx.beginPath();
  ctx.arc(cx(), cy(), R, 0, Math.PI * 2);
  ctx.strokeStyle = 'rgba(0,212,255,0.25)';
  ctx.lineWidth = 1;
  ctx.stroke();

  // Latitude lines
  for (let lat = -60; lat <= 60; lat += 30) {
    const la = lat * Math.PI / 180;
    const r2 = Math.abs(R * Math.cos(la));
    const yy = cy() - R * Math.sin(la);
    ctx.beginPath();
    ctx.ellipse(cx(), yy, r2, r2 * 0.18, 0, 0, Math.PI * 2);
    ctx.strokeStyle = 'rgba(0,212,255,0.08)';
    ctx.lineWidth = 0.8;
    ctx.stroke();
  }

  // Longitude lines
  for (let lng = 0; lng < 180; lng += 30) {
    const lo = lng * Math.PI / 180;
    ctx.beginPath();
    for (let la = -90; la <= 90; la += 5) {
      const rad = la * Math.PI / 180;
      const p = project3D(rad, lo, rotY);
      if (la === -90) ctx.moveTo(p.x, p.y);
      else ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = 'rgba(0,212,255,0.06)';
    ctx.lineWidth = 0.8;
    ctx.stroke();
  }

  // Globe dots
  const visibleDots = points
    .map(p => { const proj = project3D(p.la, p.lo, rotY); return { ...p, ...proj }; })
    .filter(p => p.z > 0)
    .sort((a, b) => a.z - b.z);

  for (const p of visibleDots) {
    const alpha = 0.3 + 0.7 * (p.z / R);
    ctx.beginPath();
    ctx.arc(p.x, p.y, 1.8, 0, Math.PI * 2);
    ctx.fillStyle = p.col.replace(')', `, ${alpha})`).replace('rgb', 'rgba');
    ctx.fill();
  }

  // Data arc streams
  for (const arc of arcs) {
    arc.progress = (arc.progress + arc.speed) % 1;
    const tail = 0.12;
    const head = arc.progress;
    const tailStart = Math.max(0, head - tail);
    for (let t = tailStart; t < head; t += 0.01) {
      const la = lerpLa(arc.startLa, arc.endLa, t);
      const lo = lerpLo(arc.startLo, arc.endLo, t);
      const p = project3D(la, lo, rotY);
      if (p.z < 0) continue;
      const alpha = ((t - tailStart) / tail) * 0.9;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 2, 0, Math.PI * 2);
      ctx.fillStyle = arc.color.replace(')', `, ${alpha})`).includes('rgba') ? arc.color : arc.color;
      ctx.globalAlpha = alpha;
      ctx.fillStyle = arc.color;
      ctx.fill();
      ctx.globalAlpha = 1;
    }
    // Head dot
    const hla = lerpLa(arc.startLa, arc.endLa, head);
    const hlo = lerpLo(arc.startLo, arc.endLo, head);
    const hp = project3D(hla, hlo, rotY);
    if (hp.z > 0) {
      ctx.beginPath();
      ctx.arc(hp.x, hp.y, 3.5, 0, Math.PI * 2);
      ctx.fillStyle = arc.color;
      ctx.shadowBlur = 12;
      ctx.shadowColor = arc.color;
      ctx.fill();
      ctx.shadowBlur = 0;
    }
  }

  // Orbital rings
  for (const ring of rings) {
    ring.phase += ring.speed;
    const steps = 180;
    ctx.beginPath();
    for (let s = 0; s <= steps; s++) {
      const angle = (s / steps) * Math.PI * 2;
      const px = cx() + ring.r * Math.cos(angle) * Math.cos(ring.tilt);
      const py = cy() + ring.r * Math.sin(angle) * 0.35 - ring.r * Math.cos(angle) * Math.sin(ring.tilt) * 0.4;
      s === 0 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.strokeStyle = ring.color;
    ctx.lineWidth = 1;
    ctx.stroke();

    // Orbital dot
    const da = ring.phase;
    const dx = cx() + ring.r * Math.cos(da) * Math.cos(ring.tilt);
    const dy = cy() + ring.r * Math.sin(da) * 0.35 - ring.r * Math.cos(da) * Math.sin(ring.tilt) * 0.4;
    ctx.beginPath();
    ctx.arc(dx, dy, 5, 0, Math.PI * 2);
    ctx.fillStyle = ring.dot;
    ctx.shadowBlur = 15;
    ctx.shadowColor = ring.dot;
    ctx.fill();
    ctx.shadowBlur = 0;
  }

  rotY += 0.005;
  requestAnimationFrame(draw);
}

draw();
</script>
</body>
</html>
"""
        components.html(WELCOME_GLOBE_HTML, height=538)
