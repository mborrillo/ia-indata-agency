# SIMIR — Sistema de Inteligencia para Gestión de Inventarios Retail

Proyecto **retail-prueba** dentro de la agencia ia-indata-agency. Spec en [spec.md](spec.md), plan en [PLAN.md](PLAN.md).

## Cómo ejecutar

### Requisitos

- Python 3.11+
- Variable de entorno **NEON_DATABASE_URL** (o **DATABASE_URL**) con la URL de Neon.

### ETL diario

Desde la raíz del repo o desde esta carpeta:

```bash
# Opción 1: desde raíz del repo
export NEON_DATABASE_URL="postgresql://..."
python projects/retail-prueba/etl/run_daily.py

# Opción 2: desde projects/retail-prueba
cd projects/retail-prueba
pip install -r requirements.txt
export NEON_DATABASE_URL="postgresql://..."
python -m etl.run_daily
```

El pipeline: aplica DDL (`sql/01_schemas.sql` … `04_gold_views.sql`), carga Bronze desde `data/*.csv`, transforma a Silver. Las vistas Gold se alimentan solas desde Silver.

### App Streamlit

```bash
cd projects/retail-prueba
pip install -r requirements.txt
export NEON_DATABASE_URL="postgresql://..."
streamlit run app.py
```

La app lee solo vistas Gold: `v_rotacion_inventario`, `v_alertas_stock`, `v_oportunidad_venta`.

### Tests

Desde la raíz del repo (usa `pyproject.toml`):

```bash
pip install -r requirements.txt
pip install -r projects/retail-prueba/requirements.txt
pytest
```

## Estructura

- `sql/` — DDL Medallón (esquemas, tablas Bronze/Silver, vistas Gold).
- `etl/` — Carga Bronze, transformación Silver, `run_daily.py`.
- `data/` — CSVs de ejemplo (ventas, stock, precios).
- `app.py` — Streamlit para el gerente de tienda.
- `tests/` — Tests unitarios KPIs e integridad.

## Verificación (spec §5)

- Trazabilidad: métricas de la app provienen de vistas Gold.
- Tests de cálculo: `tests/test_kpis.py` valida fórmulas de rotación y stock crítico.
- Integridad: `tests/test_integrity.py` valida grano Silver sin duplicados.
- Security: sin API keys en código; usar NEON_DATABASE_URL en entorno/secrets.
