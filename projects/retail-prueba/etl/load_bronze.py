"""
Carga datos crudos desde CSVs a capa Bronze.
Versión con logging máximo para ver cada paso.
"""

import logging
import pandas as pd
import os
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def load_bronze(engine):
    logger.info("=== INICIO CARGA BRONZE ===")
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    data_dir = os.path.join(project_root, 'data')
    
    logger.info(f"Ruta calculada para carpeta data: {data_dir}")
    
    if not os.path.exists(data_dir):
        logger.error(f"Directorio data/ NO encontrado en {data_dir}")
        return
    
    logger.info(f"Archivos encontrados en data/: {os.listdir(data_dir)}")
    
    csv_mapping = {
        'ventas': 'ventas.csv',
        'stock': 'stock.csv',
        'precios': 'precios.csv'
    }
    
    for table, filename in csv_mapping.items():
        full_path = os.path.join(data_dir, filename)
        logger.info(f"--- Procesando {filename} (ruta completa: {full_path}) ---")
        
        if not os.path.isfile(full_path):
            logger.warning(f"Archivo {filename} NO existe")
            continue
        
        try:
            logger.info(f"Leyendo archivo CSV: {full_path}")
            df = pd.read_csv(full_path)
            row_count = len(df)
            logger.info(f"CSV leído correctamente: {row_count} filas | Columnas: {list(df.columns)}")
            
            if row_count == 0:
                logger.warning(f"CSV {filename} está vacío (0 filas)")
                continue
            
            logger.info(f"Insertando {row_count} filas en la tabla retail_bronze.{table}")
            df.to_sql(table, engine, schema='retail_bronze', if_exists='replace', index=False)
            logger.info(f"ÉXITO TOTAL: {row_count} filas insertadas en retail_bronze.{table}")
        except pd.errors.EmptyDataError:
            logger.warning(f"CSV {filename} vacío o formato inválido")
        except Exception as e:
            logger.error(f"ERROR CRÍTICO al procesar {filename}: {str(e)}", exc_info=True)
    
    logger.info("=== CARGA BRONZE FINALIZADA ===")
