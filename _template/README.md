# Punto de partida para cada proyecto nuevo (_template/)

## Cómo usar este template
1. Copia toda esta carpeta → pégala en `projects/nombre-cliente/`
2. Edita `spec.md` con los datos reales del cliente
3. Crea un proyecto nuevo en Neon.tech (1 click, gratis)
4. Copia `.env.example` → `.env` (NUNCA subir el .env al repo)
5. Adapta los scripts en `etl/` a las fuentes del cliente
6. Despliega `app.py` en Streamlit Community Cloud

## Estructura
```
_template/
├── spec.md              ← Definición del proyecto (rellenar)
├── app.py               ← Dashboard Streamlit base
├── requirements.txt     ← Dependencias base
├── .env.example         ← Variables requeridas (sin valores)
├── .gitignore           ← Protección de credenciales
├── etl/
│   └── ingest_base.py   ← Script ETL adaptable
├── sql/
│   ├── 01_bronze.sql    ← Tablas de ingesta
│   ├── 02_silver.sql    ← Limpieza y estandarización
│   └── 03_gold_views.sql← Vistas para el dashboard
└── tests/
    └── test_etl.py      ← Validaciones básicas
```
