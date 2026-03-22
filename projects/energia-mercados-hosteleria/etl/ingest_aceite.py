"""
ETL: Precio Aceite de Oliva Virgen Extra (AOVE) España → hosteleria.bronze_aceite
Fuentes en cascada (de más a menos fiable):
  1. oleista.com — agrega datos de fuentes públicas, actualización diaria
  2. precioaceitedeoliva.net — datos de Infaoliva y Junta de Andalucía
  3. MAPA API observable — datos oficiales semanales del Ministerio

Precio: €/kg en origen España (NO futuros de soja de Chicago)
Frecuencia: semanal (se ejecuta todos los días pero solo carga si hay dato nuevo)
"""
import os, sys, logging, re, requests
from datetime import datetime, date, timedelta
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from bs4 import BeautifulSoup

load_dotenv()
logging.basicConfig(level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
log = logging.getLogger(__name__)

DB_URL  = os.getenv("NEON_DATABASE_URL")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-ES,es;q=0.9",
}

PRECIO_MIN, PRECIO_MAX = 1.5, 15.0  # €/kg rango válido AOVE


def get_engine():
    return create_engine(DB_URL, pool_pre_ping=True, pool_recycle=300,
                         connect_args={"connect_timeout": 10})


def precio_valido(p: float) -> bool:
    return PRECIO_MIN < p < PRECIO_MAX


def extract_oleista() -> dict | None:
    """
    oleista.com agrega datos de Infaoliva, Junta de Andalucía y MAPA.
    Actualiza diariamente con datos de mercado en origen.
    """
    try:
        r = requests.get("https://oleista.com/es/precios/espana",
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Buscar precio AOVE — oleista muestra tabla con categorías
        texto = soup.get_text(" ", strip=True)

        # Patrones de precio en €/kg o €/100kg
        # "Virgen Extra" seguido de precio
        patrones = [
            r'[Vv]irgen [Ee]xtra[^\d]*(\d+[.,]\d{2,3})',
            r'AOVE[^\d]*(\d+[.,]\d{2,3})',
            r'(\d+[.,]\d{2,3})\s*€/kg',
        ]
        for patron in patrones:
            matches = re.findall(patron, texto)
            for m in matches:
                precio = float(m.replace(",", "."))
                # Si viene en €/100kg, convertir
                if precio > 100:
                    precio = precio / 100
                if precio_valido(precio):
                    log.info("oleista.com — AOVE: %.3f €/kg", precio)
                    return {
                        "tipo":     "AOVE",
                        "precio_kg": round(precio, 4),
                        "fuente":   "oleista.com",
                    }
        return None
    except Exception as e:
        log.warning("oleista.com no disponible: %s", e)
        return None


def extract_precioaceitedeoliva() -> dict | None:
    """
    precioaceitedeoliva.net — datos de Infaoliva y Junta de Andalucía.
    """
    try:
        r = requests.get("https://precioaceitedeoliva.net/",
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text(" ", strip=True)

        # Buscar precio virgen extra
        patrones = [
            r'[Vv]irgen [Ee]xtra[^\d]{0,30}(\d+[.,]\d{2,3})',
            r'(\d+[.,]\d{2,3})\s*€/(?:kg|Kg)',
        ]
        for patron in patrones:
            matches = re.findall(patron, texto[:3000])  # solo primeros 3000 chars
            for m in matches:
                precio = float(m.replace(",", "."))
                if precio > 100:
                    precio = precio / 100
                if precio_valido(precio):
                    log.info("precioaceitedeoliva.net — AOVE: %.3f €/kg", precio)
                    return {
                        "tipo":     "AOVE",
                        "precio_kg": round(precio, 4),
                        "fuente":   "precioaceitedeoliva.net",
                    }
        return None
    except Exception as e:
        log.warning("precioaceitedeoliva.net no disponible: %s", e)
        return None


def extract_infaoliva_home() -> dict | None:
    """
    Infaoliva homepage — muestra precios diarios actualizados.
    URL correcta: https://www.infaoliva.com/ (no /cotizaciones)
    """
    try:
        r = requests.get("https://www.infaoliva.com/",
                         headers=HEADERS, timeout=20)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")
        texto = soup.get_text(" ", strip=True)

        patrones = [
            r'[Vv]irgen [Ee]xtra[^\d]{0,50}(\d+[.,]\d{2,3})',
            r'AOVE[^\d]{0,30}(\d+[.,]\d{2,3})',
        ]
        for patron in patrones:
            matches = re.findall(patron, texto[:5000])
            for m in matches:
                precio = float(m.replace(",", "."))
                if precio > 100:
                    precio = precio / 100
                if precio_valido(precio):
                    log.info("infaoliva.com — AOVE: %.3f €/kg", precio)
                    return {
                        "tipo":     "AOVE",
                        "precio_kg": round(precio, 4),
                        "fuente":   "infaoliva.com",
                    }
        return None
    except Exception as e:
        log.warning("infaoliva.com no disponible: %s", e)
        return None


def already_loaded(fecha: str) -> bool:
    try:
        with get_engine().connect() as conn:
            row = conn.execute(text(
                "SELECT 1 FROM hosteleria.bronze_aceite "
                "WHERE fecha=:f AND tipo='AOVE'"), {"f": fecha}
            ).fetchone()
        return row is not None
    except Exception:
        return False


def load(reg: dict, fecha: str):
    reg["fecha"] = fecha
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
             fecha, reg["precio_kg"], reg["fuente"])


if __name__ == "__main__":
    if not DB_URL:
        log.error("NEON_DATABASE_URL no definida"); sys.exit(1)

    # Obtener el lunes de esta semana (datos son semanales)
    hoy   = date.today()
    lunes = (hoy - timedelta(days=hoy.weekday())).strftime("%Y-%m-%d")

    if already_loaded(lunes):
        log.info("Aceite AOVE ya cargado para semana del %s. Saltando.", lunes)
        sys.exit(0)

    log.info("=== ETL Aceite AOVE — semana del %s ===", lunes)

    # Intentar fuentes en cascada
    reg = (extract_oleista() or
           extract_precioaceitedeoliva() or
           extract_infaoliva_home())

    if not reg:
        log.error("Sin datos de aceite en ninguna fuente disponible")
        sys.exit(1)

    load(reg, lunes)
