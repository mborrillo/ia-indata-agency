"""
Dashboard Streamlit base.
Conecta a Neon y visualiza las vistas Gold.
"""
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# ── Config de página ──────────────────────────────────────────
st.set_page_config(
    page_title="[NOMBRE PROYECTO]",
    page_icon="📊",
    layout="wide"
)

# ── Conexión BD ───────────────────────────────────────────────
@st.cache_resource
def get_conn():
    return psycopg2.connect(os.getenv("NEON_DATABASE_URL"))

@st.cache_data(ttl=3600)
def query(sql: str) -> pd.DataFrame:
    return pd.read_sql(sql, get_conn())

# ── Layout ────────────────────────────────────────────────────
st.title("📊 [NOMBRE PROYECTO]")
st.caption("Datos actualizados diariamente · Fuente: [fuente]")

# Fila KPIs
kpi = query("SELECT * FROM v_resumen_kpi LIMIT 1")
if not kpi.empty:
    col1, col2, col3 = st.columns(3)
    col1.metric("Promedio", f"{kpi['promedio'].iloc[0]:.2f}")
    col2.metric("Máximo",   f"{kpi['maximo'].iloc[0]:.2f}")
    col3.metric("Mínimo",   f"{kpi['minimo'].iloc[0]:.2f}")

st.divider()

# Gráfico serie temporal
serie = query("SELECT * FROM v_serie_temporal ORDER BY fecha DESC LIMIT 365")
if not serie.empty:
    fig = px.line(
        serie, x="fecha", y="valor",
        color="categoria",
        title="Evolución temporal",
        template="plotly_white"
    )
    st.plotly_chart(fig, use_container_width=True)

# Tabla detalle
with st.expander("Ver datos completos"):
    st.dataframe(serie, use_container_width=True)
```

**`_template/requirements.txt`:**
```
streamlit>=1.32.0
plotly>=5.20.0
pandas>=2.2.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
requests>=2.31.0
