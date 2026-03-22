# HOWTO — Crear un proyecto nuevo desde cero (Paso a Paso)

Guía completa paso a paso basada en los proyectos reales de la agencia.
**Tiempo estimado:** 6-10 horas para un proyecto nuevo completo.

---

## Requisitos previos

- Cuenta en [Neon.tech](https://neon.tech) — registro gratuito con GitHub
- Cuenta en [Streamlit Community Cloud](https://share.streamlit.io) — gratuito
- Acceso a este repo en GitHub

---

## Paso 1 — Definir el problema (spec.md)

**Este es el paso más importante. No escribas código sin completarlo.**

1. Copia `_template/spec.md` → `projects/nombre-proyecto/spec.md`
2. Rellena obligatoriamente:
   - **Problema real** — en una frase qué no puede ver el cliente hoy
   - **Meta cuantificada** — reducir X en 15%, aumentar Y en 10%
   - **Fuentes de datos** — nombre, URL, frecuencia, si es gratis
   - **KPIs** — máximo 5, con fórmula exacta en lenguaje del cliente
3. Regla: si no puedes explicar el problema en una frase, no está listo

---

## Paso 2 — Crear el proyecto en Neon

1. Entra a [console.neon.tech](https://console.neon.tech) → **New Project**
2. Nombre sugerido: `memo-[sector]` (ej. `memo-hosteleria`)
3. Copia la **connection string** — la necesitarás en varios pasos
4. En el **SQL Editor** de Neon, ejecuta el contenido de `sql/01_schema_and_gold.sql`
5. Verifica que tablas y vistas se crearon:
   ```sql
   SELECT table_name FROM information_schema.tables
   WHERE table_schema = 'nombre_schema';
   ```

---

## Paso 3 — Crear la estructura en GitHub

Desde el navegador de GitHub, crea estos archivos en `projects/nombre-proyecto/`:

```
projects/nombre-proyecto/
├── spec.md                    ← del Paso 1
├── app.py                     ← adaptar de _template/app.py
├── requirements.txt           ← añadir librerías específicas
├── .env.example               ← listar variables (sin valores reales)
├── .gitignore                 ← copiar de _template/.gitignore
├── etl/
│   ├── run_daily.py           ← orquestador principal
│   ├── backfill.py            ← carga histórica (ver Paso 6)
│   └── ingest_[fuente].py    ← uno por cada fuente de datos
├── sql/
│   └── 01_schema_and_gold.sql ← ya ejecutado en Neon
└── tests/
    └── test_etl.py            ← validaciones de calidad
```

**Regla importante:** nunca subas el `.env` al repo. Siempre en `.gitignore`.

---

## Paso 4 — Configurar el Secret en GitHub

1. En el repo → **Settings → Secrets and variables → Actions → New repository secret**
2. Nombre: `NOMBREPROYECTO_NEON_URL` (ej. `HOSTELERIA_NEON_URL`)
3. Valor: la connection string de Neon del Paso 2

---

## Paso 5 — Crear el workflow de GitHub Actions

1. Copia `_template/backfill.yml.example` → `.github/workflows/nombre-proyecto-daily.yml`
2. Reemplaza los tres placeholders en MAYÚSCULAS:
   - `[NOMBRE PROYECTO]` → nombre descriptivo
   - `[NOMBRE-CARPETA]` → nombre exacto de la carpeta en `projects/`
   - `[NOMBRE_SECRET]` → nombre del secret del Paso 4
3. **Nombra el archivo sin espacios ni caracteres especiales** — esto es importante,
   los nombres con guiones o caracteres especiales causan que GitHub Actions
   no detecte cambios correctamente
4. Haz commit

El workflow se ejecuta automáticamente L-V. Para ejecutarlo manualmente:
**Actions → nombre del workflow → Run workflow**

---

## Paso 6 — Ejecutar el backfill (obligatorio)

El backfill carga el histórico de datos para que el dashboard tenga contexto
desde el primer día. Sin él, los gráficos históricos estarán vacíos.

1. Adapta `etl/backfill.py` del proyecto:
   - Una función `backfill_[fuente](dias)` por cada ETL
   - Patrón: obtener fechas pendientes → extraer → cargar con upsert
   - La función `fechas_pendientes()` ya está en el template — no duplicar

2. Crea `.github/workflows/backfill-nombre-proyecto.yml`:
   ```yaml
   name: Backfill — nombre-proyecto

   on:
     workflow_dispatch:
       inputs:
         dias:
           description: 'Días a cargar'
           default: '20'

   jobs:
     backfill:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         - uses: actions/setup-python@v5
           with:
             python-version: '3.11'
         - run: pip install -r projects/nombre-proyecto/requirements.txt
         - name: Ejecutar backfill
           env:
             NEON_DATABASE_URL: ${{ secrets.NOMBRE_SECRET }}
           run: |
             cd projects/nombre-proyecto
             python etl/backfill.py ${{ github.event.inputs.dias }}
   ```

3. Ejecuta: **Actions → Backfill → Run workflow → 20 días**

4. Verifica en Neon:
   ```sql
   SELECT COUNT(*), MIN(fecha), MAX(fecha) FROM schema.tabla_principal;
   ```

5. Puedes dejar el workflow de backfill para el futuro o borrarlo

---

## Paso 7 — Desplegar en Streamlit

1. Ve a [share.streamlit.io](https://share.streamlit.io) → **New app**
2. Configura:
   - Repositorio: `mborrillo/ia-indata-agency`
   - Branch: `main`
   - Main file: `projects/nombre-proyecto/app.py`
3. En **Advanced settings → Secrets** añade:
   ```
   NEON_DATABASE_URL = "tu_connection_string_de_neon"
   ```
4. Deploy → espera 2-3 minutos

**Si los datos no aparecen después del deploy:** haz Reboot desde el menú
de la app en Streamlit. La conexión a Neon puede necesitar reiniciarse.

---

## Paso 8 — Actualizar CONTEXT.md

Siempre al terminar un proyecto o una sesión de trabajo:

1. Abre `CONTEXT.md` en la raíz del repo
2. Actualiza la fecha y el resumen del cambio
3. Añade el proyecto nuevo a la tabla de proyectos activos
4. Documenta cualquier decisión técnica nueva o error resuelto
5. Commit

**Por qué importa:** el CONTEXT.md es la memoria de la agencia. Cuando
abres una nueva sesión con Claude u otra IA, pegas su contenido y la IA
tiene todo el contexto sin que tengas que reexplicar nada.

---

## Checklist final — no entregar sin esto

- [ ] `spec.md` completado con problema real, KPIs y fuentes
- [ ] SQL ejecutado en Neon — tablas y vistas creadas y verificadas
- [ ] ETL ejecuta en verde en GitHub Actions
- [ ] Backfill ejecutado — mínimo 20 días de histórico en BD
- [ ] `pytest tests/ -v` pasa sin errores
- [ ] Dashboard desplegado — carga en menos de 5 segundos
- [ ] Un usuario sin conocimientos técnicos entiende cada KPI en 5 segundos
- [ ] 0 credenciales en el código ni en el repo
- [ ] `CONTEXT.md` actualizado

---

## Tiempos de referencia

| Tarea | Estimación |
|-------|-----------|
| spec.md | 30-60 min |
| SQL schema + vistas Gold | 45-90 min |
| ETL (fuentes ya conocidas) | 1-2 horas |
| ETL (fuentes nuevas) | 2-4 horas |
| Dashboard Streamlit | 1-2 horas |
| Backfill + verificación | 15-30 min |
| Deploy Streamlit | 10 min |
| **Total (sector conocido)** | **~6 horas** |
| **Total (sector nuevo)** | **~10 horas** |

---

## Problemas frecuentes y soluciones

| Problema | Causa | Solución |
|----------|-------|----------|
| `module not found` en Actions | Paquete no está en `requirements.txt` | Añadirlo y hacer commit |
| Datos no aparecen en dashboard | Conexión Neon caída | Reboot en Streamlit |
| Workflow usa archivos viejos | Caché de pip de GitHub Actions | Actions → Caches → borrar todos |
| `+nan%` en variación | Solo hay 1 día de datos | Ejecutar backfill |
| ETL ejecuta código viejo | Caché del runner | Añadir comentario al `requirements.txt` para cambiar el hash |
| API devuelve error 500/404 | URL de la fuente cambió | Buscar nueva URL o fuente alternativa |
| `NEON_DATABASE_URL` no definida | Secret mal configurado o nombre incorrecto | Verificar nombre exacto en Settings → Secrets |

---

## Proyectos de referencia

Puedes usar estos proyectos como base para nuevos sectores:

| Proyecto | Qué reutilizar |
|----------|---------------|
| `energia-mercados` | PVPC, Yahoo Finance, BCE, IPC — cualquier proyecto que necesite datos macro |
| `energia-mercados-hosteleria` | PVPC + gas + aceite + IPC alimentación — sectores con costes energéticos |
