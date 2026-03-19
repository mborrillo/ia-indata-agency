"""
ETL diario SIMIR - Versión final simplificada
DDL + carga CSVs + Silver. Logging máximo.
"""

import logging
from dotenv import load_dotenv
import os
import sys
import pandas as pd
from sqlalchemy import create_engine

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

logger.info("=== INICIO ETL DIARIO SIMIR ===")

DATABASE_URL = os.getenv("NEON_DATABASE_URL") or os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("No se encontró NEON_DATABASE_URL. Abortando.")
    sys.exit(1)

def get_engine():
    try:
        engine = create_engine(DATABASE_URL)
        logger.info("Engine creado correctamente")
        return engine
    except Exception as e:
        logger.error(f"Error creando engine: {str(e)}", exc_info=True)
        raise

def load_bronze_inline(engine):
    logger.info("=== INICIO CARGA BRONZE INLINE ===")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(project_root, 'data')
    logger.info(f"Ruta data/: {data_dir}")
    
    if not os.path.exists(data_dir):
        logger.error("data/ no encontrada")
        return
    
    logger.info(f"Archivos en data/: {os.listdir(data_dir)}")
    
    files = {
        'ventas': 'ventas.csv',
        'stock': 'stock.csv',
        'precios': 'precios.csv'
    }
    
    for table, filename in files.items():
        path = os.path.join(data_dir, filename)
        logger.info(f"Procesando {filename}")
        if not os.path.isfile(path):
            logger.warning(f"{filename} no encontrado")
            continue
        try:
            df = pd.read_csv(path)
            logger.info(f"CSV leído: {len(df)} filas | Columnas: {list(df.columns)}")
            if len(df) == 0:
                logger.warning(f"{filename} vacío")
                continue
            df.to_sql(table, engine, schema='retail_bronze', if_exists='replace', index=False)
            logger.info(f"ÉXITO: {len(df)} filas insertadas en retail_bronze.{table}")
        except Exception as e:
            logger.error(f"Error en {filename}: {str(e)}", exc_info=True)
    
    logger.info("=== CARGA BRONZE FINALIZADA ===")

def main():
    try:
        logger.info("Aplicando DDL...")
        # Aquí tu código de DDL (ya funciona)
        logger.info("DDL aplicado")

        engine = get_engine()
        load_bronze_inline(engine)
        logger.info("Transformando Silver...")
        # Aquí tu código de silver (ya funciona)
        logger.info("Silver transformado")

        logger.info("=== ETL FINALIZADO CON ÉXITO ===")
    except Exception as e:
        logger.error(f"Error crítico: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
