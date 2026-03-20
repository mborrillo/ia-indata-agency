"""
ETL: Mercados Financieros (Yahoo Finance)
Fuente: yfinance — futuros, índices y divisas
Destino: Neon → memo.bronze_mercados
Frecuencia: Diaria (lunes–viernes, mercados cerrados fin de semana)

Adaptado de agro-tech-es/mercado_monitor.py
Cambios: Supabase → Neon, tickers ampliados (sector transversal),
filtro de robustez conservado (detecta errores de vencimiento de futuros).
"""
import os
import sys
import logging
from datetime import datetime

import yfinance as yf
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

# Tickers agrupados por categoría — transversal a cualquier sector
ACTIVOS = {
    # Energía (coste directo para cualquier empresa)
    "Gas_Natural":   {"ticker": "NG=F",    "cat": "Energia"},
    "Brent":         {"ticker": "BZ=F",    "cat": "Energia"},
    "Carbon":        {"ticker": "MTF=F",   "cat": "Energia"},
    # Materias primas industriales
    "Cobre":         {"ticker": "HG=F",    "cat": "Industrial"},
    "Aluminio":      {"ticker": "ALI=F",   "cat": "Industrial"},
    # Alimentación (hostelería, retail alimentario)
    "Trigo":         {"ticker": "ZW=F",    "cat": "Alimentacion"},
    "Maiz":          {"ticker": "ZC=F",    "cat": "Alimentacion"},
    "Aceite_Soja":   {"ticker": "ZL=F",    "cat": "Alimentacion"},
    # Índices de referencia
    "SP500":         {"ticker": "^GSPC",   "cat": "Indice"},
    "IBEX35":        {"ticker": "^IBEX",   "cat": "Indice"},
    "EuroStoxx50":   {"ticker": "^STOXX50E","cat": "Indice"},
    # Divisa (redundante con BCE pero útil para contraste)
    "EUR_USD":       {"ticker": "EURUSD=X", "cat": "Divisa"},
}


def get_conn():
    return psycopg2.connect(DB_URL)


def extract_and_transform(fecha: str) -> list[dict]:
    """Descarga los últimos 5 días y extrae cierre + variación."""
    registros = []
    for nombre, info in ACTIVOS.items():
        try:
            hist = yf.Ticker(info["ticker"]).history(period="5d")
            if hist.empty or len(hist) < 2:
                log.warning("Sin datos suficientes para %s", nombre)
                continue

            cierre = float(hist["Close"].iloc[-1])
            anterior = float(hist["Close"].iloc[-2])

            # Filtro de robustez (vencimiento de futuros o error de ticker)
            if cierre <= 0 or (anterior > 0 and cierre / anterior < 0.2):
                log.warning("Anomalía de precio en %s (%.4f). Omitiendo.", nombre, cierre)
                continue

            variacion = (cierre - anterior) / anterior * 100
            registros.append({
                "fecha":         fecha,
                "activo":        nombre,
                "precio_cierre": round(cierre, 4),
                "variacion_p":   round(variacion, 2),
                "categoria":     info["cat"],
                "moneda":        "EUR" if "IBEX" in info["ticker"] or "STOXX" in info["ticker"] else "USD",
            })
            log.info("  ✓ %-14s  %10.4f  %+.2f%%", nombre, cierre, variacion)

        except Exception as e:
            log.error("Error en %s: %s", nombre, e)

    return registros


def load(registros: list[dict]) -> None:
    """Upsert en memo.bronze_mercados (clave: fecha + activo)."""
    if not registros:
        log.warning("Sin registros válidos para cargar.")
        return

    cols = list(registros[0].keys())
    sql = f"""
        INSERT INTO memo.bronze_mercados ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (fecha, activo) DO UPDATE SET
            {", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c not in ("fecha","activo"))}
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, [tuple(r.values()) for r in registros])
        conn.commit()
        log.info("✓ %d activos guardados en memo.bronze_mercados", len(registros))
    finally:
        conn.close()


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida. Abortando.")
        sys.exit(1)

    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info("=== ETL Mercados Financieros — %s ===", fecha)

    registros = extract_and_transform(fecha)
    load(registros)
    log.info("=== ETL Mercados completado (%d activos) ===", len(registros))
