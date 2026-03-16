"""
Carga datos crudos a capa Bronze
"""

import logging
import pandas as pd
from sqlalchemy import text

logger = logging.getLogger(__name__)

def load_bronze(engine):
    logger.info("Iniciando carga de archivos CSV a Bronze...")
    try:
        # Ejemplo: cargar ventas.csv
        df = pd.read_csv("../data/ventas.csv")
        df.to_sql("ventas", engine, schema="retail_bronze", if_exists="replace", index=False)
        logger.info(f"Cargadas {len(df)} filas en retail_bronze.ventas")
        
        # Repetir para stock.csv, precios.csv...
        
    except Exception as e:
        logger.error(f"Error durante carga Bronze: {str(e)}", exc_info=True)
        raise
