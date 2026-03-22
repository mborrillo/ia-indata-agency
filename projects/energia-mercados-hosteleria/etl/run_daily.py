"""
run_daily.py — Orquestador ETL diario MEMO Hostelería
Ejecuta los 4 scripts en secuencia. Si uno falla, los demás siguen.
GitHub Actions llama a este archivo cada día laborable.
"""
import logging, sys
from datetime import datetime, date

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

    # ── PVPC ──────────────────────────────────────────────────
    try:
        from etl.ingest_pvpc import extract, transform, load, enrich_var
        def etl_pvpc():
            fecha = date.today().strftime("%Y-%m-%d")
            pvpc  = extract(fecha)
            if not pvpc: raise ValueError("REE sin datos")
            reg = transform(pvpc, fecha)
            if not reg: raise ValueError("PVPC sin parsear")
            load(enrich_var(reg))
        resultados["PVPC"] = run("Luz PVPC", etl_pvpc)
    except ImportError as e:
        log.error("Import PVPC: %s", e); resultados["PVPC"] = False

    # ── GAS — yfinance NG=F ───────────────────────────────────
    try:
        from etl.ingest_gas import extract as g_extract, load as g_load
        def etl_gas():
            fecha = date.today().strftime("%Y-%m-%d")
            reg   = g_extract(fecha)
            if not reg: raise ValueError("Gas sin datos")
            g_load(reg)
        resultados["Gas"] = run("Gas Natural", etl_gas)
    except ImportError as e:
        log.error("Import Gas: %s", e); resultados["Gas"] = False

    # ── ACEITE — scraping en cascada ──────────────────────────
    try:
        from etl.ingest_aceite import (
            extract_oleista, extract_precioaceitedeoliva,
            extract_infaoliva_home, load as a_load, already_loaded
        )
        def etl_aceite():
            hoy   = date.today()
            lunes = (hoy - __import__('datetime').timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")
            if already_loaded(lunes):
                log.info("Aceite ya cargado esta semana. Saltando.")
                return
            reg = (extract_oleista() or
                   extract_precioaceitedeoliva() or
                   extract_infaoliva_home())
            if not reg: raise ValueError("Aceite sin datos en ninguna fuente")
            a_load(reg, lunes)
        resultados["Aceite"] = run("Aceite AOVE", etl_aceite)
    except ImportError as e:
        log.error("Import Aceite: %s", e); resultados["Aceite"] = False

    # ── IPC General + Alimentación ────────────────────────────
    try:
        from etl.ingest_ipc import extract_ine, load as i_load, already_loaded as i_loaded, SERIES_INE
        def etl_ipc():
            for indicador, serie_id in SERIES_INE.items():
                reg = extract_ine(indicador, serie_id)
                if not reg:
                    log.warning("%s — sin dato disponible", indicador)
                    continue
                if i_loaded(reg["fecha"], reg["indicador"]):
                    log.info("%s %s ya existe. Saltando.", indicador, reg["fecha"])
                    continue
                i_load(reg)
        resultados["IPC"] = run("IPC General + Alimentación", etl_ipc)
    except ImportError as e:
        log.error("Import IPC: %s", e); resultados["IPC"] = False

    # ── Resumen ───────────────────────────────────────────────
    log.info("════ RESUMEN ════")
    fallos = []
    for nombre, ok in resultados.items():
        log.info("  %s — %s", nombre, "✓ OK" if ok else "✗ FALLO")
        if not ok: fallos.append(nombre)

    if fallos:
        log.error("Fallaron: %s", ", ".join(fallos))
        sys.exit(1)
    log.info("════ ETL completado sin errores ════")
