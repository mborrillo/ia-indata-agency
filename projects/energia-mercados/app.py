"""
MEMO — Monitor de Energía y Mercados
Dashboard Streamlit — ia-indata Agency
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="MEMO — Monitor Energía y Mercados",
    page_icon="⚡",
    layout="wide",
)

# ── Conexión ──────────────────────────────────────────────────────────────────
DB_URL = os.getenv("NEON_DATABASE_URL")

@st.cache_resource
def get_conn():
    return psycopg2.connect(DB_URL)

@st.cache_data(ttl=3600)
def q(sql: str) -> pd.DataFrame:
    try:
        return pd.read_sql(sql, get_conn())
    except Exception as e:
        st.error(f"Error BD: {e}")
        return pd.DataFrame()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⚡ MEMO — Monitor de Energía y Mercados")
st.caption("Datos actualizados diariamente · REE · Yahoo Finance · BCE · INE")

if not DB_URL:
    st.warning("⚠️ Sin conexión a BD — configura NEON_DATABASE_URL")
    st.stop()

# ── Navegación ────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["⚡ Energía", "📈 Mercados", "🌍 Macro"])

# ═══════════════════════════════════════════════════════════
# TAB 1: ENERGÍA
# ═══════════════════════════════════════════════════════════
with tab1:
    resumen = q("SELECT * FROM memo.v_energia_resumen")

    if resumen.empty:
        st.info("Sin datos de energía todavía. Ejecuta el ETL primero.")
    else:
        r = resumen.iloc[0]

        # Semáforo color
        color_map = {"BAJO": "🟢", "NORMAL": "🟡", "ALTO": "🔴"}
        semaforo = r.get("semaforo", "—")
        icono = color_map.get(semaforo, "⚪")

        # KPI cards
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Precio medio hoy", f"{r['precio_medio']:.4f} €/kWh",
                    f"{r['var_per_prev']:+.1f}% vs ayer" if r.get("var_per_prev") else None)
        col2.metric("Precio mínimo", f"{r['precio_min']:.4f} €/kWh",
                    f"Hora {int(r['hora_min'])}:00")
        col3.metric("Precio máximo", f"{r['precio_max']:.4f} €/kWh",
                    f"Hora {int(r['hora_max'])}:00")
        col4.metric(f"Semáforo {icono}", semaforo,
                    f"Media 30d: {r['media_30d']:.4f}")

        st.divider()

        # Histórico
        hist = q("SELECT * FROM memo.v_energia_historico ORDER BY fecha ASC")
        if not hist.empty:
            hist["fecha"] = pd.to_datetime(hist["fecha"])
            fig = go.Figure()
            fig.add_trace(go.Scatter(
                x=hist["fecha"], y=hist["precio_medio"],
                name="Precio medio", line=dict(color="#1e3a8a", width=1.5)
            ))
            fig.add_trace(go.Scatter(
                x=hist["fecha"], y=hist["media_movil_7d"],
                name="Media móvil 7d", line=dict(color="#f59e0b", width=2, dash="dash")
            ))
            fig.update_layout(
                title="Evolución precio luz (€/kWh)",
                template="plotly_white",
                legend=dict(orientation="h", y=-0.2),
                height=380,
            )
            st.plotly_chart(fig, use_container_width=True)

            with st.expander("Ver datos históricos completos"):
                st.dataframe(
                    hist[["fecha","precio_medio","precio_min","precio_max","semaforo"]],
                    use_container_width=True
                )

# ═══════════════════════════════════════════════════════════
# TAB 2: MERCADOS
# ═══════════════════════════════════════════════════════════
with tab2:
    mercados = q("SELECT * FROM memo.v_mercados_resumen")

    if mercados.empty:
        st.info("Sin datos de mercados todavía. Ejecuta el ETL primero.")
    else:
        # Filtro por categoría
        cats = ["Todas"] + sorted(mercados["categoria"].unique().tolist())
        cat_sel = st.selectbox("Filtrar por categoría", cats)

        df = mercados if cat_sel == "Todas" else mercados[mercados["categoria"] == cat_sel]

        # Tabla resumen con colores
        def color_var(val):
            if isinstance(val, float):
                if val > 2:   return "color: #16a34a; font-weight: 500"
                if val < -2:  return "color: #dc2626; font-weight: 500"
            return ""

        st.dataframe(
            df[["activo","categoria","precio_cierre","variacion_p","moneda","tendencia","fecha"]]
            .style.applymap(color_var, subset=["variacion_p"]),
            use_container_width=True, height=350
        )

        st.divider()

        # Gráfico barras variación
        fig2 = px.bar(
            df.sort_values("variacion_p"),
            x="variacion_p", y="activo",
            color="tendencia",
            color_discrete_map={"SUBE": "#16a34a", "BAJA": "#dc2626", "ESTABLE": "#6b7280"},
            orientation="h",
            title=f"Variación diaria % — {cat_sel}",
            template="plotly_white",
            height=400,
        )
        fig2.add_vline(x=0, line_dash="dash", line_color="gray", line_width=1)
        st.plotly_chart(fig2, use_container_width=True)

# ═══════════════════════════════════════════════════════════
# TAB 3: MACRO
# ═══════════════════════════════════════════════════════════
with tab3:
    macro = q("SELECT * FROM memo.v_macro_resumen")

    if macro.empty:
        st.info("Sin datos macro todavía. Ejecuta el ETL primero.")
    else:
        col1, col2 = st.columns(2)
        for _, row in macro.iterrows():
            if "USD" in row["indicador"]:
                col1.metric(
                    "💱 Tipo cambio EUR/USD",
                    f"{row['valor']}",
                    help="Fuente: Banco Central Europeo"
                )
                col1.caption(f"Fecha: {row['fecha']}")
            else:
                col2.metric(
                    "📊 IPC España (variación anual)",
                    f"{row['valor']}%",
                    help="Fuente: INE — IPC general"
                )
                col2.caption(f"Período: {row['fecha'][:7]}")

        st.divider()

        # Histórico EUR/USD
        hist_div = q("""
            SELECT fecha, tasa FROM memo.bronze_divisa
            WHERE par = 'EUR/USD'
            ORDER BY fecha ASC
        """)
        if not hist_div.empty:
            hist_div["fecha"] = pd.to_datetime(hist_div["fecha"])
            fig3 = px.line(
                hist_div, x="fecha", y="tasa",
                title="EUR/USD histórico (BCE)",
                template="plotly_white",
                color_discrete_sequence=["#7c3aed"],
                height=320,
            )
            st.plotly_chart(fig3, use_container_width=True)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🏢 ia-indata Agency · Proyecto MEMO · "
           "[GitHub](https://github.com/mborrillo/ia-indata-agency) · "
           "Datos: REE, Yahoo Finance, BCE, INE")
