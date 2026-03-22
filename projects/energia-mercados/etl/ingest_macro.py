"""
ETL: Tipo de Cambio EUR/USD (BCE) + IPC España (INE)
Fuentes:
  - BCE: data-api.ecb.europa.eu (SDMX-JSON, sin autenticación)
  - INE: servicios.ine.es — IPC General (IPC206449) + IPC Alimentación (IPC206450)
Destino: Neon → memo.bronze_divisa + memo.bronze_macro
Frecuencia: Diaria para BCE, mensual para INE
"""
import os, sys, logging, requests
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")

BCE_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    "?format=jsondata&lastNObservations=1"
)

# Ambas series INE — general y alimentación
SERIES_INE = {
    "IPC_GENERAL":      "IPC206449",
    "IPC_ALIMENTACION": "IPC206450",
}

MESES = {
    "Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,
    "Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12,
}


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


# ── BCE: EUR/USD ──────────────────────────────────────────────────────────────

def extract_bce() -> dict | None:
    try:
        r = requests.get(BCE_URL, timeout=15)
        r.raise_for_status()
        data   = r.json()
        obs    = data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
        last   = max(obs.keys(), key=int)
        tasa   = float(obs[last][0])
        fechas = data["structure"]["dimensions"]["observation"][0]["values"]
        fecha  = fechas[int(last)]["id"]
        log.info("BCE EUR/USD — %s: %.4f", fecha, tasa)
        return {"fecha": fecha, "par": "EUR/USD", "tasa": round(tasa, 4)}
    except Exception as e:
        log.error("Error BCE: %s", e); return None


def load_divisa(reg: dict):
    sql = """
        INSERT INTO memo.bronze_divisa (fecha, par, tasa)
        VALUES (:fecha, :par, :tasa)
        ON CONFLICT (fecha, par) DO UPDATE SET tasa = EXCLUDED.tasa
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ EUR/USD %s guardado", reg["fecha"])


# ── INE: IPC General + IPC Alimentación ──────────────────────────────────────

def parse_fecha_ine(nombre: str) -> str:
    partes = nombre.strip().split()
    if len(partes) == 2:
        mes  = MESES.get(partes[0], 1)
        anio = int(partes[1])
        return f"{anio}-{mes:02d}-01"
    return datetime.now().strftime("%Y-%m-01")


def extract_ine_serie(indicador: str, serie_id: str) -> dict | None:
    url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_id}?nult=1"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        datos = r.json()
        if not datos:
            log.warning("INE %s — lista vacía", indicador); return None
        ultimo = datos[0]
        valor  = ultimo.get("Valor")
        if valor is None:
            log.warning("INE %s — valor nulo", indicador); return None
        fecha = parse_fecha_ine(ultimo.get("NombrePeriodo",""))
        log.info("INE %s — %s: %.2f%%", indicador, fecha, float(valor))
        return {
            "fecha":     fecha,
            "indicador": indicador,
            "valor":     round(float(valor), 2),
            "unidad":    "tasa_variacion_anual_%",
        }
    except Exception as e:
        log.error("Error INE %s: %s", indicador, e); return None


def already_loaded_macro(fecha: str, indicador: str) -> bool:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT 1 FROM memo.bronze_macro WHERE fecha=:f AND indicador=:i"),
                {"f": fecha, "i": indicador}
            ).fetchone()
        return row is not None
    except Exception:
        return False


def load_macro(reg: dict):
    sql = """
        INSERT INTO memo.bronze_macro (fecha, indicador, valor, unidad)
        VALUES (:fecha, :indicador, :valor, :unidad)
        ON CONFLICT (fecha, indicador) DO UPDATE SET valor = EXCLUDED.valor
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ %s %s guardado", reg["indicador"], reg["fecha"])


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    log.info("=== ETL Macro (BCE + IPC General + IPC Alimentación) ===")

    # EUR/USD
    bce = extract_bce()
    if bce:
        load_divisa(bce)

    # Ambos IPCs
    for indicador, serie_id in SERIES_INE.items():
        reg = extract_ine_serie(indicador, serie_id)
        if reg:
            if not already_loaded_macro(reg["fecha"], reg["indicador"]):
                load_macro(reg)
            else:
                log.info("%s %s ya existe. Saltando.", indicador, reg["fecha"])

    log.info("=== ETL Macro completado ===")
