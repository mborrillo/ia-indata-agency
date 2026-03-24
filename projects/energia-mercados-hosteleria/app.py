"""
MEMO Hostelería — Monitor de Costes para Restauración
ia indata agency · Badajoz, Extremadura

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
# ║  CONFIGURACIÓN GENERAL DE LA PÁGINA                              ║
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

/* EMPUJAR EL CONTENIDO PRINCIPAL HACIA ABAJO PARA COMPENSAR HEADER Y TABS FIJOS */
.block-container { padding: 160px 3rem 5rem !important; max-width: 1300px !important; }

/* Header fijo */
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
    border-bottom:1px solid var(--bdr); 
    backdrop-filter: blur(10px); 
}
.hdr-logo { font-family:'DM Sans',sans-serif; font-size:22px; font-weight:700; color:var(--teal); letter-spacing:0.01em; }
.hdr-sub  { font-size:12px; color:var(--muted); text-transform:uppercase; letter-spacing:.06em; margin-top:3px; }
.hdr-badge { margin-left:auto; font-family:'Space Mono',monospace; font-size:11px; color:var(--teal); background:rgba(45,212,191,.08); border:1px solid rgba(45,212,191,.2); padding:5px 12px; border-radius:20px; }

/* Tabs / Navegación fija */
[data-testid="stTabs"] [role="tablist"] { 
    position: fixed;
    top: 85px; /* Altura donde termina el header */
    left: 0;
    right: 0;
    z-index: 999;
    background: var(--bg); 
    padding: 0 3rem 10px !important; 
    border-bottom: 1px solid var(--bdr) !important; 
    border-radius: 0 !important;
    gap: 4px !important; 
}
[data-testid="stTabs"] [role="tab"] { background: transparent !important; border: none !important; color: var(--muted) !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; padding: 8px 18px !important; border-radius: 7px !important; transition: all 0.15s !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: var(--bg3) !important; color: var(--purple) !important; border: 1px solid rgba(196,181,253,0.2) !important; }
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) { color: var(--text) !important; background: rgba(255,255,255,0.04) !important; }

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
.sem-verde    { background:rgba(52,211,153,0.12); color:var(--green); border:1px solid rgba(52,211,153,0.3); }
.sem-amarillo { background:rgba(251,191,36,0.10); color:var(--amber); border:1px solid rgba(251,191,36,0.25); }
.sem-rojo     { background:rgba(248,113,113,0.10); color:var(--red);  border:1px solid rgba(248,113,113,0.25); }
.sem-bajo     { background:rgba(52,211,153,0.12); color:var(--green); border:1px solid rgba(52,211,153,0.3); }
.sem-normal   { background:rgba(251,191,36,0.10); color:var(--amber); border:1px solid rgba(251,191,36,0.25); }
.sem-alto     { background:rgba(248,113,113,0.10); color:var(--red);  border:1px solid rgba(248,113,113,0.25); }

/* Recomendación */
.rec { background:var(--bg3); border-left:3px solid var(--teal); border-radius:0 8px 8px 0; padding:12px 16px; font-size:14px; color:var(--text); margin-top:8px; }
.rec.warn { border-left-color:var(--amber); }
.rec.bad  { border-left-color:var(--red); }

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
[data-testid="stMultiSelect"] [data-baseweb="tag"] { background-color:rgba(196,181,253,0.15) !important; border:1px solid rgba(196,181,253,0.35) !important; color:#c4b5fd !important; border-radius:6px !important; }
[data-testid="stMultiSelect"] [data-baseweb="tag"] span,
[data-testid="stMultiSelect"] [data-baseweb="tag"] [aria-label="Remove"] { color:#c4b5fd !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child,
[data-baseweb="select"] > div:first-child { background:var(--bg2) !important; border:1px solid var(--bdr2) !important; border-radius:8px !important; color:var(--text) !important; }
[data-testid="stMultiSelect"] [data-baseweb="select"] > div:first-child:focus-within,
[data-baseweb="select"] > div:first-child:focus-within { border-color:rgba(196,181,253,0.5) !important; box-shadow:0 0 0 2px rgba(196,181,253,0.12) !important; }
[data-baseweb="popover"] [data-baseweb="menu"] { background:var(--bg3) !important; border:1px solid var(--bdr2) !important; border-radius:8px !important; }
[data-baseweb="menu"] li { color:var(--text) !important; }
[data-baseweb="menu"] li:hover,
[data-baseweb="menu"] [aria-selected="true"] { background:rgba(196,181,253,0.1) !important; color:#c4b5fd !important; }
</style>
""", unsafe_allow_html=True)

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_engine():
    from sqlalchemy import create_engine
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})

def q(sql: str) -> pd.DataFrame:
    try:
        with get_engine().connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.warning(f"Error al consultar datos: {e}")
        return pd.DataFrame()

PLOTLY = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans", color="#94a3b8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", tickfont=dict(size=11)),
)

def csv_dl(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def csv_nombre(seccion: str) -> str:
    """Genera nombre: seccion_YYYY-MM-DD.csv"""
    from datetime import date
    return f"{seccion}_{date.today().strftime('%Y-%m-%d')}.csv"


def df_para_csv(df):
    """Ordena por fecha descendente antes de exportar."""
    df = df.copy()
    for col in df.columns:
        if any(k in col.lower() for k in ["fecha", "período", "date"]):
            try:
                df = df.sort_values(col, ascending=False).reset_index(drop=True)
                break
            except Exception:
                pass
    return df


def color_var(v):
    """HTML con color según signo de variación. Maneja float, int, str y NaN."""
    try:
        import math
        if v is None:
            return '<span style="color:#c4b5fd">—</span>'
        if isinstance(v, float) and math.isnan(v):
            return '<span style="color:#c4b5fd">—</span>'
        n = float(str(v).replace("%", "").replace("+", "").strip())
        if n > 0:  return f'<span style="color:#c4b5fd;font-weight:600">▲ {n:.2f}%</span>'
        if n < 0:  return f'<span style="color:#f87171;font-weight:600">▼ {abs(n):.2f}%</span>'
        return f'<span style="color:#c4b5fd">— {n:.2f}%</span>'
    except Exception:
        return f'<span style="color:#c4b5fd">{v}</span>'


def tabla_html(df, col_var="Variación %"):
    """Tabla HTML con variación coloreada. col_var es la columna a colorear."""
    df = df.copy()
    for c in df.columns:
        if c != col_var:
            df[c] = df[c].astype(str).replace("NaT", "—").replace("nan", "—")
    cols = list(df.columns)
    ths  = "".join(f"<th>{c}</th>" for c in cols)
    rows = ""
    for _, row in df.iterrows():
        tds = ""
        for c in cols:
            val = row[c]
            if c == col_var:
                tds += f"<td>{color_var(val)}</td>"
            else:
                tds += f"<td>{val}</td>"
        rows += f"<tr>{tds}</tr>"
    return f"""
    <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:10px;overflow:hidden;margin-top:8px">
      <table style="width:100%;border-collapse:collapse">
        <thead><tr style="font-size:10px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--muted)">{ths}</tr></thead>
        <tbody style="font-size:13px;color:var(--text)">{rows}</tbody>
      </table>
    </div>"""


def sem_class(s: str) -> str:
    return {"VERDE":"sem-verde","AMARILLO":"sem-amarillo","ROJO":"sem-rojo",
            "BAJO":"sem-bajo","NORMAL":"sem-normal","ALTO":"sem-alto"}.get(s.upper(),"sem-normal")

def sem_icon(s: str) -> str:
    return {"VERDE":"✅","AMARILLO":"⚠️","ROJO":"🔴",
            "BAJO":"🟢","NORMAL":"🟡","ALTO":"🔴"}.get(s.upper(),"⚪")

# ── Guard ─────────────────────────────────────────────────────────────────────
if not DB_URL:
    st.error("⚠ NEON_DATABASE_URL no configurada")
    st.stop()

# ── RENDER HEADER (Fijo) ──────────────────────────────────────────────────────
st.markdown("""
<div class="hdr">
  <div>
    <div class="hdr-logo">🍳 MEMO Hostelería</div>
    <div class="hdr-sub">Monitor para Empresas &amp; Mercados Operativos · Hostelería · ia-indata agency</div>
  </div>
  <div class="hdr-badge">● LIVE · actualización diaria</div>
</div>
""", unsafe_allow_html=True)

# ── TABS NATIVOS (Fijos por CSS) ──────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "⚡ Luz", "🔥 Gas & Aceite", "📊 IPC Alimentación", "📈 Histórico"
])

# ── CONTENIDO ──
# ════════════════════════════════════════════════════════════
# TAB 1 — LUZ
# ════════════════════════════════════════════════════════════
with tab1:
    luz  = q("SELECT * FROM hosteleria.v_luz_hoy")
    hora = q("SELECT * FROM hosteleria.v_hora_valle")

    # ÍNDICE DE COSTE TOTAL (Movido dentro de los Tabs para que no tape el header/scroll)
    indice = q("SELECT * FROM hosteleria.v_indice_coste")
    if not indice.empty:
        r_ind = indice.iloc[0]
        sg = str(r_ind.get("semaforo_global","AMARILLO")).upper()
        st.markdown('<div class="slabel">Estado general de costes hoy</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:14px;
                    padding:24px 28px;margin-bottom:28px;display:flex;align-items:center;gap:32px">
          <div>
            <div class="klbl">Índice de Coste Total</div>
            <span class="sem {sem_class(sg)}">{sem_icon(sg)} {sg}</span>
          </div>
          <div style="flex:1;display:grid;grid-template-columns:repeat(4,1fr);gap:16px">
            <div><div class="klbl">Luz</div>
              <span class="sem {sem_class(str(r_ind.get('luz','NORMAL')))} " style="font-size:12px;padding:4px 10px">
              {sem_icon(str(r_ind.get('luz','—')))} {r_ind.get('luz','—')}</span></div>
            <div><div class="klbl">Gas</div>
              <span class="sem {sem_class(str(r_ind.get('gas','NORMAL')))}" style="font-size:12px;padding:4px 10px">
              {sem_icon(str(r_ind.get('gas','—')))} {r_ind.get('gas','—')}</span></div>
            <div><div class="klbl">Aceite</div>
              <span style="font-size:13px;color:var(--dim)">{r_ind.get('aceite','—')}</span></div>
            <div><div class="klbl">IPC alimentación vs general</div>
              <span style="font-size:13px;font-family:'Space Mono',monospace;
              color:{'var(--red)' if float(r_ind.get('spread_ipc') or 0)>2 else 'var(--purple)'}">
              {float(r_ind.get('spread_ipc') or 0):+.2f} pts</span></div>
          </div>
        </div>
        """, unsafe_allow_html=True)

    if luz.empty:
        st.info("Sin datos de luz. Ejecuta el ETL.")
    else:
        r = luz.iloc[0]
        sem = str(r.get("semaforo","NORMAL")).upper()
        rec = str(r.get("recomendacion",""))
        pct = float(r.get("pct_vs_media") or 0)
        rec_cls = "ok" if sem=="BAJO" else ("bad" if sem=="ALTO" else "warn")

        st.markdown('<div class="slabel">Precio de la luz hoy</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="krow k4">
          <div class="kpi">
            <div class="kacc" style="background:var(--teal)"></div>
            <div class="klbl">Precio medio hoy</div>
            <div class="kval lg">{float(r['precio_medio']):.4f}</div>
            <div class="kdelta">€/kWh · {pct:+.1f}% vs media 30d</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:var(--purple)"></div>
            <div class="klbl">Hora más barata</div>
            <div class="kval">{int(r['hora_min'])}:00h</div>
            <div class="kdelta ok">{float(r['precio_min']):.4f} €/kWh</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:var(--red)"></div>
            <div class="klbl">Hora más cara</div>
            <div class="kval">{int(r['hora_max'])}:00h</div>
            <div class="kdelta bad">{float(r['precio_max']):.4f} €/kWh</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:var(--amber)"></div>
            <div class="klbl">Estado vs mes anterior</div>
            <div style="margin-top:6px"><span class="sem {sem_class(sem)}">{sem_icon(sem)} {sem}</span></div>
          </div>
        </div>
        <div class="rec {rec_cls}">💡 {rec}</div>
        """, unsafe_allow_html=True)

        if not hora.empty:
            h = hora.iloc[0]
            ahorro_pct  = float(h.get("ahorro_potencial_pct") or 0)
            precio_min_h = float(h.get("precio_en_mejor_hora") or 0)
            precio_max_h = float(h.get("precio_en_peor_hora") or 0)
            kwh_ejemplo  = 40
            ahorro_euros = (precio_max_h - precio_min_h) * kwh_ejemplo
            st.markdown(f"""
            <div class="krow k2" style="max-width:500px;margin-top:16px">
              <div class="kpi">
                <div class="kacc" style="background:var(--purple)"></div>
                <div class="klbl">Mejor franja para cocinar</div>
                <div class="kval">{h.get('franja','—')}</div>
                <div class="kdelta ok">Hora {int(h['mejor_hora'])}:00 — {precio_min_h:.4f} €/kWh</div>
              </div>
              <div class="kpi">
                <div class="kacc" style="background:var(--purple)"></div>
                <div class="klbl">Ahorro potencial hoy</div>
                <div class="kval" style="color:var(--purple)">{ahorro_euros:.2f} €</div>
                <div class="kdelta ok">({ahorro_pct:.1f}% vs hora más cara · base 40 kWh)</div>
              </div>
            </div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 2 — GAS & ACEITE
# ════════════════════════════════════════════════════════════
with tab2:
    gas    = q("SELECT * FROM hosteleria.v_gas_estado")
    aceite = q("SELECT * FROM hosteleria.v_aceite_estado")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown('<div class="slabel">Gas natural — cocinas industriales</div>', unsafe_allow_html=True)
        if gas.empty:
            st.info("Sin datos de gas.")
        else:
            g = gas.iloc[0]
            sg = str(g.get("semaforo","NORMAL")).upper()
            pct_g = float(g.get("pct_vs_media") or 0)
            st.markdown(f"""
            <div class="kpi">
              <div class="kacc" style="background:var(--amber)"></div>
              <div class="klbl">Precio gas hoy</div>
              <div class="kval lg">{float(g['precio_mwh']):.2f}</div>
              <div class="kdelta">€/MWh · {pct_g:+.1f}% vs media 30d</div>
              <div style="margin-top:12px"><span class="sem {sem_class(sg)}">{sem_icon(sg)} {sg}</span></div>
            </div>
            """, unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="slabel">Aceite de oliva virgen extra (AOVE) — precio España</div>', unsafe_allow_html=True)
        if aceite.empty:
            st.info("Sin datos de aceite.")
        else:
            a = aceite.iloc[0]
            tend = str(a.get("tendencia","ESTABLE"))
            rec_a = str(a.get("recomendacion_compra",""))
            diff  = float(a.get("diff_vs_media_4sem") or 0)
            tend_color = "var(--red)" if tend=="SUBIENDO" else ("var(--purple)" if tend=="BAJANDO" else "var(--amber)")
            rec_cls_a  = "bad" if tend=="SUBIENDO" else ("ok" if tend=="BAJANDO" else "warn")
            st.markdown(f"""
            <div class="kpi">
              <div class="kacc" style="background:{tend_color}"></div>
              <div class="klbl">Precio AOVE en origen · España</div>
              <div class="kval lg">{float(a['precio_actual']):.3f}</div>
              <div class="kdelta">€/kg · tendencia 4 semanas: <strong style="color:{tend_color}">{tend}</strong></div>
              <div class="kdelta" style="margin-top:4px">{diff:+.3f} €/kg vs media 4 semanas</div>
            </div>
            <div class="rec {rec_cls_a}" style="margin-top:8px">🫒 {rec_a}</div>
            """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 3 — IPC ALIMENTACIÓN
# ════════════════════════════════════════════════════════════
with tab3:
    ipc = q("SELECT * FROM hosteleria.v_ipc_spread")

    if ipc.empty:
        st.info("Sin datos de IPC. Se actualiza mensualmente.")
    else:
        r = ipc.iloc[0]
        spread   = float(r.get("spread") or 0)
        alerta   = str(r.get("alerta_margen",""))
        ipc_gen  = float(r.get("ipc_general") or 0)
        ipc_ali  = float(r.get("ipc_alimentacion") or 0)
        alerta_cls = "bad" if spread > 2 else ("warn" if spread > 0 else "ok")
        color_spread = "var(--red)" if spread>2 else ("var(--amber)" if spread>0 else "var(--purple)")

        st.markdown('<div class="slabel">¿Suben tus costes más que la inflación?</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="krow k3">
          <div class="kpi">
            <div class="kacc" style="background:var(--dim)"></div>
            <div class="klbl">Inflación general España</div>
            <div class="kval">{ipc_gen:+.1f}%</div>
            <div class="kdelta">variación anual · INE</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:var(--amber)"></div>
            <div class="klbl">Inflación en alimentación</div>
            <div class="kval" style="color:{'var(--red)' if ipc_ali>ipc_gen else 'var(--purple)'}">{ipc_ali:+.1f}%</div>
            <div class="kdelta">variación anual · INE</div>
          </div>
          <div class="kpi">
            <div class="kacc" style="background:{color_spread}"></div>
            <div class="klbl">Diferencial sobre tus costes</div>
            <div class="kval" style="color:{color_spread}">{spread:+.2f} pts</div>
            <div class="kdelta">alimentación minus inflación general</div>
          </div>
        </div>
        <div class="rec {alerta_cls}">📊 {alerta}</div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="margin-top:20px;padding:16px;background:var(--bg3);border-radius:10px;
                    border:1px solid var(--bdr);font-size:13px;color:var(--dim)">
        <strong style="color:var(--text)">¿Cómo leer este dato?</strong><br><br>
        Si la inflación de alimentación es mayor que la inflación general, tus costes de
        materia prima suben más rápido que el resto de la economía. Si no subes precios de
        carta al mismo ritmo, tu margen se estrecha mes a mes.
        </div>
        """, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 4 — HISTÓRICO
# ════════════════════════════════════════════════════════════
with tab4:
    hist = q("SELECT * FROM hosteleria.v_luz_historico ORDER BY fecha ASC")

    if hist.empty:
        st.info("Sin datos históricos todavía.")
    else:
        hist["fecha"] = pd.to_datetime(hist["fecha"])
        hist["YY-MM"] = hist["fecha"].dt.strftime("%Y-%m")
        hist["YY-WW"] = hist["fecha"].dt.strftime("%Y-W%W")

        st.markdown('<div class="slabel">Filtros</div>', unsafe_allow_html=True)
        meses_h = sorted(hist["YY-MM"].unique(), reverse=True)
        weeks_h = sorted(hist["YY-WW"].unique(), reverse=True)
        fc1, fc2 = st.columns(2)
        with fc1:
            sel_mes = st.multiselect("Mes", meses_h, default=[], key="h_mes",
                                      placeholder="Todos los meses")
        with fc2:
            sel_wk  = st.multiselect("Semana", weeks_h, default=[], key="h_wk",
                                      placeholder="Todas las semanas")

        filt = hist.copy()
        if sel_mes: filt = filt[filt["YY-MM"].isin(sel_mes)]
        if sel_wk:  filt = filt[filt["YY-WW"].isin(sel_wk)]
        filt = filt.sort_values("fecha")

        if not filt.empty:
            pm = filt["precio_medio"].mean()
            pmin = filt["precio_min"].min()
            pmax = filt["precio_max"].max()
            filt["var"] = filt["precio_medio"].pct_change() * 100
            var_med = filt["var"].mean()
            import math
            if len(filt) < 2 or math.isnan(var_med):
                var_display  = "Sin histórico suficiente"
                txt_color    = "var(--muted)" 
                var_fontsize = "14px"
            else:
                var_display  = f"{var_med:+.2f}%"
                txt_color    = "var(--purple)" if var_med <= 0 else "var(--red)" 
                var_fontsize = "22px"

            st.markdown(f"""
            <div class="krow k4" style="margin-top:4px">
              <div class="kpi"><div class="kacc" style="background:var(--teal)"></div>
                <div class="klbl">Precio medio período</div>
                <div class="kval">{pm:.4f}</div><div class="kdelta">€/kWh</div></div>
              <div class="kpi"><div class="kacc" style="background:var(--purple)"></div>
                <div class="klbl">Mínimo período</div>
                <div class="kval">{pmin:.4f}</div></div>
              <div class="kpi"><div class="kacc" style="background:var(--red)"></div>
                <div class="klbl">Máximo período</div>
                <div class="kval">{pmax:.4f}</div></div>
              <div class="kpi"><div class="kacc" style="background:var(--purple)"></div>
                <div class="klbl">Variación media diaria</div>
                <div class="kval" style="font-size:{var_fontsize};color:{txt_color}">{var_display}</div></div>
            </div>
            """, unsafe_allow_html=True)

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=filt["fecha"], y=filt["precio_max"], fill=None, mode="lines",
                line=dict(color="rgba(0,0,0,0)", width=0), showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(
                x=filt["fecha"], y=filt["precio_min"], fill="tonexty",
                fillcolor="rgba(45,212,191,0.07)", mode="lines",
                line=dict(color="rgba(0,0,0,0)", width=0), name="Rango"))
            fig.add_trace(go.Scatter(
                x=filt["fecha"], y=filt["precio_medio"], mode="lines+markers",
                line=dict(color="#2dd4bf", width=2), marker=dict(size=4), name="Precio medio"))
            if "media_movil_7d" in filt.columns:
                fig.add_trace(go.Scatter(
                    x=filt["fecha"], y=filt["media_movil_7d"], mode="lines",
                    line=dict(color="#fbbf24", width=1.5, dash="dot"), name="Media 7d"))
            fig.update_layout(**PLOTLY, height=300)
            st.markdown('<div class="cbox"><div class="ctitle">Evolución precio luz · €/kWh</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("Ver tabla completa"):
                tabla = filt.sort_values("fecha", ascending=False).copy()
                tabla["fecha_d"] = tabla["fecha"].dt.date
                t = tabla[["fecha_d","precio_medio","precio_min","precio_max","media_movil_7d","YY-MM","YY-WW","var"]].copy()
                t.columns = ["Fecha","Precio medio","Mínimo","Máximo","Media 7d","Mes","Semana","Variación %"]
                hc1, hc2 = st.columns([2, 5])
                with hc1:
                    st.download_button("⬇ CSV",
                        df_para_csv(t).to_csv(index=False).encode("utf-8"),
                        csv_nombre("hosteleria_luz"),
                        "text/csv", key="dl_hist_tbl")
                with hc2:
                    st.caption(f"{len(t)} registros")
                st.markdown(tabla_html(t), unsafe_allow_html=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="ftr">
  <div class="ftxt">ia indata agency · MEMO Hostelería ·
    <a href="https://github.com/mborrillo/ia-indata-agency"
       style="color:var(--teal);text-decoration:none">GitHub ↗</a>
  </div>
  <div class="ftags">
    <span class="ftag">REE</span>
    <span class="ftag">MAPA</span>
    <span class="ftag">INE</span>
    <span class="ftag">Neon</span>
  </div>
</div>
""", unsafe_allow_html=True)
