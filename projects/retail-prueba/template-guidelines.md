# template-guidelines.md – Reglas fijas para todos los proyectos de la agencia

Estas reglas se aplican siempre para que Cursor/IA genere código consistente, sin KeyError comunes ni configuraciones raras.

## 1. Nombres de columnas obligatorios en vistas Gold (retail_gold.*)
- v_rotacion_inventario: debe tener al menos estas columnas
  - producto_id (text)
  - tienda_id (text)
  - total_unidades_vendidas (numeric)
  - stock_promedio (numeric)
  - indice_rotacion (numeric)  ← usada en métrica principal

- v_alertas_stock: debe tener al menos
  - producto_id (text)
  - tienda_id (text)
  - stock_actual (numeric)
  - venta_media_7d (numeric)
  - dias_de_stock (numeric)
  - es_stock_critico (boolean)  ← True/False para contar críticos

- v_oportunidad_venta: debe tener al menos
  - producto_id (text)
  - tienda_id (text)
  - fecha (date)
  - precio_local (numeric)
  - tendencia_local_7d (numeric)
  - diff_vs_tendencia (numeric)
  - pct_vs_tendencia (numeric)  ← usada para detectar oportunidades (>0)

Si la vista no tiene estas columnas → la app mostrará "Sin datos" en lugar de fallar con KeyError.

## 2. Estructura de carpetas obligatoria (siempre igual)
projects/<nombre-proyecto>/
├── app.py                     # Dashboard Streamlit (siempre este nombre)
├── requirements.txt           # Dependencias pinned cuando sea posible
├── .env.example               # Plantilla conexión Neon
├── etl/
│   ├── run_daily.py           # Orquestador principal
│   ├── config.py
│   ├── db.py
│   ├── load_bronze.py
│   └── silver.py
├── sql/
│   ├── 01_schemas.sql
│   ├── 02_bronze_tables.sql
│   ├── 03_silver_tables.sql
│   └── 04_gold_views.sql
├── data/                      # CSVs de ejemplo (subir siempre al repo)
└── tests/
    ├── test_kpis.py
    └── test_integrity.py

## 3. Buenas prácticas obligatorias en el código generado
- Usar python-dotenv + os.getenv("NEON_DATABASE_URL")
- Logging básico con logging.basicConfig (nivel INFO, formato con fecha)
- @st.cache_data(ttl=300) en funciones que leen DB
- try/except + logger.error + st.error en lecturas DB
- Nunca hardcodear credenciales
- Si vista Gold vacía → mostrar st.info("Vista vacía, ejecuta ETL") y fallback a datos fake si es posible
- Columnas de KPIs: usar exactamente los nombres de arriba (indice_rotacion, es_stock_critico, pct_vs_tendencia)

## 4. Workflow GitHub Actions
- Siempre .github/workflows/run_daily.yml
- Instalar requirements.txt
- Ejecutar python projects/<nombre>/etl/run_daily.py
- Usar secret NEON_DATABASE_URL

Última actualización: 17 marzo 2026
