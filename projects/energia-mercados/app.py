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

/* ══════════════════════════════════════════════════════════════════
   HEADER FIJO — Logo y tabs quedan visibles al hacer scroll
   ══════════════════════════════════════════════════════════════════ */
.sticky-header {
    position: sticky;
    top: 0;
    z-index: 999;
    background: var(--bg);
    padding: 1.5rem 0 1rem 0;
    margin-bottom: 1.5rem;
    border-bottom: 1px solid var(--bdr);
}

/* ── HEADER ── Logo, subtítulo y badge "LIVE"
   .memo-logo / .hdr-logo → tamaño y color del nombre de la app
   .memo-sub  / .hdr-sub  → subtítulo bajo el logo
   .memo-badge / .hdr-badge → píldora "LIVE" arriba a la derecha */
.memo-header {
    display: flex; align-items: center; gap: 14px;
    padding-bottom: 22px; border-bottom: 1px solid var(--bdr); margin-bottom: 20px;
}
.memo-logo { font-family: 'DM Sans', sans-serif; font-size: 24px; font-weight: 700; color: var(--teal); letter-spacing: 0.01em; }
.memo-sub  { font-size: 12px; color: var(--muted); letter-spacing: 0.06em; text-transform: uppercase; margin-top: 3px; }
.memo-badge { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 11px; color: var(--teal); background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.2); padding: 5px 12px; border-radius: 20px; }

/* ── TABS — pestañas de sección
   .tab-bar → contenedor de los tabs
   .tab-btn → cada botón/tab individual */
.tab-bar { display: flex; gap: 6px; padding-bottom: 0; }
.tab-btn { font-size: 13px; font-weight: 500; letter-spacing: 0.02em; color: var(--dim); background: transparent; border: 1px solid var(--bdr); padding: 9px 18px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { background: var(--bg3); border-color: var(--bdr2); color: var(--text2); }
.tab-btn.active { background: var(--bg3); border-color: var(--purple); color: var(--purple); }

/* ── SEPARADORES DE SECCIÓN — línea con texto en mayúsculas
   font-size → tamaño del texto del separador
   color     → usa --dim para sutil o --text para destacado */
.section-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dim); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--bdr); }

/* ── TARJETAS KPI ─────────────────────────────────────────────
   .kpi-row.k4 → grid de 4 columnas | .k3 → 3 | .k2 → 2
   .kpi        → tarjeta completa: border-radius para redondeo
   .kpi-accent → barra de color de 2px en la parte superior
   .kpi-label  → etiqueta pequeña arriba (ej. "PRECIO MEDIO HOY")
   .kpi-value  → número grande principal | .lg → versión más grande
   .kpi-delta  → texto pequeño debajo del valor principal
   .kpi-delta.up / .down → colores para delta positivo/negativo */
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

/* ── SEMÁFOROS DE ESTADO — píldoras de color
   .sem-bajo / .sem-verde   → estado favorable (verde)
   .sem-normal / .sem-amarillo → estado neutro (ámbar)
   .sem-alto / .sem-rojo    → estado desfavorable (rojo)
   Para cambiar colores: editar background, color y border */
.semaforo { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; padding: 6px 14px; border-radius: 20px; margin-top: 4px; }
.sem-bajo   { background: rgba(52,211,153,0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }
.sem-normal { background: rgba(251,191,36,0.10);  color: var(--amber); border: 1px solid rgba(251,191,36,0.22); }
.sem-alto   { background: rgba(248,113,113,0.10); color: var(--red);   border: 1px solid rgba(248,113,113,0.22); }

/* ── TABLA DE DATOS ────────────────────────────────────────────
   .mkt-table th → cabeceras: font-size, color, padding
   .mkt-table td → celdas: font-size, color, padding
   .cat-pill     → píldoras de categoría en la tabla
   Cada .cat-[nombre] tiene su propio color de fondo y texto */
.mkt-table { width: 100%; border-collapse: collapse; }
.mkt-table th { font-size: 10px; font-weight: 600; letter-spacing: 0.1em; text-transform: uppercase; color: var(--muted); padding: 10px 14px; border-bottom: 1px solid var(--bdr); text-align: left; }
.mkt-table td { padding: 12px 14px; border-bottom: 1px solid var(--bdr); font-size: 13px; color: var(--text); }
.mkt-table tr:hover td { background: var(--bg4); }
.mkt-table tr:last-child td { border-bottom: none; }
.cat-pill { display: inline-block; font-size: 10px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; padding: 3px 8px; border-radius: 4px; }
.cat-Energia      { background: rgba(251,191,36,0.12);  color: var(--amber); }
.cat-Industrial   { background: rgba(196,181,253,0.12); color: var(--purple); }
.cat-Alimentacion { background: rgba(52,211,153,0.10);  color: var(--green); }
.cat-Tecnologia   { background: rgba(45,212,191,0.10);  color: var(--teal); }
.mkt-sym { font-family: 'Space Mono', monospace; color: var(--text2); }
.mkt-val { font-family: 'Space Mono', monospace; }
.mkt-val.up   { color: var(--green); }
.mkt-val.down { color: var(--red); }

/* ── CHARTS — contenedor de gráfico Plotly
   .chart-box    → caja que envuelve cada gráfico
   .chart-title  → título que va en la parte superior
   border-radius → redondeo de las esquinas */
.chart-box { background: var(--bg2); border: 1px solid var(--bdr); border-radius: 12px; padding: 20px; margin-bottom: 28px; transition: border-color 0.2s; }
.chart-box:hover { border-color: var(--bdr2); }
.chart-title { font-size: 12px; font-weight: 600; letter-spacing: 0.05em; text-transform: uppercase; color: var(--dim); margin-bottom: 14px; }

/* ── FOOTER ───────────────────────────────────────────────────
   .memo-footer   → contenedor principal del pie de página
   .source-tag    → cada píldora de fuente de datos */
.memo-footer { display: flex; justify-content: space-between; align-items: center; padding: 28px 0 14px; margin-top: 50px; border-top: 1px solid var(--bdr); font-size: 12px; color: var(--muted); }
.footer-left { display: flex; gap: 8px; align-items: center; }
.footer-sources { display: flex; gap: 6px; }
.source-tag { background: var(--bg3); border: 1px solid var(--bdr); padding: 4px 10px; border-radius: 6px; font-size: 10px; font-weight: 500; letter-spacing: 0.05em; color: var(--dim); }

/* ── TABS — pestañas de sección
   .tab-bar → contenedor de los tabs
   .tab-btn → cada botón/tab individual */
.tab-bar { display: flex; gap: 6px; padding-bottom: 0; }
.tab-btn { font-size: 13px; font-weight: 500; letter-spacing: 0.02em; color: var(--dim); background: transparent; border: 1px solid var(--bdr); padding: 9px 18px; border-radius: 8px; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { background: var(--bg3); border-color: var(--bdr2); color: var(--text2); }
.tab-btn.active { background: var(--bg3); border-color: var(--purple); color: var(--purple); }

/* ── EXPANDERS — acordeones de Streamlit para tablas
   Estilos que se aplican a st.expander */
[data-testid="stExpander"] { background: var(--bg2); border: 1px solid var(--bdr); border-radius: 10px; margin-bottom: 12px; }
[data-testid="stExpander"]:hover { border-color: var(--bdr2); }
[data-testid="stExpanderDetails"] { padding: 16px 20px; }
summary { color: var(--text) !important; font-weight: 500; font-size: 13px; }
summary:hover { color: var(--purple) !important; }
</style>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════╗
# ║  BASE DE DATOS — conexión y utilidades                         ║
# ║  NEON_DATABASE_URL → cadena de conexión a PostgreSQL (Neon)    ║
# ║  get_engine()      → motor SQLAlchemy (cacheado)               ║
# ║  q(sql)            → ejecuta query y devuelve DataFrame        ║
# ╚══════════════════════════════════════════════════════════════════╝
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})

def q(sql: str) -> pd.DataFrame:
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.error(f"Error en consulta SQL: {e}")
        return pd.DataFrame()

# ╔══════════════════════════════════════════════════════════════════╗
# ║  HELPER FUNCTIONS — funciones auxiliares reutilizables         ║
# ║  tabla_html       → convierte DataFrame en tabla HTML          ║
# ║  csv_bytes        → convierte DataFrame a bytes CSV            ║
# ║  csv_nombre       → genera nombre de archivo con timestamp     ║
# ║  apply_filter     → filtra DataFrame por columna si hay valor  ║
# ║  semaforo_precio  → devuelve clase CSS según valor/thresholds  ║
# ╚══════════════════════════════════════════════════════════════════╝
def tabla_html(df, highlight_col=None):
    """
    Convierte un DataFrame en HTML de tabla estilizada
    highlight_col: nombre de columna a resaltar con clase up/down
    """
    if df.empty:
        return "<p style='color:var(--muted);padding:20px'>Sin datos disponibles</p>"
    html = '<table class="mkt-table"><thead><tr>'
    for col in df.columns:
        html += f'<th>{col}</th>'
    html += '</tr></thead><tbody>'
    for _, row in df.iterrows():
        html += '<tr>'
        for col in df.columns:
            val = row[col]
            if pd.isna(val):
                val = "—"
            elif highlight_col and col == highlight_col:
                try:
                    v = float(str(val).replace("%", "").replace("+", ""))
                    cls = "up" if v > 0 else "down"
                    html += f'<td><span class="mkt-val {cls}">{val}</span></td>'
                    continue
                except:
                    pass
            html += f'<td>{val}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html

def csv_bytes(df):
    """Convierte DataFrame a bytes CSV para descarga"""
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def csv_nombre(base="memo_export"):
    """Genera nombre de archivo CSV con timestamp"""
    return f"{base}_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"

def apply_filter(df, col, values):
    """Aplica filtro a DataFrame si values no está vacío"""
    if not values:
        return df
    return df[df[col].isin(values)]

def semaforo_precio(p, norm_low, norm_high):
    """
    Devuelve clase de semáforo según precio:
    p < norm_low      → sem-bajo  (verde)
    norm_low ≤ p ≤ norm_high → sem-normal (amarillo)
    p > norm_high     → sem-alto  (rojo)
    """
    if p < norm_low:
        return "sem-bajo", "BAJO"
    elif p > norm_high:
        return "sem-alto", "ALTO"
    else:
        return "sem-normal", "NORMAL"

# ╔══════════════════════════════════════════════════════════════════╗
# ║  PLOTLY LAYOUT — configuración global para todos los gráficos  ║
# ║  template → tema oscuro de Plotly                               ║
# ║  paper_bgcolor / plot_bgcolor → fondos transparentes           ║
# ║  margin → márgenes del gráfico                                  ║
# ║  font   → tipografía y color del texto                          ║
# ╚══════════════════════════════════════════════════════════════════╝
PLOTLY_LAYOUT = {
    "template": "plotly_dark",
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "margin": dict(l=10, r=10, t=30, b=40),
    "font": dict(family="DM Sans, sans-serif", size=11, color="#94a3b8"),
    "xaxis": dict(showgrid=False, zeroline=False),
    "yaxis": dict(showgrid=True, gridcolor="rgba(255,255,255,0.04)", zeroline=False),
}

# ╔══════════════════════════════════════════════════════════════════╗
# ║  HEADER — Logo, subtítulo y badge LIVE                         ║
# ║  Se muestra al inicio de la app, antes de las tabs             ║
# ╚══════════════════════════════════════════════════════════════════╝
st.markdown('<div class="sticky-header">', unsafe_allow_html=True)

st.markdown("""
<div class="memo-header">
  <div style="display:flex;flex-direction:column">
    <div class="memo-logo">MEMO</div>
    <div class="memo-sub">Monitor de Empresas & Mercados Operativos</div>
  </div>
  <div class="memo-badge">● LIVE</div>
</div>
""", unsafe_allow_html=True)

# ╔══════════════════════════════════════════════════════════════════╗
# ║  TABS — Sistema de navegación por secciones                    ║
# ║  st.tabs() → crea las pestañas de Streamlit                    ║
# ║  tab1, tab2, tab3, tab4 → cada sección de la app               ║
# ╚══════════════════════════════════════════════════════════════════╝
tab1, tab2, tab3, tab4 = st.tabs(["⚡ Energía", "💹 Mercados", "📊 Empresas", "🌍 Macroeconomía"])

st.markdown('</div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — ENERGÍA
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown('<div class="section-label">Indicadores de red eléctrica</div>', unsafe_allow_html=True)

    # ── KPIs estáticos REE ────────────────────────────────────────────────────
    ree = q("SELECT * FROM memo.bronze_ree_static ORDER BY fecha DESC LIMIT 1")
    if not ree.empty:
        row = ree.iloc[0]
        precio_hoy = float(row["precio_medio_hoy"])
        precio_ayer = float(row["precio_medio_ayer"]) if row["precio_medio_ayer"] else precio_hoy
        dem_hoy = float(row["demanda_hoy_mwh"])
        dem_ayer = float(row["demanda_ayer_mwh"]) if row["demanda_ayer_mwh"] else dem_hoy
        delta_p = ((precio_hoy - precio_ayer) / precio_ayer * 100) if precio_ayer else 0
        delta_d = ((dem_hoy - dem_ayer) / dem_ayer * 100) if dem_ayer else 0

        sem_cls, sem_txt = semaforo_precio(precio_hoy, 80, 120)

        st.markdown(f"""
        <div class="kpi-row kpi-3">
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--teal)"></div>
            <div class="kpi-label">Precio medio hoy</div>
            <div class="kpi-value lg">{precio_hoy:.2f} €/MWh</div>
            <div class="kpi-delta {'up' if delta_p>0 else 'down'}">{delta_p:+.2f}% vs ayer</div>
            <div class="semaforo {sem_cls}">{sem_txt}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--purple)"></div>
            <div class="kpi-label">Demanda hoy</div>
            <div class="kpi-value">{dem_hoy:,.0f} MWh</div>
            <div class="kpi-delta {'up' if delta_d>0 else 'down'}">{delta_d:+.2f}% vs ayer</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--amber)"></div>
            <div class="kpi-label">% Renovable</div>
            <div class="kpi-value">{float(row['renovable_pct']):.1f}%</div>
            <div class="kpi-delta">del total generado</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Histórico de precios REE ──────────────────────────────────────────────
    st.markdown('<div class="section-label">Histórico de precios</div>', unsafe_allow_html=True)
    hist = q("SELECT * FROM memo.bronze_ree_hist ORDER BY fecha")
    if not hist.empty:
        hist["fecha"] = pd.to_datetime(hist["fecha"])
        hist = hist.sort_values("fecha").reset_index(drop=True)
        hist["YY-MM"] = hist["fecha"].dt.strftime("%Y-%m")
        hist["YY-WW"] = hist["fecha"].dt.strftime("%Y-W%W")

        # Filtros
        meses = sorted(hist["YY-MM"].unique(), reverse=True)
        weeks = sorted(hist["YY-WW"].unique(), reverse=True)

        c1, c2 = st.columns(2)
        with c1:
            sel_mes = st.multiselect("Mes (YY-MM)", meses, default=[], key="e_mes",
                                      placeholder="Todos los meses")
        with c2:
            sel_wk = st.multiselect("Semana (YY-WW)", weeks, default=[], key="e_wk",
                                     placeholder="Todas las semanas")

        h = apply_filter(hist, "YY-MM", sel_mes)
        h = apply_filter(h, "YY-WW", sel_wk)
        h = h.sort_values("fecha").reset_index(drop=True)

        if not h.empty:
            # KPIs reactivos
            precio_avg = h["precio_medio"].mean()
            precio_max = h["precio_medio"].max()
            precio_min = h["precio_medio"].min()
            dias_alto = (h["precio_medio"] > 120).sum()

            st.markdown(f"""
            <div class="kpi-row kpi-4" style="margin-bottom:20px">
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--amber)"></div>
                <div class="kpi-label">Precio promedio</div>
                <div class="kpi-value">{precio_avg:.2f} €/MWh</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--red)"></div>
                <div class="kpi-label">Precio máximo</div>
                <div class="kpi-value">{precio_max:.2f} €/MWh</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--green)"></div>
                <div class="kpi-label">Precio mínimo</div>
                <div class="kpi-value">{precio_min:.2f} €/MWh</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--purple)"></div>
                <div class="kpi-label">Días precio alto (>120)</div>
                <div class="kpi-value">{dias_alto}</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Gráfico reactivo
            h_plot = h.copy()
            h_plot["fecha_d"] = h_plot["fecha"].dt.date
            fig1 = go.Figure()
            fig1.add_trace(go.Scatter(
                x=h_plot["fecha_d"], y=h_plot["precio_medio"],
                mode="lines+markers",
                line=dict(color="#2dd4bf", width=2),
                marker=dict(size=5, color="#2dd4bf"),
                fill="tozeroy", fillcolor="rgba(45,212,191,0.08)",
                name="Precio medio",
            ))
            fig1.update_layout(**PLOTLY_LAYOUT, height=300)
            st.markdown('<div class="chart-box"><div class="chart-title">Precio medio diario · REE</div>', unsafe_allow_html=True)
            st.plotly_chart(fig1, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Tabla con descarga integrada
            with st.expander("Ver tabla de datos históricos"):
                ht = h.sort_values("fecha", ascending=False).copy()
                ht["fecha_d"] = ht["fecha"].dt.date
                ht_show = ht[["fecha_d", "precio_medio", "demanda", "renovable_pct", "YY-MM", "YY-WW"]].copy()
                ht_show.columns = ["Fecha", "Precio €/MWh", "Demanda MWh", "% Renovable", "Mes", "Semana"]
                dc1, dc2 = st.columns([2, 5])
                with dc1:
                    st.download_button("⬇ CSV", csv_bytes(ht_show),
                        csv_nombre("memo_ree"), "text/csv", key="dl_ree")
                with dc2:
                    st.caption(f"{len(ht_show)} registros")
                st.markdown(tabla_html(ht_show), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — MERCADOS
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown('<div class="section-label">Cotizaciones · Yahoo Finance</div>', unsafe_allow_html=True)

    # ── KPIs estáticos mercados ───────────────────────────────────────────────
    mkt_stat = q("SELECT * FROM memo.silver_stock_static")
    if not mkt_stat.empty:
        total = len(mkt_stat)
        sube = (mkt_stat["change_pct"] > 0).sum()
        baja = (mkt_stat["change_pct"] < 0).sum()
        neut = total - sube - baja
        st.markdown(f"""
        <div class="kpi-row kpi-4" style="margin-bottom:28px">
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--teal)"></div>
            <div class="kpi-label">Total valores</div>
            <div class="kpi-value">{total}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--green)"></div>
            <div class="kpi-label">Al alza</div>
            <div class="kpi-value">{sube}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--red)"></div>
            <div class="kpi-label">A la baja</div>
            <div class="kpi-value">{baja}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--amber)"></div>
            <div class="kpi-label">Sin cambio</div>
            <div class="kpi-value">{neut}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    # ── Histórico de mercados ─────────────────────────────────────────────────
    st.markdown('<div class="section-label">Histórico de mercados</div>', unsafe_allow_html=True)
    hist_mkt = q("SELECT * FROM memo.silver_stock_hist ORDER BY fecha, symbol")
    if not hist_mkt.empty:
        hist_mkt["fecha"] = pd.to_datetime(hist_mkt["fecha"])
        hist_mkt = hist_mkt.sort_values(["fecha","symbol"]).reset_index(drop=True)
        hist_mkt["var_pct"] = hist_mkt.groupby("symbol")["close"].pct_change() * 100
        hist_mkt["YY-MM"] = hist_mkt["fecha"].dt.strftime("%Y-%m")
        hist_mkt["YY-WW"] = hist_mkt["fecha"].dt.strftime("%Y-W%W")

        # Filtros — CAMBIO: multiselect en lugar de selectbox
        syms = sorted(hist_mkt["symbol"].unique())
        meses_mkt = sorted(hist_mkt["YY-MM"].unique(), reverse=True)
        weeks_mkt = sorted(hist_mkt["YY-WW"].unique(), reverse=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            sel_sym = st.multiselect("Símbolo", syms, default=[], key="mkt_sym",
                                      placeholder="Todos los símbolos")
        with c2:
            sel_mes_mkt = st.multiselect("Mes (YY-MM)", meses_mkt, default=[], key="mkt_mes",
                                          placeholder="Todos los meses")
        with c3:
            sel_wk_mkt = st.multiselect("Semana (YY-WW)", weeks_mkt, default=[], key="mkt_wk",
                                         placeholder="Todas las semanas")

        hm = apply_filter(hist_mkt, "symbol", sel_sym)
        hm = apply_filter(hm, "YY-MM", sel_mes_mkt)
        hm = apply_filter(hm, "YY-WW", sel_wk_mkt)
        hm = hm.sort_values(["fecha","symbol"]).reset_index(drop=True)

        if not hm.empty:
            # ── CAMBIO: PRIMERO GRÁFICO, DESPUÉS TABLA ───────────────────────
            # Gráfico de líneas: Variación diaria %
            fig2 = go.Figure()
            for sym in hm["symbol"].unique():
                df_sym = hm[hm["symbol"] == sym].copy()
                df_sym["fecha_d"] = df_sym["fecha"].dt.date
                fig2.add_trace(go.Scatter(
                    x=df_sym["fecha_d"], y=df_sym["var_pct"],
                    mode="lines+markers", name=sym, line=dict(width=2),
                    marker=dict(size=4),
                ))
            fig2.update_layout(**PLOTLY_LAYOUT, height=320, showlegend=True,
                               legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
            st.markdown('<div class="chart-box"><div class="chart-title">Variación diaria % · histórico</div>', unsafe_allow_html=True)
            st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Tabla de mercados con descarga
            with st.expander("Ver tabla de mercados históricos"):
                hmt = hm.sort_values("fecha", ascending=False).copy()
                hmt["var_str"] = hmt["var_pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
                hmt["fecha_d"] = hmt["fecha"].dt.date
                hmt_show = hmt[["fecha_d","symbol","close","var_str","YY-MM","YY-WW"]].copy()
                hmt_show.columns = ["Fecha","Símbolo","Cierre USD","Variación %","Mes","Semana"]
                dc1, dc2 = st.columns([2, 5])
                with dc1:
                    st.download_button("⬇ CSV", csv_bytes(hmt_show),
                        csv_nombre("memo_mercados"), "text/csv", key="dl_mkt")
                with dc2:
                    st.caption(f"{len(hmt_show)} registros")
                st.markdown(tabla_html(hmt_show, "Variación %"), unsafe_allow_html=True)

    # Tabla estática de mercados
    with st.expander("Ver tabla resumen mercados (última cotización)"):
        ms = mkt_stat.copy()
        ms["var_str"] = ms["change_pct"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
        ms_show = ms[["symbol","price","var_str","categoria"]].copy()
        ms_show.columns = ["Símbolo","Precio USD","Var. día %","Categoría"]
        st.markdown(tabla_html(ms_show, "Var. día %"), unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — EMPRESAS
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown('<div class="section-label">Carteras de valores</div>', unsafe_allow_html=True)

    # ── Tabla agregada por empresa ───────────────────────────────────────────
    portf = q("""
        SELECT
          empresa, categoria,
          COUNT(*) AS n_valores,
          SUM(posicion_actual_usd) AS total_usd
        FROM memo.silver_portfolio_positions
        GROUP BY empresa, categoria
        ORDER BY total_usd DESC
    """)
    if not portf.empty:
        total_inv = portf["total_usd"].sum()
        n_emp = len(portf)
        st.markdown(f"""
        <div class="kpi-row kpi-2" style="max-width:620px;margin-bottom:28px">
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--purple)"></div>
            <div class="kpi-label">Inversión total</div>
            <div class="kpi-value lg">${total_inv:,.0f}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--teal)"></div>
            <div class="kpi-label">Empresas en cartera</div>
            <div class="kpi-value">{n_emp}</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabla HTML con formato
        html = '<table class="mkt-table"><thead><tr>'
        html += '<th>Empresa</th><th>Categoría</th><th>Valores</th><th>Total USD</th>'
        html += '</tr></thead><tbody>'
        for _, row in portf.iterrows():
            cat_cls = f"cat-{row['categoria']}" if pd.notna(row["categoria"]) else "cat-pill"
            html += f"""
            <tr>
              <td><span class="mkt-sym">{row['empresa']}</span></td>
              <td><span class="cat-pill {cat_cls}">{row['categoria'] or 'N/A'}</span></td>
              <td>{row['n_valores']}</td>
              <td class="mkt-val">${row['total_usd']:,.0f}</td>
            </tr>
            """
        html += '</tbody></table>'
        with st.expander("Ver detalle de carteras por empresa"):
            st.markdown(html, unsafe_allow_html=True)
            emp_df = portf.copy()
            emp_df.columns = ["Empresa","Categoría","Valores","Total USD"]
            dc1, dc2 = st.columns([2,5])
            with dc1:
                st.download_button("⬇ CSV", csv_bytes(emp_df),
                    csv_nombre("memo_empresas"), "text/csv", key="dl_emp")
            with dc2:
                st.caption(f"{len(emp_df)} empresas")

    # ── Posiciones individuales ───────────────────────────────────────────────
    pos = q("SELECT * FROM memo.silver_portfolio_positions ORDER BY posicion_actual_usd DESC")
    if not pos.empty:
        with st.expander("Ver todas las posiciones"):
            pos_show = pos[["empresa","symbol","cantidad","precio_compra_usd","posicion_actual_usd","categoria"]].copy()
            pos_show.columns = ["Empresa","Símbolo","Cantidad","Precio compra USD","Posición USD","Categoría"]
            st.markdown(tabla_html(pos_show), unsafe_allow_html=True)
            dc1, dc2 = st.columns([2,5])
            with dc1:
                st.download_button("⬇ CSV posiciones", csv_bytes(pos_show),
                    csv_nombre("memo_posiciones"), "text/csv", key="dl_pos")
            with dc2:
                st.caption(f"{len(pos_show)} posiciones")

# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — MACROECONOMÍA
# ══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-label">Indicadores macroeconómicos</div>', unsafe_allow_html=True)

    # ── Datos macro estáticos (EUR/USD + IPC) ─────────────────────────────────
    macro = q("SELECT * FROM memo.bronze_macro WHERE fecha = (SELECT MAX(fecha) FROM memo.bronze_macro)")
    hist_div = q("SELECT fecha, tasa FROM memo.silver_divisa_hist ORDER BY fecha")

    if not macro.empty:
        cards_html = ""
        for _, row in macro.iterrows():
            if "USD" in str(row["indicador"]):
                cards_html += f"""
                <div class="kpi">
                  <div class="kpi-accent" style="background:var(--purple)"></div>
                  <div class="kpi-label">💱 EUR / USD · BCE</div>
                  <div class="kpi-value lg">{float(row['valor']):.4f}</div>
                  <div class="kpi-delta">Fecha: {str(row['fecha'])[:10]}</div>
                </div>"""
            else:
                val = float(row["valor"]) if row["valor"] else 0
                c = "up" if val > 0 else "down"
                cards_html += f"""
                <div class="kpi">
                  <div class="kpi-accent" style="background:var(--teal)"></div>
                  <div class="kpi-label">📊 IPC España · INE</div>
                  <div class="kpi-value lg" style="color:{'var(--red)' if val>3 else 'var(--green)'}">{val:+.1f}%</div>
                  <div class="kpi-delta {c}">variación anual · {str(row['fecha'])[:7]}</div>
                </div>"""
        st.markdown(f'<div class="kpi-row kpi-2" style="max-width:620px">{cards_html}</div>', unsafe_allow_html=True)

    if not hist_div.empty:
        hist_div["fecha"] = pd.to_datetime(hist_div["fecha"])
        hist_div = hist_div.sort_values("fecha").reset_index(drop=True)
        hist_div["variacion_p"] = hist_div["tasa"].pct_change() * 100
        hist_div["YY-MM"] = hist_div["fecha"].dt.strftime("%Y-%m")
        hist_div["YY-WW"] = hist_div["fecha"].dt.strftime("%Y-W%W")

        # Filtros macro
        st.markdown('<div class="section-label">Filtros EUR/USD</div>', unsafe_allow_html=True)
        meses_m = sorted(hist_div["YY-MM"].unique(), reverse=True)
        weeks_m = sorted(hist_div["YY-WW"].unique(), reverse=True)
        mc1, mc2 = st.columns(2)
        with mc1:
            sel_mes_m = st.multiselect("Mes (YY-MM)", meses_m, default=[], key="m_mes",
                                        placeholder="Todos los meses")
        with mc2:
            sel_wk_m  = st.multiselect("Semana (YY-WW)", weeks_m, default=[], key="m_wk",
                                        placeholder="Todas las semanas")

        hd = apply_filter(hist_div, "YY-MM", sel_mes_m)
        hd = apply_filter(hd, "YY-WW", sel_wk_m)
        hd = hd.sort_values("fecha").reset_index(drop=True)

        if not hd.empty:
            # Tarjetas reactivas EUR/USD
            var_avg_m  = hd["variacion_p"].mean()
            n_sube_m   = (hd["variacion_p"] > 0).sum()
            n_baja_m   = (hd["variacion_p"] < 0).sum()
            color_avg_m = "#c4b5fd" if var_avg_m >= 0 else "#f87171"
            tasa_ini   = hd["tasa"].iloc[0]
            tasa_fin   = hd["tasa"].iloc[-1]
            var_total  = (tasa_fin - tasa_ini) / tasa_ini * 100 if tasa_ini else 0

            st.markdown(f"""
            <div class="kpi-row kpi-4" style="margin-bottom:20px">
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--purple)"></div>
                <div class="kpi-label">EUR/USD actual</div>
                <div class="kpi-value lg">{tasa_fin:.4f}</div>
                <div class="kpi-delta">último dato del período</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--green)"></div>
                <div class="kpi-label">Días al alza</div>
                <div class="kpi-value">{n_sube_m}</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--red)"></div>
                <div class="kpi-label">Días a la baja</div>
                <div class="kpi-value">{n_baja_m}</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--amber)"></div>
                <div class="kpi-label">Variación total período</div>
                <div class="kpi-value" style="font-size:24px;color:{color_avg_m}">{var_total:+.2f}%</div>
                <div class="kpi-delta">media diaria: {var_avg_m:+.3f}%</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Gráfico reactivo
            hd_plot = hd.copy()
            hd_plot["fecha_d"] = hd_plot["fecha"].dt.date
            fig3 = go.Figure(go.Scatter(
                x=hd_plot["fecha_d"], y=hd_plot["tasa"],
                mode="lines+markers",
                line=dict(color="#a78bfa", width=2),
                marker=dict(size=5, color="#a78bfa"),
                fill="tozeroy", fillcolor="rgba(167,139,250,0.06)",
                name="EUR/USD",
            ))
            fig3.update_layout(**PLOTLY_LAYOUT, height=280)
            st.markdown('<div class="chart-box"><div class="chart-title">EUR/USD histórico · BCE</div>', unsafe_allow_html=True)
            st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Tabla EUR/USD con descarga integrada
            with st.expander("Ver tabla histórica EUR/USD"):
                td = hd.sort_values("fecha", ascending=False).copy()
                td["var_str"] = td["variacion_p"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
                td["fecha_d"] = td["fecha"].dt.date
                td_show = td[["fecha_d","tasa","var_str","YY-MM","YY-WW"]].copy()
                td_show.columns = ["Fecha","EUR/USD","Variación %","Mes","Semana"]
                dc1, dc2 = st.columns([2, 5])
                with dc1:
                    st.download_button("⬇ CSV", csv_bytes(td_show),
                        csv_nombre("memo_eurusd"), "text/csv", key="dl_div_tbl")
                with dc2:
                    st.caption(f"{len(td_show)} registros")
                st.markdown(tabla_html(td_show), unsafe_allow_html=True)

    # Tabla IPC — descarga en el label de sección
    hist_ipc = q("""
        SELECT fecha, valor FROM memo.bronze_macro
        WHERE indicador = 'IPC_GENERAL_ESP' ORDER BY fecha DESC
    """)
    if not hist_ipc.empty:
        hist_ipc["fecha"] = pd.to_datetime(hist_ipc["fecha"])
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
  <div class="footer-sources">
    <span class="source-tag">REE</span>
    <span class="source-tag">Yahoo Finance</span>
    <span class="source-tag">BCE</span>
    <span class="source-tag">INE</span>
  </div>
</div>
""", unsafe_allow_html=True)
