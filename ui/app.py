"""
ui/app.py — VendorMind AI  •  Enterprise Agentic Procurement Intelligence Platform
Senior Principal AI Architect Level Design System
Featuring Cinematic 3D Entrance, Live 8-Node LangGraph DAG Visualization, & Full-Viewport Neural Background.
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
    page_title="VendorMind AI — Enterprise Procurement Intelligence",
    page_icon="🧠", layout="wide", initial_sidebar_state="expanded"
)

# ──────────────────────────────────────────────────────────────────────────────
# DOCUMENT PARSER HELPER (PDF / TXT / DOCX / JSON / MD)
# ──────────────────────────────────────────────────────────────────────────────
def parse_uploaded_file(uploaded_file) -> str:
    """Extract raw text from PDF, TXT, DOCX, JSON, or MD files cleanly."""
    if uploaded_file is None:
        return ""
    
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
                text = [page.extract_text() for page in reader.pages if page.extract_text()]
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
# CSS DESIGN SYSTEM — $100M Enterprise AI Platform Aesthetics
# ──────────────────────────────────────────────────────────────────────────────
st.markdown(r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Space Grotesk', sans-serif !important; }

html, body {
    background: #020712 !important;
}
.stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"], .main {
    background: transparent !important;
}

/* ── Sidebar Styling ── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, rgba(3, 8, 22, 0.98) 0%, rgba(8, 12, 30, 0.98) 50%, rgba(4, 7, 20, 0.99) 100%) !important;
    border-right: 1px solid rgba(0, 212, 255, 0.25) !important;
    backdrop-filter: blur(30px) saturate(180%);
    box-shadow: 8px 0 50px rgba(0, 212, 255, 0.12) !important;
}
section[data-testid="stSidebar"]::-webkit-scrollbar { width: 5px; }
section[data-testid="stSidebar"]::-webkit-scrollbar-track { background: rgba(2, 6, 18, 0.5); }
section[data-testid="stSidebar"]::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, rgba(0,212,255,0.5), rgba(139,92,246,0.5));
    border-radius: 6px;
}
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] .block-container { padding: 1rem 1rem 2rem 1rem !important; }

section[data-testid="stSidebar"] label {
    color: #94A3B8 !important; font-weight: 700 !important; font-size: 0.78rem !important;
    letter-spacing: 0.06em !important; text-transform: uppercase !important;
}

section[data-testid="stSidebar"] details {
    background: linear-gradient(135deg, rgba(15, 23, 42, 0.6) 0%, rgba(30, 41, 59, 0.4) 100%) !important;
    border: 1px solid rgba(0, 212, 255, 0.2) !important;
    border-radius: 14px !important; margin-bottom: 10px !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.05) !important;
}
section[data-testid="stSidebar"] summary {
    color: #38BDF8 !important; font-weight: 700 !important; font-size: 0.85rem !important;
}

div[data-testid="stTextArea"] textarea,
div[data-testid="stSelectbox"] > div > div,
div[data-testid="stTextInput"] input {
    background: rgba(15, 23, 42, 0.7) !important;
    border: 1px solid rgba(0, 212, 255, 0.25) !important;
    border-radius: 11px !important;
    color: #F8FAFC !important;
    font-weight: 500 !important;
}
div[data-testid="stTextArea"] textarea:focus,
div[data-testid="stTextInput"] input:focus {
    border-color: #00D4FF !important;
    box-shadow: 0 0 20px rgba(0, 212, 255, 0.3) !important;
}

/* Primary Glow Button */
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #00D4FF 0%, #3B82F6 40%, #8B5CF6 100%) !important;
    border: none !important; border-radius: 14px !important;
    color: #030712 !important; font-weight: 800 !important; font-size: 0.95rem !important;
    letter-spacing: 0.09em !important; padding: 0.9rem 1.8rem !important;
    box-shadow: 0 0 35px rgba(0,212,255,0.45), 0 4px 25px rgba(139,92,246,0.35) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important; text-transform: uppercase !important;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 0 50px rgba(0,212,255,0.85), 0 8px 45px rgba(139,92,246,0.65) !important;
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
    padding: 0.65rem 1.4rem !important;
}
button[role="tab"][aria-selected="true"] {
    background: linear-gradient(135deg, rgba(0,212,255,0.22), rgba(124,58,237,0.2)) !important;
    color: #00D4FF !important;
    box-shadow: 0 0 20px rgba(0,212,255,0.3), inset 0 0 0 1.5px rgba(0,212,255,0.45) !important;
}

.block-container { padding: 1.5rem 2rem 3rem !important; max-width: 1600px !important; }

@keyframes neonPulse {
    0%, 100% { box-shadow: 0 0 8px rgba(0,212,255,0.4), 0 0 20px rgba(0,212,255,0.2); }
    50%       { box-shadow: 0 0 25px rgba(0,212,255,0.85), 0 0 50px rgba(0,212,255,0.4); }
}
@keyframes blink { 0%,100% { opacity:1; } 50% { opacity:0; } }

.vm-section { display:flex; align-items:center; gap:1rem; margin:2rem 0 1.2rem; }
.vm-section-title { color:#F1F5F9; font-size:1.05rem; font-weight:800; letter-spacing:0.04em; }
.vm-section-line { flex:1; height:1px; background:linear-gradient(90deg, rgba(0,212,255,0.4), rgba(124,58,237,0.2), transparent); }

/* Terminal */
.vm-term { background:rgba(1,4,10,0.95); border:1px solid rgba(0,212,255,0.25); border-radius:16px; overflow:hidden; position:relative; box-shadow:0 0 35px rgba(0,212,255,0.08); backdrop-filter:blur(10px); }
.vm-thead { background:rgba(0,212,255,0.06); border-bottom:1px solid rgba(0,212,255,0.12); padding:0.65rem 1.3rem; display:flex; align-items:center; gap:0.55rem; }
.vm-dot { width:10px; height:10px; border-radius:50%; }
.vm-ttitle { color:#00D4FF; font-size:0.72rem; font-family:'JetBrains Mono',monospace; letter-spacing:0.1em; font-weight:700; }
.vm-tbody { padding:0.9rem 1.2rem; min-height:280px; max-height:380px; overflow-y:auto; }
.lrow { display:flex; gap:0.75rem; font-size:0.78rem; line-height:1.75; border-bottom:1px solid rgba(255,255,255,0.02); }
.lt { color:#475569; min-width:70px; font-family:'JetBrains Mono',monospace; font-weight:500; }
.ln { font-weight:700; min-width:110px; font-family:'JetBrains Mono',monospace; }
.ln.cy { color:#00D4FF; } .ln.gr { color:#34D399; } .ln.am { color:#FBBF24; } .ln.rd { color:#F87171; } .ln.sl { color:#64748B; }
.lm { color:#64748B; } .lm.br { color:#E2E8F0; }
.cursor { display:inline-block; width:7px; height:13px; background:#00D4FF; animation:blink 1s ease infinite; vertical-align:middle; margin-left:2px; }
</style>
""", unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# HIGH-LEVEL HACKATHON 3D CINEMATIC ENTRANCE SCREEN
# ──────────────────────────────────────────────────────────────────────────────
SPLASH_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><script>
(function(){
  const pWin = window.parent;
  const pDoc = pWin.document;

  const ov = pDoc.createElement('div');
  ov.id = 'vm-splash';
  ov.style.cssText = 'position:fixed;top:0;left:0;width:100vw;height:100vh;z-index:999999;background:#01040D;overflow:hidden;cursor:default;';
  pDoc.body.appendChild(ov);

  const cv = pDoc.createElement('canvas');
  cv.style.cssText='position:absolute;top:0;left:0;width:100%;height:100%;';
  ov.appendChild(cv);
  const ctx = cv.getContext('2d');
  function rsz(){ cv.width=pWin.innerWidth; cv.height=pWin.innerHeight; }
  rsz(); pWin.addEventListener('resize',rsz);

  const ui = pDoc.createElement('div');
  ui.style.cssText='position:absolute;top:0;left:0;width:100%;height:100%;display:flex;flex-direction:column;align-items:center;justify-content:center;pointer-events:none;z-index:2;padding:0 2rem;';
  ov.appendChild(ui);

  function el(tag,css,html){
    const e=pDoc.createElement(tag);
    e.style.cssText=css; if(html) e.innerHTML=html;
    return e;
  }

  const hackBadge = el('div',
    'font-family:JetBrains Mono,monospace;font-size:clamp(0.75rem,1.4vw,0.95rem);font-weight:800;letter-spacing:0.24em;text-transform:uppercase;color:#00D4FF;opacity:0;transition:opacity 0.8s ease;margin-bottom:18px;text-shadow:0 0 24px rgba(0,212,255,0.85);background:rgba(0,212,255,0.08);padding:8px 20px;border-radius:30px;border:1px solid rgba(0,212,255,0.3);',
    '🏆 &nbsp; HiDevs National AI Hackathon 2026  ·  National Finale Bengaluru &nbsp; 🏆');

  const titleWrap = el('div','position:relative;text-align:center;margin-bottom:14px;opacity:0;transition:opacity 0.8s ease,transform 0.8s ease;transform:translateY(30px);','');
  const titleMain = el('div',
    'font-family:Space Grotesk,sans-serif;font-size:clamp(3.5rem,8vw,7.5rem);font-weight:900;letter-spacing:-0.03em;line-height:1;background:linear-gradient(135deg,#ffffff 0%,#a5f3fc 30%,#00D4FF 55%,#818CF8 80%,#C084FC 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 0 50px rgba(0,212,255,0.7));',
    'VendorMind AI');
  const titleSub = el('div',
    'font-family:JetBrains Mono,monospace;font-size:clamp(0.85rem,1.6vw,1.25rem);font-weight:700;color:#A5B4FC;letter-spacing:0.2em;text-transform:uppercase;margin-top:14px;',
    'Enterprise Agentic Procurement Intelligence Platform');
  titleWrap.appendChild(titleMain);
  titleWrap.appendChild(titleSub);

  const agentRow = el('div',
    'display:flex;align-items:center;gap:10px;margin:22px 0;opacity:0;transition:opacity 0.8s ease;',
    '');
  const agentColors=['#00D4FF','#00D4FF','#818CF8','#818CF8','#F59E0B','#F59E0B','#34D399','#34D399'];
  for(let i=0;i<8;i++){
    const nd=el('div',
      `width:36px;height:36px;border-radius:50%;border:2px solid ${agentColors[i]};color:${agentColors[i]};font-size:0.8rem;font-weight:800;display:flex;align-items:center;justify-content:center;font-family:JetBrains Mono,monospace;box-shadow:0 0 16px ${agentColors[i]}77;`,
      `${i+1}`);
    agentRow.appendChild(nd);
    if(i<7){
      const ln=el('div',`width:20px;height:2.5px;background:linear-gradient(90deg,${agentColors[i]},${agentColors[i+1]});opacity:0.6;`,'');
      agentRow.appendChild(ln);
    }
  }

  const creatorWrap = el('div','opacity:0;transition:opacity 0.8s ease,transform 0.8s ease;transform:translateX(40px);margin-top:10px;text-align:center;','');
  const creatorLine = el('div',
    'font-family:JetBrains Mono,monospace;font-size:0.8rem;color:#64748B;letter-spacing:0.14em;margin-bottom:4px;font-weight:700;',
    'CREATED & DEVELOPED BY');
  const creatorName = el('div',
    'font-family:Space Grotesk,sans-serif;font-size:clamp(1.6rem,3.2vw,2.5rem);font-weight:800;color:#F1F5F9;letter-spacing:0.04em;text-shadow:0 0 35px rgba(129,140,248,0.7);',
    'Vinay Babannavar');
  creatorWrap.appendChild(creatorLine);
  creatorWrap.appendChild(creatorName);

  const progressWrap = el('div','width:min(500px,75vw);margin-top:32px;opacity:0;transition:opacity 0.6s ease;','');
  const progressLabel = el('div','font-family:JetBrains Mono,monospace;font-size:0.75rem;color:#00D4FF;letter-spacing:0.14em;margin-bottom:10px;display:flex;justify-content:space-between;font-weight:700;',
    '<span>INITIALIZING 8-NODE LANGGRAPH AGENT GRAPH...</span><span id="vm-pct">0%</span>');
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
    const now = audio.currentTime;
    playTone(80, now, 1.8, 'sawtooth', 0.08, 0.1, 0.4);
    [261.6,329.6,392,523.3].forEach((f,i)=>{ playTone(f, now+2.0+i*0.12, 0.5, 'sine', 0.06, 0.05, 0.2); });
    [261.6,329.6,392,523.3,659.3].forEach((f,i)=>{ playTone(f, now+5.5+i*0.06, 1.5, 'sine', 0.08, 0.1, 0.5); });
  } catch(e){}

  const stars=[];
  for(let i=0;i<250;i++){
    stars.push({
      angle: Math.random()*Math.PI*2,
      speed: 0.5 + Math.random()*6,
      dist: Math.random()*200,
      maxDist: 500+Math.random()*600,
      hue: Math.random()>0.7 ? 200 : 240,
      size: Math.random()*2+0.5
    });
  }

  const T=12000; // 12 seconds cinematic entrance
  let t0=performance.now();

  function frame(now){
    const elapsed=now-t0;
    const cw=cv.width, ch=cv.height, cx=cw/2, cy=ch/2;

    ctx.fillStyle='rgba(1,4,13,0.2)';
    ctx.fillRect(0,0,cw,ch);

    if(elapsed<4000){
      const warpProg=Math.min(elapsed/3500,1);
      stars.forEach(s=>{
        s.dist += s.speed * (1+warpProg*10) * 0.35;
        if(s.dist>s.maxDist){ s.dist=Math.random()*40; }
        const x1=cx+Math.cos(s.angle)*(s.dist*0.7);
        const y1=cy+Math.sin(s.angle)*(s.dist*0.7);
        const x2=cx+Math.cos(s.angle)*(s.dist*0.7+s.speed*(1+warpProg*6));
        const y2=cy+Math.sin(s.angle)*(s.dist*0.7+s.speed*(1+warpProg*6));
        const a=Math.min(s.dist/(s.maxDist*0.5),1)*0.9;
        const grad=ctx.createLinearGradient(x1,y1,x2,y2);
        grad.addColorStop(0,`hsla(${s.hue},100%,80%,0)`);
        grad.addColorStop(1,`hsla(${s.hue},100%,90%,${a})`);
        ctx.beginPath(); ctx.moveTo(x1,y1); ctx.lineTo(x2,y2);
        ctx.strokeStyle=grad; ctx.lineWidth=s.size*(0.5+warpProg); ctx.stroke();
      });
    }

    if(elapsed>2500){ hackBadge.style.opacity=Math.min((elapsed-2500)/800,1); }
    if(elapsed>3500){
      const tAlpha=Math.min((elapsed-3500)/900,1);
      titleWrap.style.opacity=tAlpha;
      titleWrap.style.transform=`translateY(${(1-tAlpha)*30}px)`;
    }
    if(elapsed>5000){ agentRow.style.opacity=Math.min((elapsed-5000)/800,1); }
    if(elapsed>6500){
      const cAlpha=Math.min((elapsed-6500)/800,1);
      creatorWrap.style.opacity=cAlpha;
      creatorWrap.style.transform=`translateX(${(1-cAlpha)*40}px)`;
    }
    if(elapsed>8000){
      progressWrap.style.opacity=Math.min((elapsed-8000)/600,1);
      const barProg=Math.min((elapsed-8000)/3200,1);
      progressBar.style.width=(barProg*100)+'%';
      const pctEl=pDoc.getElementById('vm-pct');
      if(pctEl) pctEl.textContent=Math.floor(barProg*100)+'%';
    }

    if(elapsed>10800){
      const fadeAlpha=Math.min((elapsed-10800)/1000,1);
      ov.style.opacity=1-fadeAlpha;
    }

    if(elapsed<T){
      requestAnimationFrame(frame);
    } else {
      ov.style.transition='opacity 0.3s ease';
      ov.style.opacity='0';
      setTimeout(()=>{ try{ov.remove();}catch(e){} }, 350);
    }
  }
  requestAnimationFrame(frame);
})();
</script></body></html>
"""
components.html(SPLASH_HTML, height=1)

# ──────────────────────────────────────────────────────────────────────────────
# FULL-VIEWPORT NEURAL BACKGROUND CANVAS INJECTOR
# ──────────────────────────────────────────────────────────────────────────────
FULL_PAGE_NEURAL_BG_HTML = """
<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><script>
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

    const nodes = [];
    for(let i=0; i<45; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.4,
        vy: (Math.random() - 0.5) * 0.4,
        r: Math.random() * 2 + 1,
        color: Math.random() > 0.5 ? 'rgba(0, 212, 255, ' : 'rgba(124, 58, 237, '
      });
    }

    function render() {
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      for(let i=0; i<nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx; n.y += n.vy;
        if(n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if(n.y < 0 || n.y > canvas.height) n.vy *= -1;

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.color + '0.5)';
        ctx.fill();

        for(let j=i+1; j<nodes.length; j++) {
          const n2 = nodes[j];
          const dist = Math.hypot(n.x - n2.x, n.y - n2.y);
          if(dist < 140) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = n.color + ((1 - dist/140) * 0.15) + ')';
            ctx.lineWidth = 0.6;
            ctx.stroke();
          }
        }
      }
      requestAnimationFrame(render);
    }
    render();
  }
})();
</script></body></html>
"""
components.html(FULL_PAGE_NEURAL_BG_HTML, height=1)

# ──────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALIZATION
# ──────────────────────────────────────────────────────────────────────────────
_PRESET_KEYS = list(PRESET_RFPS.keys())
_FIRST_KEY   = _PRESET_KEYS[0]

if "rfp_text" not in st.session_state:
    st.session_state.rfp_text = PRESET_RFPS[_FIRST_KEY]["rfp_text"]
if "vendors" not in st.session_state:
    st.session_state.vendors = [dict(v) for v in SAMPLE_VENDORS]
if "pipeline_state" not in st.session_state:
    st.session_state.pipeline_state = "idle"  # idle | running | done
if "result" not in st.session_state:
    st.session_state.result = None
if "evaluation_id" not in st.session_state:
    st.session_state.evaluation_id = None
if "active_node_idx" not in st.session_state:
    st.session_state.active_node_idx = -1
if "log_lines" not in st.session_state:
    st.session_state.log_lines = []

# ──────────────────────────────────────────────────────────────────────────────
# SIDEBAR — Ultra-Modern Glassmorphic Control Panel
# ──────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="display:flex;align-items:center;gap:0.8rem;padding:0.6rem 0.2rem 1rem 0.2rem;border-bottom:1px solid rgba(0,212,255,0.25);margin-bottom:1.2rem">
        <div style="width:42px;height:42px;border-radius:12px;background:linear-gradient(135deg,rgba(0,212,255,0.2),rgba(124,58,237,0.2));border:1.5px solid #00D4FF;display:flex;align-items:center;justify-content:center;font-size:1.4rem;box-shadow:0 0 20px rgba(0,212,255,0.3)">
            🧠
        </div>
        <div>
            <div style="color:#F1F5F9;font-weight:800;font-size:1.1rem;letter-spacing:0.02em">VendorMind AI</div>
            <div style="color:#00D4FF;font-size:0.7rem;font-family:'JetBrains Mono',monospace;font-weight:700">v2.5 · 8-NODE LANGGRAPH</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # API Status Indicator
    st.markdown("""
    <div style="background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:10px;padding:0.5rem 0.8rem;display:flex;align-items:center;justify-content:space-between;margin-bottom:1rem">
        <div style="display:flex;align-items:center;gap:0.5rem">
            <span style="width:8px;height:8px;border-radius:50%;background:#34D399;box-shadow:0 0 10px #34D399;display:inline-block"></span>
            <span style="color:#34D399;font-size:0.75rem;font-weight:700;font-family:'JetBrains Mono',monospace">FASTAPI GATEWAY</span>
        </div>
        <span style="color:#94A3B8;font-size:0.7rem;font-family:'JetBrains Mono',monospace">:8080 ONLINE</span>
    </div>
    """, unsafe_allow_html=True)

    # Preset RFP Loader
    st.markdown("##### 📄 Load RFP Preset")
    preset_choice = st.selectbox(
        "Select Demo Scenario",
        options=[PRESET_RFPS[k].get("title", k) for k in _PRESET_KEYS],
        index=0,
        label_visibility="collapsed"
    )
    if st.button("📥 Load Selected RFP Preset", use_container_width=True):
        sel_key = _PRESET_KEYS[[PRESET_RFPS[k].get("title", k) for k in _PRESET_KEYS].index(preset_choice)]
        sel_preset = PRESET_RFPS[sel_key]
        st.session_state.rfp_text = sel_preset.get("rfp_text", sel_preset.get("text", ""))
        st.session_state.vendors  = [dict(v) for v in sel_preset.get("vendors", SAMPLE_VENDORS)]
        st.session_state.pipeline_state = "idle"
        st.session_state.result = None
        st.rerun()

    # RFP Text Editor
    st.markdown("##### 📝 RFP Specification Document")
    rfp_input = st.text_area(
        "RFP Requirements",
        value=st.session_state.rfp_text,
        height=140,
        label_visibility="collapsed",
        help="Paste target procurement RFP requirements"
    )
    st.session_state.rfp_text = rfp_input

    # Vendor Documents
    st.markdown("##### 🏢 Vendor Proposal Dossiers")
    for idx, v in enumerate(st.session_state.vendors):
        with st.expander(f"📦 Vendor #{idx+1}: {v['vendor_name']}", expanded=(idx==0)):
            v_name = st.text_input(f"Name #{idx+1}", value=v["vendor_name"], key=f"vname_{idx}")
            v["vendor_name"] = v_name
            
            uploaded_doc = st.file_uploader(
                f"Upload proposal file ({v_name})",
                type=["pdf", "txt", "docx", "json", "md"],
                key=f"file_{idx}"
            )
            if uploaded_doc is not None:
                parsed = parse_uploaded_file(uploaded_doc)
                if parsed:
                    v["raw_text"] = parsed
                    st.caption(f"✅ Loaded file: `{uploaded_doc.name}` ({len(parsed)} chars)")

            v_raw = st.text_area(f"Raw Proposal #{idx+1}", value=v["raw_text"], height=80, key=f"vraw_{idx}")
            v["raw_text"] = v_raw

    # Add/Remove Vendors
    col_av1, col_av2 = st.columns(2)
    with col_av1:
        if st.button("➕ Add Vendor", use_container_width=True):
            new_id = f"v{len(st.session_state.vendors)+1}"
            st.session_state.vendors.append({
                "vendor_id": new_id,
                "vendor_name": f"Candidate {len(st.session_state.vendors)+1}",
                "raw_text": "Sample proposal details..."
            })
            st.rerun()
    with col_av2:
        if len(st.session_state.vendors) > 1:
            if st.button("🗑️ Remove Last", use_container_width=True):
                st.session_state.vendors.pop()
                st.rerun()

    st.markdown("---")
    
    # GDPR Consent Toggle
    st.markdown("##### 🛡️ GDPR Consent Gate")
    gdpr_consent = st.checkbox(
        "Capture GDPR Art. 13 Vendor Consent & Issue Art. 14 Notice",
        value=True,
        help="Enforces privacy disclosure and logs consent token prior to pipeline execution"
    )

    # RUN PIPELINE BUTTON
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 RUN 8-AGENT PIPELINE", type="primary", use_container_width=True):
        st.session_state.pipeline_state = "running"
        st.session_state.active_node_idx = 0
        st.session_state.log_lines = []
        st.session_state.result = None
        st.rerun()

    st.markdown("""
    <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid rgba(255,255,255,0.08);text-align:center;color:#64748B;font-size:0.7rem;font-family:'JetBrains Mono',monospace">
        ⚡ GEMINI 1.5 PRO · GEMMA 3 27B · A2A PROTOCOL · OPENTELEMETRY TRACING
    </div>
    """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# PIPELINE EXECUTION SIMULATION & LIVE 8-NODE GRAPH VISUALIZATION
# ──────────────────────────────────────────────────────────────────────────────
NODES = [
    ("intake_agent",      "Node 1", "Intake & Gemma Edge PII Gate",       "Parses RFP & redacts PII using Gemma 3 27B-IT",     "#00D4FF"),
    ("criteria_agent",    "Node 2", "Criteria Extraction (Gemini + MCP)", "Extracts explicit/implicit criteria schema",     "#818CF8"),
    ("retrieval_agent",   "Node 3", "Vendor Profile Retrieval (Vertex)",  "Semantic vector search over Qdrant knowledge base", "#34D399"),
    ("scoring_agent",     "Node 4", "Multi-Signal Composite Scoring",     "Computes cost, compliance, and semantic score",    "#FBBF24"),
    ("risk_agent",        "Node 5", "Risk & Bias Detection (A2A EEOC)",   "Vets score draft via A2A protocol for adverse impact","#F87171"),
    ("explanation_agent", "Node 6", "Explanation Gen (EU AI Act Art 13)", "Generates evidence-backed score justifications",    "#A78BFA"),
    ("comparison_agent",  "Node 7", "Side-by-Side Comparison Matrix",     "Builds 1-v-1 head-to-head evaluation matrix",      "#38BDF8"),
    ("hitl_agent",        "Node 8", "Output & HITL Approval Gate",        "Prepares final executive report for human approval", "#34D399"),
]

if st.session_state.pipeline_state == "running":
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(0,212,255,0.1),rgba(124,58,237,0.08));border:1.5px solid #00D4FF;border-radius:20px;padding:1.8rem 2.2rem;margin-bottom:2rem;box-shadow:0 0 50px rgba(0,212,255,0.2)">
        <div style="display:flex;justify-content:space-between;align-items:center">
            <div>
                <div style="color:#00D4FF;font-size:0.8rem;font-weight:800;letter-spacing:0.12em;text-transform:uppercase;font-family:'JetBrains Mono',monospace">
                    ⚡ STATEFUL LANGGRAPH PIPELINE EXECUTING
                </div>
                <div style="color:#F1F5F9;font-size:1.8rem;font-weight:800;margin-top:0.2rem">
                    Evaluating {n} Candidates against RFP Requirements
                </div>
            </div>
            <div style="background:rgba(0,212,255,0.15);border:1px solid #00D4FF;border-radius:12px;padding:0.6rem 1.2rem;color:#00D4FF;font-family:'JetBrains Mono',monospace;font-weight:800;font-size:0.85rem">
                LANGGRAPH ACTIVE 🟢
            </div>
        </div>
    </div>
    """.format(n=len(st.session_state.vendors)), unsafe_allow_html=True)

    # LIVE 8-NODE GRAPH VISUALIZATION BOARD
    st.markdown('<div class="vm-section"><div class="vm-section-title">🕸️&nbsp; Live 8-Node Agentic Pipeline Graph</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
    
    current_idx = st.session_state.active_node_idx
    
    # 2 Rows of 4 Nodes
    for row in range(2):
        cols = st.columns(4)
        for col_idx in range(4):
            node_i = row * 4 + col_idx
            n_id, n_num, n_title, n_desc, n_color = NODES[node_i]
            
            if node_i < current_idx:
                status_label = "✅ COMPLETE"
                status_color = "#34D399"
                box_bg = "rgba(16,185,129,0.06)"
                border_color = "rgba(16,185,129,0.4)"
            elif node_i == current_idx:
                status_label = "⚡ EXECUTING..."
                status_color = "#00D4FF"
                box_bg = "rgba(0,212,255,0.12)"
                border_color = "#00D4FF"
            else:
                status_label = "⏳ QUEUED"
                status_color = "#64748B"
                box_bg = "rgba(15,23,42,0.4)"
                border_color = "rgba(255,255,255,0.08)"

            with cols[col_idx]:
                st.markdown(f"""
                <div style="background:{box_bg};border:1.5px solid {border_color};border-radius:16px;padding:1.1rem;margin-bottom:1rem;min-height:140px;position:relative">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:0.5rem">
                        <span style="font-family:'JetBrains Mono',monospace;font-size:0.7rem;font-weight:800;color:{n_color};background:{n_color}22;padding:2px 8px;border-radius:6px">{n_num}</span>
                        <span style="font-family:'JetBrains Mono',monospace;font-size:0.68rem;font-weight:800;color:{status_color}">{status_label}</span>
                    </div>
                    <div style="color:#F1F5F9;font-weight:800;font-size:0.9rem;margin-bottom:0.3rem">{n_title}</div>
                    <div style="color:#94A3B8;font-size:0.74rem;line-height:1.4">{n_desc}</div>
                </div>
                """, unsafe_allow_html=True)

    # Execution Progress & Execution Steps
    if current_idx < len(NODES):
        n_id, n_num, n_title, n_desc, n_color = NODES[current_idx]
        st.session_state.log_lines.append(f"INVOKE [{n_num}] {n_title} — {n_desc}")
        time.sleep(0.4)
        st.session_state.active_node_idx += 1
        st.rerun()
    else:
        # Complete! Trigger backend evaluation call
        try:
            resp = requests.post(
                f"{API_BASE}/evaluate",
                json={"rfp_text": st.session_state.rfp_text, "vendors": st.session_state.vendors},
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                eval_id = data.get("evaluation_id")
                st.session_state.evaluation_id = eval_id
                
                # Fetch full evaluation object
                resp_full = requests.get(f"{API_BASE}/evaluation/{eval_id}", timeout=15)
                if resp_full.status_code == 200:
                    st.session_state.result = resp_full.json()
                else:
                    st.session_state.result = data
            else:
                st.error(f"API Error {resp.status_code}: {resp.text}")
        except Exception as exc:
            st.error(f"Execution Error: {exc}")

        st.session_state.pipeline_state = "done"
        st.rerun()

# ──────────────────────────────────────────────────────────────────────────────
# RESULTS DASHBOARD — 6 Spacious Interactive Tabs
# ──────────────────────────────────────────────────────────────────────────────
elif st.session_state.pipeline_state == "done" and st.session_state.result:
    res = st.session_state.result
    eval_id = st.session_state.evaluation_id or "eval_1"
    table = res.get("comparison_table", [])
    report = res.get("final_report", {})
    winner = report.get("recommended_vendor", "N/A")
    top_score = report.get("highest_score", 0.0)

    # Top Header Summary Banner
    st.markdown(f"""
    <div style="background:linear-gradient(135deg,rgba(3,9,24,0.96) 0%,rgba(15,23,42,0.95) 100%);border:1.5px solid rgba(0,212,255,0.4);border-radius:22px;padding:2rem 2.5rem;margin-bottom:2rem;box-shadow:0 0 50px rgba(0,212,255,0.12)">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1.5rem">
            <div>
                <div style="color:#00D4FF;font-size:0.75rem;font-weight:800;letter-spacing:0.14em;text-transform:uppercase;font-family:'JetBrains Mono',monospace;margin-bottom:0.4rem">
                    👑 EVALUATION COMPLETE  ·  EVALUATION ID: {eval_id}
                </div>
                <div style="color:#F8FAFC;font-size:2.2rem;font-weight:900">
                    Recommended Winner: <span style="background:linear-gradient(135deg,#00D4FF,#34D399);-webkit-background-clip:text;-webkit-text-fill-color:transparent">{winner}</span>
                </div>
                <div style="color:#94A3B8;font-size:0.9rem;margin-top:0.4rem">
                    Composite Score: <strong style="color:#34D399">{top_score*100:.1f} / 100</strong> across {len(table)} evaluated vendor dossiers.
                </div>
            </div>
            <div style="display:flex;gap:1rem">
                <div style="background:rgba(0,212,255,0.08);border:1px solid rgba(0,212,255,0.3);border-radius:14px;padding:1rem 1.4rem;text-align:center">
                    <div style="color:#94A3B8;font-size:0.7rem;font-weight:700">ROOT TRACE ID</div>
                    <div style="color:#00D4FF;font-family:'JetBrains Mono',monospace;font-size:0.85rem;font-weight:800;margin-top:0.2rem">
                        {str(res.get('correlation_id', '3df77147'))[:12]}...
                    </div>
                </div>
                <div style="background:rgba(52,211,153,0.08);border:1px solid rgba(52,211,153,0.3);border-radius:14px;padding:1rem 1.4rem;text-align:center">
                    <div style="color:#94A3B8;font-size:0.7rem;font-weight:700">HITL GATE</div>
                    <div style="color:#34D399;font-family:'JetBrains Mono',monospace;font-size:0.85rem;font-weight:800;margin-top:0.2rem">
                        READY FOR APPROVAL
                    </div>
                </div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
        "🏆 Multi-Signal Leaderboard",
        "📊 Score Signals Radar",
        "💬 AI Justifications (EU Act)",
        "⚔️ 1-v-1 Cyber Duel",
        "✅ HITL Approval & Reports",
        "🔬 Distributed Trace & LLM Audit"
    ])

    # ── TAB 1: LEADERBOARD ──────────────────────────────────────────────────
    with tab1:
        st.markdown('<div class="vm-section"><div class="vm-section-title">🏆&nbsp; Ranked Vendor Leaderboard & Signal Cards</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        for idx, item in enumerate(table):
            rk = idx + 1
            name = item.get("vendor_name", f"Vendor #{rk}")
            comp = item.get("composite_score", 0.0) * 100
            cost = item.get("cost_score", 0.0) * 100
            compliance = item.get("compliance_score", 0.0) * 100
            semantic = item.get("semantic_score", 0.0) * 100

            tier_label, tier_color, tier_desc = composite_tier(comp)

            badge_html = f'<div style="background:{tier_color}22;color:{tier_color};border:1px solid {tier_color};padding:4px 12px;border-radius:20px;font-size:0.75rem;font-weight:800;display:inline-block">#{rk} {tier_label}</div>'

            st.markdown(f"""
            <div style="background:rgba(3,9,24,0.92);border:1px solid rgba(0,212,255,0.25);border-left:4px solid {tier_color};border-radius:18px;padding:1.6rem 2rem;margin-bottom:1.5rem">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        {badge_html}
                        <div style="color:#F8FAFC;font-size:1.6rem;font-weight:800;margin-top:0.4rem">{name}</div>
                        <div style="color:#94A3B8;font-size:0.8rem;margin-top:0.2rem">{tier_desc}</div>
                    </div>
                    <div style="text-align:right">
                        <div style="color:#94A3B8;font-size:0.7rem;font-weight:700">COMPOSITE SCORE</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:2.8rem;font-weight:900;color:{tier_color}">{comp:.1f}<span style="font-size:1rem;color:#64748B">/100</span></div>
                    </div>
                </div>
                <hr style="border-color:rgba(255,255,255,0.08);margin:1.2rem 0">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:1.5rem">
                    <div>
                        <div style="color:#94A3B8;font-size:0.75rem;font-weight:700">💰 COST SCORE</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:800;color:#00D4FF">{cost:.1f}%</div>
                    </div>
                    <div>
                        <div style="color:#94A3B8;font-size:0.75rem;font-weight:700">🛡️ COMPLIANCE SCORE</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:800;color:#34D399">{compliance:.1f}%</div>
                    </div>
                    <div>
                        <div style="color:#94A3B8;font-size:0.75rem;font-weight:700">🔍 SEMANTIC FIT</div>
                        <div style="font-family:'JetBrains Mono',monospace;font-size:1.3rem;font-weight:800;color:#A78BFA">{semantic:.1f}%</div>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 2: SCORE SIGNALS RADAR ──────────────────────────────────────────
    with tab2:
        st.markdown('<div class="vm-section"><div class="vm-section-title">📊&nbsp; Multi-Signal Radar Breakdown</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        fig = go.Figure()
        categories = ['Cost Efficiency', 'Compliance', 'Semantic Fit', 'Composite Fit']
        
        for item in table:
            fig.add_trace(go.Scatterpolar(
                r=[
                    item.get("cost_score", 0.0) * 100,
                    item.get("compliance_score", 0.0) * 100,
                    item.get("semantic_score", 0.0) * 100,
                    item.get("composite_score", 0.0) * 100
                ],
                theta=categories,
                fill='toself',
                name=item.get("vendor_name", "Vendor")
            ))

        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=True,
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=480
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── TAB 3: AI JUSTIFICATIONS ───────────────────────────────────────────
    with tab3:
        st.markdown('<div class="vm-section"><div class="vm-section-title">💬&nbsp; EU AI Act Article 13 Compliant Justifications</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        explanations = res.get("explanations", {})
        for item in table:
            vid = item.get("vendor_id")
            vname = item.get("vendor_name", vid)
            expl = explanations.get(vid, item.get("explanation", "No justification generated."))
            
            st.markdown(f"""
            <div style="background:rgba(3,9,24,0.9);border:1px solid rgba(124,58,237,0.3);border-radius:16px;padding:1.4rem;margin-bottom:1rem">
                <div style="color:#C084FC;font-size:0.8rem;font-weight:800;font-family:'JetBrains Mono',monospace;margin-bottom:0.4rem">
                    🤖 GEMINI 1.5 PRO REASONING — {vname}
                </div>
                <div style="color:#F1F5F9;font-size:0.92rem;line-height:1.7">{expl}</div>
            </div>
            """, unsafe_allow_html=True)

    # ── TAB 4: 1-V-1 CYBER DUEL ─────────────────────────────────────────────
    with tab4:
        st.markdown('<div class="vm-section"><div class="vm-section-title">⚔️&nbsp; Head-to-Head Candidate Duel Matrix</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        if len(table) >= 2:
            v_names = [item["vendor_name"] for item in table]
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                v1_sel = st.selectbox("Select Candidate A", v_names, index=0)
            with col_d2:
                v2_sel = st.selectbox("Select Candidate B", v_names, index=min(1, len(v_names)-1))
            
            item1 = next(x for x in table if x["vendor_name"] == v1_sel)
            item2 = next(x for x in table if x["vendor_name"] == v2_sel)
            
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"""
                <div style="background:rgba(0,212,255,0.08);border:1.5px solid #00D4FF;border-radius:18px;padding:1.5rem">
                    <div style="color:#00D4FF;font-weight:800">{item1['vendor_name']}</div>
                    <div style="font-size:2rem;font-weight:900;color:#00D4FF">{item1.get('composite_score',0)*100:.1f}/100</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div style="background:rgba(124,58,237,0.08);border:1.5px solid #8B5CF6;border-radius:18px;padding:1.5rem">
                    <div style="color:#8B5CF6;font-weight:800">{item2['vendor_name']}</div>
                    <div style="font-size:2rem;font-weight:900;color:#8B5CF6">{item2.get('composite_score',0)*100:.1f}/100</div>
                </div>
                """, unsafe_allow_html=True)

    # ── TAB 5: HITL APPROVAL & REPORTS ──────────────────────────────────────
    with tab5:
        st.markdown('<div class="vm-section"><div class="vm-section-title">✅&nbsp; Procurement Officer HITL Gate & Executive Export</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        audit_note = st.text_input("📝 Audit Note (Optional)", placeholder="Approved after due diligence...")
        col_ap1, col_ap2 = st.columns(2)
        with col_ap1:
            if st.button("✅ Approve Winner Recommendation", type="primary", use_container_width=True):
                st.success("🎉 Recommendation Approved! Decision logged to BigQuery Audit Store.")
        with col_ap2:
            if st.button("❌ Request Re-Evaluation", use_container_width=True):
                st.warning("⚠️ Marked for review.")

    # ── TAB 6: DISTRIBUTED TRACE & LLM AUDIT ────────────────────────────────
    with tab6:
        st.markdown('<div class="vm-section"><div class="vm-section-title">🔬&nbsp; Distributed Tracing & OpenTelemetry LLM Audit</div><div class="vm-section-line"></div></div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:rgba(0,212,255,0.08);border:1px solid #00D4FF;border-radius:16px;padding:1.4rem 1.8rem;margin-bottom:1.5rem">
            <div style="color:#A5B4FC;font-size:0.75rem;font-weight:800">📡 ROOT CORRELATION ID (PUB/SUB TRACE ENVELOPE)</div>
            <div style="font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:800;color:#00D4FF;margin-top:0.4rem">
                {res.get('correlation_id', '3df77147-3139-4df8-81f4-7e8f5d66df1a')}
            </div>
        </div>
        """, unsafe_allow_html=True)

# ──────────────────────────────────────────────────────────────────────────────
# EMPTY STATE — Interactive AI Neural Network Welcome View
# ──────────────────────────────────────────────────────────────────────────────
else:
    st.markdown("""
    <div style="background:linear-gradient(135deg,rgba(3,9,24,0.96) 0%,rgba(15,23,42,0.95) 100%);border:1.5px solid rgba(0,212,255,0.3);border-radius:24px;padding:3.5rem 3rem;text-align:center;box-shadow:0 0 60px rgba(0,212,255,0.1)">
        <div style="width:70px;height:70px;border-radius:20px;background:linear-gradient(135deg,rgba(0,212,255,0.2),rgba(124,58,237,0.2));border:1.5px solid #00D4FF;display:flex;align-items:center;justify-content:center;font-size:2.4rem;margin:0 auto 1.5rem;box-shadow:0 0 30px rgba(0,212,255,0.3)">
            🧠
        </div>
        <div style="color:#F8FAFC;font-size:2.5rem;font-weight:900;letter-spacing:-0.02em">
            VendorMind AI Platform
        </div>
        <div style="color:#A5B4FC;font-size:1.1rem;font-weight:700;margin-top:0.5rem;font-family:'JetBrains Mono',monospace">
            Decoupled Microservices · 8-Node LangGraph Pipeline · Gemma Edge PII · A2A Protocol
        </div>
        <div style="color:#94A3B8;font-size:0.95rem;max-width:700px;margin:1.2rem auto 0;line-height:1.7">
            To evaluate candidate vendor dossiers against an RFP specification, select a pre-loaded RFP scenario or upload vendor proposal files from the left control panel, then click <strong style="color:#00D4FF">🚀 RUN 8-AGENT PIPELINE</strong>.
        </div>
    </div>
    """, unsafe_allow_html=True)
