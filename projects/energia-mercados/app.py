"""
MEMO — Monitor de Energía y Mercados
ia-indata Agency · v2
"""
import os
import psycopg2
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
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
    --bg:     #2c303f;    #4a5065-2c303f-0c0e14
    --bg2:    #12151f;
    --bg3:    #181c28;
    --bdr:    rgba(255,255,255,0.06);
    --bdr2:   rgba(255,255,255,0.12);
    --teal:   #2dd4bf;
    --purple: #a78bfa;
    --amber:  #fbbf24;
    --red:    #f87171;
    --green:  #34d399;
    --text:   #e2e8f0;
    --muted:  #64748b;
    --dim:    #94a3b8;
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
    display: flex;
    align-items: center;
    gap: 14px;
    padding-bottom: 22px;
    border-bottom: 1px solid var(--bdr);
    margin-bottom: 28px;
}
.memo-logo {
    font-family: 'Space Mono', monospace;
    font-size: 22px;
    font-weight: 700;
    color: var(--teal);
    letter-spacing: -0.5px;
    line-height: 1;
}
.memo-sub {
    font-size: 12px;
    color: var(--muted);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-top: 3px;
}
.memo-badge {
    margin-left: auto;
    font-family: 'Space Mono', monospace;
    font-size: 11px;
    color: var(--teal);
    background: rgba(45,212,191,0.08);
    border: 1px solid rgba(45,212,191,0.2);
    padding: 5px 12px;
    border-radius: 20px;
}

/* ── Section title ── */
.section-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 14px;
    display: flex;
    align-items: center;
    gap: 8px;
}
.section-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: var(--bdr);
}

/* ── KPI Cards ── */
.kpi-row { display: grid; gap: 12px; margin-bottom: 28px; }
.kpi-4 { grid-template-columns: repeat(4, 1fr); }
.kpi-3 { grid-template-columns: repeat(3, 1fr); }
.kpi-2 { grid-template-columns: repeat(2, 1fr); }

.kpi {
    background: var(--bg2);
    border: 1px solid var(--bdr);
    border-radius: 12px;
    padding: 20px 22px;
    position: relative;
    overflow: hidden;
    transition: border-color 0.2s, transform 0.15s;
}
.kpi:hover { border-color: var(--bdr2); transform: translateY(-1px); }
.kpi-accent {
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    border-radius: 12px 12px 0 0;
}
.kpi-label {
    font-size: 11px;
    font-weight: 500;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 10px;
}
.kpi-value {
    font-family: 'Space Mono', monospace;
    font-size: 26px;
    font-weight: 700;
    color: var(--text);
    line-height: 1;
    margin-bottom: 8px;
}
.kpi-value.lg { font-size: 32px; }
.kpi-delta {
    font-size: 12px;
    color: var(--dim);
    display: flex;
    align-items: center;
    gap: 5px;
}
.kpi-delta.up   { color: var(--green); }
.kpi-delta.down { color: var(--red); }
.kpi-delta.warn { color: var(--amber); }

/* ── Semáforo pill ── */
.semaforo {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.05em;
    padding: 6px 14px;
    border-radius: 20px;
    margin-top: 4px;
}
.sem-bajo   { background: rgba(52,211,153,0.12); color: var(--green); border: 1px solid rgba(52,211,153,0.25); }
.sem-normal { background: rgba(251,191,36,0.10); color: var(--amber); border: 1px solid rgba(251,191,36,0.22); }
.sem-alto   { background: rgba(248,113,113,0.10); color: var(--red);  border: 1px solid rgba(248,113,113,0.22); }

/* ── Mercados table ── */
.mkt-table { width: 100%; border-collapse: collapse; }
.mkt-table th {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--muted);
    padding: 10px 14px;
    border-bottom: 1px solid var(--bdr);
    text-align: left;
}
.mkt-table td {
    padding: 12px 14px;
    border-bottom: 1px solid var(--bdr);
    font-size: 13px;
    color: var(--text);
}
.mkt-table tr:hover td { background: var(--bg3); }
.mkt-table tr:last-child td { border-bottom: none; }
.cat-pill {
    display: inline-block;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 3px 8px;
    border-radius: 4px;
}
.cat-Energia     { background: rgba(251,191,36,0.12); color: var(--amber); }
.cat-Industrial  { background: rgba(167,139,250,0.12); color: var(--purple); }
.cat-Alimentacion{ background: rgba(52,211,153,0.10); color: var(--green); }
.cat-Indice      { background: rgba(45,212,191,0.10); color: var(--teal); }
.cat-Divisa      { background: rgba(255,255,255,0.07); color: var(--dim); }
.var-up   { color: var(--green); font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700; }
.var-down { color: var(--red);   font-family: 'Space Mono', monospace; font-size: 12px; font-weight: 700; }
.var-flat { color: var(--dim);   font-family: 'Space Mono', monospace; font-size: 12px; }
.price-mono { font-family: 'Space Mono', monospace; font-size: 13px; }

/* ── Nav tabs ── */
[data-testid="stTabs"] [role="tablist"] {
    background: var(--bg2) !important;
    border: 1px solid var(--bdr) !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 2px !important;
    margin-bottom: 24px;
}
[data-testid="stTabs"] [role="tab"] {
    background: transparent !important;
    border: none !important;
    color: var(--muted) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    padding: 8px 18px !important;
    border-radius: 7px !important;
    transition: all 0.15s !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    background: var(--bg3) !important;
    color: var(--teal) !important;
    border: 1px solid var(--bdr2) !important;
}
[data-testid="stTabs"] [role="tab"]:hover:not([aria-selected="true"]) {
    color: var(--text) !important;
    background: rgba(255,255,255,0.04) !important;
}

/* ── Chart containers ── */
.chart-box {
    background: var(--bg2);
    border: 1px solid var(--bdr);
    border-radius: 12px;
    padding: 20px 20px 12px;
    margin-bottom: 16px;
}
.chart-title {
    font-size: 12px;
    font-weight: 500;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--dim);
    margin-bottom: 2px;
}

/* ── Footer ── */
.memo-footer {
    border-top: 1px solid var(--bdr);
    padding-top: 20px;
    margin-top: 40px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.footer-left {
    font-size: 11px;
    color: var(--muted);
    font-family: 'Space Mono', monospace;
}
.footer-sources {
    display: flex;
    gap: 12px;
}
.source-tag {
    font-size: 10px;
    color: var(--muted);
    background: var(--bg2);
    border: 1px solid var(--bdr);
    padding: 3px 9px;
    border-radius: 4px;
    letter-spacing: 0.05em;
    text-transform: uppercase;
}
</style>
""", unsafe_allow_html=True)

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_conn():
    return psycopg2.connect(DB_URL)

@st.cache_data(ttl=3600)
def q(sql):
    try:
        return pd.read_sql(sql, get_conn())
    except Exception as e:
        return pd.DataFrame()

# ── Plotly dark theme ─────────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="DM Sans, sans-serif", color="#94a3b8", size=12),
    margin=dict(l=0, r=0, t=10, b=0),
    legend=dict(
        bgcolor="rgba(0,0,0,0)",
        bordercolor="rgba(255,255,255,0.08)",
        borderwidth=1,
        font=dict(size=11),
        orientation="h",
        yanchor="bottom", y=-0.25,
        xanchor="left", x=0,
    ),
    xaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=11),
    ),
    yaxis=dict(
        gridcolor="rgba(255,255,255,0.04)",
        zerolinecolor="rgba(255,255,255,0.08)",
        tickfont=dict(size=11),
    ),
)

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

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⚡  Energía", "📈  Mercados", "🌍  Macro"])

# ════════════════════════════════════════════════════════════
# TAB 1 — ENERGÍA
# ════════════════════════════════════════════════════════════
with tab1:
    res = q("SELECT * FROM memo.v_energia_resumen")

    if res.empty:
        st.info("Sin datos aún. Ejecuta el ETL.")
    else:
        r = res.iloc[0]
        sem = str(r.get("semaforo", "NORMAL")).upper()
        sem_class = {"BAJO": "sem-bajo", "NORMAL": "sem-normal", "ALTO": "sem-alto"}.get(sem, "sem-normal")
        sem_dot   = {"BAJO": "▼", "NORMAL": "◆", "ALTO": "▲"}.get(sem, "◆")

        var = r.get("var_per_prev")
        delta_class = "up" if var and var < 0 else ("down" if var and var > 0 else "")
        delta_arrow = "↓" if var and var < 0 else ("↑" if var and var > 0 else "→")
        delta_txt   = f"{delta_arrow} {abs(var):.1f}% vs ayer" if var else "primer registro"

        media30 = r.get("media_30d", 0)
        diff30  = r["precio_medio"] - media30
        diff30_pct = (diff30 / media30 * 100) if media30 else 0

        st.markdown('<div class="section-label">Precio PVPC hoy</div>', unsafe_allow_html=True)
        st.markdown(f"""
        <div class="kpi-row kpi-4">
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--teal)"></div>
            <div class="kpi-label">Precio medio</div>
            <div class="kpi-value lg">{r['precio_medio']:.4f}</div>
            <div class="kpi-delta {delta_class}">{delta_txt}</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--green)"></div>
            <div class="kpi-label">Mínimo del día</div>
            <div class="kpi-value">{r['precio_min']:.4f}</div>
            <div class="kpi-delta">🕐 Hora {int(r['hora_min'])}:00 &nbsp;€/kWh</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--red)"></div>
            <div class="kpi-label">Máximo del día</div>
            <div class="kpi-value">{r['precio_max']:.4f}</div>
            <div class="kpi-delta">🕐 Hora {int(r['hora_max'])}:00 &nbsp;€/kWh</div>
          </div>
          <div class="kpi">
            <div class="kpi-accent" style="background:var(--amber)"></div>
            <div class="kpi-label">Estado vs media 30d</div>
            <div style="margin-top:6px">
              <span class="semaforo {sem_class}">{sem_dot} {sem}</span>
            </div>
            <div class="kpi-delta" style="margin-top:8px">media: {media30:.4f} &nbsp;({diff30_pct:+.1f}%)</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico histórico
        hist = q("SELECT fecha, precio_medio, precio_min, precio_max, media_movil_7d FROM memo.v_energia_historico ORDER BY fecha ASC")
        if not hist.empty:
            hist["fecha"] = pd.to_datetime(hist["fecha"]).dt.date

            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["fecha"], y=hist["precio_max"],
                fill=None, mode="lines",
                line=dict(color="rgba(248,113,113,0)", width=0),
                showlegend=False, hoverinfo="skip",
            ))
            fig.add_trace(go.Scatter(
                x=hist["fecha"], y=hist["precio_min"],
                fill="tonexty",
                fillcolor="rgba(45,212,191,0.07)",
                mode="lines",
                line=dict(color="rgba(45,212,191,0)", width=0),
                name="Rango min/max",
            ))
            fig.add_trace(go.Scatter(
                x=hist["fecha"], y=hist["precio_medio"],
                mode="lines+markers",
                line=dict(color="#2dd4bf", width=2),
                marker=dict(size=5, color="#2dd4bf"),
                name="Precio medio",
            ))
            if "media_movil_7d" in hist.columns:
                fig.add_trace(go.Scatter(
                    x=hist["fecha"], y=hist["media_movil_7d"],
                    mode="lines",
                    line=dict(color="#fbbf24", width=1.5, dash="dot"),
                    name="Media móvil 7d",
                ))
            fig.update_layout(**PLOTLY_LAYOUT, height=300)
            st.markdown('<div class="chart-box"><div class="chart-title">Evolución precio luz · €/kWh</div>', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            st.markdown('</div>', unsafe_allow_html=True)

            with st.expander("Ver tabla histórica completa"):
                tabla_e = hist[["fecha","precio_medio","precio_min","precio_max","media_movil_7d"]].copy()
                tabla_e = tabla_e.sort_values("fecha", ascending=False).reset_index(drop=True)
                tabla_e.columns = ["Fecha","Precio medio","Mínimo","Máximo","Media 7d"]
                st.dataframe(tabla_e, use_container_width=True, hide_index=True)

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

        # KPI summary
        n_sube  = len(df[df["tendencia"] == "SUBE"])
        n_baja  = len(df[df["tendencia"] == "BAJA"])
        n_est   = len(df[df["tendencia"] == "ESTABLE"])
        var_avg = df["variacion_p"].mean()

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
            <div class="kpi-value {'kpi-delta up' if var_avg>=0 else 'kpi-delta down'}"
                 style="font-family:'Space Mono',monospace;font-size:24px;font-weight:700;
                        color:{'#34d399' if var_avg>=0 else '#f87171'}">{var_avg:+.2f}%</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Tabla custom
        rows_html = ""
        for _, row in df.sort_values("categoria").iterrows():
            var = row["variacion_p"]
            var_class = "var-up" if var > 2 else ("var-down" if var < -2 else "var-flat")
            var_arrow = "▲" if var > 2 else ("▼" if var < -2 else "—")
            cat_cls = f"cat-{row['categoria']}"
            rows_html += f"""
            <tr>
              <td><strong>{row['activo'].replace('_',' ')}</strong></td>
              <td><span class="cat-pill {cat_cls}">{row['categoria']}</span></td>
              <td class="price-mono">{row['precio_cierre']:,.4f}</td>
              <td class="{var_class}">{var_arrow} {abs(var):.2f}%</td>
              <td style="color:var(--muted);font-size:12px">{row['moneda']}</td>
            </tr>"""

        st.markdown(f"""
        <div style="background:var(--bg2);border:1px solid var(--bdr);border-radius:12px;overflow:hidden;margin-bottom:20px">
          <table class="mkt-table">
            <thead><tr>
              <th>Activo</th><th>Categoría</th><th>Precio cierre</th>
              <th>Variación</th><th>Moneda</th>
            </tr></thead>
            <tbody>{rows_html}</tbody>
          </table>
        </div>
        """, unsafe_allow_html=True)

        # Gráfico barras
        df_sorted = df.sort_values("variacion_p")
        colors = ["#f87171" if v < -2 else ("#34d399" if v > 2 else "#475569")
                  for v in df_sorted["variacion_p"]]
        fig2 = go.Figure(go.Bar(
            x=df_sorted["variacion_p"],
            y=df_sorted["activo"].str.replace("_", " "),
            orientation="h",
            marker_color=colors,
            text=[f"{v:+.2f}%" for v in df_sorted["variacion_p"]],
            textposition="outside",
            textfont=dict(size=11, family="Space Mono"),
        ))
        fig2.add_vline(x=0, line_color="rgba(255,255,255,0.15)", line_width=1)
        fig2.update_layout(**PLOTLY_LAYOUT, height=320)
        st.markdown('<div class="chart-box"><div class="chart-title">Variación diaria %</div>', unsafe_allow_html=True)
        st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════
# TAB 3 — MACRO
# ════════════════════════════════════════════════════════════
with tab3:
    macro = q("SELECT * FROM memo.v_macro_resumen")
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
        hist_div["fecha"] = pd.to_datetime(hist_div["fecha"]).dt.date
        fig3 = go.Figure(go.Scatter(
            x=hist_div["fecha"], y=hist_div["tasa"],
            mode="lines+markers",
            line=dict(color="#a78bfa", width=2),
            marker=dict(size=5, color="#a78bfa"),
            fill="tozeroy",
            fillcolor="rgba(167,139,250,0.06)",
            name="EUR/USD",
        ))
        fig3.update_layout(**PLOTLY_LAYOUT, height=280)
        st.markdown('<div class="chart-box"><div class="chart-title">EUR/USD histórico · BCE</div>', unsafe_allow_html=True)
        st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
        st.markdown('</div>', unsafe_allow_html=True)

        # Tabla histórica EUR/USD con variación
        if not hist_div.empty:
            with st.expander("Ver tabla histórica EUR/USD"):
                td = hist_div[["fecha","tasa"]].copy()
                td = td.sort_values("fecha", ascending=False).reset_index(drop=True)
                td["variacion"] = td["tasa"].pct_change(-1) * 100
                td["variacion"] = td["variacion"].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
                )
                td.columns = ["Fecha","EUR/USD","Variación %"]
                st.dataframe(td, use_container_width=True, hide_index=True)

        # Tabla histórica IPC con variación
        hist_ipc = q("""
            SELECT fecha, valor FROM memo.bronze_macro
            WHERE indicador = 'IPC_GENERAL_ESP'
            ORDER BY fecha DESC
        """)
        if not hist_ipc.empty:
            with st.expander("Ver histórico IPC España"):
                ti = hist_ipc.copy()
                ti["variacion"] = ti["valor"].pct_change(-1) * 100
                ti["variacion"] = ti["variacion"].apply(
                    lambda x: f"{x:+.2f}%" if pd.notna(x) else "—"
                )
                ti.columns = ["Fecha","IPC (var. anual %)","Variación vs anterior %"]
                st.dataframe(ti, use_container_width=True, hide_index=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="memo-footer">
  <div class="footer-left">ia-indata Agency · MEMO v2 ·
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
