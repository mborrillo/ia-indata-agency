"""
Carga datos crudos desde CSVs a capa Bronze.
Lee archivos desde la carpeta data/ relativa al proyecto.
Usa logging y manejo de errores para ver exactamente qué pasa.
"""

import logging
import pandas as pd
import os
from sqlalchemy import create_engine

logger = logging.getLogger(__name__)

def load_bronze(engine):
    logger.info("Iniciando carga Bronze desde CSVs...")
    
    # Ruta absoluta relativa al proyecto (funciona tanto local como en Actions)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(base_dir, 'data')
    
    logger.info(f"Buscando CSVs en directorio: {data_dir}")
    
    if not os.path.exists(data_dir):
        logger.error(f"Directorio data/ NO encontrado en {data_dir}")
        return
    
    csv_files = {
        'ventas': 'ventas.csv',
        'stock': 'stock.csv',
        'precios': 'precios.csv'
    }
    
    for table_name, csv_filename in csv_files.items():
        csv_path = os.path.join(data_dir, csv_filename)
        logger.info(f"Procesando archivo: {csv_path}")
        
        if not os.path.exists(csv_path):
            logger.warning(f"Archivo NO encontrado: {csv_path}")
            continue
        
        try:
            df = pd.read_csv(csv_path)
            if df.empty:
                logger.warning(f"CSV vacío: {csv_filename}")
                continue
            
            row_count = len(df)
            df.to_sql(table_name, engine, schema='retail_bronze', if_exists='replace', index=False)
            logger.info(f"ÉXITO: {row_count} filas insertadas en retail_bronze.{table_name} desde {csv_filename}")
        except Exception as e:
            logger.error(f"ERROR cargando {csv_filename}: {str(e)}", exc_info=True)
            continue
    
    logger.info("Carga Bronze finalizada")
