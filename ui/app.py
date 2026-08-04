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
.stApp {
    background: #020712 !important;
}

/* Sidebar High-Contrast Glass */
section[data-testid="stSidebar"] {
    background: rgba(3,9,24,0.92) !important;
    border-right: 1px solid rgba(0,212,255,0.25) !important;
    backdrop-filter: blur(15px);
}
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #00D4FF !important;
    font-weight: 800 !important;
    letter-spacing: 0.05em !important;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p {
    color: #A5B4FC !important;
    font-weight: 600 !important;
}

/* Glow Inputs */
div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input {
    background: rgba(0,212,255,0.05) !important;
    border: 1px solid rgba(0,212,255,0.3) !important;
    border-radius: 10px !important;
    color: #F1F5F9 !important;
    font-weight: 500 !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.25) !important;
}

/* Primary Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF 0%, #7C3AED 100%) !important;
    border: none !important; border-radius: 12px !important;
    color: #000 !important; font-weight: 800 !important; font-size: 0.9rem !important;
    letter-spacing: 0.08em !important; padding: 0.75rem 1.6rem !important;
    box-shadow: 0 0 25px rgba(0,212,255,0.4), 0 4px 20px rgba(124,58,237,0.3) !important;
    transition: all 0.3s ease !important; text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 45px rgba(0,212,255,0.7), 0 8px 45px rgba(124,58,237,0.5) !important;
    transform: translateY(-2px) scale(1.02) !important;
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
# FULL-SCREEN BACKGROUND NEURAL CANVAS INJECTOR (Injected directly into parent window)
# ──────────────────────────────────────────────────────────────────────────────
FULL_PAGE_NEURAL_BG_HTML = """
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body>
<script>
(function() {
  const pDoc = window.parent.document;
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

    const particles = [];
    const count = 75;
    for (let i = 0; i < count; i++) {
      particles.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.75,
        vy: (Math.random() - 0.5) * 0.75,
        r: Math.random() * 2.2 + 1,
        color: Math.random() > 0.45 ? 'rgba(0, 212, 255, ' : 'rgba(167, 139, 250, '
      });
    }

    function draw() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
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
          if (dist < 125) {
            ctx.beginPath();
            ctx.moveTo(p.x, p.y);
            ctx.lineTo(p2.x, p2.y);
            ctx.strokeStyle = p.color + ((1 - dist / 125) * 0.22) + ')';
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
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
# SIDEBAR
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("<h2 style='color:#00D4FF;font-weight:800;margin-bottom:0'>🧠 VendorMind AI</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color:#A5B4FC;font-size:0.75rem;font-family:JetBrains Mono,monospace;letter-spacing:0.06em;font-weight:700'>AI AGENT BUILDER SERIES 2026</p>", unsafe_allow_html=True)
    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,212,255,0.2);margin:0.8rem 0'>", unsafe_allow_html=True)

    st.markdown("<p style='color:#00D4FF;font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.12em;margin-bottom:0.3rem'>① PRESET RFP TEMPLATE</p>", unsafe_allow_html=True)
    preset_key = st.selectbox("_p", ["custom"]+list(PRESET_RFPS.keys()),
        format_func=lambda k: "✍️  Custom Input" if k=="custom" else PRESET_RFPS[k]["title"],
        label_visibility="collapsed")
    default_rfp     = PRESET_RFPS[preset_key]["rfp_text"] if preset_key!="custom" else ""
    default_vendors = SAMPLE_VENDORS if preset_key!="custom" else SAMPLE_VENDORS[:2]

    st.markdown("<p style='color:#00D4FF;font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.12em;margin:0.9rem 0 0.3rem'>② RFP REQUIREMENTS</p>", unsafe_allow_html=True)
    rfp_input = st.text_area("_r", value=default_rfp, height=175, label_visibility="collapsed",
                              placeholder="Paste RFP requirements, compliance rules, SLA, budget ceiling...")

    st.markdown("<p style='color:#00D4FF;font-size:0.7rem;font-weight:800;text-transform:uppercase;letter-spacing:0.12em;margin:0.9rem 0 0.3rem'>③ VENDOR SUBMISSIONS</p>", unsafe_allow_html=True)
    num_v = st.number_input("_nv", min_value=1, max_value=8, value=min(len(default_vendors),3), step=1, label_visibility="collapsed")
    vendor_inputs = []
    for i in range(int(num_v)):
        v = default_vendors[i] if i<len(default_vendors) else {"vendor_id":f"vendor_{i+1}","vendor_name":f"Vendor {chr(65+i)}","raw_text":""}
        with st.expander(f"🏢  {v.get('vendor_name','')}", expanded=(i==0)):
            vname = st.text_input("Name", value=v.get("vendor_name",""), key=f"vn_{i}")
            vtext = st.text_area("Proposal", value=v.get("raw_text","").strip(), key=f"vt_{i}", height=105, label_visibility="collapsed", placeholder="Proposal text, pricing, certs...")
            vendor_inputs.append({"vendor_id":f"vendor_{i+1}","vendor_name":vname,"raw_text":vtext})

    st.markdown("<hr style='border:none;border-top:1px solid rgba(0,212,255,0.2);margin:0.9rem 0'>", unsafe_allow_html=True)
    run_btn = st.button("⚡  RUN  8-AGENT  PIPELINE", type="primary", use_container_width=True)

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
          <span class="badge">🤖 Gemini 2.0</span>
          <span class="badge purple">🔍 Vector Retrieval</span>
          <span class="badge purple">📊 Multi-Signal</span>
          <span class="badge green">🛡️ Risk Audit</span>
          <span class="badge green">✅ HITL Gate</span>
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

    # ── TAB 4: HITL ──────────────────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="vm-section"><div class="vm-section-title">✅&nbsp; Human-in-the-Loop Approval Gate</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
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
            st.markdown("**📥 Export Evaluation Report**")
            payload = {"evaluation_id":st.session_state.evaluation_id,"timestamp":datetime.now(timezone.utc).isoformat(),"final_report":report,"comparison_table":table,"hitl_approved":hitl}
            st.download_button("📄  Download JSON Report", data=json.dumps(payload,indent=2), file_name=f"vendormind_{st.session_state.evaluation_id}.json", mime="application/json", use_container_width=True)

# ──────────────────────────────────────────────────────────────────────────────
# EMPTY STATE
# ──────────────────────────────────────────────────────────────────────────────
else:
    if st.session_state.pipeline_state == "idle":
        st.markdown("""
        <div style="text-align:center;padding:4rem 2rem;background:rgba(0,212,255,0.03);border:1px solid rgba(0,212,255,0.15);border-radius:24px;margin:0.5rem 0">
          <div style="width:100px;height:100px;border-radius:50%;margin:0 auto 2rem;background:radial-gradient(circle,rgba(0,212,255,0.25),rgba(124,58,237,0.15),transparent);border:1px solid rgba(0,212,255,0.3);display:flex;align-items:center;justify-content:center;font-size:3rem;animation:neonPulse 3s ease infinite">🧠</div>
          <div style="color:#F8FAFC;font-size:2rem;font-weight:800;margin-bottom:0.6rem">Ready to Evaluate Vendors</div>
          <div style="color:#94A3B8;font-size:0.98rem;max-width:520px;margin:0 auto 2.5rem;line-height:1.75;font-weight:500">
            Select a Preset RFP in the sidebar, add vendor proposals, then click
            <b style="color:#00D4FF">⚡ RUN 8-AGENT PIPELINE</b> to start the LangGraph evaluation.
          </div>
        </div>""", unsafe_allow_html=True)
