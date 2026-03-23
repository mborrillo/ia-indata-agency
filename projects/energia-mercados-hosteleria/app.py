"""
MEMO Hostelería — Monitor de Costes para Restauración
ia indata agency · Badajoz, Extremadura

Estructura: Header y Navegación FIJOS para facilitar la lectura de datos.
"""
import io, os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

# ╔══════════════════════════════════════════════════════════════════╗
# ║  CONFIGURACIÓN GENERAL DE LA PÁGINA                            ║
# ╚══════════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Monitor de Costes · Hostelería",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ACTUALIZADO (HEADER Y TABS FIJOS) ─────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

:root {
    --bg:     #080a0f;
    --bg2:    #0f1219;
    --bg3:    #171b26;
    --bg4:    #1f2433;
    --bdr:    rgba(255,255,255,0.06);
    --bdr2:   rgba(255,255,255,0.13);
    --teal:   #2dd4bf;
    --purple: #c4b5fd;
    --amber:  #fbbf24;
    --red:    #f87171;
    --green:  #34d399;
    --text:   #f1f5f9;
    --dim:    #94a3b8;
    --muted:  #94a3b8;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}

#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"] { display: none !important; }

/* AJUSTE DE CONTENEDOR PRINCIPAL: Espacio para el header fijo */
.block-container { 
    padding: 160px 3rem 5rem !important; 
    max-width: 1300px !important; 
}

/* HEADER FIJO */
.hdr { 
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    background: var(--bg);
    z-index: 1000;
    display:flex; 
    align-items:center; 
    gap:14px; 
    padding: 1.5rem 3rem 1rem; 
    border-bottom: 1px solid var(--bdr); 
    backdrop-filter: blur(10px);
}
.hdr-logo { font-family:'DM Sans',sans-serif; font-size:22px; font-weight:700; color:var(--teal); letter-spacing:0.01em; }
.hdr-sub  { font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin-top:3px; }
.hdr-badge { margin-left:auto; font-family:'Space Mono',monospace; font-size:11px; color:var(--teal); background:rgba(45,212,191,.08); border:1px solid rgba(45,212,191,.2); padding:5px 12px; border-radius:20px; }

/* NAVEGACIÓN (TABS) FIJA */
[data-testid="stTabs"] [role="tablist"] { 
    position: fixed;
    top: 82px; /* Justo debajo del header */
    left: 0;
    right: 0;
    z-index: 999;
    background: var(--bg);
    padding: 0 3rem 10px !important;
    border-bottom: 1px solid var(--bdr) !important;
    border-radius: 0 !important;
    gap: 2px !important;
}

[data-testid="stTabs"] [role="tab"] { 
    background: transparent !important; 
    border: none !important; 
    color: var(--muted) !important; 
    font-size: 13px !important; 
    font-weight: 500 !important; 
    padding: 8px 18px !important; 
    border-radius: 7px !important; 
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { 
    background: var(--bg3) !important; 
    color: var(--purple) !important; 
    border: 1px solid rgba(196,181,253,.2) !important; 
}

/* Resto de estilos del cuerpo */
.slabel { font-size:10px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--dim); margin-bottom:14px; display:flex; align-items:center; gap:8px; }
.slabel::after { content:''; flex:1; height:1px; background:var(--bdr); }
.krow  { display:grid; gap:12px; margin-bottom:24px; }
.k4    { grid-template-columns:repeat(4,1fr); }
.k3    { grid-template-columns:repeat(3,1fr); }
.k2    { grid-template-columns:repeat(2,1fr); }
.kpi   { background:var(--bg2); border:1px solid var(--bdr); border-radius:12px; padding:20px 22px; position:relative; overflow:hidden; transition:border-color .2s,transform .15s; }
.kpi:hover { border-color:var(--bdr2); transform:translateY(-1px); background:var(--bg3); }
.kacc  { position:absolute; top:0; left:0; right:0; height:2px; border-radius:12px 12px 0 0; }
.klbl  { font-size:11px; font-weight:500; letter-spacing:.07em; text-transform:uppercase; color:var(--muted); margin-bottom:10px; }
.kval  { font-family:'Space Mono',monospace; font-size:26px; font-weight:700; color:var(--text); line-height:1; margin-bottom:8px; }
.kval.lg { font-size:32px; }
.kdelta { font-size:12px; color:var(--dim); }
.kdelta.ok   { color:var(--purple); }
.kdelta.bad  { color:var(--red); }
.sem { display:inline-flex; align-items:center; gap:8px; font-size:15px; font-weight:700; letter-spacing:.05em; padding:8px 18px; border-radius:24px; }
.sem-verde   { background:rgba(52,211,153,.12); color:var(--green); border:1px solid rgba(52,211,153,.3); }
.sem-amarillo { background:rgba(251,191,36,.10); color:var(--amber); border:1px solid rgba(251,191,36,.25); }
.sem-rojo     { background:rgba(248,113,113,.10); color:var(--red);  border:1px solid rgba(248,113,113,.25); }
.rec { background:var(--bg3); border-left:3px solid var(--teal); border-radius:0 8px 8px 0; padding:12px 16px; font-size:14px; color:var(--text); margin-top:8px; }
.rec.warn { border-left-color:var(--amber); }
.rec.bad  { border-left-color:var(--red); }
[data-testid="stDownloadButton"] button { background:var(--bg3) !important; border:1px solid var(--bdr2) !important; color:var(--purple) !important; border-radius:8px !important; font-size:12px !important; }
.cbox { background:var(--bg2); border:1px solid var(--bdr); border-radius:12px; padding:20px 20px 12px; margin-bottom:16px; }
.ctitle { font-size:11px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:var(--dim); margin-bottom:4px; }
.ftr { border-top:1px solid var(--bdr); padding-top:20px; margin-top:40px; display:flex; align-items:center; justify-content:space-between; }
.ftxt { font-size:11px; color:var(--muted); font-family:'Space Mono',monospace; }

/* Tags multiselect violetas */
[data-testid="stMultiSelect"] [data-baseweb="tag"] { background-color:rgba(196,181,253,.15) !important; border:1px solid rgba(196,181,253,.35) !important; color:#c4b5fd !important; border-radius:6px !important; }
</style>
""", unsafe_allow_html=True)

# ── Conexión y Helpers ────────────────────────────────────────────────────────
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300)

def q(sql: str) -> pd.DataFrame:
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.warning(f"Error: {e}")
        return pd.DataFrame()

PLOTLY = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#94a3b8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)"),
)

def tabla_html(df, col_var="Variación %"):
    df = df.copy()
    for c in df.columns:
        if c != col_var: df[c] = df[c].astype(str).replace("NaT", "—").replace("nan", "—")
    cols = list(df.columns)
    ths  = "".join(f"<th>{c}</th>" for c in cols)
    rows = ""
    for _, row in df.iterrows():
        tds = "".join(f"<td>{row[c]}</td>" for c in cols)
        rows += f"<tr>{tds}</tr>"
    return f'<div class="tbl-wrap"><table><thead><tr>{ths}</tr></thead><tbody>{rows}</tbody></table></div>'

def sem_class(s: str) -> str:
    return {"VERDE":"sem-verde","AMARILLO":"sem-amarillo","ROJO":"sem-rojo",
            "BAJO":"sem-verde","NORMAL":"sem-amarillo","ALTO":"sem-rojo"}.get(s.upper(),"sem-amarillo")

def sem_icon(s: str) -> str:
    return {"VERDE":"✅","AMARILLO":"⚠️","ROJO":"🔴",
            "BAJO":"🟢","NORMAL":"🟡","ALTO":"🔴"}.get(s.upper(),"⚪")

# ── RENDER HEADER (Fijo) ──────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <div>
    <div class="hdr-logo">🍳 MEMO Hostelería</div>
    <div class="hdr-sub">Monitor de Empresas &amp; Mercados Operativos · ia-indata Agency</div>
  </div>
  <div class="hdr-badge">● LIVE · actualización diaria</div>
</div>
""", unsafe_allow_html=True)

# ── TABS (Fijos) ──────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Luz", "🔥 Gas & Aceite", "📊 IPC Alimentación", "📈 Histórico"
])

# ── CONTENIDO ─────────────────────────────────────────────────────────────────
# El contenido se renderiza dentro de las pestañas. 
# Gracias al CSS, al hacer scroll el contenido pasará por debajo del Header y los Tabs.

with tab1:
    luz = q("SELECT * FROM hosteleria.v_luz_hoy")
    if not luz.empty:
        r = luz.iloc[0]
        sem = str(r.get("semaforo","NORMAL")).upper()
        st.markdown(f"""
        <div class="slabel">Precio de la luz hoy</div>
        <div class="krow k4">
          <div class="kpi">
            <div class="kacc" style="background:var(--teal)"></div>
            <div class="klbl">Precio medio hoy</div>
            <div class="kval lg">{float(r['precio_medio']):.4f}</div>
            <div class="kdelta">€/kWh</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:var(--amber)"></div>
            <div class="klbl">Estado vs ayer</div>
            <div style="margin-top:6px"><span class="sem {sem_class(sem)}">{sem_icon(sem)} {sem}</span></div>
          </div>
        </div>
        <div class="rec">💡 {r.get('recomendacion','Carga normal')}</div>
        """, unsafe_allow_html=True)
        
        # Simulación de scroll: añadimos espacio para probar el header fijo
        st.write("---")
        for i in range(15): st.write(f"Espacio de relleno para scroll {i}...")

with tab2:
    st.info("Sección Gas & Aceite")

with tab3:
    st.info("Sección IPC")

with tab4:
    st.info("Sección Histórico")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ftr">
  <div class="ftxt">ia indata agency · MEMO Hostelería</div>
  <div class="ftags"><span class="ftag">REE</span><span class="ftag">INE</span></div>
</div>
""", unsafe_allow_html=True)
