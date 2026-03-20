"""
run_daily.py — Orquestador ETL diario MEMO
Ejecuta los 3 scripts en secuencia. GitHub Actions llama a este archivo.
Cada script es independiente: si uno falla, los demás siguen ejecutándose.
"""
import logging
import sys
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def run(nombre: str, fn):
    """Ejecuta una función ETL y captura errores sin detener el pipeline."""
    log.info("── Iniciando: %s ──", nombre)
    try:
        fn()
        log.info("── Completado: %s ──", nombre)
        return True
    except Exception as e:
        log.error("── FALLO en %s: %s ──", nombre, e)
        return False


if __name__ == "__main__":
    log.info("════ ETL Diario MEMO — %s ════", datetime.now().strftime("%Y-%m-%d %H:%M"))

    resultados = {}

    # Importar y ejecutar cada ETL
    try:
        from etl.ingest_energia import extract as e_ext, transform as e_tr, load as e_ld, enrich_var_prev
        from datetime import datetime as dt
        def etl_energia():
            fecha = dt.now().strftime("%Y-%m-%d")
            pvpc = e_ext(fecha)
            if not pvpc:
                raise ValueError("REE no devolvió datos")
            reg = e_tr(pvpc, fecha)
            if not reg:
                raise ValueError("No se pudo parsear PVPC")
            reg = enrich_var_prev(reg)
            e_ld(reg)
        resultados["Energía PVPC"] = run("Energía PVPC", etl_energia)
    except ImportError as e:
        log.error("Import fallido para Energía: %s", e)
        resultados["Energía PVPC"] = False

    try:
        from etl.ingest_mercados import extract_and_transform, load as m_ld
        from datetime import datetime as dt
        def etl_mercados():
            fecha = dt.now().strftime("%Y-%m-%d")
            registros = extract_and_transform(fecha)
            m_ld(registros)
        resultados["Mercados"] = run("Mercados", etl_mercados)
    except ImportError as e:
        log.error("Import fallido para Mercados: %s", e)
        resultados["Mercados"] = False

    try:
        from etl.ingest_macro import extract_bce, load_divisa, extract_ine, load_macro
        def etl_macro():
            bce = extract_bce()
            if bce:
                load_divisa(bce)
            ine = extract_ine()
            if ine:
                load_macro(ine)
        resultados["Macro (BCE+INE)"] = run("Macro (BCE+INE)", etl_macro)
    except ImportError as e:
        log.error("Import fallido para Macro: %s", e)
        resultados["Macro (BCE+INE)"] = False

    # Resumen
    log.info("════ RESUMEN ════")
    fallos = []
    for nombre, ok in resultados.items():
        estado = "✓ OK" if ok else "✗ FALLO"
        log.info("  %s — %s", nombre, estado)
        if not ok:
            fallos.append(nombre)

    if fallos:
        log.error("Fallaron: %s", ", ".join(fallos))
        sys.exit(1)  # GitHub Actions marcará el job como fallido

    log.info("════ ETL completado sin errores ════")
