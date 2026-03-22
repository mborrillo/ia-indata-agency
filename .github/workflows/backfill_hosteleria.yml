"""
backfill_hosteleria.py — Carga histórica MEMO Hostelería
Puebla los últimos N días para tener histórico real desde el primer día.

Uso:
    python backfill_hosteleria.py        # últimos 180 días
    python backfill_hosteleria.py 30     # últimos N días
"""
import os, sys, logging, requests
from datetime import datetime, date, timedelta
from collections import Counter
import yfinance as yf
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")
DIAS   = int(sys.argv[1]) if len(sys.argv) > 1 else 180

REE_URL = "https://api.esios.ree.es/archives/70/download_json?locale=es&date={fecha}"
MESES   = {"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,
           "Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12}

FACTOR_MMBTU_TO_MWH = 0.29307
EUR_USD_APPROX       = 1.15


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def fechas_pendientes(tabla: str, col: str, dias: int) -> list[str]:
    hoy   = date.today()
    todas = [(hoy - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(1, dias+1)]
    try:
        with get_engine().connect() as conn:
            existentes = {r[0][:10] for r in conn.execute(
                text(f"SELECT {col}::text FROM hosteleria.{tabla}"))}
    except Exception:
        existentes = set()
    pendientes = sorted([f for f in todas if f not in existentes])
    log.info("  %s: %d pendientes de %d solicitadas", tabla, len(pendientes), dias)
    return pendientes


# ── PVPC ──────────────────────────────────────────────────────────────────────

def tramo(hora: int, fin_sem: bool) -> str:
    if fin_sem or hora < 8: return "Valle"
    if hora in {10,11,12,13,18,19,20,21}: return "Punta"
    return "Llano"


def backfill_pvpc(dias: int):
    log.info("═══ Backfill PVPC (%d días) ═══", dias)
    fechas = fechas_pendientes("bronze_pvpc", "fecha", dias)
    if not fechas:
        log.info("  Sin fechas pendientes"); return

    registros = []
    for fecha in fechas:
        try:
            r = requests.get(REE_URL.format(fecha=fecha), timeout=15)
            r.raise_for_status()
            pvpc = r.json().get("PVPC", [])
            if not pvpc: continue

            fin_sem = datetime.strptime(fecha, "%Y-%m-%d").weekday() >= 5
            horas = {}
            for i, h in enumerate(pvpc):
                for campo in ("PCB", "TCHA"):
                    if campo in h:
                        try: horas[i] = float(h[campo].replace(",",".")) / 1000; break
                        except ValueError: pass
            if not horas: continue

            precios  = list(horas.values())
            hora_min = min(horas, key=horas.get)
            hora_max = max(horas, key=horas.get)
            registros.append({
                "fecha":         fecha,
                "precio_medio":  round(sum(precios)/len(precios), 5),
                "precio_min":    round(horas[hora_min], 5),
                "hora_min":      hora_min,
                "precio_max":    round(horas[hora_max], 5),
                "hora_max":      hora_max,
                "tramo_mayoria": Counter(tramo(h, fin_sem) for h in horas).most_common(1)[0][0],
                "var_per_prev":  None,
            })
            log.info("  ✓ PVPC %s — %.4f €/kWh", fecha, sum(precios)/len(precios))
        except Exception as e:
            log.error("  ✗ PVPC %s: %s", fecha, e)

    # Calcular var_per_prev entre registros del backfill
    registros.sort(key=lambda x: x["fecha"])
    for i, reg in enumerate(registros):
        if i > 0:
            prev = registros[i-1]["precio_medio"]
            reg["var_per_prev"] = round((reg["precio_medio"] - prev) / prev * 100, 2)

    if registros:
        cols = list(registros[0].keys())
        sql  = f"""
            INSERT INTO hosteleria.bronze_pvpc ({", ".join(cols)})
            VALUES ({", ".join(f":{c}" for c in cols)})
            ON CONFLICT (fecha) DO UPDATE SET
                {", ".join(f"{c}=EXCLUDED.{c}" for c in cols if c != "fecha")}
        """
        with get_engine().begin() as conn:
            conn.execute(text(sql), registros)
        log.info("  ✓ %d registros PVPC cargados", len(registros))


# ── GAS — yfinance ────────────────────────────────────────────────────────────

def backfill_gas(dias: int):
    log.info("═══ Backfill Gas Natural (%d días) ═══", dias)
    fechas = fechas_pendientes("bronze_gas", "fecha", dias)
    if not fechas:
        log.info("  Sin fechas pendientes"); return

    try:
        # yfinance devuelve histórico de varios días de una vez
        hist = yf.Ticker("NG=F").history(period=f"{dias + 10}d")
        if hist.empty:
            log.error("  yfinance NG=F sin datos"); return

        hist = hist.reset_index()
        hist["fecha_str"] = hist["Date"].dt.strftime("%Y-%m-%d")

        registros = []
        for i, row in hist.iterrows():
            fecha = row["fecha_str"]
            if fecha not in fechas:
                continue
            cierre_usd    = float(row["Close"])
            anterior      = float(hist.iloc[i-1]["Close"]) if i > 0 else cierre_usd
            variacion     = (cierre_usd - anterior) / anterior * 100 if anterior else 0
            precio_eur_mwh = (cierre_usd / EUR_USD_APPROX) / FACTOR_MMBTU_TO_MWH

            registros.append({
                "fecha":       fecha,
                "precio_mwh":  round(precio_eur_mwh, 4),
                "var_per_prev": round(variacion, 2),
            })
            log.info("  ✓ Gas %s — %.2f EUR/MWh", fecha, precio_eur_mwh)

        if registros:
            sql = """
                INSERT INTO hosteleria.bronze_gas (fecha, precio_mwh, var_per_prev)
                VALUES (:fecha, :precio_mwh, :var_per_prev)
                ON CONFLICT (fecha) DO UPDATE SET
                    precio_mwh=EXCLUDED.precio_mwh, var_per_prev=EXCLUDED.var_per_prev
            """
            with get_engine().begin() as conn:
                conn.execute(text(sql), registros)
            log.info("  ✓ %d registros Gas cargados", len(registros))

    except Exception as e:
        log.error("  ✗ Gas backfill: %s", e)


# ── ACEITE — precio semanal histórico ────────────────────────────────────────

def backfill_aceite():
    """
    Para el aceite, buscamos el precio semanal de las últimas semanas.
    oleista.com no tiene histórico vía scraping, así que cargamos el
    precio actual como referencia para todas las semanas sin dato.
    Cuando el ETL diario corra, irá actualizando semana a semana.
    """
    log.info("═══ Backfill Aceite AOVE ═══")
    try:
        from bs4 import BeautifulSoup
        import re
        headers = {"User-Agent": "Mozilla/5.0"}

        r = requests.get("https://oleista.com/es/precios/espana",
                         headers=headers, timeout=20)
        r.raise_for_status()
        soup  = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text(" ", strip=True)

        precio = None
        for patron in [r'[Vv]irgen [Ee]xtra[^\d]*(\d+[.,]\d{2,3})',
                        r'AOVE[^\d]*(\d+[.,]\d{2,3})']:
            for m in re.findall(patron, texto):
                p = float(m.replace(",", "."))
                if p > 100: p /= 100
                if 1.5 < p < 15.0:
                    precio = round(p, 4)
                    break
            if precio: break

        if not precio:
            log.warning("  Sin precio AOVE disponible para backfill")
            return

        # Cargar para las últimas 4 semanas (lunes de cada semana)
        hoy = date.today()
        semanas_cargadas = 0
        for w in range(4):
            lunes = (hoy - timedelta(days=hoy.weekday() + w*7)).strftime("%Y-%m-%d")
            try:
                with get_engine().connect() as conn:
                    existe = conn.execute(text(
                        "SELECT 1 FROM hosteleria.bronze_aceite WHERE fecha=:f AND tipo='AOVE'"),
                        {"f": lunes}).fetchone()
                if existe:
                    log.info("  Aceite semana %s ya existe. Saltando.", lunes)
                    continue
                with get_engine().begin() as conn:
                    conn.execute(text("""
                        INSERT INTO hosteleria.bronze_aceite (fecha, tipo, precio_kg, fuente)
                        VALUES (:f, 'AOVE', :p, 'oleista.com_backfill')
                        ON CONFLICT (fecha, tipo) DO NOTHING
                    """), {"f": lunes, "p": precio})
                log.info("  ✓ Aceite semana %s — %.3f €/kg", lunes, precio)
                semanas_cargadas += 1
            except Exception as e:
                log.error("  ✗ Aceite %s: %s", lunes, e)

        log.info("  ✓ %d semanas de aceite cargadas", semanas_cargadas)

    except Exception as e:
        log.error("  ✗ Aceite backfill: %s", e)


# ── IPC — carga histórica últimos meses ───────────────────────────────────────

def backfill_ipc():
    log.info("═══ Backfill IPC (últimos 12 meses) ═══")
    series = {
        "IPC_GENERAL":      "IPC206449",
        "IPC_ALIMENTACION": "IPC206450",
    }
    for indicador, serie_id in series.items():
        url = f"https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/{serie_id}?nult=12"
        try:
            r = requests.get(url, timeout=20,
                             headers={"Accept": "application/json"})
            r.raise_for_status()
            datos = r.json()
            if not datos: continue

            cargados = 0
            for item in datos:
                if not isinstance(item, dict): continue
                valor_raw = item.get("Valor")
                if valor_raw is None: continue
                try:
                    valor = float(str(valor_raw).replace(",", "."))
                except (ValueError, TypeError):
                    continue
                nombre  = item.get("NombrePeriodo","")
                partes  = nombre.strip().split()
                if len(partes) != 2: continue
                mes  = MESES.get(partes[0], 1)
                anio = int(partes[1])
                fecha = f"{anio}-{mes:02d}-01"

                try:
                    with get_engine().connect() as conn:
                        existe = conn.execute(text(
                            "SELECT 1 FROM hosteleria.bronze_ipc "
                            "WHERE fecha=:f AND indicador=:i"),
                            {"f": fecha, "i": indicador}).fetchone()
                    if existe: continue
                    with get_engine().begin() as conn:
                        conn.execute(text("""
                            INSERT INTO hosteleria.bronze_ipc (fecha, indicador, valor, unidad)
                            VALUES (:fecha, :indicador, :valor, 'tasa_variacion_anual_%')
                            ON CONFLICT (fecha, indicador) DO UPDATE SET valor=EXCLUDED.valor
                        """), {"fecha": fecha, "indicador": indicador, "valor": round(valor, 2)})
                    log.info("  ✓ %s %s: %.2f%%", indicador, fecha, valor)
                    cargados += 1
                except Exception as e:
                    log.error("  ✗ %s %s: %s", indicador, fecha, e)

            log.info("  %s: %d registros nuevos", indicador, cargados)
        except Exception as e:
            log.error("  ✗ %s: %s", indicador, e)


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    log.info("════ BACKFILL MEMO Hostelería — últimos %d días ════", DIAS)
    log.info("Fecha inicio: %s",
             (date.today() - timedelta(days=DIAS)).strftime("%Y-%m-%d"))

    backfill_pvpc(DIAS)
    backfill_gas(DIAS)
    backfill_aceite()
    backfill_ipc()

    log.info("════ BACKFILL COMPLETADO ════")
    log.info("Verifica en Neon:")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM hosteleria.bronze_pvpc;")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM hosteleria.bronze_gas;")
    log.info("  SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM hosteleria.bronze_aceite;")
    log.info("  SELECT COUNT(*) FROM hosteleria.bronze_ipc;")
