"""
ETL: Precio Aceite de Oliva Virgen Extra (AOVE) España → hosteleria.bronze_aceite
Fuente: MAPA (Ministerio de Agricultura) — informe semanal de precios en origen
URL: https://www.mapa.gob.es/es/agricultura/temas/producciones-agricolas/aceite-oliva/

Estrategia: el MAPA publica los precios semanales del mercado nacional en su web.
Usamos la API del Observatorio de Precios del MAPA cuando está disponible,
y como fallback el precio de referencia del pool de operadores (POOLred via Infaoliva).

Nota: el precio es €/kg en origen España — NO el futuro de aceite de soja de Chicago.
Esta distinción es crítica para que el dato sea útil para un hostelero español.
"""
import os, sys, logging, requests
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL = os.getenv("NEON_DATABASE_URL")

# Fuente 1: API MAPA — Observatorio de precios
MAPA_URL = (
    "https://www.mapa.gob.es/app/vocweb/api/indicadores?"
    "categoria=ACEITE_OLIVA&periodo=SEMANAL&nult=1"
)

# Fuente 2: Infaoliva (fallback) — precios diarios del sector
INFAOLIVA_URL = "https://www.infaoliva.com/cotizaciones"

# Fuente 3: POOLred — sistema oficial del sector oleícola
POOLRED_URL = "https://www.poolred.com/cotizaciones/cotizacion-diaria/"


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def extract_mapa() -> dict | None:
    """Intenta obtener precio del MAPA via API oficial."""
    try:
        r = requests.get(MAPA_URL, timeout=15,
                         headers={"Accept": "application/json"})
        if r.status_code != 200:
            return None
        data = r.json()
        if not data:
            return None
        ultimo = data[0] if isinstance(data, list) else data
        precio = float(ultimo.get("valor", 0) or ultimo.get("precio", 0))
        if precio <= 0:
            return None
        log.info("MAPA API — AOVE: %.3f €/kg", precio)
        return {
            "fecha":    date.today().strftime("%Y-%m-%d"),
            "tipo":     "AOVE",
            "precio_kg": round(precio, 4),
            "fuente":   "MAPA_API",
        }
    except Exception as e:
        log.warning("MAPA API no disponible: %s", e)
        return None


def extract_poolred() -> dict | None:
    """Scraping de POOLred — fuente oficial del sector oleícola español."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(POOLRED_URL, timeout=15, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar precio AOVE en la tabla de cotizaciones
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True).lower()
                if "virgen extra" in label or "aove" in label:
                    precio_txt = cells[1].get_text(strip=True)
                    precio_txt = precio_txt.replace(",", ".").replace("€", "").strip()
                    try:
                        precio = float(precio_txt)
                        if 2.0 < precio < 12.0:  # rango razonable €/kg
                            log.info("POOLred — AOVE: %.3f €/kg", precio)
                            return {
                                "fecha":     date.today().strftime("%Y-%m-%d"),
                                "tipo":      "AOVE",
                                "precio_kg": round(precio, 4),
                                "fuente":    "POOLred",
                            }
                    except ValueError:
                        continue
        return None
    except Exception as e:
        log.warning("POOLred no disponible: %s", e)
        return None


def extract_infaoliva() -> dict | None:
    """Scraping de Infaoliva como último fallback."""
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        r = requests.get(INFAOLIVA_URL, timeout=15, headers=headers)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar el precio AOVE en la página
        for elem in soup.find_all(["td", "span", "div"]):
            txt = elem.get_text(strip=True).replace(",", ".")
            if "virgen extra" in txt.lower():
                # Buscar el número más cercano que sea un precio razonable
                import re
                nums = re.findall(r'\d+\.\d{2,3}', txt)
                for n in nums:
                    precio = float(n)
                    if 2.0 < precio < 12.0:
                        log.info("Infaoliva — AOVE: %.3f €/kg", precio)
                        return {
                            "fecha":     date.today().strftime("%Y-%m-%d"),
                            "tipo":      "AOVE",
                            "precio_kg": round(precio, 4),
                            "fuente":    "Infaoliva",
                        }
        return None
    except Exception as e:
        log.warning("Infaoliva no disponible: %s", e)
        return None


def already_loaded(fecha: str) -> bool:
    """Evita duplicar si ya tenemos dato esta semana."""
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT 1 FROM hosteleria.bronze_aceite WHERE fecha=:f AND tipo='AOVE'"),
                {"f": fecha}
            ).fetchone()
        return row is not None
    except Exception:
        return False


def load(reg: dict):
    sql = """
        INSERT INTO hosteleria.bronze_aceite (fecha, tipo, precio_kg, fuente)
        VALUES (:fecha, :tipo, :precio_kg, :fuente)
        ON CONFLICT (fecha, tipo) DO UPDATE SET
            precio_kg = EXCLUDED.precio_kg,
            fuente    = EXCLUDED.fuente
    """
    with get_engine().begin() as conn:
        conn.execute(text(sql), reg)
    log.info("✓ Aceite AOVE %s — %.3f €/kg (%s)",
             reg["fecha"], reg["precio_kg"], reg["fuente"])


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    fecha = date.today().strftime("%Y-%m-%d")

    # Solo ejecutar una vez por semana (lunes) para datos semanales
    if date.today().weekday() != 0:
        log.info("Aceite: solo se actualiza los lunes (datos semanales)")
        # Aun así cargamos si no hay dato de esta semana
        lunes = (date.today() - timedelta(days=date.today().weekday())).strftime("%Y-%m-%d")
        if already_loaded(lunes):
            log.info("Ya hay dato de aceite para esta semana. Saltando.")
            sys.exit(0)
        fecha = lunes

    if already_loaded(fecha):
        log.info("Ya hay dato de aceite para %s. Saltando.", fecha)
        sys.exit(0)

    # Intentar fuentes en cascada
    reg = extract_mapa() or extract_poolred() or extract_infaoliva()

    if not reg:
        log.error("No se pudo obtener precio del aceite de ninguna fuente")
        sys.exit(1)

    reg["fecha"] = fecha
    load(reg)
