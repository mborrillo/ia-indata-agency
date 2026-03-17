"""
SIMIR – App Streamlit para el gerente de tienda.
Resumen (KPI cards) → Comparativa (gráficos) → Detalle (tablas) → Reporte ejecutivo.
Solo lectura desde vistas Gold. Usa NEON_DATABASE_URL desde secrets o .env.
"""

import logging
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy
from datetime import datetime

# Cargar variables de entorno (para local)
load_dotenv()

# Configuración de logging (visible en consola y Cloud)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.info("Aplicación Streamlit SIMIR iniciada")

# Conexión a la base de datos
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("No se encontró NEON_DATABASE_URL ni DATABASE_URL")
    st.warning("No se encontró conexión a la base de datos. Modo demo sin datos.")
    USE_DB = False
else:
    logger.info("Conexión a Neon configurada")
    st.success("Conexión a base de datos configurada correctamente.")
    USE_DB = True

def get_engine():
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        logger.info("Engine creado correctamente")
        return engine
    except Exception as e:
        logger.error(f"Error creando engine: {str(e)}", exc_info=True)
        st.error(f"Error de conexión: {str(e)}")
        return None

@st.cache_data(ttl=300)  # Cache 5 minutos
def read_gold(view_name: str) -> pd.DataFrame:
    if not USE_DB:
        logger.info(f"Modo sin DB: vacío para {view_name}")
        return pd.DataFrame()
    
    engine = get_engine()
    if engine is None:
        return pd.DataFrame()
    
    try:
        query = f"SELECT * FROM retail_gold.{view_name}"
        df = pd.read_sql(query, engine)
        logger.info(f"{len(df)} filas cargadas de {view_name}")
        if df.empty:
            st.info(f"Vista {view_name} existe pero está vacía.")
        return df
    except Exception as e:
        logger.error(f"Error leyendo {view_name}: {str(e)}", exc_info=True)
        st.error(f"Error al leer {view_name}: {str(e)}")
        return pd.DataFrame()

# Configuración de página
st.set_page_config(page_title="SIMIR - Gestión Inventarios Retail", layout="wide")
st.title("SIMIR – Sistema de Inteligencia Mercados Retail")

# Cargar datos
rotacion_df = read_gold("v_rotacion_inventario")
alertas_df = read_gold("v_alertas_stock")
oportunidad_df = read_gold("v_oportunidad_venta")

# Pestañas
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Comparativa", "Detalle", "Reporte Ejecutivo"])

with tab1:
    st.subheader("Resumen KPIs")
    col1, col2, col3 = st.columns(3)
    
    # Rotación Promedio - columna real: indice_rotacion
    if not rotacion_df.empty and 'indice_rotacion' in rotacion_df.columns:
        col1.metric("Rotación Promedio", f"{rotacion_df['indice_rotacion'].mean():.2f}")
    else:
        col1.metric("Rotación Promedio", "Sin datos")
    
    # Stock Crítico - columna real: es_stock_critico (contar True)
    if not alertas_df.empty and 'es_stock_critico' in alertas_df.columns:
        criticos = alertas_df['es_stock_critico'].sum()
        col2.metric("Stock Crítico", criticos)
    else:
        col2.metric("Stock Crítico", "Sin datos")
    
    # Oportunidades Detectadas - columna real: pct_vs_tendencia (ej. contar >0)
    if not oportunidad_df.empty and 'pct_vs_tendencia' in oportunidad_df.columns:
        oportunidades = len(oportunidad_df[oportunidad_df['pct_vs_tendencia'] > 0])
        col3.metric("Oportunidades Detectadas", oportunidades)
    else:
        col3.metric("Oportunidades Detectadas", "Sin datos")

with tab2:
    st.subheader("Comparativa Gráfica")
    if not rotacion_df.empty:
        # Usamos columnas reales: fecha no existe, usamos producto_id y tienda_id como color
        if 'indice_rotacion' in rotacion_df.columns:
            fig = px.bar(rotacion_df, 
                         x='producto_id', 
                         y='indice_rotacion', 
                         color='tienda_id', 
                         title="Índice de Rotación por Producto y Tienda")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay columna 'indice_rotacion' para gráfico.")
    else:
        st.info("Sin datos para comparativa.")

with tab3:
    st.subheader("Detalle por Vista")
    vista = st.selectbox("Seleccionar vista Gold", 
                         ["v_rotacion_inventario", "v_alertas_stock", "v_oportunidad_venta"])
    df = read_gold(vista)
    if not df.empty:
        st.dataframe(df)
    else:
        st.info(f"No hay filas en {vista}.")

with tab4:
    st.subheader("Reporte Ejecutivo")
    if not rotacion_df.empty and 'indice_rotacion' in rotacion_df.columns:
        st.write("**Resumen Ejecutivo**")
        st.write(f"- Rotación promedio general: **{rotacion_df['indice_rotacion'].mean():.2f}**")
        st.write(f"- Total productos analizados: **{len(rotacion_df['producto_id'].unique())}**")
        st.write("- Recomendación: revisar productos con índice bajo para optimizar stock.")
    else:
        st.info("Reporte no disponible sin datos en v_rotacion_inventario.")

logger.info("App renderizada correctamente")
