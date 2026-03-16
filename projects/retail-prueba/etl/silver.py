"""B3: Transformación Bronze → Silver. Dedup, grano (producto_id, tienda_id, fecha)."""
import pandas as pd
from sqlalchemy import text

from etl.db import get_engine


def ventas_bronze_to_silver() -> int:
    engine = get_engine()
    df = pd.read_sql(
        text("""
            SELECT producto_id, tienda_id, fecha,
                   SUM(unidades) AS unidades, SUM(importe) AS importe
            FROM retail_bronze.ventas
            GROUP BY producto_id, tienda_id, fecha
        """),
        engine,
    )
    df = df.astype({"unidades": "float64", "importe": "float64"})
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE retail_silver.ventas"))
    df.to_sql(
        "ventas",
        engine,
        schema="retail_silver",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def stock_bronze_to_silver() -> int:
    engine = get_engine()
    df = pd.read_sql(
        text("""
            SELECT producto_id, tienda_id, fecha,
                   AVG(cantidad) AS cantidad
            FROM retail_bronze.stock
            GROUP BY producto_id, tienda_id, fecha
        """),
        engine,
    )
    df = df.astype({"cantidad": "float64"})
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE retail_silver.stock"))
    df.to_sql(
        "stock",
        engine,
        schema="retail_silver",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def precios_bronze_to_silver() -> int:
    engine = get_engine()
    df = pd.read_sql(
        text("""
            SELECT producto_id, tienda_id, fecha,
                   AVG(precio_local) AS precio_local
            FROM retail_bronze.precios
            GROUP BY producto_id, tienda_id, fecha
        """),
        engine,
    )
    df = df.astype({"precio_local": "float64"})
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE retail_silver.precios"))
    df.to_sql(
        "precios",
        engine,
        schema="retail_silver",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def run_silver():
    n_v = ventas_bronze_to_silver()
    n_s = stock_bronze_to_silver()
    n_p = precios_bronze_to_silver()
    return {"ventas": n_v, "stock": n_s, "precios": n_p}
