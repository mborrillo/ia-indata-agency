"""
run_daily.py — Orquestador ETL_diario_MEMO_Hostelería
Ejecuta los 4 scripts en secuencia. Si uno falla, los demás siguen.
GitHub Actions llama a este archivo cada día laborable.
"""
import logging, sys
from datetime import datetime

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)


def run(nombre: str, fn):
    log.info("── %s ──", nombre)
    try:
        fn()
        log.info("✓ %s completado", nombre)
        return True
    except Exception as e:
        log.error("✗ %s falló: %s", nombre, e)
        return False


if __name__ == "__main__":
    log.info("════ ETL Hostelería — %s ════", datetime.now().strftime("%Y-%m-%d %H:%M"))
    resultados = {}

    try:
        from etl.ingest_pvpc import extract, transform, load, enrich_var
        from datetime import datetime as dt
        def etl_pvpc():
            fecha = dt.now().strftime("%Y-%m-%d")
            pvpc  = extract(fecha)
            if not pvpc: raise ValueError("REE sin datos")
            reg = transform(pvpc, fecha)
            if not reg: raise ValueError("PVPC sin parsear")
            load(enrich_var(reg))
        resultados["PVPC"] = run("Luz PVPC", etl_pvpc)
    except ImportError as e:
        log.error("Import PVPC: %s", e); resultados["PVPC"] = False

    try:
        from etl.ingest_gas import extract as g_ext, enrich_var as g_enrich, load as g_load
        from datetime import datetime as dt
        def etl_gas():
            fecha = dt.now().strftime("%Y-%m-%d")
            reg   = g_ext(fecha)
            if not reg: raise ValueError("Gas sin datos")
            g_load(g_enrich(reg))
        resultados["Gas"] = run("Gas Natural", etl_gas)
    except ImportError as e:
        log.error("Import Gas: %s", e); resultados["Gas"] = False

    try:
        from etl.ingest_aceite import extract_mapa, extract_poolred, extract_infaoliva, load as a_load, already_loaded
        from datetime import date
        def etl_aceite():
            fecha = date.today().strftime("%Y-%m-%d")
            if already_loaded(fecha): return  # ya cargado esta semana
            reg = extract_mapa() or extract_poolred() or extract_infaoliva()
            if not reg: raise ValueError("Aceite sin datos en ninguna fuente")
            reg["fecha"] = fecha
            a_load(reg)
        resultados["Aceite"] = run("Aceite AOVE", etl_aceite)
    except ImportError as e:
        log.error("Import Aceite: %s", e); resultados["Aceite"] = False

    try:
        from etl.ingest_ipc import extract_serie, load as i_load, already_loaded as i_loaded, SERIES_INE
        def etl_ipc():
            for indicador, serie_id in SERIES_INE.items():
                reg = extract_serie(indicador, serie_id)
                if reg and not i_loaded("bronze_ipc", "hosteleria", reg["fecha"], reg["indicador"]):
                    i_load(reg, "bronze_ipc", "hosteleria")
        resultados["IPC"] = run("IPC General + Alimentación", etl_ipc)
    except ImportError as e:
        log.error("Import IPC: %s", e); resultados["IPC"] = False

    # Resumen
    log.info("════ RESUMEN ════")
    fallos = []
    for nombre, ok in resultados.items():
        log.info("  %s — %s", nombre, "✓ OK" if ok else "✗ FALLO")
        if not ok: fallos.append(nombre)

    if fallos:
        log.error("Fallaron: %s", ", ".join(fallos))
        sys.exit(1)
    log.info("════ ETL completado sin errores ════")
