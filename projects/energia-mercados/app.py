"""
MEMO — Monitor de Energía y Mercados
ia-indata Agency · v3 final
"""
import io
import os
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="MEMO · Energía & Mercados",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,300&display=swap');

:root {
    --bg:     #0c0e14; #080a0f
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
    --text2:  #cbd5e1;
    --dim:    #94a3b8;
    --muted:  #475569;
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

/* ── Header ── */
.memo-header {
    display: flex; align-items: center; gap: 14px;
    padding-bottom: 22px; border-bottom: 1px solid var(--bdr); margin-bottom: 28px;
}
.memo-logo { font-family: 'Space Mono', monospace; font-size: 22px; font-weight: 700; color: var(--teal); letter-spacing: -0.5px; }
.memo-sub  { font-size: 12px; color: var(--muted); letter-spacing: 0.06em; text-transform: uppercase; margin-top: 3px; }
.memo-badge { margin-left: auto; font-family: 'Space Mono', monospace; font-size: 11px; color: var(--teal); background: rgba(45,212,191,0.08); border: 1px solid rgba(45,212,191,0.2); padding: 5px 12px; border-radius: 20px; }

/* ── Section label ── */
.section-label { font-size: 10px; font-weight: 600; letter-spacing: 0.12em; text-transform: uppercase; color: var(--dim); margin-bottom: 14px; display: flex; align-items: center; gap: 8px; }
.section-label::after { content: ''; flex: 1; height: 1px; background: var(--bdr); }

/* ── KPI Cards ── */
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

/* ── Semáforo ── */
.semaforo { display: inline-flex; align-items: center; gap: 7px; font-size: 13px; font-weight: 600; letter-spacing: 0.05em; padding: 6px 14px; border-radius: 20px; margin-top: 4px; }
.sem-bajo   { background: rgba(52,211,153,0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }
.sem-normal { background: rgba(251,191,36,0.10);  color: var(--amber); border: 1px solid rgba(251,191,36,0.22); }
.sem-alto   { background: rgba(248,113,113,0.10); color: var(--red);   border: 1px solid rgba(248,113,113,0.22); }

/* ── Mercados table ── */
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

/* ── Nav tabs ── */
[data-testid="stTabs"] [role="tablist"] { background: var(--bg2) !important; border: 1px solid var(--bdr) !important; border-radius: 10px !important; padding: 4px !important; gap: 2px !important; margin-bottom: 24px; }
[data-testid="stTabs"] [role="tab"] { background: transparent !important; border: none !important; color: var(--muted) !important; font-family: 'DM Sans', sans-serif !important; font-size: 13px !important; font-weight: 500 !important; padding: 8px 18px !important; border-radius: 7px !important; transition: all 0.15s !important; }
[data-testid="stTabs"] [role="tab"][aria-selected="true"] { background: var(--bg3) !important; color: var(--purple) !important; border: 1px solid rgba(196,181,253,0.2) !important; }
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) { color: var(--text) !important; background: rgba(255,255,255,0.04) !important; }

/* ── Multiselect & Selectbox violeta ── */
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

/* ── Download button ── */
[data-testid="stDownloadButton"] button { background: var(--bg3) !important; border: 1px solid var(--bdr2) !important; color: var(--purple) !important; border-radius: 8px !important; font-size: 12px !important; padding: 6px 14px !important; transition: all 0.15s !important; }
[data-testid="stDownloadButton"] button:hover { border-color: rgba(196,181,253,0.4) !important; background: rgba(196,181,253,0.08) !important; }

/* ── Expander ── */
[data-testid="stExpander"] summary:hover { color: #c4b5fd !important; }
[data-testid="stExpander"] details { background: var(--bg2) !important; border: 1px solid var(--bdr) !important; border-radius: 10px !important; }

/* ── Chart containers ── */
.chart-box { background: var(--bg2); border: 1px solid var(--bdr); border-radius: 12px; padding: 20px 20px 12px; margin-bottom: 16px; }
.chart-title { font-size: 12px; font-weight: 500; letter-spacing: 0.06em; text-transform: uppercase; color: var(--dim); margin-bottom: 2px; }

/* ── Footer ── */
.memo-footer { border-top: 1px solid var(--bdr); padding-top: 20px; margin-top: 40px; display: flex; align-items: center; justify-content: space-between; }
.footer-left { font-size: 11px; color: var(--muted); font-family: 'Space Mono', monospace; }
.footer-sources { display: flex; gap: 12px; }
.source-tag { font-size: 10px; color: var(--muted); background: var(--bg2); border: 1px solid var(--bdr); padding: 3px 9px; border-radius: 4px; letter-spacing: 0.05em; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_conn():
    return psycopg2.connect(DB_URL)

@st.cache_data(ttl=300)
def q(sql):
    try:
        return pd.read_sql(sql, get_conn())
    except Exception:
        return pd.DataFrame()

# ── Plotly theme ──────────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(bgcolor="rgba(0,0,0,0)", bordercolor="rgba(255,255,255,0.08)",
                borderwidth=1, font=dict(size=11), orientation="h",
                yanchor="bottom", y=-0.25, xanchor="left", x=0),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.08)", tickfont=dict(size=11)),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.08)", tickfont=dict(size=11)),
)

# ── Helpers ───────────────────────────────────────────────────────────────────
def color_var(v):
    """Devuelve HTML con color según signo de variación."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return '<span style="color:#c4b5fd">—</span>'
    try:
        n = float(str(v).replace("%","").replace("+",""))
        if n > 0:  return f'<span style="color:#34d399;font-weight:600">▲ {n:.2f}%</span>'
        if n < 0:  return f'<span style="color:#f87171;font-weight:600">▼ {abs(n):.2f}%</span>'
        return f'<span style="color:#c4b5fd">— {n:.2f}%</span>'
    except Exception:
        return f'<span style="color:#c4b5fd">{v}</span>'

def tabla_html(df, col_var="Variación %"):
    """Renderiza DataFrame como tabla HTML con variación coloreada."""
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
      <table class="mkt-table">
        <thead><tr>{ths}</tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </div>"""

def csv_bytes(df):
    return df.to_csv(index=False).encode("utf-8")

def apply_filter(df, col, sel):
    """Si sel está vacío devuelve todo, si no filtra."""
    return df if not sel else df[df[col].isin(sel)]

# ── Guard ─────────────────────────────────────────────────────────────────────
if not DB_URL:
    st.error("⚠ NEON_DATABASE_URL no configurada")
    st.stop()

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="memo-header">
  <div>
    <div class="memo-logo">⚡ MEMO</div>
    <div class="memo-sub">Monitor de Energía &amp; Mercados · ia-indata Agency</div>
  </div>
  <div class="memo-badge">● LIVE · datos diarios</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["⚡  Energía", "📈  Mercados", "🌍  Macro"])

# ════════════════════════════════════════════════════════════
# TAB 1 — ENERGÍA
# ════════════════════════════════════════════════════════════
with tab1:
    hist_raw = q("""
        SELECT fecha, precio_medio, precio_min, precio_max, media_movil_7d
        FROM memo.v_energia_historico ORDER BY fecha ASC
    """)

    if hist_raw.empty:
        st.info("Sin datos de energía. Ejecuta el ETL.")
    else:
        hist_raw["fecha"] = pd.to_datetime(hist_raw["fecha"])
        hist_raw["YY-MM"] = hist_raw["fecha"].dt.strftime("%Y-%m")
        hist_raw["YY-WW"] = hist_raw["fecha"].dt.strftime("%Y-W%W")

        # ── Filtros (fuera del expander — reactivos) ──
        st.markdown('<div class="section-label">Filtros</div>', unsafe_allow_html=True)
        fc1, fc2 = st.columns(2)
        meses_e = sorted(hist_raw["YY-MM"].unique(), reverse=True)
        weeks_e = sorted(hist_raw["YY-WW"].unique(), reverse=True)
        with fc1:
            sel_mes_e = st.multiselect("Mes (YY-MM)", meses_e, default=[], key="e_mes",
                                        placeholder="Todos los meses")
        with fc2:
            sel_wk_e  = st.multiselect("Semana (YY-WW)", weeks_e, default=[], key="e_wk",
                                        placeholder="Todas las semanas")

        # Datos filtrados para tarjetas, gráfico y tabla
        hist = hist_raw.copy()
        hist = apply_filter(hist, "YY-MM", sel_mes_e)
        hist = apply_filter(hist, "YY-WW", sel_wk_e)
        hist = hist.sort_values("fecha").reset_index(drop=True)

        if hist.empty:
            st.warning("Sin datos para el filtro seleccionado.")
        else:
            # Calcular variación para KPIs del período filtrado
            precio_med  = hist["precio_medio"].mean()
            precio_min  = hist["precio_min"].min()
            precio_max  = hist["precio_max"].max()
            hora_min_r  = q("SELECT hora_min FROM memo.v_energia_resumen LIMIT 1")
            hora_max_r  = q("SELECT hora_max FROM memo.v_energia_resumen LIMIT 1")
            hora_min_v  = int(hora_min_r.iloc[0,0]) if not hora_min_r.empty else "—"
            hora_max_v  = int(hora_max_r.iloc[0,0]) if not hora_max_r.empty else "—"

            hist["var_p"] = hist["precio_medio"].pct_change() * 100
            var_avg = hist["var_p"].mean()
            n_dias  = len(hist)
            n_sube  = (hist["var_p"] > 0).sum()
            n_baja  = (hist["var_p"] < 0).sum()

            # Semáforo del período
            media_global = hist_raw["precio_medio"].mean()
            sem_val  = "BAJO" if precio_med < media_global * 0.85 else ("ALTO" if precio_med > media_global * 1.15 else "NORMAL")
            sem_cls  = {"BAJO":"sem-bajo","NORMAL":"sem-normal","ALTO":"sem-alto"}[sem_val]
            sem_dot  = {"BAJO":"▼","NORMAL":"◆","ALTO":"▲"}[sem_val]
            color_avg = "#34d399" if var_avg >= 0 else "#f87171"

            st.markdown('<div class="section-label">KPIs del período seleccionado</div>', unsafe_allow_html=True)
            st.markdown(f"""
            <div class="kpi-row kpi-4">
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--teal)"></div>
                <div class="kpi-label">Precio medio período</div>
                <div class="kpi-value lg">{precio_med:.4f}</div>
                <div class="kpi-delta">{n_dias} días seleccionados</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--green)"></div>
                <div class="kpi-label">Mínimo período</div>
                <div class="kpi-value">{precio_min:.4f}</div>
                <div class="kpi-delta">€/kWh</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--red)"></div>
                <div class="kpi-label">Máximo período</div>
                <div class="kpi-value">{precio_max:.4f}</div>
                <div class="kpi-delta">€/kWh</div>
              </div>
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--purple)"></div>
                <div class="kpi-label">Variación media</div>
                <div class="kpi-value" style="font-size:24px;color:{color_avg}">{var_avg:+.2f}%</div>
                <div class="kpi-delta">▲ {n_sube} días · ▼ {n_baja} días</div>
              </div>
            </div>
            <div class="kpi-row kpi-2" style="max-width:400px;margin-top:-16px">
              <div class="kpi">
                <div class="kpi-accent" style="background:var(--amber)"></div>
                <div class="kpi-label">Estado vs histórico</div>
                <div style="margin-top:6px"><span class="semaforo {sem_cls}">{sem_dot} {sem_val}</span></div>
              </div>
            </div>
            """, unsafe_allow_html=True)

            # Gráfico — reactivo al filtro
            hist_plot = hist.copy()
            hist_plot["fecha_d"] = hist_plot["fecha"].dt.date
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=hist_plot["fecha_d"], y=hist_plot["precio_max"],
                fill=None, mode="lines", line=dict(color="rgba(0,0,0,0)", width=0),
                showlegend=False, hoverinfo="skip"))
            fig.add_trace(go.Scatter(x=hist_plot["fecha_d"], y=hist_plot["precio_min"],
                fill="tonexty", fillcolor="rgba(45,212,191,0.07)",
                mode="lines", line=dict(color="rgba(0,0,0,0)", width=0), name="Rango min/max"))
            fig.add_trace(go.Scatter(x=hist_plot["fecha_d"], y=hist_plot["precio_medio"],
                mode="lines+markers", line=dict(color="#2dd4bf", width=2),
                marker=dict(size=5, color="#2dd4bf"), name="Precio medio"))
            if "media_movil_7d" in hist_plot.columns:
                fig.add_trace(go.Scatter(x=hist_plot["fecha_d"], y=hist_plot["media_movil_7d"],
                    mode="lines", line=dict(color="#fbbf24", width=1.5, dash="dot"), name="Media móvil 7d"))
            fig.update_layout(**PLOTLY_LAYOUT, height=300)
            st.markdown('<div class="chart-box"><div class="chart-title">Evolución precio luz · €/kWh</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            # Tabla con descarga
            with st.expander("Ver tabla histórica"):
                tabla = hist.sort_values("fecha", ascending=False).copy()
                tabla["var_str"] = tabla["var_p"].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
                tabla["fecha_d"] = tabla["fecha"].dt.date
                t_show = tabla[["fecha_d","precio_medio","precio_min","precio_max","media_movil_7d","YY-MM","YY-WW","var_str"]].copy()
                t_show.columns = ["Fecha","Precio medio","Mínimo","Máximo","Media 7d","Mes","Semana","Variación %"]
                st.markdown(tabla_html(t_show), unsafe_allow_html=True)
                dl_col, info_col = st.columns([1, 4])
                with dl_col:
                    st.download_button("⬇ Descargar CSV", csv_bytes(t_show),
                        "memo_energia.csv", "text/csv", key="dl_energia")
                with info_col:
                    st.caption(f"{len(t_show)} registros")

# ════════════════════════════════════════════════════════════
# TAB 2 — MERCADOS
# ════════════════════════════════════════════════════════════
with tab2:
    mkt = q("SELECT * FROM memo.v_mercados_resumen")

    if mkt.empty:
        st.info("Sin datos de mercados.")
    else:
        cats = ["Todas"] + sorted(mkt["categoria"].unique().tolist())
        col_f, _ = st.columns([2, 5])
        with col_f:
            cat_sel = st.selectbox("Categoría", cats, label_visibility="collapsed")

        df = mkt if cat_sel == "Todas" else mkt[mkt["categoria"] == cat_sel]

        # KPIs reactivos al filtro de categoría
        n_sube  = len(df[df["tendencia"] == "SUBE"])
        n_baja  = len(df[df["tendencia"] == "BAJA"])
        n_est   = len(df[df["tendencia"] == "ESTABLE"])
        var_avg = df["variacion_p"].mean()
        color_avg = "#34d399" if var_avg >= 0 else "#f87171"

        st.markdown(f"""
        <div class="kpi-row kpi-4" style="margin-bottom:20px">
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--green)"></div>
            <div class="kpi-label">Activos al alza</div>
            <div class="kpi-value">{n_sube}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--red)"></div>
            <div class="kpi-label">Activos a la baja</div>
            <div class="kpi-value">{n_baja}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--muted)"></div>
            <div class="kpi-label">Estables</div>
            <div class="kpi-value">{n_est}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--purple)"></div>
            <div class="kpi-label">Variación media</div>
            <div class="kpi-value" style="font-size:24px;color:{color_avg}">{var_avg:+.2f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabla mercados con colores
        rows_html = ""
        for _, row in df.sort_values("categoria").iterrows():
            var = row["variacion_p"]
            if var > 2:    var_cell = f'<span style="color:#34d399;font-weight:600">▲ {abs(var):.2f}%</span>'
            elif var < -2: var_cell = f'<span style="color:#f87171;font-weight:600">▼ {abs(var):.2f}%</span>'
            else:           var_cell = f'<span style="color:#c4b5fd">— {abs(var):.2f}%</span>'
            cat_cls = f"cat-{row['categoria']}"
            rows_html += f"""
            <tr>
              <td><strong>{row['activo'].replace('_',' ')}</strong></td>
              <td><span class="cat-pill {cat_cls}">{row['categoria']}</span></td>
              <td class="price-mono">{row['precio_cierre']:,.4f}</td>
              <td>{var_cell}</td>
              <td style="color:var(--muted);font-size:12px">{row['moneda']}</td>
            </tr>"""

        st.markdown(f"""
        <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:12px;overflow:hidden;margin-bottom:12px">
          <table class="mkt-table">
            <thead><tr>
              <th>Activo</th><th>Categoría</th><th>Precio cierre</th>
              <th>Variación</th><th>Moneda</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

        # Descarga tabla mercados
        df_dl = df[["activo","categoria","precio_cierre","variacion_p","moneda","tendencia","fecha"]].copy()
        df_dl["activo"] = df_dl["activo"].str.replace("_"," ")
        st.download_button("⬇ Descargar CSV", csv_bytes(df_dl),
            "memo_mercados.csv", "text/csv", key="dl_mkt")

        # Gráfico barras reactivo
        df_sorted = df.sort_values("variacion_p")
        colors = ["#f87171" if v < -2 else ("#34d399" if v > 2 else "#c4b5fd")
                  for v in df_sorted["variacion_p"]]
        fig2 = go.Figure(go.Bar(
            x=df_sorted["variacion_p"],
            y=df_sorted["activo"].str.replace("_"," "),
            orientation="h", marker_color=colors,
            text=[f"{v:+.2f}%" for v in df_sorted["variacion_p"]],
            textposition="outside",
            textfont=dict(size=11, family="Space Mono"),
        ))
        fig2.add_vline(x=0, line_color="rgba(255,255,255,0.15)", line_width=1)
        fig2.update_layout(**PLOTLY_LAYOUT, height=max(280, len(df)*36))
        st.markdown('<div class="chart-box"><div class="chart-title">Variación diaria %</div>', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 3 — MACRO
# ════════════════════════════════════════════════════════════
with tab3:
    macro    = q("SELECT * FROM memo.v_macro_resumen")
    hist_div = q("SELECT fecha, tasa FROM memo.bronze_divisa WHERE par='EUR/USD' ORDER BY fecha ASC")

    if not macro.empty:
        st.markdown('<div class="section-label">Indicadores macroeconómicos</div>', unsafe_allow_html=True)
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
        mc1, mc2 = st.columns(2)
        meses_m = sorted(hist_div["YY-MM"].unique(), reverse=True)
        weeks_m = sorted(hist_div["YY-WW"].unique(), reverse=True)
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
            color_avg_m = "#34d399" if var_avg_m >= 0 else "#f87171"
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

            # Tabla EUR/USD con descarga
            with st.expander("Ver tabla histórica EUR/USD"):
                td = hd.sort_values("fecha", ascending=False).copy()
                td["var_str"] = td["variacion_p"].apply(lambda x: f"{x:+.2f}%" if pd.notna(x) else "—")
                td["fecha_d"] = td["fecha"].dt.date
                td_show = td[["fecha_d","tasa","var_str","YY-MM","YY-WW"]].copy()
                td_show.columns = ["Fecha","EUR/USD","Variación %","Mes","Semana"]
                st.markdown(tabla_html(td_show), unsafe_allow_html=True)
                dl2, info2 = st.columns([1,4])
                with dl2:
                    st.download_button("⬇ Descargar CSV", csv_bytes(td_show),
                        "memo_eurusd.csv", "text/csv", key="dl_div")
                with info2:
                    st.caption(f"{len(td_show)} registros")

    # Tabla IPC
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
            dl3, info3 = st.columns([1,4])
            with dl3:
                st.download_button("⬇ Descargar CSV", csv_bytes(ti_show),
                    "memo_ipc.csv", "text/csv", key="dl_ipc")
            with info3:
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
