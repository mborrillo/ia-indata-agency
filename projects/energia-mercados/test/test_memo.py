"""
Tests de calidad de datos — MEMO
Ejecutar con: pytest tests/ -v
Requiere NEON_DATABASE_URL en el entorno.
"""
import os
import pytest
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DB_URL = os.getenv("NEON_DATABASE_URL")


@pytest.fixture(scope="module")
def conn():
    if not DB_URL:
        pytest.skip("NEON_DATABASE_URL no configurada")
    c = psycopg2.connect(DB_URL)
    yield c
    c.close()


def read(conn, sql):
    return pd.read_sql(sql, conn)


# ── Energía ───────────────────────────────────────────────────────────────────

def test_energia_tiene_datos(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_energia")
    assert df["n"].iloc[0] > 0, "bronze_energia está vacía"


def test_energia_sin_fechas_nulas(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_energia WHERE fecha IS NULL")
    assert df["n"].iloc[0] == 0, "Hay fechas nulas en bronze_energia"


def test_energia_precios_positivos(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_energia WHERE precio_medio <= 0")
    assert df["n"].iloc[0] == 0, "Hay precios <= 0 en bronze_energia"


def test_energia_sin_duplicados(conn):
    df = read(conn, """
        SELECT fecha, COUNT(*) AS n
        FROM memo.bronze_energia
        GROUP BY fecha HAVING COUNT(*) > 1
    """)
    assert df.empty, f"Fechas duplicadas en bronze_energia: {df['fecha'].tolist()}"


def test_gold_energia_resumen_existe(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.v_energia_resumen")
    assert df["n"].iloc[0] > 0, "v_energia_resumen está vacía"


def test_gold_semaforo_valores_validos(conn):
    df = read(conn, "SELECT DISTINCT semaforo FROM memo.v_energia_resumen")
    valores_validos = {"BAJO", "NORMAL", "ALTO"}
    invalidos = set(df["semaforo"].tolist()) - valores_validos
    assert not invalidos, f"Valores inválidos en semáforo: {invalidos}"


# ── Mercados ──────────────────────────────────────────────────────────────────

def test_mercados_tiene_datos(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_mercados")
    assert df["n"].iloc[0] > 0, "bronze_mercados está vacía"


def test_mercados_sin_duplicados(conn):
    df = read(conn, """
        SELECT fecha, activo, COUNT(*) AS n
        FROM memo.bronze_mercados
        GROUP BY fecha, activo HAVING COUNT(*) > 1
    """)
    assert df.empty, "Duplicados (fecha, activo) en bronze_mercados"


def test_mercados_precios_positivos(conn):
    df = read(conn, """
        SELECT COUNT(*) AS n FROM memo.bronze_mercados
        WHERE precio_cierre <= 0
    """)
    assert df["n"].iloc[0] == 0, "Hay precios <= 0 en bronze_mercados"


# ── Divisa y Macro ────────────────────────────────────────────────────────────

def test_divisa_tiene_datos(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_divisa")
    assert df["n"].iloc[0] > 0, "bronze_divisa está vacía"


def test_divisa_tasa_razonable(conn):
    """EUR/USD debería estar entre 0.8 y 1.5 en condiciones normales."""
    df = read(conn, """
        SELECT COUNT(*) AS n FROM memo.bronze_divisa
        WHERE tasa < 0.8 OR tasa > 1.5
    """)
    assert df["n"].iloc[0] == 0, "Tasas EUR/USD fuera de rango razonable"


def test_macro_tiene_datos(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.bronze_macro")
    assert df["n"].iloc[0] > 0, "bronze_macro está vacía"


# ── Vistas Gold ───────────────────────────────────────────────────────────────

def test_gold_mercados_resumen(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.v_mercados_resumen")
    assert df["n"].iloc[0] > 0, "v_mercados_resumen está vacía"


def test_gold_macro_resumen(conn):
    df = read(conn, "SELECT COUNT(*) AS n FROM memo.v_macro_resumen")
    assert df["n"].iloc[0] > 0, "v_macro_resumen está vacía"
