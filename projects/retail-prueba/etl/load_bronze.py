"""
Carga datos crudos desde CSVs a capa Bronze.
Lee archivos desde la carpeta data/ relativa al script.
"""

import logging
import pandas as pd
import os
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def load_bronze(engine):
    logger.info("Iniciando carga Bronze desde CSVs...")
    
    # Ruta relativa desde el directorio del script
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, '..', '..', 'data')
    
    logger.info(f"Buscando CSVs en: {data_dir}")
    
    files = {
        'ventas': 'ventas.csv',
        'stock': 'stock.csv',
        'precios': 'precios.csv'
    }
    
    for table, filename in files.items():
        csv_path = os.path.join(data_dir, filename)
        if not os.path.exists(csv_path):
            logger.warning(f"Archivo no encontrado: {csv_path}")
            continue
        
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                logger.warning(f"CSV vacío: {filename}")
                continue
                
            df.to_sql(table, engine, schema='retail_bronze', if_exists='replace', index=False)
            logger.info(f"Cargadas {len(df)} filas en retail_bronze.{table} desde {filename}")
        except Exception as e:
            logger.error(f"Error cargando {filename}: {str(e)}")
            continue
    
    logger.info("Carga Bronze finalizada")
