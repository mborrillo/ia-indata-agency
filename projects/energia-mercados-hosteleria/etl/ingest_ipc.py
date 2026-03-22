"""
ETL: IPC General + IPC Alimentación (INE) → hosteleria.bronze_ipc
Series INE:
  IPC General España:        IPC206449
  IPC Alimentación España:   IPC206450
Frecuencia: mensual.
Fix: manejo robusto del formato de respuesta del INE (puede variar).
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


def parse_fecha(nombre: str) -> str:
    """'Marzo 2026' → '2026-03-01'"""
    partes = (nombre or "").strip().split()
    if len(partes) == 2:
        mes  = MESES.get(partes[0], 1)
        anio = int(partes[1])
        return f"{anio}-{mes:02d}-01"
    return datetime.now().strftime("%Y-%m-01")


def extract_ine(indicador: str, serie_id: str) -> dict | None:
    """
    Descarga último dato de una serie INE con manejo robusto de respuesta.
    El INE a veces devuelve la serie completa, a veces solo el último dato.
    """
    urls_a_probar = [
        f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_id}?nult=1",
        f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_id}?nult=2",
    ]

    for url in urls_a_probar:
        try:
            r = requests.get(url, timeout=20,
                             headers={"Accept": "application/json"})

            # El INE puede devolver 200 con body vacío o con 0
            if r.status_code != 200:
                log.warning("INE %s HTTP %d", indicador, r.status_code)
                continue

            # Intentar parsear JSON de forma segura
            try:
                contenido = r.json()
            except Exception:
                log.warning("INE %s — respuesta no es JSON", indicador)
                continue

            # La respuesta puede ser: lista, dict, int, None
            if not contenido:
                log.warning("INE %s — respuesta vacía", indicador)
                continue

            # Si es lista, tomar el primer elemento
            if isinstance(contenido, list):
                datos = contenido
            elif isinstance(contenido, dict):
                # A veces el INE envuelve en {"Data": [...]}
                datos = contenido.get("Data", contenido.get("data", [contenido]))
            else:
                log.warning("INE %s — formato inesperado: %s", indicador, type(contenido))
                continue

            if not datos:
                continue

            # Buscar el primer elemento con Valor no nulo
            for item in datos:
                if not isinstance(item, dict):
                    continue
                valor_raw = item.get("Valor") or item.get("valor")
                if valor_raw is None:
                    continue
                try:
                    valor = float(str(valor_raw).replace(",", "."))
                except (ValueError, TypeError):
                    continue

                nombre_periodo = item.get("NombrePeriodo") or item.get("nombre_periodo", "")
                fecha = parse_fecha(nombre_periodo)

                log.info("INE %s — %s: %.2f%%", indicador, fecha, valor)
                return {
                    "fecha":     fecha,
                    "indicador": indicador,
                    "valor":     round(valor, 2),
                    "unidad":    "tasa_variacion_anual_%",
                }

        except requests.exceptions.RequestException as e:
            log.warning("INE %s request error: %s", indicador, e)
            continue
        except Exception as e:
            log.warning("INE %s error inesperado: %s", indicador, e)
            continue

    log.error("INE %s — no se pudo obtener dato de ninguna URL", indicador)
    return None


def already_loaded(fecha: str, indicador: str) -> bool:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT 1 FROM hosteleria.bronze_ipc "
                "WHERE fecha=:f AND indicador=:i"),
                {"f": fecha, "i": indicador}
            ).fetchone()
        return row is not None
    except Exception:
        return False


def load(reg: dict):
    sql = """
        INSERT INTO hosteleria.bronze_ipc (fecha, indicador, valor, unidad)
        VALUES (:fecha, :indicador, :valor, :unidad)
        ON CONFLICT (fecha, indicador) DO UPDATE SET valor = EXCLUDED.valor
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ %s %s: %.2f%%", reg["indicador"], reg["fecha"], reg["valor"])


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    log.info("=== ETL IPC General + Alimentación ===")
    cargados = 0

    for indicador, serie_id in SERIES_INE.items():
        reg = extract_ine(indicador, serie_id)
        if not reg:
            log.warning("%s — sin dato disponible este mes", indicador)
            continue
        if already_loaded(reg["fecha"], reg["indicador"]):
            log.info("%s %s ya existe. Saltando.", indicador, reg["fecha"])
            continue
        load(reg)
        cargados += 1

    log.info("=== IPC completado — %d registros nuevos ===", cargados)
