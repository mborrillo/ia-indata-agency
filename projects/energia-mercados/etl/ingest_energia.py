"""
ETL: Precio Luz PVPC (REE)
Fuente: Red Eléctrica de España — api.esios.ree.es
Destino: Neon → memo.bronze_energia
Frecuencia: Diaria (GitHub Actions, lunes–viernes 08:00 UTC)

Adaptado de agro-tech-es/energia_monitor.py
Cambios: Supabase → psycopg2/Neon, mismo parsing REE probado en producción.
"""
import os
import sys
import logging
import requests
from datetime import datetime, timedelta
from collections import Counter

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
REE_URL = "https://api.esios.ree.es/archives/70/download_json?locale=es&date={fecha}"


def get_conn():
    return psycopg2.connect(DB_URL)


def tramo(hora: int, fin_semana: bool) -> str:
    if fin_semana or hora < 8:
        return "Valle"
    if hora in {10, 11, 12, 13, 18, 19, 20, 21}:
        return "Punta"
    return "Llano"


def extract(fecha: str) -> dict | None:
    """Descarga las 24h de PVPC de REE para la fecha dada."""
    try:
        r = requests.get(REE_URL.format(fecha=fecha), timeout=15)
        r.raise_for_status()
        pvpc = r.json().get("PVPC", [])
        if not pvpc:
            log.warning("REE devolvió PVPC vacío para %s", fecha)
            return None
        return pvpc
    except Exception as e:
        log.error("Error descargando REE: %s", e)
        return None


def transform(pvpc: list, fecha: str) -> dict | None:
    """Parsea las 24h y calcula analítica diaria."""
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
        log.warning("No se pudieron parsear precios para %s", fecha)
        return None

    precios = list(horas.values())
    hora_min = min(horas, key=horas.get)
    hora_max = max(horas, key=horas.get)
    tramo_mayoría = Counter(tramo(h, fin_semana) for h in horas).most_common(1)[0][0]

    log.info(
        "%s — media: %.4f €/kWh | min: %.4f h%d | max: %.4f h%d | tramo: %s",
        fecha, sum(precios)/len(precios),
        horas[hora_min], hora_min,
        horas[hora_max], hora_max,
        tramo_mayoría,
    )

    return {
        "fecha": fecha,
        "precio_medio": round(sum(precios) / len(precios), 5),
        "precio_min":   round(horas[hora_min], 5),
        "hora_min":     hora_min,
        "precio_max":   round(horas[hora_max], 5),
        "hora_max":     hora_max,
        "tramo_mayoria": tramo_mayoría,
    }


def enrich_var_prev(registro: dict) -> dict:
    """Añade variación % respecto al día anterior (dato ya en BD)."""
    fecha_ayer = (
        datetime.strptime(registro["fecha"], "%Y-%m-%d") - timedelta(days=1)
    ).strftime("%Y-%m-%d")
    try:
        conn = get_conn()
        with conn.cursor() as cur:
            cur.execute(
                "SELECT precio_medio FROM memo.bronze_energia WHERE fecha = %s",
                (fecha_ayer,),
            )
            row = cur.fetchone()
        conn.close()
        if row:
            prev = row[0]
            registro["var_per_prev"] = round(
                (registro["precio_medio"] - prev) / prev * 100, 2
            )
            log.info("var_per_prev vs %s: %+.2f%%", fecha_ayer, registro["var_per_prev"])
        else:
            registro["var_per_prev"] = None
            log.warning("Sin dato previo para calcular var_per_prev (%s)", fecha_ayer)
    except Exception as e:
        log.warning("No se pudo calcular var_per_prev: %s", e)
        registro["var_per_prev"] = None
    return registro


def load(registro: dict) -> None:
    """Upsert en memo.bronze_energia (clave única: fecha)."""
    cols = list(registro.keys())
    sql = f"""
        INSERT INTO memo.bronze_energia ({", ".join(cols)})
        VALUES %s
        ON CONFLICT (fecha) DO UPDATE SET
            {", ".join(f"{c} = EXCLUDED.{c}" for c in cols if c != "fecha")}
    """
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            execute_values(cur, sql, [tuple(registro.values())])
        conn.commit()
        log.info("✓ Registro %s guardado en memo.bronze_energia", registro["fecha"])
    finally:
        conn.close()


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida. Abortando.")
        sys.exit(1)

    fecha = datetime.now().strftime("%Y-%m-%d")
    log.info("=== ETL Energía PVPC — %s ===", fecha)

    pvpc = extract(fecha)
    if not pvpc:
        sys.exit(1)

    registro = transform(pvpc, fecha)
    if not registro:
        sys.exit(1)

    registro = enrich_var_prev(registro)
    load(registro)
    log.info("=== ETL Energía completado ===")
