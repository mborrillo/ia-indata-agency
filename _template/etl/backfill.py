"""
backfill.py — Carga histórica de datos
Archivo estándar del template ia-indata-agency.

Ejecutar UNA VEZ al iniciar el proyecto, o cuando se necesite
repoblar el histórico tras un problema.

Uso:
    python etl/backfill.py        # últimos 20 días (por defecto)
    python etl/backfill.py 30     # últimos N días

Adaptación para cada proyecto:
  1. Añadir una función backfill_[fuente]() por cada ETL del proyecto
  2. Llamarlas desde el bloque __main__
  3. El patrón es siempre: obtener fechas pendientes → extraer → cargar
"""
import os, sys, logging
from datetime import date, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")
DIAS   = int(sys.argv[1]) if len(sys.argv) > 1 else 20


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def fechas_pendientes(schema: str, tabla: str, col_fecha: str, dias: int) -> list[str]:
    """
    Devuelve solo las fechas que NO están ya en la BD.
    Evita duplicados y permite ejecutar el backfill varias veces sin problema.
    """
    hoy   = date.today()
    todas = [(hoy - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, dias + 1)]
    try:
        with get_engine().connect() as conn:
            existentes = {
                r[0][:10] for r in conn.execute(
                    text(f"SELECT {col_fecha}::text FROM {schema}.{tabla}")
                )
            }
    except Exception:
        existentes = set()
    pendientes = sorted([f for f in todas if f not in existentes])
    log.info("  %s.%s: %d fechas pendientes de %d solicitadas",
             schema, tabla, len(pendientes), dias)
    return pendientes


# ── EJEMPLO: adaptar esta función por cada fuente del proyecto ────────────────

def backfill_ejemplo(dias: int):
    """
    Plantilla de función de backfill.
    Duplicar y renombrar por cada fuente: backfill_pvpc, backfill_precios, etc.
    """
    log.info("═══ Backfill [nombre fuente] (%d días) ═══", dias)

    # 1. Obtener fechas que faltan en la BD
    fechas = fechas_pendientes("SCHEMA", "TABLA", "fecha", dias)
    if not fechas:
        log.info("  Sin fechas pendientes."); return

    registros = []
    for fecha in fechas:
        try:
            # 2. Extraer datos de la fuente para esta fecha
            # dato = requests.get(URL.format(fecha=fecha))
            # ...procesar dato...

            registros.append({
                "fecha": fecha,
                # "columna": valor,
            })
            log.info("  ✓ [fuente] %s", fecha)
        except Exception as e:
            log.error("  ✗ [fuente] %s: %s", fecha, e)

    # 3. Cargar en BD (upsert — seguro de ejecutar varias veces)
    if registros:
        cols = list(registros[0].keys())
        sql  = f"""
            INSERT INTO SCHEMA.TABLA ({", ".join(cols)})
            VALUES ({", ".join(f":{c}" for c in cols)})
            ON CONFLICT (fecha) DO UPDATE SET
                {", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c != "fecha")}
        """
        with get_engine().begin() as conn:
            conn.execute(text(sql), registros)
        log.info("  ✓ %d registros cargados", len(registros))


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida. Abortando.")
        sys.exit(1)

    log.info("════ BACKFILL [NOMBRE PROYECTO] — últimos %d días ════", DIAS)
    log.info("Desde: %s",
             (date.today() - timedelta(days=DIAS)).strftime("%Y-%m-%d"))

    # Llamar a cada función de backfill del proyecto
    # backfill_pvpc(DIAS)
    # backfill_precios(DIAS)
    # backfill_macro(DIAS)

    log.info("════ BACKFILL COMPLETADO ════")
    log.info("Verifica en Neon con:")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM SCHEMA.TABLA;")
