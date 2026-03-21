"""
ETL: Tipo de Cambio EUR/USD (BCE) + IPC España (INE)
Fuentes:
  - BCE: data-api.ecb.europa.eu (SDMX-JSON, sin autenticación)
  - INE: servicios.ine.es (JSON, sin autenticación)
Destino: Neon → memo.bronze_divisa + memo.bronze_macro
Frecuencia: Diaria para BCE, mensual para INE (el script detecta si hay dato nuevo)
"""
import os
import sys
import logging
import requests
from datetime import datetime

import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")

BCE_URL = (
    "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    "?format=jsondata&lastNObservations=1"
)
INE_URL = "https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC251856?nult=1"


def get_conn():
    return psycopg2.connect(DB_URL)


# ── BCE: EUR/USD ──────────────────────────────────────────────────────────────

def extract_bce() -> dict | None:
    """Último tipo de cambio EUR/USD publicado por el BCE."""
    try:
        r = requests.get(BCE_URL, timeout=15)
        r.raise_for_status()
        data = r.json()
        obs = data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
        # La última observación es la más reciente
        last_key = max(obs.keys(), key=int)
        tasa = float(obs[last_key][0])

        # Fecha desde el structure
        fechas = data["structure"]["dimensions"]["observation"][0]["values"]
        fecha_str = fechas[int(last_key)]["id"]  # formato YYYY-MM-DD

        log.info("BCE EUR/USD — %s: %.4f", fecha_str, tasa)
        return {"fecha": fecha_str, "par": "EUR/USD", "tasa": round(tasa, 4)}

    except Exception as e:
        log.error("Error BCE: %s", e)
        return None


def load_divisa(registro: dict) -> None:
    sql = """
        INSERT INTO memo.bronze_divisa (fecha, par, tasa)
        VALUES (%s, %s, %s)
        ON CONFLICT (fecha, par) DO UPDATE SET tasa = EXCLUDED.tasa
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (registro["fecha"], registro["par"], registro["tasa"]))
        conn.commit()
        log.info("✓ EUR/USD %s guardado", registro["fecha"])
    finally:
        conn.close()


# ── INE: IPC España ───────────────────────────────────────────────────────────

def extract_ine() -> dict | None:
    """Último dato de IPC general España (serie IPC206449)."""
    try:
        r = requests.get(INE_URL, timeout=15)
        r.raise_for_status()
        datos = r.json()
        if not datos:
            log.warning("INE devolvió lista vacía")
            return None

        ultimo = datos[0]
        # Fecha en formato "MMMM YYYY" → convertir a primer día del mes
        fecha_raw = ultimo.get("NombrePeriodo", "")
        valor = float(ultimo.get("Valor", 0))

        # Parsear "Marzo 2026" → "2026-03-01"
        meses = {
            "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4,
            "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8,
            "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12,
        }
        partes = fecha_raw.split()
        if len(partes) == 2:
            mes = meses.get(partes[0], 1)
            anio = int(partes[1])
            fecha_iso = f"{anio}-{mes:02d}-01"
        else:
            fecha_iso = datetime.now().strftime("%Y-%m-01")

        log.info("INE IPC — %s: %.2f", fecha_iso, valor)
        return {
            "fecha": fecha_iso,
            "indicador": "IPC_GENERAL_ESP",
            "valor": round(valor, 2),
            "unidad": "tasa_variacion_anual_%",
        }

    except Exception as e:
        log.error("Error INE: %s", e)
        return None


def load_macro(registro: dict) -> None:
    sql = """
        INSERT INTO memo.bronze_macro (fecha, indicador, valor, unidad)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (fecha, indicador) DO UPDATE SET valor = EXCLUDED.valor
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(sql, (
                registro["fecha"], registro["indicador"],
                registro["valor"], registro["unidad"],
            ))
        conn.commit()
        log.info("✓ IPC %s guardado", registro["fecha"])
    finally:
        conn.close()


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida. Abortando.")
        sys.exit(1)

    log.info("=== ETL Divisa + Macro — %s ===", datetime.now().strftime("%Y-%m-%d"))

    bce = extract_bce()
    if bce:
        load_divisa(bce)

    ine = extract_ine()
    if ine:
        load_macro(ine)

    log.info("=== ETL Macro completado ===")
