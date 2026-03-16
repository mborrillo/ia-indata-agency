"""
SIMIR — App Streamlit para el gerente de tienda.
C1–C5: Resumen (KPI cards) → Comparativa (gráficos) → Detalle (tablas) + Reporte ejecutivo.
Solo lectura desde vistas Gold. DATABASE_URL o NEON_DATABASE_URL en entorno.
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px

try:
    import sqlalchemy
except ImportError:
    st.error("Instalar: pip install sqlalchemy psycopg2-binary")
    st.stop()

DATABASE_URL = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    st.warning("Definir NEON_DATABASE_URL o DATABASE_URL para conectar a Neon.")
    st.info("Usando datos de ejemplo estáticos para demo.")
    USE_DB = False
else:
    USE_DB = True

st.set_page_config(page_title="SIMIR — Inventarios Retail", layout="wide")
st.title("SIMIR — Sistema de Inteligencia para Gestión de Inventarios Retail")

# --- Conexión Gold ---
@st.cache_resource
def get_engine():
    if not USE_DB:
        return None
    return sqlalchemy.create_engine(DATABASE_URL)

def read_gold(view: str) -> pd.DataFrame:
    if not USE_DB:
        return pd.DataFrame()
    engine = get_engine()
    return pd.read_sql(f'SELECT * FROM retail_gold.{view}', engine)

# --- C2: Resumen — KPI cards ---
st.header("Resumen")
rotacion = read_gold("v_rotacion_inventario")
alertas = read_gold("v_alertas_stock")

if USE_DB and not rotacion.empty:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Productos con rotación", rotacion["producto_id"].nunique())
    with col2:
        st.metric("Índice rotación (media)", f"{rotacion['indice_rotacion'].mean():.2f}" if "indice_rotacion" in rotacion.columns else "—")
    with col3:
        st.metric("Alertas stock crítico", len(alertas) if not alertas.empty else 0)
else:
    st.caption("Conecta NEON_DATABASE_URL para ver KPIs desde Gold.")

# --- C3: Comparativa — gráficos ---
st.header("Comparativa")
if USE_DB and not rotacion.empty:
    fig = px.bar(
        rotacion.head(20),
        x="producto_id",
        y="indice_rotacion",
        color="tienda_id",
        title="Índice de rotación por producto/tienda (top 20)",
        labels={"indice_rotacion": "Rotación", "producto_id": "Producto"},
    )
    st.plotly_chart(fig, use_container_width=True)
if USE_DB and not alertas.empty:
    st.subheader("Stock crítico (detalle)")
    st.dataframe(alertas, use_container_width=True, hide_index=True)
else:
    st.caption("Sin datos de comparativa hasta conectar BD.")

# --- C4: Detalle — tablas filtrables ---
st.header("Detalle")
if USE_DB:
    tab_rot, tab_alert, tab_opp = st.tabs(["Rotación", "Alertas stock", "Oportunidad venta"])
    with tab_rot:
        df_rot = read_gold("v_rotacion_inventario")
        if not df_rot.empty:
            st.dataframe(df_rot, use_container_width=True, hide_index=True)
    with tab_alert:
        df_alert = read_gold("v_alertas_stock")
        if not df_alert.empty:
            st.dataframe(df_alert, use_container_width=True, hide_index=True)
    with tab_opp:
        try:
            df_opp = read_gold("v_oportunidad_venta")
            if not df_opp.empty:
                st.dataframe(df_opp, use_container_width=True, hide_index=True)
            else:
                st.caption("Sin datos de oportunidad de venta.")
        except Exception:
            st.caption("Vista v_oportunidad_venta no disponible o sin datos.")
else:
    st.caption("Conecta la BD para ver tablas Gold.")

# --- C5: Reporte ejecutivo ---
st.header("Reporte ejecutivo")
if USE_DB and (not rotacion.empty or not alertas.empty):
    st.markdown("""
    - **Objetivo SIMIR:** Reducir 12% stock inmovilizado y aumentar 8% ventas mediante alertas.
    - **KPIs:** Rotación (Ventas/Stock prom), Stock crítico (<7 días venta prevista), Oportunidad (precio vs tendencia).
    - **Trazabilidad:** Todas las métricas provienen de vistas Gold (retail_gold).
    """)
else:
    st.caption("Resumen ejecutivo disponible con datos Gold cargados.")
