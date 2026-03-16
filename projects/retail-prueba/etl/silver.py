"""
Transformación a capa Silver
"""

import logging
from sqlalchemy import text

logger = logging.getLogger(__name__)

def transform_silver(engine):
    logger.info("Iniciando transformación Silver...")
    try:
        with engine.connect() as conn:
            # Ejemplo: eliminar duplicados, normalizar, etc.
            conn.execute(text("TRUNCATE retail_silver.ventas;"))
            conn.execute(text("""
                INSERT INTO retail_silver.ventas
                SELECT DISTINCT producto_id, tienda_id, fecha, cantidad, precio
                FROM retail_bronze.ventas
            """))
            logger.info("Transformación Silver completada para ventas")
    except Exception as e:
        logger.error(f"Error en transformación Silver: {str(e)}", exc_info=True)
        raise
