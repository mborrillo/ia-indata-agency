"""
Tests básicos de calidad de datos.
Ejecutar con: pytest tests/
"""
import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("NEON_DATABASE_URL")


def get_conn():
    return psycopg2.connect(DB_URL)


def test_bronze_no_empty():
    """La tabla bronze debe tener datos tras la ingesta."""
    conn = get_conn()
    df = pd.read_sql("SELECT COUNT(*) as n FROM bronze_datos", conn)
    conn.close()
    assert df["n"].iloc[0] > 0, "bronze_datos está vacía"


def test_bronze_no_nulls_fecha():
    """La columna fecha no puede tener nulos."""
    conn = get_conn()
    df = pd.read_sql(
        "SELECT COUNT(*) as n FROM bronze_datos WHERE fecha IS NULL", conn
    )
    conn.close()
    assert df["n"].iloc[0] == 0, "Hay fechas nulas en bronze_datos"


def test_gold_view_exists():
    """Las vistas Gold deben existir y devolver datos."""
    conn = get_conn()
    df = pd.read_sql("SELECT COUNT(*) as n FROM v_resumen_kpi", conn)
    conn.close()
    assert df["n"].iloc[0] > 0, "v_resumen_kpi está vacía"


def test_no_future_dates():
    """No debe haber fechas futuras en los datos."""
    conn = get_conn()
    df = pd.read_sql(
        "SELECT COUNT(*) as n FROM bronze_datos WHERE fecha > CURRENT_DATE",
        conn
    )
    conn.close()
    assert df["n"].iloc[0] == 0, "Hay fechas futuras en bronze_datos"
