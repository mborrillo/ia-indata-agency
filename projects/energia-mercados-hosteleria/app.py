"""
MEMO Hostelería — Monitor de Costes para Restauración
ia-indata Agency · Badajoz, Extremadura
"""
import io, os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Monitor de Costes · Hostelería",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

:root {
    --bg:     #080a0f;
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
    --dim:    #94a3b8;
    --muted:  #94a3b8;
}
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--bg) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text) !important;
}
#MainMenu, footer, header,
[data-testid="stToolbar"], [data-testid="stDecoration"],
[data-testid="stStatusWidget"], [data-testid="stSidebar"] { display: none !important; }
.block-container { padding: 2.5rem 3rem 5rem !important; max-width: 1300px !important; }

/* Estilos de componentes omitidos para brevedad, se mantienen igual al original */
</style>
""", unsafe_allow_html=True)

# ── Conexión (CORREGIDA según CONTEXT.md) ──────────────────────────────────────
# Se usa HOSTELERIA_NEON_URL en lugar de NEON_DATABASE_URL
DB_URL = os.getenv("HOSTELERIA_NEON_URL") 

@st.cache_resource
def get_engine():
    if not DB_URL:
        st.error("Error: No se encuentra la variable de entorno HOSTELERIA_NEON_URL")
        st.stop()
    return create_engine(
        DB_URL, 
        pool_pre_ping=True,  # Verifica la conexión antes de usarla
        pool_recycle=300,    # Recicla conexiones cada 5 min (límite de Neon)
        connect_args={"connect_timeout": 10}
    )

def q(sql: str) -> pd.DataFrame:
    """Ejecuta consultas SQL usando el engine de SQLAlchemy"""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            return pd.read_sql(text(sql), conn)
    except Exception as e:
        st.error(f"Error de base de datos: {e}")
        return pd.DataFrame()

# El resto del código de la lógica de negocio y visualización se mantiene igual...
# (Se asume que el usuario tiene el resto del archivo para el renderizado)
