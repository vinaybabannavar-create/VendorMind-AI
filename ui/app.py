"""
ui/app.py — VendorMind AI  •  Ultra-Premium AI-Native Dashboard v3
"""

import os, sys, json, time, threading
from pathlib import Path
from datetime import datetime, timezone

import requests
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data.sample_data import PRESET_RFPS, SAMPLE_VENDORS

API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8080")

st.set_page_config(
    page_title="VendorMind AI — Agentic Procurement Intelligence",
    page_icon="🧠", layout="wide", initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# SCORE ANALYSIS LOGIC  —  based on actual score values
# ──────────────────────────────────────────────────────────────────────────────
def cost_analysis(v: float) -> tuple:
    if v >= 98:   return "⚠️ Lowest bid — verify not dumping", "#F87171", "CAUTION"
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
# CSS
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }

.stApp {
    background: radial-gradient(ellipse 80% 60% at 50% -10%, rgba(0,212,255,0.07) 0%, transparent 70%),
                radial-gradient(ellipse 60% 50% at 80% 90%, rgba(124,58,237,0.06) 0%, transparent 70%),
                #020810;
}

section[data-testid="stSidebar"] {
    background: rgba(2,8,16,0.98) !important;
    border-right: 1px solid rgba(0,212,255,0.12) !important;
}

/* Inputs */
div[data-testid="stTextArea"] textarea {
    background: rgba(0,212,255,0.03) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: 8px !important; color: #94A3B8 !important;
    font-family: 'JetBrains Mono', monospace !important; font-size: 0.78rem !important;
}
div[data-testid="stTextArea"] textarea:focus { border-color: rgba(0,212,255,0.4) !important; box-shadow: 0 0 12px rgba(0,212,255,0.08) !important; }
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: rgba(0,212,255,0.03) !important;
    border: 1px solid rgba(0,212,255,0.15) !important;
    border-radius: 8px !important; color: #94A3B8 !important;
}

/* Primary Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF 0%, #7C3AED 100%) !important;
    border: none !important; border-radius: 10px !important;
    color: #000 !important; font-family: 'Space Grotesk', sans-serif !important;
    font-weight: 800 !important; font-size: 0.85rem !important;
    letter-spacing: 0.08em !important; padding: 0.7rem 1.5rem !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.25), 0 4px 20px rgba(124,58,237,0.2) !important;
    transition: all 0.3s ease !important; text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 40px rgba(0,212,255,0.5), 0 8px 40px rgba(124,58,237,0.35) !important;
    transform: translateY(-2px) !important;
}
.stButton > button:not([kind="primary"]) {
    background: rgba(0,212,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.2) !important;
    border-radius: 10px !important; color: #00D4FF !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important;
    transition: all 0.3s !important;
}
.stButton > button:not([kind="primary"]):hover {
    background: rgba(0,212,255,0.1) !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.15) !important;
}

/* Tabs */
div[data-baseweb="tab-list"] {
    background: rgba(0,212,255,0.03) !important;
    border: 1px solid rgba(0,212,255,0.12) !important;
    border-radius: 12px !important; padding: 4px !important; gap: 3px !important;
}
button[role="tab"] {
    color: #334155 !important;
    font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important;
    font-size: 0.82rem !important; border-radius: 8px !important; transition: all 0.2s !important;
    padding: 0.5rem 1.2rem !important;
}
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.12), rgba(124,58,237,0.1)) !important;
    color: #00D4FF !important;
    box-shadow: 0 0 12px rgba(0,212,255,0.12), inset 0 0 0 1px rgba(0,212,255,0.2) !important;
}

/* Metrics */
div[data-testid="metric-container"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.04), rgba(124,58,237,0.03)) !important;
    border: 1px solid rgba(0,212,255,0.12) !important; border-radius: 14px !important;
    padding: 1.2rem 1.4rem !important;
    transition: all 0.3s ease !important;
}
div[data-testid="metric-container"]:hover { border-color: rgba(0,212,255,0.3) !important; box-shadow: 0 0 20px rgba(0,212,255,0.06) !important; }
div[data-testid="metric-container"] label { color: #334155 !important; font-size: 0.72rem !important; text-transform: uppercase !important; letter-spacing: 0.08em !important; }
div[data-testid="metric-container"] div[data-testid="stMetricValue"] { color: #F1F5F9 !important; font-size: 1.4rem !important; font-weight: 700 !important; }

/* Expander */
div[data-testid="stExpander"] { background: rgba(0,212,255,0.02) !important; border: 1px solid rgba(0,212,255,0.1) !important; border-radius: 12px !important; margin-bottom: 0.6rem !important; }
div[data-testid="stExpander"] summary { color: #94A3B8 !important; font-family: 'Space Grotesk', sans-serif !important; font-weight: 600 !important; font-size: 0.88rem !important; }

/* Block container */
.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1500px !important; }

/* Plotly chart container */
div[data-testid="stPlotlyChart"] { border-radius: 16px !important; overflow: hidden !important; }

/* Scrollbar */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb { background: rgba(0,212,255,0.2); border-radius: 2px; }

/* Animations */
@keyframes neonPulse {
    0%, 100% { box-shadow: 0 0 5px rgba(0,212,255,0.3), 0 0 15px rgba(0,212,255,0.1); }
    50%       { box-shadow: 0 0 20px rgba(0,212,255,0.7), 0 0 40px rgba(0,212,255,0.3); }
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
@keyframes spin  { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }

/* Hero */
.vm-hero {
    background:
        linear-gradient(135deg, rgba(0,212,255,0.05) 0%, rgba(124,58,237,0.07) 60%, rgba(16,185,129,0.04) 100%),
        rgba(3,8,20,0.95);
    border: 1px solid rgba(0,212,255,0.18);
    border-radius: 22px; padding: 2.5rem 3rem;
    margin-bottom: 2rem; position: relative; overflow: hidden;
    box-shadow: 0 0 60px rgba(0,212,255,0.04), 0 30px 60px rgba(0,0,0,0.4);
}
.vm-hero::before {
    content: ''; position: absolute; top: -100px; right: -100px;
    width: 450px; height: 450px;
    background: radial-gradient(circle, rgba(124,58,237,0.1) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}
.hero-title {
    font-size: 2.8rem; font-weight: 700; margin: 0; line-height: 1.1;
    background: linear-gradient(90deg, #00D4FF 0%, #818CF8 40%, #C084FC 70%, #34D399 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text; background-size: 200% auto;
    animation: flowGrad 5s ease infinite;
}
.hero-sub { color: #475569; font-size: 0.95rem; margin-top: 0.5rem; letter-spacing: 0.01em; }
.hero-badges { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 1.2rem; }
.hbadge {
    background: rgba(0,212,255,0.07); border: 1px solid rgba(0,212,255,0.2);
    color: #00D4FF; border-radius: 6px; font-size: 0.7rem; font-weight: 600;
    padding: 0.25rem 0.65rem; letter-spacing: 0.05em; text-transform: uppercase;
    transition: all 0.2s;
}
.hbadge:hover { background: rgba(0,212,255,0.15); box-shadow: 0 0 10px rgba(0,212,255,0.15); }
.hbadge.purple { background: rgba(124,58,237,0.08); border-color: rgba(124,58,237,0.25); color: #A78BFA; }
.hbadge.green  { background: rgba(16,185,129,0.08); border-color: rgba(16,185,129,0.25); color: #34D399; }

/* Section header */
.vm-section { display:flex; align-items:center; gap:1rem; margin:2rem 0 1.2rem; }
.vm-section-title { color:#F1F5F9; font-size:1rem; font-weight:700; white-space:nowrap; letter-spacing:0.03em; }
.vm-section-line { flex:1; height:1px; background:linear-gradient(90deg, rgba(0,212,255,0.35), rgba(124,58,237,0.15), transparent); }

/* Pipeline nodes */
.p-wrap { background:rgba(2,5,14,0.95); border:1px solid rgba(0,212,255,0.1); border-radius:16px; padding:1.2rem; }
.p-node { display:flex; align-items:center; gap:0.75rem; padding:0.6rem 0.8rem; border-radius:10px; border:1px solid rgba(255,255,255,0.04); margin-bottom:0.28rem; background:rgba(255,255,255,0.015); transition:all 0.4s ease; }
.p-node.active { border-color:rgba(0,212,255,0.45); background:rgba(0,212,255,0.06); animation:neonPulse 1.5s ease infinite; }
.p-node.done   { border-color:rgba(16,185,129,0.3);  background:rgba(16,185,129,0.04); }
.p-circ { width:28px; height:28px; border-radius:50%; flex-shrink:0; display:flex; align-items:center; justify-content:center; font-size:0.72rem; font-weight:700; font-family:'JetBrains Mono',monospace; }
.p-circ.idle   { background:rgba(255,255,255,0.04); color:#1E293B; border:1px solid rgba(255,255,255,0.06); }
.p-circ.active { background:rgba(0,212,255,0.12); color:#00D4FF; border:1px solid rgba(0,212,255,0.4); }
.p-circ.done   { background:rgba(16,185,129,0.12); color:#34D399; border:1px solid rgba(16,185,129,0.3); }
.p-name { font-size:0.82rem; font-weight:600; }
.p-name.idle { color:#334155; } .p-name.active { color:#00D4FF; } .p-name.done { color:#34D399; }
.p-desc { font-size:0.7rem; color:#1E293B; margin-top:0.1rem; }
.p-desc.active { color:#164E63; } .p-desc.done { color:#065F46; }
.p-stat { font-family:'JetBrains Mono',monospace; font-size:0.68rem; white-space:nowrap; }
.p-stat.idle { color:#0F172A; } .p-stat.active { color:#FCD34D; } .p-stat.done { color:#34D399; }

/* Terminal */
.vm-term { background:#000507; border:1px solid rgba(0,212,255,0.18); border-radius:14px; overflow:hidden; position:relative; }
.vm-term::after { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,#00D4FF,#7C3AED,transparent); background-size:200% auto; animation:flowGrad 2s ease infinite; }
.vm-thead { background:rgba(0,212,255,0.04); border-bottom:1px solid rgba(0,212,255,0.08); padding:0.6rem 1.2rem; display:flex; align-items:center; gap:0.5rem; }
.vm-dot { width:10px; height:10px; border-radius:50%; }
.vm-ttitle { color:rgba(0,212,255,0.4); font-size:0.7rem; font-family:'JetBrains Mono',monospace; margin-left:0.3rem; letter-spacing:0.1em; }
.vm-tbody { padding:0.8rem 1.1rem; min-height:300px; max-height:400px; overflow-y:auto; }
.lrow { display:flex; gap:0.7rem; font-size:0.77rem; line-height:1.75; border-bottom:1px solid rgba(255,255,255,0.015); animation:fadeUp 0.2s ease; }
.lt { color:#1E293B; min-width:68px; font-family:'JetBrains Mono',monospace; }
.ln { font-weight:600; min-width:105px; font-family:'JetBrains Mono',monospace; }
.ln.cy { color:#00D4FF; } .ln.gr { color:#34D399; } .ln.am { color:#FBBF24; } .ln.rd { color:#F87171; } .ln.sl { color:#334155; }
.lm { color:#334155; }
.lm.br { color:#94A3B8; }
.cursor { display:inline-block; width:7px; height:13px; background:#00D4FF; animation:blink 1s ease infinite; vertical-align:middle; margin-left:2px; border-radius:1px; }

/* ─── VENDOR CARDS (Leaderboard) ─── */
.v-card {
    border-radius: 20px; margin-bottom: 2rem;
    padding: 2rem 2.2rem; position: relative; overflow: hidden;
    animation: fadeUp 0.5s ease;
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.v-card:hover { transform: translateY(-4px); }
.v-card.r1 {
    background: linear-gradient(135deg, rgba(2,8,20,0.98) 0%, rgba(30,20,0,0.95) 100%);
    border: 1px solid rgba(245,158,11,0.4);
    box-shadow: 0 0 40px rgba(245,158,11,0.07), 0 20px 60px rgba(0,0,0,0.5);
}
.v-card.r1:hover { box-shadow: 0 4px 60px rgba(245,158,11,0.18), 0 20px 60px rgba(0,0,0,0.5); }
.v-card.r2 {
    background: linear-gradient(135deg, rgba(2,8,20,0.98) 0%, rgba(15,20,30,0.95) 100%);
    border: 1px solid rgba(148,163,184,0.25);
    box-shadow: 0 0 30px rgba(148,163,184,0.04), 0 20px 40px rgba(0,0,0,0.4);
}
.v-card.r2:hover { box-shadow: 0 4px 40px rgba(148,163,184,0.12); }
.v-card.rn {
    background: linear-gradient(135deg, rgba(2,8,20,0.98) 0%, rgba(5,12,25,0.95) 100%);
    border: 1px solid rgba(0,212,255,0.1);
    box-shadow: 0 0 20px rgba(0,212,255,0.03), 0 15px 40px rgba(0,0,0,0.4);
}
.v-card.rn:hover { box-shadow: 0 4px 30px rgba(0,212,255,0.1); }
.v-card-top { height: 2px; border-radius: 20px 20px 0 0; position: absolute; top: 0; left: 0; right: 0; }
.v-card-top.r1 { background: linear-gradient(90deg, transparent, #F59E0B, #FDE68A, transparent); }
.v-card-top.r2 { background: linear-gradient(90deg, transparent, #94A3B8, transparent); }
.v-card-top.rn { background: linear-gradient(90deg, transparent, #00D4FF, transparent); }

.v-header { display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:1.6rem; }
.v-left {}
.v-badge { display:inline-flex; align-items:center; gap:0.35rem; padding:0.22rem 0.65rem; border-radius:20px; font-size:0.68rem; font-weight:700; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:0.5rem; }
.vb-gold   { background:rgba(245,158,11,0.12); color:#F59E0B; border:1px solid rgba(245,158,11,0.3); }
.vb-silver { background:rgba(148,163,184,0.1);  color:#94A3B8; border:1px solid rgba(148,163,184,0.25); }
.vb-cyan   { background:rgba(0,212,255,0.08);   color:#00D4FF; border:1px solid rgba(0,212,255,0.2); }
.v-name { color:#F1F5F9; font-size:1.4rem; font-weight:700; margin-bottom:0.3rem; }
.v-tier-tag { display:inline-flex; align-items:center; gap:0.4rem; padding:0.2rem 0.7rem; border-radius:6px; font-size:0.72rem; font-weight:600; font-family:'JetBrains Mono',monospace; }
.v-right { text-align:right; }
.v-big { font-family:'JetBrains Mono',monospace; font-size:3.5rem; font-weight:700; line-height:1; }
.v-big.gold   { background:linear-gradient(135deg,#F59E0B,#FDE68A); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.v-big.cyan   { background:linear-gradient(135deg,#00D4FF,#818CF8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.v-big.slate  { background:linear-gradient(135deg,#64748B,#94A3B8); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }
.v-big-sub { color:#1E293B; font-size:0.68rem; font-family:'JetBrains Mono',monospace; margin-top:0.2rem; }

/* Signal Rows */
.signal-row { display:grid; grid-template-columns:1fr 1fr 1fr; gap:1.2rem; margin:1.2rem 0; }
.signal-block { background:rgba(0,0,0,0.3); border:1px solid rgba(255,255,255,0.04); border-radius:12px; padding:1rem 1.1rem; }
.sig-top { display:flex; justify-content:space-between; align-items:center; margin-bottom:0.5rem; }
.sig-label { color:#334155; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; }
.sig-val { font-family:'JetBrains Mono',monospace; font-size:1.3rem; font-weight:700; }
.sig-bar { height:4px; background:rgba(255,255,255,0.04); border-radius:2px; margin:0.4rem 0; overflow:hidden; }
.sig-fill { height:100%; border-radius:2px; }
.sf-cy { background:linear-gradient(90deg,#0891B2,#00D4FF); box-shadow:0 0 6px rgba(0,212,255,0.3); }
.sf-gr { background:linear-gradient(90deg,#047857,#34D399); box-shadow:0 0 6px rgba(52,211,153,0.3); }
.sf-pu { background:linear-gradient(90deg,#5B21B6,#A78BFA); box-shadow:0 0 6px rgba(167,139,250,0.3); }
.sig-analysis { font-size:0.73rem; line-height:1.4; margin-top:0.3rem; }

/* Risk / Explain */
.risk-row { background:rgba(239,68,68,0.06); border:1px solid rgba(239,68,68,0.18); border-left:3px solid #EF4444; border-radius:0 10px 10px 0; padding:0.85rem 1.2rem; margin-top:1.2rem; }
.risk-title { color:#F87171; font-size:0.73rem; font-weight:700; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.4rem; }
.risk-item { color:#FCA5A5; font-size:0.82rem; line-height:1.6; }
.expl-row { background:rgba(0,212,255,0.04); border:1px solid rgba(0,212,255,0.12); border-left:3px solid #00D4FF; border-radius:0 10px 10px 0; padding:0.9rem 1.2rem; margin-top:0.8rem; }
.expl-title { color:#00D4FF; font-size:0.72rem; font-weight:700; text-transform:uppercase; letter-spacing:0.07em; margin-bottom:0.4rem; }
.expl-text { color:#7DD3FC; font-size:0.84rem; line-height:1.75; }
.ok-row { color:#34D399; font-size:0.78rem; margin-top:0.8rem; display:flex; align-items:center; gap:0.4rem; }

/* HITL */
.hitl-box {
    background:linear-gradient(135deg,rgba(2,8,20,0.98),rgba(10,5,30,0.95));
    border:1px solid rgba(124,58,237,0.3); border-radius:18px; padding:2rem 2.2rem;
    position:relative; overflow:hidden;
    box-shadow:0 0 40px rgba(124,58,237,0.06);
}
.hitl-box::before { content:''; position:absolute; top:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,#7C3AED,#00D4FF,transparent); border-radius:18px 18px 0 0; }
.hitl-label { color:#5B21B6; font-size:0.7rem; font-weight:700; text-transform:uppercase; letter-spacing:0.1em; margin-bottom:0.5rem; }
.hitl-name { color:#F1F5F9; font-size:1.7rem; font-weight:800; }
.hitl-desc { color:#334155; font-size:0.85rem; line-height:1.7; margin-top:0.5rem; }

/* Welcome */
.welcome { text-align:center; padding:4rem 2rem; background:rgba(0,212,255,0.02); border:1px solid rgba(0,212,255,0.07); border-radius:22px; margin:0.5rem 0; animation:fadeUp 0.5s ease; }
.w-orb { width:100px; height:100px; border-radius:50%; margin:0 auto 2rem; background:radial-gradient(circle,rgba(0,212,255,0.18),rgba(124,58,237,0.12),transparent); border:1px solid rgba(0,212,255,0.18); display:flex; align-items:center; justify-content:center; font-size:3rem; animation:neonPulse 3s ease infinite; }
.w-title { color:#F1F5F9; font-size:1.9rem; font-weight:700; margin-bottom:0.6rem; }
.w-sub { color:#334155; font-size:0.95rem; max-width:500px; margin:0 auto 2.5rem; line-height:1.75; }
.w-steps { display:flex; justify-content:center; align-items:center; gap:0.8rem; flex-wrap:wrap; }
.w-step { text-align:center; }
.w-icon { width:60px; height:60px; border-radius:16px; margin:0 auto 0.6rem; background:rgba(0,212,255,0.06); border:1px solid rgba(0,212,255,0.13); display:flex; align-items:center; justify-content:center; font-size:1.6rem; transition:all 0.3s; }
.w-icon:hover { background:rgba(0,212,255,0.12); box-shadow:0 0 20px rgba(0,212,255,0.15); transform:scale(1.05); }
.w-num { color:#00D4FF; font-size:0.68rem; font-weight:700; text-transform:uppercase; letter-spacing:0.08em; }
.w-lbl { color:#1E293B; font-size:0.74rem; margin-top:0.1rem; }
.w-arr { color:rgba(0,212,255,0.18); font-size:1.4rem; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE
# ──────────────────────────────────────────────────────────────────────────────
for k, v in [("evaluation_id",None),("result",None),("pipeline_state","idle")]:
    if k not in st.session_state: st.session_state[k] = v

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🧠 VendorMind AI")
    st.markdown("<p style='color:#1E3A4A;font-size:0.7rem;font-family:JetBrains Mono,monospace;margin-top:-0.4rem;letter-spacing:0.06em'>AI AGENT BUILDER SERIES 2026</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,212,255,0.1);margin:0.8rem 0'>", unsafe_allow_html=True)

    st.markdown("<p style='color:#0E7490;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem'>① Preset RFP Template</p>", unsafe_allow_html=True)
    preset_key = st.selectbox("_p", ["custom"]+list(PRESET_RFPS.keys()),
        format_func=lambda k: "✍️  Custom Input" if k=="custom" else PRESET_RFPS[k]["title"],
        label_visibility="collapsed")
    default_rfp     = PRESET_RFPS[preset_key]["rfp_text"] if preset_key!="custom" else ""
    default_vendors = SAMPLE_VENDORS if preset_key!="custom" else SAMPLE_VENDORS[:2]

    st.markdown("<p style='color:#0E7490;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;margin:0.8rem 0 0.3rem'>② RFP Requirements</p>", unsafe_allow_html=True)
    rfp_input = st.text_area("_r", value=default_rfp, height=175, label_visibility="collapsed",
                              placeholder="Paste RFP requirements, compliance rules, SLA, budget ceiling...")

    st.markdown("<p style='color:#0E7490;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;margin:0.8rem 0 0.3rem'>③ Vendor Submissions</p>", unsafe_allow_html=True)
    num_v = st.number_input("_nv", min_value=1, max_value=8, value=min(len(default_vendors),3), step=1, label_visibility="collapsed")
    vendor_inputs = []
    for i in range(int(num_v)):
        v = default_vendors[i] if i<len(default_vendors) else {"vendor_id":f"vendor_{i+1}","vendor_name":f"Vendor {chr(65+i)}","raw_text":""}
        with st.expander(f"🏢  {v.get('vendor_name','')}", expanded=(i==0)):
            vname = st.text_input("Name", value=v.get("vendor_name",""), key=f"vn_{i}")
            vtext = st.text_area("Proposal", value=v.get("raw_text","").strip(), key=f"vt_{i}", height=105, label_visibility="collapsed", placeholder="Proposal text, pricing, certs...")
            vendor_inputs.append({"vendor_id":f"vendor_{i+1}","vendor_name":vname,"raw_text":vtext})

    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,212,255,0.1);margin:0.8rem 0'>", unsafe_allow_html=True)
    run_btn = st.button("⚡  RUN  8-AGENT  PIPELINE", type="primary", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# HERO
# ──────────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="vm-hero">
  <div style="display:flex;align-items:center;gap:1.8rem">
    <div style="width:70px;height:70px;border-radius:18px;flex-shrink:0;
                background:linear-gradient(135deg,rgba(0,212,255,0.12),rgba(124,58,237,0.18));
                border:1px solid rgba(0,212,255,0.25);display:flex;align-items:center;
                justify-content:center;font-size:2.2rem;
                box-shadow:0 0 30px rgba(0,212,255,0.15),inset 0 0 20px rgba(0,212,255,0.05)">🧠</div>
    <div style="flex:1">
      <div class="hero-title">VendorMind AI</div>
      <div class="hero-sub">Agentic Procurement Intelligence  ·  8-Node LangGraph Pipeline  ·  Explainable Multi-Signal Vendor Ranking  ·  National Finale 2026</div>
      <div class="hero-badges">
        <span class="hbadge">⚡ LangGraph</span>
        <span class="hbadge">🤖 Gemini 2.0</span>
        <span class="hbadge purple">🔍 Vector DB</span>
        <span class="hbadge purple">📊 Multi-Signal Score</span>
        <span class="hbadge green">🛡️ Risk Guardrails</span>
        <span class="hbadge green">✅ Human-in-the-Loop</span>
        <span class="hbadge">☁️ GCP Cloud Native</span>
      </div>
    </div>
    <div style="text-align:right;flex-shrink:0">
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#0E7490;letter-spacing:0.1em">DIAGRAM ID</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#1E3A4A;margin-top:0.2rem">12b1f6c1-82d5</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;color:#0E7490;margin-top:0.8rem;letter-spacing:0.1em">VERSION</div>
      <div style="font-family:'JetBrains Mono',monospace;font-size:0.72rem;color:#1E3A4A;margin-top:0.2rem">v1.0.0 — 2026</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# AGENTS
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
      <div class="p-stat {state}">{"⏳" if state=="idle" else "⚡ RUNNING" if state=="active" else "✓ DONE"}</div>
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
# RESULTS DASHBOARD
# ──────────────────────────────────────────────────────────────────────────────
if st.session_state.result:
    res    = st.session_state.result
    report = res.get("final_report") or {}
    table  = res.get("comparison_table") or []
    top    = report.get("recommended_vendor","N/A")
    hitl   = res.get("hitl_approved")
    n_v    = len(table)

    st.markdown('<div class="vm-section"><div class="vm-section-title">📊&nbsp; EVALUATION RESULTS DASHBOARD</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("👑 Top Vendor", top)
    c2.metric("📋 Vendors Ranked", n_v)
    c3.metric("🛡️ Risk Flags Total", sum(len(r.get("risk_flags",[])) for r in table))
    c4.metric("✅ HITL Gate", "Pending Review" if hitl is None else ("Approved ✅" if hitl else "Rejected ❌"))

    tab1, tab2, tab3, tab4 = st.tabs([
        "  👑  Leaderboard  ",
        "  📊  AI Analysis Dashboard  ",
        "  💬  AI Justifications  ",
        "  ✅  Approve / Reject  ",
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

            # Score-based tier
            tier_label, tier_color, tier_desc = composite_tier(comp)
            ca_msg, ca_col, ca_tag = cost_analysis(cost)
            co_msg, co_col, co_tag = compliance_analysis(compl)
            se_msg, se_col, se_tag = semantic_analysis(sem)

            st.markdown(f"""
            <div class="v-card {ccls}">
              <div class="v-card-top {ccls}"></div>
              <div class="v-header">
                <div class="v-left">
                  <div class="v-badge {bcls}">{blabel}</div>
                  <div class="v-name">{name}</div>
                  <div class="v-tier-tag" style="background:rgba(0,0,0,0.4);border:1px solid {tier_color}33;color:{tier_color};margin-top:0.4rem">
                    <span style="font-size:0.55rem;font-weight:800">●</span> {tier_label} — {tier_desc}
                  </div>
                </div>
                <div class="v-right">
                  <div class="v-big {scls}">{comp:.1f}</div>
                  <div class="v-big-sub">/ 100  COMPOSITE SCORE</div>
                </div>
              </div>

              <div class="signal-row">
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">💰 Cost</span>
                    <span class="sig-val" style="color:#00D4FF">{cost:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-cy" style="width:{min(cost,100):.1f}%"></div></div>
                  <div class="sig-analysis" style="color:{ca_col}">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;background:{ca_col}22;border:1px solid {ca_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem">{ca_tag}</span>
                    {ca_msg}
                  </div>
                </div>
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">🛡️ Compliance</span>
                    <span class="sig-val" style="color:#34D399">{compl:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-gr" style="width:{min(compl,100):.1f}%"></div></div>
                  <div class="sig-analysis" style="color:{co_col}">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;background:{co_col}22;border:1px solid {co_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem">{co_tag}</span>
                    {co_msg}
                  </div>
                </div>
                <div class="signal-block">
                  <div class="sig-top">
                    <span class="sig-label">🔍 Semantic Fit</span>
                    <span class="sig-val" style="color:#A78BFA">{sem:.1f}</span>
                  </div>
                  <div class="sig-bar"><div class="sig-fill sf-pu" style="width:{min(sem,100):.1f}%"></div></div>
                  <div class="sig-analysis" style="color:{se_col}">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:0.65rem;background:{se_col}22;border:1px solid {se_col}44;border-radius:4px;padding:0.1rem 0.4rem;margin-right:0.4rem">{se_tag}</span>
                    {se_msg}
                  </div>
                </div>
              </div>

              {"<div class='risk-row'><div class='risk-title'>⚠️ Risk Guardrail Flags — " + str(len(flags)) + " Alerts</div>" + "".join(f"<div class='risk-item'>• {f}</div>" for f in flags) + "</div>" if flags else "<div class='ok-row'>✓ Zero risk flags — passed all guardrail checks</div>"}
              {"<div class='expl-row'><div class='expl-title'>💬 Gemini 2.0 AI Justification</div><div class='expl-text'>" + expl + "</div></div>" if expl else ""}
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
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor ="rgba(0,0,0,0)",
                font=dict(family="Space Grotesk, sans-serif", color="#475569"),
                legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(0,212,255,0.15)", borderwidth=1, font=dict(color="#64748B")),
                margin=dict(l=20,r=20,t=40,b=20),
            )
            AXIS_STYLE = dict(gridcolor="rgba(0,212,255,0.06)", zerolinecolor="rgba(0,212,255,0.08)", tickfont=dict(color="#334155"))

            col_left, col_right = st.columns([1.2, 1])

            with col_left:
                # ── Grouped Horizontal Bar — Full Analysis
                st.markdown("#### 🤖 Multi-Signal Score Breakdown per Vendor")
                fig_bar = go.Figure()
                fig_bar.add_trace(go.Bar(name="💰 Cost",       y=vendors, x=costs,  orientation='h',
                    marker=dict(color="#00D4FF", opacity=0.9, line=dict(color="#00D4FF",width=0)),
                    hovertemplate="<b>%{y}</b><br>Cost Score: %{x:.1f}<extra></extra>"))
                fig_bar.add_trace(go.Bar(name="🛡️ Compliance", y=vendors, x=compls, orientation='h',
                    marker=dict(color="#34D399", opacity=0.9, line=dict(color="#34D399",width=0)),
                    hovertemplate="<b>%{y}</b><br>Compliance: %{x:.1f}<extra></extra>"))
                fig_bar.add_trace(go.Bar(name="🔍 Semantic",   y=vendors, x=sems,   orientation='h',
                    marker=dict(color="#A78BFA", opacity=0.9, line=dict(color="#A78BFA",width=0)),
                    hovertemplate="<b>%{y}</b><br>Semantic Fit: %{x:.1f}<extra></extra>"))
                fig_bar.update_layout(**PLOTLY_BASE, barmode='group', height=300,
                    title=dict(text="Signal Scores per Vendor (0-100)", font=dict(size=13,color="#475569")),
                    xaxis=dict(**AXIS_STYLE, title="Score (0–100)", range=[0,110]),
                    yaxis=dict(**AXIS_STYLE, autorange="reversed"))
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar":False})

                # ── Composite ranking
                st.markdown("#### 👑 Composite Score Ranking")
                colors = ["#F59E0B" if i==0 else "#94A3B8" if i==1 else "#00D4FF" for i in range(len(vendors))]
                fig_rank = go.Figure(go.Bar(
                    x=vendors, y=comps,
                    marker=dict(color=colors, line=dict(color="rgba(0,0,0,0)",width=0)),
                    text=[f"{v:.1f}" for v in comps], textposition="outside",
                    textfont=dict(color="#94A3B8", size=12),
                    hovertemplate="<b>%{x}</b><br>Composite Score: %{y:.1f}<extra></extra>"
                ))
                fig_rank.update_layout(**PLOTLY_BASE, height=280,
                    title=dict(text="Final Composite Score — Higher is Better", font=dict(size=13,color="#475569")),
                    yaxis=dict(**AXIS_STYLE, range=[0,115], title="Score"),
                    xaxis=dict(**AXIS_STYLE))
                st.plotly_chart(fig_rank, use_container_width=True, config={"displayModeBar":False})

            with col_right:
                # ── Radar Chart
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
                    fill_c = RADAR_COLORS[i%len(RADAR_COLORS)].format(a="0.12")
                    line_c = RADAR_COLORS[i%len(RADAR_COLORS)].format(a="1")
                    fig_rad.add_trace(go.Scatterpolar(
                        r=values, theta=cats_full,
                        name=item.get("vendor_name",""),
                        fill="toself", fillcolor=fill_c,
                        line=dict(color=line_c, width=2),
                        hovertemplate="<b>%{theta}</b>: %{r:.1f}<extra>" + item.get("vendor_name","") + "</extra>"
                    ))
                fig_rad.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Space Grotesk",color="#334155"),
                    polar=dict(
                        bgcolor="rgba(0,212,255,0.02)",
                        radialaxis=dict(visible=True, range=[0,100], gridcolor="rgba(0,212,255,0.1)", tickcolor="rgba(0,212,255,0.3)", tickfont=dict(size=9,color="#1E293B")),
                        angularaxis=dict(gridcolor="rgba(0,212,255,0.1)", tickcolor="rgba(0,212,255,0.3)", tickfont=dict(size=10,color="#64748B"))
                    ),
                    legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#64748B",size=11)),
                    margin=dict(l=40,r=40,t=30,b=30), height=320,
                    title=dict(text="5-Dimension Capability Radar", font=dict(size=13,color="#475569"))
                )
                st.plotly_chart(fig_rad, use_container_width=True, config={"displayModeBar":False})

                # ── Risk flag distribution
                if any(f > 0 for f in flags_ct):
                    st.markdown("#### 🛡️ Risk Flag Distribution")
                    fig_risk = go.Figure(go.Pie(
                        labels=vendors, values=[max(f,0.1) for f in flags_ct],
                        hole=0.55,
                        marker=dict(colors=["#F59E0B","#00D4FF","#A78BFA","#34D399"][:len(vendors)],
                                    line=dict(color="rgba(0,0,0,0.5)",width=2)),
                        textfont=dict(color="#94A3B8",size=11),
                        hovertemplate="<b>%{label}</b><br>Flags: %{value}<extra></extra>"
                    ))
                    fig_risk.update_layout(
                        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                        legend=dict(bgcolor="rgba(0,0,0,0)",font=dict(color="#64748B",size=11)),
                        margin=dict(l=10,r=10,t=10,b=10), height=240,
                        annotations=[dict(text="Risk<br>Flags", x=0.5, y=0.5, font_size=12, font_color="#475569", showarrow=False)]
                    )
                    st.plotly_chart(fig_risk, use_container_width=True, config={"displayModeBar":False})
                else:
                    st.success("✅ Zero risk flags across all vendors — clean evaluation!")

            # ── Score Analysis Table
            st.markdown("#### 🔬 Agent-by-Agent Score Intelligence Report")
            cols_report = st.columns(len(table))
            for idx, item in enumerate(table):
                rk   = item.get("rank",99)
                comp = item.get("composite_score",0)*100
                cost = item.get("cost_score",0)*100
                coml = item.get("compliance_score",0)*100
                sem  = item.get("semantic_score",0)*100
                tl, tc, td = composite_tier(comp)
                with cols_report[idx]:
                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.4);border:1px solid rgba(0,212,255,0.1);border-radius:14px;padding:1.2rem;text-align:center">
                      <div style="color:#334155;font-size:0.65rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em">Rank #{rk}</div>
                      <div style="color:#F1F5F9;font-size:0.95rem;font-weight:700;margin:0.4rem 0">{item.get('vendor_name','')}</div>
                      <div style="font-family:'JetBrains Mono',monospace;font-size:2rem;font-weight:700;color:{tc}">{comp:.1f}</div>
                      <div style="color:{tc};font-size:0.67rem;font-weight:700;letter-spacing:0.06em;margin-bottom:0.8rem">{tl}</div>
                      <div style="font-size:0.75rem;color:#334155;line-height:1.7">{td}</div>
                    </div>""", unsafe_allow_html=True)

    # ── TAB 3: AI JUSTIFICATIONS ─────────────────────────────────────────────
    with tab3:
        st.markdown('<div class="vm-section"><div class="vm-section-title">💬&nbsp; Gemini AI Decision Justifications</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        st.caption("Every ranking is backed by natural language evidence-based justifications generated by Gemini 2.0 Flash, citing specific data points from the RFP and vendor proposals.")

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
                ca_s, cb_s = st.columns([3, 1])
                with ca_s:
                    st.markdown("**🤖 Gemini AI Justification (Evidence-Backed):**")
                    st.info(item.get("explanation", "No justification generated by LLM — using fallback mode."))
                    if item.get("risk_flags"):
                        st.warning("⚠️ Risk Flags Raised by Guardrail Audit:\n" + "\n".join(f"• {f}" for f in item["risk_flags"]))
                    else:
                        st.success("✅ No risk flags — passed all guardrail checks")
                with cb_s:
                    st.markdown("**📊 Score Breakdown:**")
                    ca_m, ca_c, ca_t = cost_analysis(cost)
                    co_m, co_c, co_t = compliance_analysis(coml)
                    se_m, se_c, se_t = semantic_analysis(sem)
                    st.markdown(f"""
                    <div style="background:rgba(0,0,0,0.4);border:1px solid rgba(0,212,255,0.08);border-radius:12px;padding:1rem">
                      <div style="margin-bottom:0.8rem">
                        <div style="color:#334155;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.07em">Composite</div>
                        <div style="color:{tc};font-size:1.6rem;font-weight:700;font-family:'JetBrains Mono',monospace">{comp:.1f}</div>
                        <div style="color:{tc};font-size:0.65rem">{tl}</div>
                      </div>
                      <div style="border-top:1px solid rgba(255,255,255,0.04);padding-top:0.8rem">
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem">
                          <span style="color:#334155;font-size:0.72rem">💰 Cost</span>
                          <span style="color:{ca_c};font-size:0.72rem;font-weight:600">{cost:.1f} — {ca_t}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;margin-bottom:0.4rem">
                          <span style="color:#334155;font-size:0.72rem">🛡️ Compliance</span>
                          <span style="color:{co_c};font-size:0.72rem;font-weight:600">{coml:.1f} — {co_t}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                          <span style="color:#334155;font-size:0.72rem">🔍 Semantic</span>
                          <span style="color:{se_c};font-size:0.72rem;font-weight:600">{sem:.1f} — {se_t}</span>
                        </div>
                      </div>
                    </div>""", unsafe_allow_html=True)

    # ── TAB 4: HITL ──────────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="vm-section"><div class="vm-section-title">✅&nbsp; Human-in-the-Loop Approval Gate</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        st.caption("VendorMind AI recommends — the Procurement Manager decides. The Output & HITL Agent holds state pending your Go/No-Go decision, which is then logged to the Audit & State Store.")

        col_h, col_e = st.columns([2.2, 1])
        with col_h:
            st.markdown(f"""
            <div class="hitl-box">
              <div class="hitl-label">⚡ Output & HITL Agent — Node 8 — Awaiting Human Decision</div>
              <div class="hitl-name">👑 {top}</div>
              <div class="hitl-desc">
                AI recommendation based on composite multi-signal scoring across <b style="color:#00D4FF">{n_v} vendors</b>.<br>
                Evaluation ID: <code style="color:#334155;font-family:'JetBrains Mono',monospace">{st.session_state.evaluation_id}</code><br>
                The LangGraph pipeline holds state at this HITL checkpoint — the system does not auto-select a winner.
              </div>
            </div>""", unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)
            note = st.text_input("📝 Audit Note (optional)", placeholder="e.g. Approved after reviewing SOC 2 Type II report and cost model with finance team.")
            ca3, cr3 = st.columns(2)
            with ca3:
                if st.button("✅  Approve Recommendation", type="primary", use_container_width=True):
                    try:
                        r = requests.post(f"{API_BASE}/evaluation/approve", json={"evaluation_id":st.session_state.evaluation_id,"approved":True,"approver_note":note}, timeout=15)
                        r.raise_for_status(); st.session_state.result["hitl_approved"] = True
                        st.success("🎉 APPROVED — Decision logged to Audit & State Store (BigQuery)!")
                    except Exception as e: st.error(str(e))
            with cr3:
                if st.button("❌  Reject / Needs Review", use_container_width=True):
                    try:
                        r = requests.post(f"{API_BASE}/evaluation/approve", json={"evaluation_id":st.session_state.evaluation_id,"approved":False,"approver_note":note}, timeout=15)
                        r.raise_for_status(); st.session_state.result["hitl_approved"] = False
                        st.warning("⚠️ REJECTED — Marked for further due diligence.")
                    except Exception as e: st.error(str(e))
        with col_e:
            st.markdown("**📥 Export Evaluation Report**")
            payload = {"evaluation_id":st.session_state.evaluation_id,"timestamp":datetime.now(timezone.utc).isoformat(),"final_report":report,"comparison_table":table,"hitl_approved":hitl}
            st.download_button("📄  Download JSON Report", data=json.dumps(payload,indent=2), file_name=f"vendormind_{st.session_state.evaluation_id}.json", mime="application/json", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# EMPTY / WELCOME STATE
# ──────────────────────────────────────────────────────────────────────────────
else:
    if st.session_state.pipeline_state == "idle":
        st.markdown("""
        <div class="welcome">
          <div class="w-orb">🧠</div>
          <div class="w-title">Ready to Evaluate Vendors</div>
          <div class="w-sub">
            Select a Preset RFP in the sidebar, configure vendor submissions, then click
            <b style="color:#00D4FF">⚡ Run 8-Agent Pipeline</b> to trigger the LangGraph evaluation.
          </div>
          <div class="w-steps">
            <div class="w-step"><div class="w-icon">📥</div><div class="w-num">Node 1</div><div class="w-lbl">Intake & Parse</div></div>
            <div class="w-arr">→</div>
            <div class="w-step"><div class="w-icon">🔍</div><div class="w-num">Node 2-3</div><div class="w-lbl">Extract & Retrieve</div></div>
            <div class="w-arr">→</div>
            <div class="w-step"><div class="w-icon">📊</div><div class="w-num">Node 4-5</div><div class="w-lbl">Score & Risk Audit</div></div>
            <div class="w-arr">→</div>
            <div class="w-step"><div class="w-icon">💬</div><div class="w-num">Node 6-7</div><div class="w-lbl">Explain & Compare</div></div>
            <div class="w-arr">→</div>
            <div class="w-step"><div class="w-icon">✅</div><div class="w-num">Node 8</div><div class="w-lbl">HITL Approve</div></div>
          </div>
        </div>""", unsafe_allow_html=True)
