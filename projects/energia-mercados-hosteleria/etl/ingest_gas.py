"""
ETL: Precio Gas Natural España (REE ESIOS) → hosteleria.bronze_gas
Indicador 460: precio gas natural mercado spot diario España (€/MWh)
Fuente: api.esios.ree.es — sin autenticación necesaria
"""
import os, sys, logging, requests
from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")

# Indicador REE para gas natural España
# 460 = Precio gas mercado spot diario (MIBGAS)
GAS_URL = (
    "https://apidatos.ree.es/es/datos/mercados/precio-gas?"
    "time_trunc=day&start_date={inicio}T00:00&end_date={fin}T23:59"
)


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def extract(fecha: str) -> dict | None:
    """Descarga el precio del gas del día dado desde REE."""
    try:
        r = requests.get(
            GAS_URL.format(inicio=fecha, fin=fecha),
            timeout=15
        )
        r.raise_for_status()
        data    = r.json()
        valores = data.get("included", [{}])[0].get("attributes", {}).get("values", [])
        if not valores:
            log.warning("REE gas: sin datos para %s", fecha)
            return None
        precio = float(valores[0].get("value", 0))
        log.info("Gas natural %s — %.4f €/MWh", fecha, precio)
        return {"fecha": fecha, "precio_mwh": round(precio, 4)}
    except Exception as e:
        log.error("Error gas REE: %s", e)
        return None


def enrich_var(reg: dict) -> dict:
    fecha_ayer = (datetime.strptime(reg["fecha"], "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT precio_mwh FROM hosteleria.bronze_gas WHERE fecha=:f"), {"f": fecha_ayer}
            ).fetchone()
        if row:
            reg["var_per_prev"] = round((reg["precio_mwh"] - row[0]) / row[0] * 100, 2)
        else:
            reg["var_per_prev"] = None
    except Exception:
        reg["var_per_prev"] = None
    return reg


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
    log.info("✓ Gas %s guardado", reg["fecha"])


if __name__ == "__main__":
    if not DB_URL: log.error("NEON_DATABASE_URL no definida"); sys.exit(1)
    fecha = datetime.now().strftime("%Y-%m-%d")
    reg   = extract(fecha)
    if not reg: sys.exit(1)
    reg   = enrich_var(reg)
    load(reg)
