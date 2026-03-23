"""
MEMO — Monitor de Empresas & Mercados Operativos
ia-indata Agency · v3 final
"""
import io
import os
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
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
    page_title="MEMO · Energía & Mercados",
    page_icon="⚡",
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
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

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
    /* Texto secundario */
    --text2:  #cbd5e1;
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
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"],
[data-testid="stSidebar"] { display: none !important; }

.block-container { padding: 2.5rem 3rem 5rem !important; max-width: 1360px !important; }

/* ── HEADER ── Logo, subtítulo y badge "LIVE" */
.memo-header {
    display: flex; align-items: center; gap: 14px;
    padding-bottom: 22px; border-bottom: 1px solid var(--bdr); margin-bottom: 28px;
}
.memo-logo { font-family: 'DM Sans', sans-serif; font-size: 24px; font-weight: 700; color: var(--teal); letter-spacing: 0.01em; }
.memo-sub  { font-size: 12px; color: var(--muted); letter-spacing: 0.06em; text-transform: uppercase; margin-top: 3px; }
.memo-badge { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 11px; color: var(--teal); background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.2); padding: 5px 12px; border-radius: 20px; }

/* ── SEPARADORES DE SECCIÓN */
.section-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dim); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--bdr); }

/* ── TARJETAS KPI ───────────────────────────────────────────── */
.kpi-row { display: grid; gap: 12px; margin-bottom: 28px; }
.kpi-4 { grid-template-columns: repeat(4, 1fr); }
.kpi-3 { grid-template-columns: repeat(3, 1fr); }
.kpi-2 { grid-template-columns: repeat(2, 1fr); }
.kpi { background: var(--bg2); border: 1px solid var(--bdr); border-radius: 12px; padding: 20px 22px; position: relative; overflow: hidden; transition: border-color 0.2s, transform 0.15s; }
.kpi:hover { border-color: var(--bdr2); transform: translateY(-1px); background: var(--bg3); }
.kpi-accent { position: absolute; top: 0; left: 0; right: 0; height: 2px; border-radius: 12px 12px 0 0; }
.kpi-label { font-size: 11px; font-weight: 500; letter-spacing: 0.07em; text-transform: uppercase; color: var(--muted); margin-bottom: 10px; }
.kpi-value { font-family: 'Space Mono', monospace; font-size: 26px; font-weight: 700; color: var(--text); line-height: 1; margin-bottom: 8px; }
.kpi-value.lg { font-size: 32px; }
.kpi-delta { font-size: 12px; color: var(--dim); display: flex; align-items: center; gap: 5px; }
.kpi-delta.up   { color: var(--green); }
.kpi-delta.down { color: var(--red); }

/* ── SEMÁFOROS DE ESTADO */
.semaforo { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; padding: 6px 14px; border-radius: 20px; margin-top: 4px; }
.sem-bajo   { background: rgba(52,211,153,0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }
.sem-normal { background: rgba(251,191,36,0.10);  color: var(--amber); border: 1px solid rgba(251,191,36,0.22); }
.sem-alto   { background: rgba(248,113,113,0.10); color: var(--red);   border: 1px solid rgba(248,113,113,0.22); }

/* ── TABLA DE DATOS ──────────────────────────────────────────── */
.mkt-table { width: 100%; border-collapse: collapse; }
.mkt-table th { font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); padding: 10px 14px; border-bottom: 1px solid var(--bdr); text-align: left; }
.mkt-table td { padding: 12px 14px; border-bottom: 1px solid var(--bdr); font-size: 13px; color: var(--text); }
.mkt-table tr:hover td { background: var(--bg4); }
.mkt-table tr:last-child td { border-bottom: none; }
.cat-pill { display: inline-block; font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; }
.cat-Energia      { background: rgba(251,191,36,0.12);  color: var(--amber); }
.cat-Industrial   { background: rgba(196,181,253,0.12); color: var(--purple); }
.cat-Alimentacion { background: rgba(52,211,153,0.10);  color: var(--green); }
.cat-Indice       { background: rgba(45,212,191,0.10);  color: var(--teal); }
.cat-Divisa       { background: rgba(255,255,255,0.07); color: var(--dim); }
.price-mono { font-family: 'Space Mono', monospace; font-size: 13px; }

/* ── PESTAÑAS DE NAVEGACIÓN ──────────────────────────────────── */
[data-testid="stTabs"] [role="tablist"] { background: var(--bg2) !important; border: 1px solid var(--bdr) !important; border-radius: 10px !important; padding: 4px !important; gap: 2px !important; margin-bottom: 24px; }
[data-testid="stTabs"] [role="tab"] { background: transparent !important; border: none !important; color: var(--muted) !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; padding: 8px 18px !important; border-radius: 7px !important; transition: all 0.15s !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: var(--bg3) !important; color: var(--purple) !important; border: 1px solid rgba(196,181,253,0.2) !important; }
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) { color: var(--text) !important; background: rgba(255,255,255,0.04) !important; }

/* ── FILTROS Y DESPLEGABLES ──────────────────────────────────── */
[data-testid="stMultiSelect"] [data-baseweb="tag"] { background-color: rgba(196,181,253,0.15) !important; border: 1px solid rgba(196,181,253,0.35) !important; color: #c4b5fd !important; border-radius: 6px !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] [aria-label="Remove"] { color: #c4b5fd !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child,
[data-baseweb="select"] > div:first-child,
[data-testid="stSelectbox"] > div > div { background: var(--bg2) !important; border: 1px solid var(--bdr2) !important; border-radius: 8px !important; color: var(--text) !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child:focus-within,
[data-baseweb="select"] > div:first-child:focus-within { border-color: rgba(196,181,253,0.5) !important; box-shadow: 0 0 0 2px rgba(196,181,253,0.12) !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background: var(--bg3) !important; border: 1px solid var(--bdr2) !important; border-radius: 8px !important; }
[data-baseweb="menu"] li { color: var(--text) !important; }
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] { background: rgba(196,181,253,0.1) !important; color: #c4b5fd !important; }

/* ── BOTÓN DE DESCARGA CSV ───────────────────────────────────── */
[data-testid="stDownloadButton"] button { background: var(--bg3) !important; border: 1px solid var(--bdr2) !important; color: var(--purple) !important; border-radius: 8px !important; font-size: 12px !important; padding: 6px 14px !important; transition: all 0.15s !important; }
[data-testid="stDownloadButton"] button:hover { border-color: rgba(196,181,253,0.4) !important; background: rgba(196,181,253,0.08) !important; }

/* ── ACORDEONES / EXPANDERS ──────────────────────────────────── */
[data-testid="stExpander"] summary:hover { color: #c4b5fd !important; }
[data-testid="stExpander"] details { background: var(--bg2) !important; border: 1px solid var(--bdr) !important; border-radius: 10px !important; }

/* ── CONTENEDORES DE GRÁFICOS ────────────────────────────────── */
.chart-box { background: var(--bg2); border: 1px solid var(--bdr); border-radius: 12px; padding: 20px 20px 12px; margin-bottom: 16px; }
.chart-title { font-size: 12px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; color: var(--dim); margin-bottom: 2px; }

/* ── PIE DE PÁGINA ───────────────────────────────────────────── */
.memo-footer { border-top: 1px solid var(--bdr); padding-top: 20px; margin-top: 40px; display: flex; align-items: center; justify-content: space-between; }
.footer-left { font-size: 11px; color: var(--muted); font-family: 'Space Mono', monospace; }
.source-tag  { font-size: 10px; color: var(--muted); background: var(--bg2); border: 1px solid var(--bdr); padding: 3px 9px; border-radius: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
</style>
""", unsafe_allow_html=True)

# ── Conexión (STACK OFICIAL ia-indata) ────────────────────────────────────────
DB_URL = os.getenv("MEMO_NEON_URL")

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, 
                         pool_pre_ping=True, 
                         pool_recycle=300, 
                         connect_args={"connect_timeout": 10})

def load_data(query: str) -> pd.DataFrame:
    """Carga robusta usando SQLAlchemy (Evita desconexiones de Neon)"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            df = pd.read_sql(text(query), conn)
            if "fecha" in df.columns:
                df["fecha"] = pd.to_datetime(df["fecha"])
            return df
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

# ── Helpers ───────────────────────────────────────────────────────────────────
def csv_bytes(df): return df.to_csv(index=False).encode("utf-8")
def csv_nombre(p): return f"ia_indata_{p}.csv"

def tabla_html(df, highlight_col=None):
    html = '<table class="mkt-table"><thead><tr>'
    for c in df.columns: html += f'<th>{c}</th>'
    html += '</tr></thead><tbody>'
    for _, r in df.iterrows():
        html += '<tr>'
        for c, v in r.items():
            st_td = ""
            if c == highlight_col and pd.notna(v):
                val = float(v.replace('%','').replace('+','')) if isinstance(v,str) else v
                st_td = f' style="color:{"var(--green)" if val > 0 else "var(--red)"};font-weight:600"'
            
            if c == "Categoría":
                html += f'<td><span class="cat-pill cat-{v}">{v}</span></td>'
            elif "Precio" in c or "Valor" in c:
                html += f'<td class="price-mono"{st_td}>{v}</td>'
            else:
                html += f'<td{st_td}>{v}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

# ── Datos ─────────────────────────────────────────────────────────────────────
# Carga de vista agregada
df_mkt = load_data("SELECT * FROM memo.v_precios_mercados ORDER BY categoria, nombre")

if df_mkt.empty:
    st.error("No hay conexión con la base de datos o la vista v_precios_mercados está vacía.")
    st.stop()

# ── UI ────────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="memo-header">
  <div>
    <div class="memo-logo">ia-indata MEMO</div>
    <div class="memo-sub">Monitor de Empresas & Mercados Operativos · v3</div>
  </div>
  <div class="memo-badge">LIVE · Mercado Abierto</div>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs(["🌎 Mercados & Precios", "📊 Energía (PVPC)", "📉 Macro & IPC"])

# ── TAB 1: Mercados ───────────────────────────────────────────────────────────
with tabs[0]:
    st.markdown('<div class="section-label">Precios de Referencia (Hoy)</div>', unsafe_allow_html=True)
    
    # Grid de KPIs
    f_mkt = st.columns([4, 1, 1, 2])
    with f_mkt[0]:
        cats = sorted(df_mkt["categoria"].unique())
        sel_cats = st.multiselect("Filtrar por categoría", cats, default=cats)
    
    # Tabla renderizada
    df_show = df_mkt[df_mkt["categoria"].isin(sel_cats)].copy()
    df_show = df_show[["categoria", "nombre", "valor", "variacion_pct", "actualizado_el"]]
    df_show["variacion_pct"] = df_show["variacion_pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
    df_show.columns = ["Categoría", "Instrumento", "Precio/Valor", "Var. 24h", "Últ. Actualización"]
    
    st.markdown(tabla_html(df_show, "Var. 24h"), unsafe_allow_html=True)
    
    col_dl, col_sp = st.columns([2, 5])
    with col_dl:
        st.download_button("⬇ Descargar CSV", csv_bytes(df_show), 
                           csv_nombre("mercados"), "text/csv")

# ── TAB 2: Energía ────────────────────────────────────────────────────────────
with tabs[1]:
    st.markdown('<div class="section-label">Mercado Eléctrico Español (PVPC)</div>', unsafe_allow_html=True)
    
    df_luz = load_data("SELECT * FROM memo.v_precios_luz ORDER BY fecha DESC LIMIT 15")
    
    if not df_luz.empty:
        hoy_luz = df_luz.iloc[0]
        
        # Row KPIs
        st.markdown('<div class="kpi-row kpi-3">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown(f"""<div class="kpi"><div class="kpi-accent" style="background:var(--teal)"></div>
                <div class="kpi-label">Precio Medio Hoy</div>
                <div class="kpi-value">{hoy_luz['precio_medio']:.2f}</div>
                <div class="kpi-delta">€/MWh</div></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div class="kpi"><div class="kpi-accent" style="background:var(--amber)"></div>
                <div class="kpi-label">Máximo Diario</div>
                <div class="kpi-value">{hoy_luz['precio_max']:.2f}</div>
                <div class="kpi-delta">Hora: {hoy_luz['hora_max']}:00</div></div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""<div class="kpi"><div class="kpi-accent" style="background:var(--green)"></div>
                <div class="kpi-label">Mínimo Diario</div>
                <div class="kpi-value">{hoy_luz['precio_min']:.2f}</div>
                <div class="kpi-delta">Hora: {hoy_luz['hora_min']}:00</div></div>""", unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

        # Gráfico
        st.markdown('<div class="chart-box"><div class="chart-title">Evolución PVPC (Últimos 15 días)</div>', unsafe_allow_html=True)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df_luz["fecha"], y=df_luz["precio_medio"], 
                                mode='lines+markers', line=dict(color='#2dd4bf', width=3)))
        fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                          font=dict(family="DM Sans", color="#94a3b8"), height=250, 
                          margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        st.markdown('</div>', unsafe_allow_html=True)

# ── TAB 3: Macro ──────────────────────────────────────────────────────────────
with tabs[2]:
    st.markdown('<div class="section-label">Indicadores Macroeconómicos</div>', unsafe_allow_html=True)
    
    hist_ipc = load_data("SELECT * FROM memo.v_historico_ipc ORDER BY fecha DESC")
    
    if not hist_ipc.empty:
        # Añadir variación porcentual vs mes anterior en el DataFrame
        hist_ipc_asc = hist_ipc.sort_values("fecha")
        hist_ipc_asc["var_p"] = hist_ipc_asc["valor"].pct_change() * 100
        hist_ipc = hist_ipc_asc.sort_values("fecha", ascending=False).reset_index(drop=True)

        with st.expander("Ver histórico IPC España"):
            ti = hist_ipc.copy()
            ti["var_str"] = ti["var_p"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
            ti["fecha_f"] = ti["fecha"].dt.strftime("%Y-%m")
            ti_show = ti[["fecha_f","valor","var_str"]].copy()
            ti_show.columns = ["Período","IPC var. anual %","Variación vs anterior %"]
            st.markdown(tabla_html(ti_show, "Variación vs anterior %"), unsafe_allow_html=True)
            ipc_c1, ipc_c2 = st.columns([2, 5])
            with ipc_c1:
                st.download_button("⬇ CSV IPC", csv_bytes(ti_show),
                    csv_nombre("memo_ipc"), "text/csv", key="dl_ipc")
            with ipc_c2:
                st.caption(f"{len(ti_show)} registros")

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="memo-footer">
  <div class="footer-left">ia-indata Agency · MEMO v3 · 
    <a href="https://github.com/mborrillo/ia-indata-agency" 
       style="color:var(--teal);text-decoration:none">GitHub ↗</a>
  </div>
  <div class="source-tags">
    <span class="source-tag">REE ESIOS</span>
    <span class="source-tag">Yahoo Finance</span>
    <span class="source-tag">INE Tempus</span>
    <span class="source-tag">ECB API</span>
  </div>
</div>
""", unsafe_allow_html=True)
