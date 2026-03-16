"""
SIMIR – App Streamlit para el gerente de tienda.
Resumen (KPI cards) → Comparativa (gráficos) → Detalle (tablas) → Reporte ejecutivo.
Solo lectura desde vistas Gold. DATABASE_URL o NEON_DATABASE_URL en entorno.
"""

import logging
from dotenv import load_dotenv
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy

# Cargar variables de entorno
load_dotenv()

# Configuración global de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("app.log", mode='a')  # descomenta si quieres archivo
    ]
)
logger = logging.getLogger(__name__)

logger.info("Aplicación Streamlit SIMIR iniciada")

# Variables de entorno para la conexión a la base de datos
DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.warning("No se encontró NEON_DATABASE_URL ni DATABASE_URL en .env ni variables de entorno")
    st.warning("No se encontró conexión a la base de datos. Usando datos estáticos de ejemplo.")
    USE_DB = False
else:
    logger.info(f"Conexión configurada → NEON_DATABASE_URL detectada (longitud: {len(DATABASE_URL)})")
    st.success("Conexión a base de datos configurada correctamente.")
    USE_DB = True

# Función para obtener el engine (con logging)
def get_engine():
    try:
        engine = sqlalchemy.create_engine(DATABASE_URL)
        logger.info("Engine de SQLAlchemy creado correctamente")
        return engine
    except Exception as e:
        logger.error(f"Error al crear engine de conexión: {str(e)}", exc_info=True)
        raise

# Función para leer vistas Gold (con cache y logging)
@st.cache_data(ttl=3600)  # 1 hora de cache
def read_gold(view: str) -> pd.DataFrame:
    if not USE_DB:
        logger.info(f"Modo demo: devolviendo DataFrame vacío para vista {view}")
        return pd.DataFrame()
    
    try:
        engine = get_engine()
        query = f'SELECT * FROM retail_gold.{view}'
        df = pd.read_sql(query, engine)
        logger.info(f"Consulta exitosa → {len(df)} filas cargadas desde {view}")
        return df
    except Exception as e:
        logger.error(f"Error al leer vista {view}: {str(e)}", exc_info=True)
        st.error(f"Error al conectar/leer la base de datos: {str(e)}")
        return pd.DataFrame()

# Título y configuración de página
st.set_page_config(page_title="SIMIR - Sistema de Inteligencia Mercados Retail", layout="wide")
st.title("SIMIR – Sistema de Inteligencia Mercados Retail")

# Cargar datos
rotacion_df = read_gold("v_rotacion_inventario")
alertas_df = read_gold("v_alertas_stock")
oportunidad_df = read_gold("v_oportunidad_venta")

# Pestañas
tab1, tab2, tab3, tab4 = st.tabs(["Resumen", "Comparativa", "Detalle", "Reporte Ejecutivo"])

with tab1:
    st.subheader("Resumen KPIs")
    if USE_DB and not rotacion_df.empty:
        col1, col2, col3 = st.columns(3)
        col1.metric("Rotación Promedio", f"{rotacion_df['rotacion'].mean():.2f}")
        col2.metric("Stock Crítico", len(alertas_df))
        col3.metric("Oportunidades Detectadas", len(oportunidad_df))
    else:
        st.info("Datos de ejemplo no disponibles en modo demo.")

with tab2:
    st.subheader("Comparativa Gráfica")
    if not rotacion_df.empty:
        fig = px.line(rotacion_df, x='fecha', y='rotacion', color='producto', title="Rotación por Producto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos para mostrar en modo demo.")

with tab3:
    st.subheader("Detalle por Vista")
    vista = st.selectbox("Seleccionar vista Gold", ["v_rotacion_inventario", "v_alertas_stock", "v_oportunidad_venta"])
    df = read_gold(vista)
    st.dataframe(df)

with tab4:
    st.subheader("Reporte Ejecutivo")
    st.write("Aquí iría el resumen narrativo o PDF generado...")
    # Puedes agregar generación de PDF o markdown aquí más adelante

logger.info("App Streamlit renderizada correctamente")
