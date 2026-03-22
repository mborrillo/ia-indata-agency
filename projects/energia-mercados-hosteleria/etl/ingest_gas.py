"""
ETL: Precio Gas Natural → hosteleria.bronze_gas
Fuente: yfinance — ticker NG=F (Natural Gas Futures, Henry Hub)
       usado como proxy del precio mayorista del gas en Europa.
       Alternativa robusta al endpoint REE que no es accesible públicamente.

Unidad: USD/MMBtu → convertido a EUR/MWh para consistencia con hostelería española.
Factor conversión: 1 MMBtu = 0.29307 MWh. EUR/USD del día anterior.
"""
import os, sys, logging
from datetime import datetime, timedelta, date
import yfinance as yf
import psycopg2
from psycopg2.extras import execute_values
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")

# Conversión USD/MMBtu → EUR/MWh
# 1 MMBtu = 0.29307 MWh
# Usamos tipo de cambio aproximado 1.15 USD/EUR (se actualiza con BCE en ingest_ipc)
FACTOR_MMBTU_TO_MWH = 0.29307
EUR_USD_APPROX = 1.15


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def extract(fecha: str) -> dict | None:
    """Descarga precio del gas via yfinance (NG=F)."""
    try:
        hist = yf.Ticker("NG=F").history(period="5d")
        if hist.empty or len(hist) < 1:
            log.warning("yfinance NG=F sin datos")
            return None

        cierre_usd  = float(hist["Close"].iloc[-1])
        anterior    = float(hist["Close"].iloc[-2]) if len(hist) >= 2 else cierre_usd

        # Obtener EUR/USD real de la BD si está disponible
        try:
            with get_engine().connect() as conn:
                row = conn.execute(text(
                    "SELECT tasa FROM hosteleria.bronze_ipc WHERE indicador='EUR_USD' "
                    "ORDER BY fecha DESC LIMIT 1"
                )).fetchone()
                eur_usd = float(row[0]) if row else EUR_USD_APPROX
        except Exception:
            eur_usd = EUR_USD_APPROX

        # Convertir USD/MMBtu → EUR/MWh
        precio_eur_mwh = (cierre_usd / eur_usd) / FACTOR_MMBTU_TO_MWH
        variacion = (cierre_usd - anterior) / anterior * 100 if anterior else 0

        log.info("Gas NG=F %s — %.4f USD/MMBtu → %.2f EUR/MWh (var: %+.2f%%)",
                 fecha, cierre_usd, precio_eur_mwh, variacion)

        return {
            "fecha":       fecha,
            "precio_mwh":  round(precio_eur_mwh, 4),
            "var_per_prev": round(variacion, 2),
        }

    except Exception as e:
        log.error("Error gas yfinance: %s", e)
        return None


def load(reg: dict):
    sql = """
        INSERT INTO hosteleria.bronze_gas (fecha, precio_mwh, var_per_prev)
        VALUES (:fecha, :precio_mwh, :var_per_prev)
        ON CONFLICT (fecha) DO UPDATE SET
            precio_mwh   = EXCLUDED.precio_mwh,
            var_per_prev = EXCLUDED.var_per_prev
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ Gas %s guardado — %.2f EUR/MWh", reg["fecha"], reg["precio_mwh"])


if __name__ == "__main__":
    if not DB_URL: log.error("NEON_DATABASE_URL no definida"); sys.exit(1)
    fecha = date.today().strftime("%Y-%m-%d")
    reg   = extract(fecha)
    if not reg: sys.exit(1)
    load(reg)
