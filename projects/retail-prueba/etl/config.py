"""Configuración ETL: DATABASE_URL o NEON_DATABASE_URL desde entorno."""
from dotenv import load_dotenv
import os

load_dotenv()

import os

DATABASE_URL = os.environ.get("NEON_DATABASE_URL") or os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("Definir NEON_DATABASE_URL o DATABASE_URL en el entorno.")
