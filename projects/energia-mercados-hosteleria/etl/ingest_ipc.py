"""
ETL: IPC General + IPC Alimentación (INE) → hosteleria.bronze_ipc
También usable para actualizar memo.bronze_macro (MEMO genérico).

Series INE:
  IPC General España:        IPC206449
  IPC Alimentación España:   IPC206450  ← nueva, no estaba en MEMO genérico

Frecuencia: mensual. El script detecta si ya hay dato del mes actual
y no duplica.
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


def parse_fecha(nombre_periodo: str) -> str:
    """Convierte 'Marzo 2026' → '2026-03-01'"""
    partes = nombre_periodo.strip().split()
    if len(partes) == 2:
        mes  = MESES.get(partes[0], 1)
        anio = int(partes[1])
        return f"{anio}-{mes:02d}-01"
    return datetime.now().strftime("%Y-%m-01")


def extract_serie(indicador: str, serie_id: str) -> dict | None:
    """Descarga el último dato de una serie INE."""
    url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_id}?nult=1"
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        datos = r.json()
        if not datos:
            log.warning("INE %s — lista vacía", indicador)
            return None
        ultimo = datos[0]
        valor  = ultimo.get("Valor")
        if valor is None:
            log.warning("INE %s — valor nulo", indicador)
            return None
        fecha  = parse_fecha(ultimo.get("NombrePeriodo", ""))
        log.info("INE %s — %s: %.2f%%", indicador, fecha, float(valor))
        return {
            "fecha":     fecha,
            "indicador": indicador,
            "valor":     round(float(valor), 2),
            "unidad":    "tasa_variacion_anual_%",
        }
    except Exception as e:
        log.error("Error INE %s: %s", indicador, e)
        return None


def already_loaded(tabla: str, schema: str, fecha: str, indicador: str) -> bool:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                f"SELECT 1 FROM {schema}.{tabla} WHERE fecha=:f AND indicador=:i"),
                {"f": fecha, "i": indicador}
            ).fetchone()
        return row is not None
    except Exception:
        return False


def load(reg: dict, tabla: str, schema: str):
    sql = f"""
        INSERT INTO {schema}.{tabla} (fecha, indicador, valor, unidad)
        VALUES (:fecha, :indicador, :valor, :unidad)
        ON CONFLICT (fecha, indicador) DO UPDATE SET valor = EXCLUDED.valor
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ %s.%s → %s %s: %.2f%%",
             schema, tabla, reg["indicador"], reg["fecha"], reg["valor"])


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    log.info("=== ETL IPC (General + Alimentación) ===")
    cargados = 0

    for indicador, serie_id in SERIES_INE.items():
        reg = extract_serie(indicador, serie_id)
        if not reg:
            continue

        # Cargar en hosteleria.bronze_ipc (este proyecto)
        if not already_loaded("bronze_ipc", "hosteleria", reg["fecha"], reg["indicador"]):
            load(reg, "bronze_ipc", "hosteleria")
            cargados += 1
        else:
            log.info("Ya existe %s %s en hosteleria. Saltando.", indicador, reg["fecha"])

        # Cargar también en memo.bronze_macro (MEMO genérico) si existe
        # Esto mantiene MEMO genérico actualizado con ambos IPCs
        try:
            if not already_loaded("bronze_macro", "memo", reg["fecha"], reg["indicador"]):
                load(reg, "bronze_macro", "memo")
                log.info("  → También actualizado en memo.bronze_macro")
        except Exception:
            log.warning("  → memo.bronze_macro no disponible (distinto proyecto Neon)")

    log.info("=== IPC completado — %d registros cargados ===", cargados)
