"""Conexión a Neon (PostgreSQL) para ETL."""
from dotenv import load_dotenv
import os

load_dotenv()

import sqlalchemy
from etl.config import DATABASE_URL

def get_engine():
    return sqlalchemy.create_engine(DATABASE_URL)

def run_sql_file(engine, path: str) -> None:
    with open(path, encoding="utf-8") as f:
        sql = f.read()
    with engine.begin() as conn:
        for stmt in sql.split(";"):
            stmt = stmt.strip()
            if stmt and not stmt.startswith("--"):
                conn.execute(sqlalchemy.text(stmt + ";"))
