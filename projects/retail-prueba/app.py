"""
SIMIR – App Streamlit para el gerente de tienda.
Lee vistas Gold. Fallback a datos fake si no hay conexión o datos reales.
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

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.info("Aplicación SIMIR iniciada")

DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")

USE_DB = bool(DATABASE_URL)
if USE_DB:
    logger.info("Conexión Neon detectada")
    st.success("Conexión a base de datos configurada.")
else:
    logger.warning("Sin NEON_DATABASE_URL → usando datos fake")
    st.warning("Modo demo: datos simulados (sin conexión real).")

def get_engine():
    if not USE_DB:
        return None
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        logger.info("Engine creado OK")
        return engine
    except Exception as e:
        logger.error(f"Error engine: {str(e)}")
        st.error("Error de conexión a DB.")
        return None

@st.cache_data(ttl=300)
def read_gold(view_name: str) -> pd.DataFrame:
    engine = get_engine()
    if engine is None:
        return generate_fake_data(view_name)
    
    try:
        df = pd.read_sql(f"SELECT * FROM retail_gold.{view_name}", engine)
        logger.info(f"{len(df)} filas reales de {view_name}")
        if df.empty:
            logger.info(f"Vista {view_name} vacía → fallback a fake")
            return generate_fake_data(view_name)
        return df
    except Exception as e:
        logger.error(f"Error lectura {view_name}: {str(e)}")
        st.error(f"Error leyendo {view_name}.")
        return generate_fake_data(view_name)

def generate_fake_data(view_name: str) -> pd.DataFrame:
    """Datos simulados si DB vacía o sin conexión"""
    logger.info(f"Generando datos fake para {view_name}")
    n_rows = 20
    productos = ['P001', 'P002', 'P003', 'P004', 'P005']
    tiendas = ['Madrid', 'Barcelona', 'Valencia', 'Sevilla', 'Bilbao']
    
    if view_name == "v_rotacion_inventario":
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n_rows),
            'tienda_id': np.random.choice(tiendas, n_rows),
            'total_unidades_vendidas': np.random.randint(20, 150, n_rows),
            'stock_promedio': np.random.randint(50, 300, n_rows),
            'indice_rotacion': np.random.uniform(1.5, 7.0, n_rows)
        })
    
    elif view_name == "v_alertas_stock":
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n_rows),
            'tienda_id': np.random.choice(tiendas, n_rows),
            'stock_actual': np.random.randint(10, 200, n_rows),
            'venta_media_7d': np.random.uniform(5, 50, n_rows),
            'dias_de_stock': np.random.uniform(1, 30, n_rows),
            'es_stock_critico': np.random.choice([True, False], n_rows, p=[0.3, 0.7])
        })
    
    elif view_name == "v_oportunidad_venta":
        fechas = [datetime.now().date() - timedelta(days=i) for i in range(n_rows)]
        return pd.DataFrame({
            'producto_id': np.random.choice(productos, n_rows),
            'tienda_id': np.random.choice(tiendas, n_rows),
            'fecha': fechas,
            'precio_local': np.random.uniform(20, 80, n_rows),
            'tendencia_local_7d': np.random.uniform(18, 85, n_rows),
            'diff_vs_tendencia': np.random.uniform(-10, 15, n_rows),
            'pct_vs_tendencia': np.random.uniform(-20, 30, n_rows)
        })
    
    return pd.DataFrame()

# Página
st.set_page_config(page_title="SIMIR - Retail Intelligence", layout="wide")
st.title("SIMIR – Inteligencia Mercados Retail")

rotacion_df = read_gold("v_rotacion_inventario")
alertas_df = read_gold("v_alertas_stock")
oportunidad_df = read_gold("v_oportunidad_venta")

tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Comparativa", "Detalle", "Reporte Ejecutivo"])

with tab1:
    st.subheader("Resumen KPIs")
    col1, col2, col3 = st.columns(3)
    
    col1.metric("Rotación Promedio", f"{rotacion_df['indice_rotacion'].mean():.2f}" if not rotacion_df.empty else "—")
    col2.metric("Stock Crítico", alertas_df['es_stock_critico'].sum() if not alertas_df.empty else "—")
    col3.metric("Oportunidades", len(oportunidad_df[oportunidad_df['pct_vs_tendencia'] > 0]) if not oportunidad_df.empty else "—")

with tab2:
    st.subheader("Comparativa")
    if not rotacion_df.empty:
        fig = px.bar(rotacion_df, x='producto_id', y='indice_rotacion', color='tienda_id',
                     title="Rotación por Producto y Tienda")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Sin datos para gráfico.")

with tab3:
    st.subheader("Detalle")
    vista = st.selectbox("Vista", ["v_rotacion_inventario", "v_alertas_stock", "v_oportunidad_venta"])
    df = read_gold(vista)
    st.dataframe(df)

with tab4:
    st.subheader("Reporte Ejecutivo")
    if not rotacion_df.empty:
        st.write(f"Rotación promedio: **{rotacion_df['indice_rotacion'].mean():.2f}**")
        st.write(f"Productos con alerta crítica: **{alertas_df['es_stock_critico'].sum()}**")
    else:
        st.info("Reporte no disponible sin datos.")

logger.info("App finalizada")
