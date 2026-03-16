"""B2: Carga a Bronze desde fuentes (CSV/seeds). Columnas técnicas: _ingested_at, _source_file."""
import os
from datetime import datetime

import pandas as pd
import sqlalchemy
from sqlalchemy import text

from etl.config import DATABASE_URL
from etl.db import get_engine

_ETL_DIR = os.path.dirname(os.path.abspath(__file__))
SOURCE_DIR = os.environ.get("RETAIL_DATA_DIR", os.path.join(_ETL_DIR, "..", "data"))
SOURCE_FILE_VENTAS = "ventas.csv"
SOURCE_FILE_STOCK = "stock.csv"
SOURCE_FILE_PRECIOS = "precios.csv"


def _ensure_data_dir():
    os.makedirs(SOURCE_DIR, exist_ok=True)


def load_ventas_bronze(source_path: str | None = None) -> int:
    path = source_path or os.path.join(SOURCE_DIR, SOURCE_FILE_VENTAS)
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    df["_ingested_at"] = datetime.utcnow()
    df["_source_file"] = path
    engine = get_engine()
    df.to_sql(
        "ventas",
        engine,
        schema="retail_bronze",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def load_stock_bronze(source_path: str | None = None) -> int:
    path = source_path or os.path.join(SOURCE_DIR, SOURCE_FILE_STOCK)
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    df["_ingested_at"] = datetime.utcnow()
    df["_source_file"] = path
    engine = get_engine()
    df.to_sql(
        "stock",
        engine,
        schema="retail_bronze",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def load_precios_bronze(source_path: str | None = None) -> int:
    path = source_path or os.path.join(SOURCE_DIR, SOURCE_FILE_PRECIOS)
    if not os.path.exists(path):
        return 0
    df = pd.read_csv(path)
    df["_ingested_at"] = datetime.utcnow()
    df["_source_file"] = path
    engine = get_engine()
    df.to_sql(
        "precios",
        engine,
        schema="retail_bronze",
        if_exists="append",
        index=False,
        method="multi",
        chunksize=1000,
    )
    return len(df)


def run_bronze():
    _ensure_data_dir()
    n_v = load_ventas_bronze()
    n_s = load_stock_bronze()
    n_p = load_precios_bronze()
    return {"ventas": n_v, "stock": n_s, "precios": n_p}
