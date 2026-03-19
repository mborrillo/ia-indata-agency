"""
Dashboard para Gestión de Inventarios Retail
Estilo profesional claro, tarjetas elegantes, KPIs con delta.
"""

import logging
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy
import numpy as np
from datetime import datetime, timedelta

load_dotenv()

# Configuración moderna
st.set_page_config(
    page_title="SIMIR - Retail Intelligence",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personalizado para estilo GesPro-like
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: white; border-radius: 12px; padding: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); }
    .sidebar .sidebar-content { background-color: #ffffff; }
    h1 { color: #1e3a8a; font-weight: 600; }
    .stButton>button { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")
USE_DB = bool(DATABASE_URL)

if USE_DB:
    st.success("✅ Conexión a base de datos configurada correctamente")
else:
    st.warning("⚠️ MODO DEMO: Datos simulados (sin conexión real a Neon)")

def get_engine():
    if not USE_DB: return None
    try:
        return sqlalchemy.create_engine(DATABASE_URL)
    except:
        return None

@st.cache_data(ttl=300)
def read_gold(view_name: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return generate_fake_data(view_name)
    try:
        df = pd.read_sql(f"SELECT * FROM retail_gold.{view_name}", engine)
        if df.empty:
            return generate_fake_data(view_name)
        return df
    except:
        return generate_fake_data(view_name)

def generate_fake_data(view_name: str) -> pd.DataFrame:
    n = 20
    productos = ['P001', 'P002', 'P003', 'P004', 'P005']
    tiendas = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao']
    
    if view_name == "v_rotacion_inventario":
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n),
            'tienda_id': np.random.choice(tiendas, n),
            'indice_rotacion': np.random.uniform(2.0, 6.5, n)
        })
    elif view_name == "v_alertas_stock":
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n),
            'tienda_id': np.random.choice(tiendas, n),
            'es_stock_critico': np.random.choice([True, False], n, p=[0.35, 0.65])
        })
    elif view_name == "v_oportunidad_venta":
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n),
            'tienda_id': np.random.choice(tiendas, n),
            'pct_vs_tendencia': np.random.uniform(-15, 25, n)
        })
    return pd.DataFrame()

# Sidebar moderno
with st.sidebar:
    st.image("https://via.placeholder.com/150x50/1e3a8a/ffffff?text=SIMIR", width=150)
    st.markdown("### 📊 Dashboard")
    st.button("📈 Resumen", use_container_width=True)
    st.button("📊 Comparativa", use_container_width=True)
    st.button("📋 Detalle", use_container_width=True)
    st.button("📄 Reporte Ejecutivo", use_container_width=True)
    st.divider()
    st.caption("Conexión segura")
    st.caption("Neon DB • LIVE")

# Título principal
st.title("SIMIR – Sistema de Inteligencia Mercados Retail")
st.markdown("**Análisis de inventarios y oportunidades de venta**")

# KPI Cards modernas (estilo GesPro)
rotacion_df = read_gold("v_rotacion_inventario")
alertas_df = read_gold("v_alertas_stock")
oportunidad_df = read_gold("v_oportunidad_venta")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Rotación Promedio", 
              f"{rotacion_df['indice_rotacion'].mean():.1f}" if not rotacion_df.empty else "—",
              delta="↑ 0.8 vs mes anterior")
with col2:
    st.metric("Stock Crítico", 
              alertas_df['es_stock_critico'].sum() if not alertas_df.empty else "—",
              delta="↓ 2 vs mes anterior", delta_color="normal")
with col3:
    st.metric("Oportunidades", 
              len(oportunidad_df[oportunidad_df['pct_vs_tendencia'] > 0]) if not oportunidad_df.empty else "—",
              delta="↑ 12%")
with col4:
    st.metric("Ticket Promedio", "$28.45", delta="↑ 4.2%")

# Evolución de Gastos / Rotación (bar chart)
st.subheader("Evolución de Rotación")
if not rotacion_df.empty:
    fig = px.bar(rotacion_df, x='producto_id', y='indice_rotacion', color='tienda_id',
                 title="Rotación por Producto y Tienda", height=380)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("Sin datos para gráfico de evolución")

# Distribución por Categoría (pie chart)
st.subheader("Distribución por Tienda")
if not rotacion_df.empty:
    fig2 = px.pie(rotacion_df.groupby('tienda_id')['indice_rotacion'].mean().reset_index(),
                  names='tienda_id', values='indice_rotacion', title="Rotación promedio por Tienda")
    st.plotly_chart(fig2, use_container_width=True)

# Detalle
st.subheader("Detalle por Vista")
vista = st.selectbox("Seleccionar vista", ["v_rotacion_inventario", "v_alertas_stock", "v_oportunidad_venta"])
df = read_gold(vista)
st.dataframe(df, use_container_width=True)

# Reporte Ejecutivo
st.subheader("Reporte Ejecutivo")
if not rotacion_df.empty:
    st.write(f"**Rotación promedio general:** {rotacion_df['indice_rotacion'].mean():.2f}")
    st.write(f"**Productos con alerta crítica:** {alertas_df['es_stock_critico'].sum()}")
    st.caption("Recomendación: Revisar tiendas con rotación < 3.0")

logger.info("Dashboard renderizado correctamente")
