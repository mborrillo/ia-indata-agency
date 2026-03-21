"""
backfill.py — Carga histórica de los últimos 30 días
Ejecutar UNA VEZ manualmente para poblar el histórico.

Uso:
    python backfill.py           # últimos 30 días
    python backfill.py 30        # últimos N días
"""
import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from collections import Counter

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
DIAS   = int(sys.argv[1]) if len(sys.argv) > 1 else 30


def get_conn():
    return psycopg2.connect(DB_URL)


# ── Helpers ───────────────────────────────────────────────────────────────────

def fechas_a_cargar(tabla: str, col_fecha: str, dias: int) -> list[str]:
    """Devuelve solo las fechas que NO están ya en la BD (evita duplicados)."""
    hoy = datetime.now().date()
    todas = [(hoy - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, dias + 1)]
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(f"SELECT {col_fecha}::text FROM {tabla}")
            existentes = {r[0][:10] for r in cur.fetchall()}
    except Exception:
        existentes = set()
    finally:
        conn.close()
    pendientes = [f for f in todas if f not in existentes]
    log.info("  %s: %d fechas pendientes de %d solicitadas", tabla, len(pendientes), dias)
    return sorted(pendientes)


# ── Energía PVPC (REE) ────────────────────────────────────────────────────────

def tramo(hora: int, fin_semana: bool) -> str:
    if fin_semana or hora < 8: return "Valle"
    if hora in {10,11,12,13,18,19,20,21}: return "Punta"
    return "Llano"


def backfill_energia(dias: int):
    log.info("═══ Backfill Energía PVPC (%d días) ═══", dias)
    fechas = fechas_a_cargar("memo.bronze_energia", "fecha", dias)
    if not fechas:
        log.info("  Sin fechas pendientes.")
        return

    registros = []
    for fecha in fechas:
        try:
            r = requests.get(
                f"https://api.esios.ree.es/archives/70/download_json?locale=es&date={fecha}",
                timeout=15
            )
            r.raise_for_status()
            pvpc = r.json().get("PVPC", [])
            if not pvpc:
                log.warning("  REE sin datos para %s", fecha)
                continue

            fin_semana = datetime.strptime(fecha, "%Y-%m-%d").weekday() >= 5
            horas = {}
            for i, h in enumerate(pvpc):
                for campo in ("PCB", "TCHA"):
                    if campo in h:
                        try:
                            horas[i] = float(h[campo].replace(",", ".")) / 1000
                            break
                        except ValueError:
                            pass

            if not horas:
                continue

            precios = list(horas.values())
            hora_min = min(horas, key=horas.get)
            hora_max = max(horas, key=horas.get)
            tramo_m  = Counter(tramo(h, fin_semana) for h in horas).most_common(1)[0][0]

            registros.append({
                "fecha":         fecha,
                "precio_medio":  round(sum(precios) / len(precios), 5),
                "precio_min":    round(horas[hora_min], 5),
                "hora_min":      hora_min,
                "precio_max":    round(horas[hora_max], 5),
                "hora_max":      hora_max,
                "tramo_mayoria": tramo_m,
                "var_per_prev":  None,  # se recalcula abajo
            })
            log.info("  ✓ Energía %s — media: %.4f €/kWh", fecha, sum(precios)/len(precios))

        except Exception as e:
            log.error("  ✗ Energía %s: %s", fecha, e)

    # Calcular var_per_prev entre registros del backfill
    registros.sort(key=lambda x: x["fecha"])
    for i, reg in enumerate(registros):
        if i > 0:
            prev = registros[i-1]["precio_medio"]
            reg["var_per_prev"] = round((reg["precio_medio"] - prev) / prev * 100, 2)

    if registros:
        cols = list(registros[0].keys())
        sql  = f"""
            INSERT INTO memo.bronze_energia ({", ".join(cols)})
            VALUES %s
            ON CONFLICT (fecha) DO UPDATE SET
                {", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "fecha")}
        """
        conn = get_conn()
        try:
            with conn.cursor() as cur:
                execute_values(cur, sql, [tuple(r.values()) for r in registros])
            conn.commit()
            log.info("  ✓ %d registros de energía cargados", len(registros))
        finally:
            conn.close()


# ── Mercados (Yahoo Finance) ──────────────────────────────────────────────────

ACTIVOS = {
    "Gas_Natural":  {"ticker": "NG=F",     "cat": "Energia"},
    "Brent":        {"ticker": "BZ=F",     "cat": "Energia"},
    "Cobre":        {"ticker": "HG=F",     "cat": "Industrial"},
    "Aluminio":     {"ticker": "ALI=F",    "cat": "Industrial"},
    "Trigo":        {"ticker": "ZW=F",     "cat": "Alimentacion"},
    "Maiz":         {"ticker": "ZC=F",     "cat": "Alimentacion"},
    "Aceite_Soja":  {"ticker": "ZL=F",     "cat": "Alimentacion"},
    "SP500":        {"ticker": "^GSPC",    "cat": "Indice"},
    "IBEX35":       {"ticker": "^IBEX",    "cat": "Indice"},
    "EuroStoxx50":  {"ticker": "^STOXX50E","cat": "Indice"},
    "EUR_USD":      {"ticker": "EURUSD=X", "cat": "Divisa"},
}


def backfill_mercados(dias: int):
    log.info("═══ Backfill Mercados Yahoo Finance (%d días) ═══", dias)

    # Pedir más días de los necesarios para cubrir fines de semana
    period = f"{dias + 10}d"
    registros = []

    for nombre, info in ACTIVOS.items():
        try:
            hist = yf.Ticker(info["ticker"]).history(period=period)
            if hist.empty:
                log.warning("  Sin datos para %s", nombre)
                continue

            hist = hist.reset_index()
            hist["Date"] = hist["Date"].dt.strftime("%Y-%m-%d")

            for i, row in hist.iterrows():
                if i == 0:
                    continue  # necesitamos fila anterior para variación
                cierre   = float(row["Close"])
                anterior = float(hist.iloc[i-1]["Close"])
                if cierre <= 0 or (anterior > 0 and cierre / anterior < 0.2):
                    continue
                variacion = (cierre - anterior) / anterior * 100
                registros.append({
                    "fecha":         row["Date"],
                    "activo":        nombre,
                    "precio_cierre": round(cierre, 4),
                    "variacion_p":   round(variacion, 2),
                    "categoria":     info["cat"],
                    "moneda":        "EUR" if "IBEX" in info["ticker"] or "STOXX" in info["ticker"] else "USD",
                })

            log.info("  ✓ %-14s  %d días cargados", nombre, len(hist) - 1)

        except Exception as e:
            log.error("  ✗ %s: %s", nombre, e)

    if registros:
        cols = list(registros[0].keys())
        sql  = f"""
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
            log.info("  ✓ %d registros de mercados cargados", len(registros))
        finally:
            conn.close()


# ── Divisa EUR/USD (BCE) ──────────────────────────────────────────────────────

def backfill_divisa(dias: int):
    log.info("═══ Backfill EUR/USD BCE (%d días) ═══", dias)
    hoy  = datetime.now().date()
    ini  = (hoy - timedelta(days=dias + 5)).strftime("%Y-%m-%d")
    fin  = hoy.strftime("%Y-%m-%d")

    url = (
        f"https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
        f"?format=jsondata&startPeriod={ini}&endPeriod={fin}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        data   = r.json()
        obs    = data["dataSets"][0]["series"]["0:0:0:0:0"]["observations"]
        fechas = data["structure"]["dimensions"]["observation"][0]["values"]

        registros = []
        for k, v in obs.items():
            tasa = v[0]
            if tasa is None:
                continue
            fecha_str = fechas[int(k)]["id"]
            registros.append(("BCE_EURUSD", fecha_str, "EUR/USD", round(float(tasa), 4)))
            log.info("  ✓ EUR/USD %s: %.4f", fecha_str, tasa)

        if registros:
            sql = """
                -- eliminado
                VALUES %s
                ON CONFLICT (fecha, par) DO UPDATE SET tasa = EXCLUDED.tasa
            """
            # Simplificado: usar columnas correctas
            sql = """
                INSERT INTO memo.bronze_divisa (fecha, par, tasa)
                VALUES %s
                ON CONFLICT (fecha, par) DO UPDATE SET tasa = EXCLUDED.tasa
            """
            conn = get_conn()
            try:
                rows = [(r[1], r[2], r[3]) for r in registros]
                with conn.cursor() as cur:
                    execute_values(cur, sql, rows)
                conn.commit()
                log.info("  ✓ %d registros de EUR/USD cargados", len(rows))
            finally:
                conn.close()

    except Exception as e:
        log.error("  ✗ BCE: %s", e)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida. Abortando.")
        sys.exit(1)

    log.info("════ BACKFILL MEMO — últimos %d días ════", DIAS)
    log.info("Fecha inicio: %s", (datetime.now() - timedelta(days=DIAS)).strftime("%Y-%m-%d"))

    backfill_energia(DIAS)
    backfill_mercados(DIAS)
    backfill_divisa(DIAS)

    log.info("════ BACKFILL COMPLETADO ════")
    log.info("Verifica en Neon:")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM memo.bronze_energia;")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM memo.bronze_mercados;")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM memo.bronze_divisa;")
