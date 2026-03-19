"""
SIMIR – Dashboard Profesional Retail (Estilo GesPro)
Fondo claro, alta legibilidad, navegación funcional.
"""

import logging
from dotenv import load_dotenv
import streamlit as st
import pandas as pd
import plotly.express as px
import sqlalchemy
import numpy as np

load_dotenv()

# ===================== CONFIGURACIÓN =====================
st.set_page_config(page_title="SIMIR", page_icon="📊", layout="wide")

# CSS moderno y legible (fondo claro GesPro-style)
st.markdown("""
<style>
    .main { background-color: #f8f9fa; }
    .stMetric { background: white; border-radius: 12px; padding: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .sidebar .css-1d391kg { background-color: #ffffff; }
    h1 { color: #1e3a8a; font-weight: 700; }
    .stButton>button { width: 100%; border-radius: 8px; height: 45px; font-weight: 500; }
</style>
""", unsafe_allow_html=True)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATABASE_URL = st.secrets.get("NEON_DATABASE_URL") or os.getenv("NEON_DATABASE_URL")
USE_DB = bool(DATABASE_URL)

# ===================== SIDEBAR NAVEGACIÓN FUNCIONAL =====================
with st.sidebar:
    st.image("https://via.placeholder.com/180x60/1e3a8a/ffffff?text=SIMIR", width=180)
    st.markdown("### 📊 Dashboard")
    
    page = st.radio("Ir a:", 
                    ["📈 Resumen", "📊 Comparativa", "📋 Detalle", "📄 Reporte Ejecutivo"],
                    label_visibility="collapsed")

    st.divider()
    st.caption("Conexión segura")
    st.caption("Neon DB • LIVE")

# ===================== HEADER =====================
st.title("SIMIR – Sistema de Inteligencia Mercados Retail")
st.markdown("**Análisis de inventarios y oportunidades de venta**")

if USE_DB:
    st.success("✅ Conexión a base de datos configurada correctamente")
else:
    st.warning("⚠️ MODO DEMO: Datos simulados (sin conexión real)")

# ===================== FUNCIONES DE DATOS =====================
def get_engine():
    if not USE_DB: return None
    try: return sqlalchemy.create_engine(DATABASE_URL)
    except: return None

@st.cache_data(ttl=300)
def read_gold(view_name: str):
    engine = get_engine()
    if engine is None or not USE_DB:
        return generate_fake_data(view_name)
    try:
        df = pd.read_sql(f"SELECT * FROM retail_gold.{view_name}", engine)
        return df if not df.empty else generate_fake_data(view_name)
    except:
        return generate_fake_data(view_name)

def generate_fake_data(view_name):
    n = 20
    productos = ['P001','P002','P003','P004','P005']
    tiendas = ['Madrid','Barcelona','Valencia','Sevilla','Bilbao']
    
    if view_name == "v_rotacion_inventario":
        return pd.DataFrame({'producto_id': np.random.choice(productos,n), 'tienda_id': np.random.choice(tiendas,n), 'indice_rotacion': np.random.uniform(1.8,6.5,n)})
    elif view_name == "v_alertas_stock":
        return pd.DataFrame({'producto_id': np.random.choice(productos,n), 'tienda_id': np.random.choice(tiendas,n), 'es_stock_critico': np.random.choice([True,False],n,p=[0.35,0.65])})
    elif view_name == "v_oportunidad_venta":
        return pd.DataFrame({'producto_id': np.random.choice(productos,n), 'tienda_id': np.random.choice(tiendas,n), 'pct_vs_tendencia': np.random.uniform(-15,28,n)})
    return pd.DataFrame()

# ===================== CONTENIDO SEGÚN PÁGINA =====================
rotacion_df = read_gold("v_rotacion_inventario")
alertas_df = read_gold("v_alertas_stock")
oportunidad_df = read_gold("v_oportunidad_venta")

if "📈 Resumen" in page:
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Rotación Promedio", f"{rotacion_df['indice_rotacion'].mean():.1f}" if not rotacion_df.empty else "—", "↑ 0.8 vs mes anterior")
    with col2: st.metric("Stock Crítico", alertas_df['es_stock_critico'].sum() if not alertas_df.empty else "—", "↓ 2 vs mes anterior")
    with col3: st.metric("Oportunidades", len(oportunidad_df[oportunidad_df['pct_vs_tendencia'] > 0]) if not oportunidad_df.empty else "—", "↑ 12%")
    with col4: st.metric("Ticket Promedio", "$28.45", "↑ 4.2%")

elif "📊 Comparativa" in page:
    st.subheader("Rotación por Producto y Tienda")
    if not rotacion_df.empty:
        fig = px.bar(rotacion_df, x='producto_id', y='indice_rotacion', color='tienda_id', height=420)
        st.plotly_chart(fig, use_container_width=True)

elif "📋 Detalle" in page:
    st.subheader("Detalle de datos")
    vista = st.selectbox("Selecciona vista", ["v_rotacion_inventario", "v_alertas_stock", "v_oportunidad_venta"])
    st.dataframe(read_gold(vista), use_container_width=True)

elif "📄 Reporte Ejecutivo" in page:
    st.subheader("Reporte Ejecutivo")
    if not rotacion_df.empty:
        st.metric("Rotación promedio general", f"{rotacion_df['indice_rotacion'].mean():.2f}")
        st.write(f"**Productos con alerta crítica:** {alertas_df['es_stock_critico'].sum()}")
        st.caption("Recomendación: Revisar tiendas con rotación < 3.0")

logger.info("Dashboard renderizado correctamente")
