# _template — Punto de partida para cada proyecto nuevo

## Cómo usar este template

1. Copia toda esta carpeta → pégala en `projects/nombre-cliente/`
2. Edita `spec.md` con los datos reales del cliente
3. Crea un proyecto nuevo en [Neon.tech](https://neon.tech) → copia la connection string
4. Copia `.env.example` → `.env` y añade credenciales (NUNCA subir el `.env` al repo)
5. Adapta los scripts en `etl/` a las fuentes del cliente
6. **Ejecuta el backfill** para tener histórico desde el primer día (ver abajo)
7. Despliega `app.py` en [Streamlit Community Cloud](https://share.streamlit.io)

---

## Estructura

```
_template/
├── spec.md                    ← Definición del proyecto (rellenar antes de escribir código)
├── app.py                     ← Dashboard Streamlit base
├── requirements.txt           ← Dependencias (añadir las específicas del proyecto)
├── .env.example               ← Variables requeridas (sin valores reales)
├── .gitignore                 ← Protección de credenciales y datos
├── backfill.yml.example       ← Workflow de backfill (copiar a .github/workflows/)
├── etl/
│   ├── backfill.py            ← Carga histórica — ejecutar UNA VEZ al iniciar
│   └── ingest_base.py         ← Script ETL adaptable por fuente de datos
├── sql/
│   ├── 01_bronze.sql          ← Tablas de ingesta cruda
│   ├── 02_silver.sql          ← Limpieza y estandarización
│   └── 03_gold_views.sql      ← Vistas para el dashboard
└── tests/
    └── test_etl.py            ← Validaciones básicas de calidad de datos
```

---

## Backfill — obligatorio en todo proyecto nuevo

El backfill carga el histórico de datos desde el primer día del proyecto.
Sin él, el dashboard arranca sin contexto y los gráficos históricos están vacíos.

### Pasos

**1.** Adapta `etl/backfill.py`:
- Añade una función `backfill_[fuente](dias)` por cada ETL del proyecto
- Sigue el patrón: obtener fechas pendientes → extraer → cargar con upsert

**2.** Copia `backfill.yml.example` → `.github/workflows/backfill_[proyecto].yml`
- Reemplaza `[NOMBRE-CARPETA]` y `[NOMBRE_SECRET]` con los valores reales

**3.** Haz commit y ejecuta desde GitHub Actions:
- Actions → "Backfill — [proyecto]" → **Run workflow** → introduce el número de días

**4.** Verifica en Neon que las tablas tienen datos:
```sql
SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM schema.tabla_principal;
```

**5.** Borra o desactiva el workflow de backfill cuando ya no lo necesites.

---

## Stack oficial

| Capa | Herramienta | Plan |
|------|-------------|------|
| Base de datos | Neon.tech | Free (proyectos ilimitados) |
| ETL + CI/CD | GitHub Actions | Free |
| Dashboard | Streamlit Community Cloud | Free |
| Alertas | n8n cloud | Free tier |

---

## Checklist antes de entregar

- [ ] `spec.md` completado con KPIs y fuentes reales
- [ ] SQL ejecutado en Neon (schema + tablas + vistas Gold)
- [ ] ETL ejecuta sin errores en GitHub Actions
- [ ] Backfill ejecutado — tablas con al menos 20 días de histórico
- [ ] Tests pasan: `pytest tests/ -v`
- [ ] Dashboard desplegado en Streamlit
- [ ] 0 credenciales en el código o en el repo
