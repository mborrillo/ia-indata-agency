"""
ETL base — copia y renombra por fuente de datos.
Ejemplos: ingest_precios.py, ingest_clima.py, ingest_ventas.py
"""
import os
import pandas as pd
from datetime import datetime, date
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("NEON_DATABASE_URL")


def extract() -> list[dict]:
    """
    Obtener datos de la fuente externa.
    Reemplaza con: requests.get(API_URL), yfinance.download(), pd.read_csv()...
    """
    # TODO: implementar según spec.md sección 2
    return []


def transform(raw: list[dict]) -> pd.DataFrame:
    """Limpiar, tipar y añadir columnas técnicas (capa Silver)."""
    if not raw:
        return pd.DataFrame()

    df = pd.DataFrame(raw)

    # Columnas técnicas obligatorias (no borrar)
    df["_ingested_at"] = datetime.utcnow()
    df["_source"] = "nombre_fuente"  # TODO: cambiar al nombre real
    df["fecha"] = pd.to_datetime(df.get("fecha", date.today()))

    # TODO: añadir transformaciones específicas del proyecto
    # df = df.dropna(subset=["columna_critica"])
    # df["columna"] = df["columna"].astype(float)

    return df


def load(df: pd.DataFrame, table: str) -> int:
    """Insertar en Neon. Append-only: nunca borra datos."""
    if df.empty:
        print(f"⚠ Sin datos para cargar en {table}")
        return 0

    conn = psycopg2.connect(DB_URL)
    try:
        cols = list(df.columns)
        rows = [tuple(r) for r in df.itertuples(index=False)]
        sql = f"""
            INSERT INTO {table} ({", ".join(cols)})
            VALUES %s
            ON CONFLICT DO NOTHING
        """
        with conn.cursor() as cur:
            execute_values(cur, sql, rows)
        conn.commit()
        print(f"✓ {len(df)} registros → {table}")
        return len(df)
    finally:
        conn.close()


if __name__ == "__main__":
    print(f"[{datetime.utcnow():%Y-%m-%d %H:%M}] Iniciando ETL...")
    raw = extract()
    clean = transform(raw)
    loaded = load(clean, "bronze_datos")
    print(f"[DONE] {loaded} registros cargados")
