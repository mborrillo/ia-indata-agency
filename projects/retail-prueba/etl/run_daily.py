#!/usr/bin/env python3
"""B5: Pipeline ETL diario. Ejecuta DDL (schemas/tablas/vistas), luego Bronze y Silver. Gold son vistas."""
import os
import sys

# Permitir importar etl desde el directorio del proyecto retail-prueba
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from etl.config import DATABASE_URL  # noqa: E402
from etl.db import get_engine, run_sql_file  # noqa: E402
from etl.load_bronze import run_bronze  # noqa: E402
from etl.silver import run_silver  # noqa: E402

SQL_DIR = os.path.join(os.path.dirname(__file__), "..", "sql")
MIGRATIONS = ["01_schemas.sql", "02_bronze_tables.sql", "03_silver_tables.sql", "04_gold_views.sql"]


def run_migrations(engine):
    for name in MIGRATIONS:
        path = os.path.join(SQL_DIR, name)
        if os.path.exists(path):
            run_sql_file(engine, path)


def main():
    if not DATABASE_URL:
        print("ERROR: Definir NEON_DATABASE_URL o DATABASE_URL")
        sys.exit(1)
    engine = get_engine()
    run_migrations(engine)
    bronze_counts = run_bronze()
    silver_counts = run_silver()
    print("Bronze:", bronze_counts)
    print("Silver:", silver_counts)


if __name__ == "__main__":
    main()
