"""
Módulo de conexión a la base de datos con logging
"""

import logging
from dotenv import load_dotenv
import os
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("NEON_RETAIL_PRUEBA") or os.getenv("DATABASE_URL")

def get_engine():
    if not DATABASE_URL:
        logger.error("No se encontró cadena de conexión a la base de datos")
        raise ValueError("DATABASE_URL no configurada")
    
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Conexión a base de datos establecida")
        return engine
    except Exception as e:
        logger.error(f"Fallo al conectar a la base de datos: {str(e)}", exc_info=True)
        raise
