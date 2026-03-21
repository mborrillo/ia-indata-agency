"""
ETL diario SIMIR: DDL → Bronze → Silver
Ejecutar diariamente (cron, GitHub Actions, etc.)
"""

import logging
from dotenv import load_dotenv
import os
import sys
import pandas as pd
from sqlalchemy import create_engine

# Cargar .env
load_dotenv()

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(),
        # logging.FileHandler("etl.log", mode='a')
    ]
)
logger = logging.getLogger(__name__)

logger.info("=== INICIO ETL DIARIO SIMIR ===")

DATABASE_URL = os.getenv("NEON_RETAIL_PRUEBA") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("No se encontró NEON_DATABASE_URL ni DATABASE_URL. Abortando ETL.")
    sys.exit(1)

def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Engine de conexión creado correctamente")
        return engine
    except Exception as e:
        logger.error(f"Error al crear engine: {str(e)}", exc_info=True)
        raise

def run_ddl():
    logger.info("Aplicando DDL (esquemas y tablas)...")
    # Aquí ejecutarías los archivos sql/01_schemas.sql, 02_bronze_tables.sql, etc.
    # Ejemplo simplificado:
    engine = get_engine()
    with engine.connect() as conn:
        # conn.execute("CREATE SCHEMA IF NOT EXISTS retail_bronze;")
        pass  # reemplaza con tu lógica real de ejecución de SQL
    logger.info("DDL aplicado correctamente")

def load_bronze():
    logger.info("Iniciando carga Bronze desde CSVs...")
    # Tu lógica actual de load_bronze.py
    logger.info("Carga Bronze completada")

def transform_silver():
    logger.info("Transformando datos a Silver...")
    # Tu lógica actual de silver.py
    logger.info("Transformación Silver finalizada")

def main():
    try:
        run_ddl()
        load_bronze()
        transform_silver()
        logger.info("=== ETL DIARIO FINALIZADO CON ÉXITO ===")
    except Exception as e:
        logger.error(f"Error crítico durante ETL diario: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
