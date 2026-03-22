"""
ETL: Precio Luz PVPC (REE) → hosteleria.bronze_pvpc
Mismo parsing que MEMO genérico, distinto schema y tabla destino.
"""
import os, sys, logging, requests
from datetime import datetime, timedelta
from collections import Counter
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL  = os.getenv("NEON_DATABASE_URL")
REE_URL = "https://api.esios.ree.es/archives/70/download_json?locale=es&date={fecha}"


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def tramo(hora: int, fin_semana: bool) -> str:
    if fin_semana or hora < 8: return "Valle"
    if hora in {10,11,12,13,18,19,20,21}: return "Punta"
    return "Llano"


def extract(fecha: str) -> list | None:
    try:
        r = requests.get(REE_URL.format(fecha=fecha), timeout=15)
        r.raise_for_status()
        pvpc = r.json().get("PVPC", [])
        return pvpc if pvpc else None
    except Exception as e:
        log.error("REE: %s", e); return None


def transform(pvpc: list, fecha: str) -> dict | None:
    fin_sem = datetime.strptime(fecha, "%Y-%m-%d").weekday() >= 5
    horas = {}
    for i, h in enumerate(pvpc):
        for campo in ("PCB", "TCHA"):
            if campo in h:
                try: horas[i] = float(h[campo].replace(",", ".")) / 1000; break
                except ValueError: pass
    if not horas: return None
    precios  = list(horas.values())
    hora_min = min(horas, key=horas.get)
    hora_max = max(horas, key=horas.get)
    log.info("PVPC %s — media: %.4f | min h%d | max h%d", fecha,
             sum(precios)/len(precios), hora_min, hora_max)
    return {
        "fecha":         fecha,
        "precio_medio":  round(sum(precios)/len(precios), 5),
        "precio_min":    round(horas[hora_min], 5),
        "hora_min":      hora_min,
        "precio_max":    round(horas[hora_max], 5),
        "hora_max":      hora_max,
        "tramo_mayoria": Counter(tramo(h, fin_sem) for h in horas).most_common(1)[0][0],
    }


def enrich_var(reg: dict) -> dict:
    fecha_ayer = (datetime.strptime(reg["fecha"], "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT precio_medio FROM hosteleria.bronze_pvpc WHERE fecha=:f"), {"f": fecha_ayer}
            ).fetchone()
        if row:
            reg["var_per_prev"] = round((reg["precio_medio"] - row[0]) / row[0] * 100, 2)
        else:
            reg["var_per_prev"] = None
    except Exception:
        reg["var_per_prev"] = None
    return reg


def load(reg: dict):
    cols = list(reg.keys())
    sql  = f"""
        INSERT INTO hosteleria.bronze_pvpc ({", ".join(cols)})
        VALUES ({", ".join(f":{c}" for c in cols)})
        ON CONFLICT (fecha) DO UPDATE SET
            {", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c != "fecha")}
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ PVPC %s guardado", reg["fecha"])


if __name__ == "__main__":
    if not DB_URL: log.error("NEON_DATABASE_URL no definida"); sys.exit(1)
    fecha = datetime.now().strftime("%Y-%m-%d")
    pvpc  = extract(fecha)
    if not pvpc: sys.exit(1)
    reg   = transform(pvpc, fecha)
    if not reg: sys.exit(1)
    reg   = enrich_var(reg)
    load(reg)
