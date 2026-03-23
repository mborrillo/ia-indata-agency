"""
MEMO Hostelería — Monitor de Costes para Restauración
ia-indata Agency · Badajoz, Extremadura

Diseño: sin jerga financiera. Todo en lenguaje de hostelero.
Regla de oro: cualquier KPI debe entenderse en menos de 5 segundos.
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
# ║  page_title  → texto que aparece en la pestaña del navegador   ║
# ║  page_icon   → emoji o URL de imagen que aparece en la pestaña ║
# ║  layout      → "wide" usa todo el ancho | "centered" centra    ║
# ╚══════════════════════════════════════════════════════════════════╝
st.set_page_config(
    page_title="Monitor de Costes · Hostelería",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* FUENTES — cambiar aquí para usar otras tipografías de Google Fonts
   Space Mono: números y valores (monoespaciada, estilo terminal)
   DM Sans: textos y etiquetas (legible, moderna)
   Para cambiar: reemplaza el nombre en la URL y en font-family */
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

/* ════════════════════════════════════════════════════════════════
   PALETA DE COLORES — edita aquí para cambiar colores globalmente
   Todos los elementos de la app usan estas variables.
   ════════════════════════════════════════════════════════════════ */
:root {
    /* Fondo base — el más oscuro. Cambiar para modo claro: #f8fafc */
    --bg:     #080a0f;
    /* Fondo de cards y paneles — una capa más clara que --bg */
    --bg2:    #0f1219;
    /* Fondo en hover y estados activos */
    --bg3:    #171b26;
    /* Fondo más claro — filas de tabla en hover */
    --bg4:    #1f2433;
    /* Borde por defecto — opacidad baja (sutil) */
    --bdr:    rgba(255,255,255,0.06);
    /* Borde en hover — más visible */
    --bdr2:   rgba(255,255,255,0.13);
    /* Color principal — logo, acentos, links */
    --teal:   #2dd4bf;
    /* Color secundario — tabs activos, variaciones, botones */
    --purple: #c4b5fd;
    /* Advertencia — semáforo NORMAL, precios en rango */
    --amber:  #fbbf24;
    /* Alerta — semáforo ALTO, variaciones negativas */
    --red:    #f87171;
    /* Solo para semáforos de estado BAJO/VERDE (buena noticia) */
    --green:  #34d399;
    /* Texto principal — blanco suave. Más blanco: #ffffff */
    --text:   #f1f5f9;
    /* Texto terciario — captions, labels de KPI */
    --dim:    #94a3b8;
    /* Texto muy apagado — pie de página, separadores */
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
.block-container { padding: 2.5rem 3rem 5rem !important; max-width: 1300px !important; }

/* Header */
.hdr { display:flex; align-items:center; gap:14px; padding-bottom:20px; border-bottom:1px solid var(--bdr); margin-bottom:28px; }
.hdr-logo { font-family:'DM Sans',sans-serif; font-size:22px; font-weight:700; color:var(--teal); letter-spacing:0.01em; }
.hdr-sub  { font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin-top:3px; }
.hdr-badge { margin-left:auto; font-family:'Space Mono',monospace; font-size:11px; color:var(--teal); background:rgba(45,212,191,.08); border:1px solid rgba(45,212,191,.2); padding:5px 12px; border-radius:20px; }

/* Section label */
.slabel { font-size:10px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--dim); margin-bottom:14px; display:flex; align-items:center; gap:8px; }
.slabel::after { content:''; flex:1; height:1px; background:var(--bdr); }

/* KPI cards */
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
.kdelta.warn { color:var(--amber); }
.kdelta.bad  { color:var(--red); }

/* Semáforo grande */
.sem { display:inline-flex; align-items:center; gap:8px; font-size:15px; font-weight:700; letter-spacing:.05em; padding:8px 18px; border-radius:24px; margin-top:4px; }
.sem-verde    { background:rgba(52,211,153,.12); color:var(--green); border:1px solid rgba(52,211,153,.3); }
.sem-amarillo { background:rgba(251,191,36,.10); color:var(--amber); border:1px solid rgba(251,191,36,.25); }
.sem-rojo     { background:rgba(248,113,113,.10); color:var(--red);  border:1px solid rgba(248,113,113,.25); }
.sem-bajo     { background:rgba(52,211,153,.12); color:var(--green); border:1px solid rgba(52,211,153,.3); }
.sem-normal   { background:rgba(251,191,36,.10); color:var(--amber); border:1px solid rgba(251,191,36,.25); }
.sem-alto     { background:rgba(248,113,113,.10); color:var(--red);  border:1px solid rgba(248,113,113,.25); }

/* Recomendación */
.rec { background:var(--bg3); border-left:3px solid var(--teal); border-radius:0 8px 8px 0; padding:12px 16px; font-size:14px; color:var(--text); margin-top:8px; }
.rec.warn { border-left-color:var(--amber); }
.rec.bad  { border-left-color:var(--red); }

/* Tabs */
[data-testid="stTabs"] [role="tablist"] { background:var(--bg2) !important; border:1px solid var(--bdr) !important; border-radius:10px !important; padding:4px !important; gap:2px !important; margin-bottom:24px; }
[data-testid="stTabs"] [role="tab"] { background:transparent !important; border:none !important; color:var(--muted) !important; font-family:'DM Sans',sans-serif !important; font-size:13px !important; font-weight:500 !important; padding:8px 18px !important; border-radius:7px !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background:var(--bg3) !important; color:var(--purple) !important; border:1px solid rgba(196,181,253,.2) !important; }

/* Descarga */
[data-testid="stDownloadButton"] button { background:var(--bg3) !important; border:1px solid var(--bdr2) !important; color:var(--purple) !important; border-radius:8px !important; font-size:12px !important; }

/* Chart box */
.cbox { background:var(--bg2); border:1px solid var(--bdr); border-radius:12px; padding:20px 20px 12px; margin-bottom:16px; }
.ctitle { font-size:11px; font-weight:500; letter-spacing:.06em; text-transform:uppercase; color:var(--dim); margin-bottom:4px; }

/* Footer */
.ftr { border-top:1px solid var(--bdr); padding-top:20px; margin-top:40px; display:flex; align-items:center; justify-content:space-between; }
.ftxt { font-size:11px; color:var(--muted); font-family:'Space Mono',monospace; }
.ftags { display:flex; gap:10px; }
.ftag { font-size:10px; color:var(--muted); background:var(--bg2); border:1px solid var(--bdr); padding:3px 9px; border-radius:4px; text-transform:uppercase; letter-spacing:.05em; }

/* ── FILTROS Y DESPLEGABLES ────────────────────────────────────────────────
   Tags seleccionados en violeta — no rojo por defecto de Streamlit */
[data-testid="stMultiSelect"] [data-baseweb="tag"] { background-color:rgba(196,181,253,.15) !important; border:1px solid rgba(196,181,253,.35) !important; color:#c4b5fd !important; border-radius:6px !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] [aria-label="Remove"] { color:#c4b5fd !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child,
[data-baseweb="select"] > div:first-child { background:var(--bg2) !important; border:1px solid var(--bdr2) !important; border-radius:8px !important; color:var(--text) !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child:focus-within,
[data-baseweb="select"] > div:first-child:focus-within { border-color:rgba(196,181,253,.5) !important; box-shadow:0 0 0 2px rgba(196,181,253,.12) !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background:var(--bg3) !important; border:1px solid var(--bdr2) !important; border-radius:8px !important; }
[data-baseweb="menu"] li { color:var(--text) !important; }
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] { background:rgba(196,181,253,.1) !important; color:#c4b5fd !important; }
</style>
""", unsafe_allow_html=True)

# ── Conexión (STACK OFICIAL ia-indata) ────────────────────────────────────────
DB_URL = os.getenv("HOSTELERIA_NEON_URL") 

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, 
                         pool_pre_ping=True, 
                         pool_recycle=300, 
                         connect_args={"connect_timeout": 10})

def q(sql: str) -> pd.DataFrame:
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        return pd.DataFrame()

PLOTLY = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#94a3b8", size=12),
    margin=dict(t=10, b=10, l=10, r=10),
    hoverlabel=dict(bgcolor="#171b26", font_size=12, font_family="DM Sans")
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def color_var(v):
    if pd.isna(v): return "var(--muted)"
    return "var(--red)" if v > 0 else "var(--green)"

def tabla_html(df):
    html = '<table class="mkt-table"><thead><tr>'
    for c in df.columns: html += f'<th>{c}</th>'
    html += '</tr></thead><tbody>'
    for _, r in df.iterrows():
        html += '<tr>'
        for i, (c, v) in enumerate(r.items()):
            if i == 0: # Fecha
                html += f'<td>{v}</td>'
            elif c == "Variación %":
                val = float(v.replace('%','')) if isinstance(v,str) else v
                col = "var(--red)" if val > 0 else "var(--green)"
                html += f'<td style="color:{col};font-weight:600">{v}</td>'
            else:
                html += f'<td class="price-mono">{v}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# ── Carga de Datos ────────────────────────────────────────────────────────────
df_raw = q("SELECT * FROM hosteleria.v_dashboard_hosteleria ORDER BY fecha DESC")

if df_raw.empty:
    st.error("No se han podido cargar los datos de la base de datos.")
    st.stop()

df = df_raw.copy()
df["fecha"] = pd.to_datetime(df["fecha"])
hoy = df.iloc[0]

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="hdr">
  <div>
    <div class="hdr-logo">MEMO Hostelería</div>
    <div class="hdr-sub">Monitor de costes para restauración · ia-indata Agency</div>
  </div>
  <div class="hdr-badge">LIVE · {hoy['fecha'].strftime('%d %b %Y')}</div>
</div>
""", unsafe_allow_html=True)

# ── FILTROS ───────────────────────────────────────────────────────────────────
f_cols = st.columns([3, 2, 2, 2])
with f_cols[0]:
    cats = sorted(df["categoria"].unique())
    sel_cat = st.multiselect("Categorías", cats, default=["Energía", "Alimentación"])

# Filtrado
filt = df[df["categoria"].isin(sel_cat)].copy()
if filt.empty:
    st.info("Selecciona al menos una categoría para ver los datos.")
    st.stop()

# ── KPIs ──────────────────────────────────────────────────────────────────────
st.markdown('<div class="slabel">Resumen de Impacto en Costes</div>', unsafe_allow_html=True)

k_cols = st.columns(4)
# Solo mostramos KPIs de las categorías seleccionadas que sean relevantes
cat_kpis = filt.groupby("categoria").first().reset_index()

for i, (idx, row) in enumerate(cat_kpis.iterrows()):
    if i >= 4: break # Máximo 4 KPIs
    with k_cols[i]:
        v = row["valor"]
        var = row["var_30d"]
        unit = "€/MWh" if row["categoria"] == "Energía" else "Índice"
        if "Aceite" in row["nombre"]: unit = "€/kg"
        
        c_var = "ok" if var < 0 else "bad"
        signo = "+" if var > 0 else ""
        
        st.markdown(f"""
        <div class="kpi">
            <div class="kacc" style="background:var(--teal)"></div>
            <div class="klbl">{row['nombre']}</div>
            <div class="kval">{v:.2f}<span style="font-size:14px;color:var(--dim);margin-left:4px">{unit}</span></div>
            <div class="kdelta {c_var}">{signo}{var:.1f}% vs mes anterior</div>
        </div>
        """, unsafe_allow_html=True)

# ── Visualización Detallada ───────────────────────────────────────────────────
st.markdown('<div class="slabel">Análisis por Categoría</div>', unsafe_allow_html=True)

tabs = st.tabs([c for c in sel_cat])

for i, cat in enumerate(sel_cat):
    with tabs[i]:
        c_df = filt[filt["categoria"] == cat].copy()
        c_hoy = c_df.iloc[0]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f'<div class="ctitle">Estado actual: {cat}</div>', unsafe_allow_html=True)
            
            # Lógica de semáforo (Simplificada para el ejemplo)
            sem_class = "sem-normal"
            sem_txt = "PRECIO ESTABLE"
            if c_hoy["var_30d"] > 5:
                sem_class = "sem-alto"
                sem_txt = "ALERTA DE SUBIDA"
            elif c_hoy["var_30d"] < -5:
                sem_class = "sem-bajo"
                sem_txt = "OPORTUNIDAD DE COMPRA"
                
            st.markdown(f'<div class="sem {sem_class}">{sem_txt}</div>', unsafe_allow_html=True)
            
            # Recomendación dinámica
            rec_html = ""
            if cat == "Energía":
                if c_hoy["var_30d"] > 0:
                    rec_html = '<div class="rec bad"><b>Ojo:</b> La luz sube. Desplaza procesos de alto consumo (lavavajillas, hornos) a horas valle si puedes.</div>'
                else:
                    rec_html = '<div class="rec"><b>Dato:</b> Precio de energía en descenso. Buen momento para mantener consumos estándar.</div>'
            elif cat == "Alimentación":
                if "Aceite" in c_hoy["nombre"] and c_hoy["var_30d"] > 2:
                    rec_html = '<div class="rec bad"><b>Alerta Aceite:</b> Tendencia alcista. Revisa escandallos de frituras y controla mermas.</div>'
                else:
                    rec_html = f'<div class="rec">Los precios de {c_hoy["nombre"]} se mantienen en rangos operativos.</div>'
            
            st.markdown(rec_html, unsafe_allow_html=True)

        with col2:
            st.markdown(f'<div class="ctitle">Evolución Histórica (90 días)</div>', unsafe_allow_html=True)
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=c_df["fecha"], y=c_df["valor"],
                mode='lines', line=dict(color='#2dd4bf', width=3),
                fill='tozeroy', fillcolor='rgba(45,212,191,0.05)',
                name=cat
            ))
            fig.update_layout(**PLOTLY, height=220)
            fig.update_xaxes(showgrid=False, nticks=5)
            fig.update_yaxes(showgrid=True, gridcolor="rgba(255,255,255,0.05)")
            st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        # Tabla de histórico
        with st.expander(f"Ver histórico de precios: {cat}"):
            t_df = c_df.copy()
            t_df["fecha_f"] = t_df["fecha"].dt.strftime('%d/%m/%Y')
            t_df["var_f"] = t_df["var_30d"].apply(lambda x: f"{x:+.1f}%")
            t_df_show = t_df[["fecha_f", "valor", "var_f"]].copy()
            t_df_show.columns = ["Fecha", "Precio/Índice", "Variación %"]
            
            st.markdown(tabla_html(t_df_show), unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ftr">
  <div class="ftxt">ia-indata Agency · MEMO Hostelería · 
    <a href="https://github.com/mborrillo/ia-indata-agency" 
       style="color:var(--teal);text-decoration:none">GitHub ↗</a>
  </div>
  <div class="ftags">
    <span class="ftag">REE ESIOS</span>
    <span class="ftag">INE TEMPUS</span>
    <span class="ftag">Yahoo Finance</span>
  </div>
</div>
""", unsafe_allow_html=True)
