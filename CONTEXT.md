# CONTEXT.md — Estado de la Agencia ia-indata

> **Memoria persistente de la agencia.** Actualiza este archivo al terminar
> cada sesión de trabajo. Pégalo al inicio de cualquier conversación con
> Claude, Gemini u otra IA para que tenga contexto completo sin reexplicar nada.

---

## Última actualización
**Fecha:** 2026-03-23
**Cambios:** Proyecto hostelería en producción. Backfill estándar añadido
al template. HOWTO.md creado. retail-prueba eliminado del repo.

---

## Stack oficial (no cambiar sin razón justificada)

| Capa | Herramienta | Notas |
|------|-------------|-------|
| Base de datos | Neon.tech (PostgreSQL) | Proyectos ilimitados en free |
| ETL + CI/CD | GitHub Actions | Schedule L-V |
| Dashboard | Streamlit Community Cloud | Gratis, deploy desde GitHub |
| Alertas | n8n cloud | Pendiente implementar |
| Conexión BD | SQLAlchemy con `pool_pre_ping=True` y `pool_recycle=300` | Evita conexiones muertas de Neon |

---

## Proyectos activos

| Proyecto | Sector | Secret GitHub | App | Estado |
|----------|--------|---------------|-----|--------|
| energia-mercados | Transversal — energía y mercados | `MEMO_NEON_URL` | [energia-mercados.streamlit.app](https://energia-mercados.streamlit.app) | ✅ Producción |
| energia-mercados-hosteleria | Hostelería — monitor de costes | `HOSTELERIA_NEON_URL` | [mercados-hosteleria.streamlit.app](https://mercados-hosteleria.streamlit.app) | ✅ Producción |

---

## Fuentes de datos en uso

| Fuente | Endpoint / Ticker | Proyecto | Frecuencia | Notas |
|--------|-------------------|----------|------------|-------|
| REE PVPC | `api.esios.ree.es/archives/70/download_json?date=YYYY-MM-DD` | ambos | Diaria | Sin auth. Formato PCB/TCHA. Funciona bien. |
| Yahoo Finance | `yfinance` múltiples tickers | energia-mercados | Diaria L-V | Sin auth. Fines de semana sin datos — normal. |
| BCE EUR/USD | `data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A` | ambos | Diaria | Sin auth. Formato SDMX-JSON. |
| INE IPC General | Serie `IPC206449` — `servicios.ine.es/wstempus/js/ES/DATOS_SERIE/` | ambos | Mensual | Respuesta puede ser lista o dict — usar parser robusto. |
| INE IPC Alimentación | Serie `IPC206450` — misma URL | hosteleria | Mensual | No existía en MEMO genérico — añadida en hostelería. |
| Gas Natural | `yfinance` ticker `NG=F` (Henry Hub) | hosteleria | Diaria L-V | USD/MMBtu → EUR/MWh con factor 0.29307. |
| Aceite AOVE | `oleista.com/es/precios/espana` (scraping) | hosteleria | Semanal | Fuente más fiable encontrada. POOLred e Infaoliva cambiaron URLs. |

---

## Decisiones técnicas consolidadas

**Conexión a BD:**
- Siempre SQLAlchemy con `pool_pre_ping=True` y `pool_recycle=300`
- Nunca `psycopg2.connect()` con `@st.cache_resource` — las conexiones mueren tras 5 min de inactividad en Neon y no reconectan
- Sin `@st.cache_data` en queries del dashboard — reconexión inmediata siempre

**ETL:**
- Un script por fuente de datos (`ingest_pvpc.py`, `ingest_gas.py`...)
- `run_daily.py` orquesta todos — si uno falla, los demás siguen ejecutándose
- `backfill.py` en cada proyecto — ejecutar UNA VEZ al iniciar el proyecto
- Upsert en todas las cargas: `ON CONFLICT DO UPDATE` — nunca duplicados
- `fechas_pendientes()` antes de cualquier backfill — evita recargar lo que ya existe

**SQL:**
- Vistas Gold con prefijo `v_` — las únicas que consulta el dashboard
- Schema por proyecto: `hosteleria.*`, `memo.*` — no por capa Bronze/Silver/Gold
- Columnas técnicas en Bronze: `_ingested_at` obligatoria

**Dashboard:**
- Lenguaje sin jerga técnica ni financiera visible al usuario final
- Regla de oro hostelería: cualquier KPI entendible en menos de 5 segundos
- Semáforos con contexto: siempre comparar vs media 30d, no valor absoluto
- Ahorro mostrar en €, porcentaje entre paréntesis como referencia
- Comprobar `len(df) >= 2` antes de `pct_change()` — evita `+nan%`

**GitHub Actions:**
- Nombres de archivos `.yml` sin espacios ni caracteres especiales — causa bugs silenciosos
- El `working-directory` global en el job puede causar que `pytest` no encuentre `tests/` — mejor `working-directory` por paso individual
- Caché de pip persiste entre runs — si un módulo "no se instala", borrar caché en Actions → Caches

**Seguridad:**
- `.env` siempre en `.gitignore` — nunca en el repo
- GitHub Secrets para Actions — nombre del secret en MAYÚSCULAS con prefijo del proyecto
- `.env.example` con estructura pero sin valores reales

---

## Errores resueltos — no repetir

| Error | Causa raíz | Solución |
|-------|-----------|----------|
| Datos desaparecen de la app tras inactividad | `psycopg2` + `@st.cache_resource` no reconecta conexiones muertas de Neon | Migrar a SQLAlchemy con `pool_pre_ping=True` |
| ETL ejecuta código viejo tras actualizar archivos | Caché de pip de GitHub Actions | Borrar caché en Actions → Caches, o añadir comentario en `requirements.txt` para cambiar hash |
| `pytest tests/` da "not found" con `working-directory` global | pytest busca desde el directorio actual, no desde la raíz | Poner `working-directory` por paso, no global, o usar ruta absoluta |
| Workflow no detecta cambios | Nombre del archivo `.yml` con caracteres especiales (guiones largos, espacios) | Renombrar el archivo con nombre simple sin caracteres especiales |
| `+nan%` en variación histórica | Solo hay 1 día de datos, `pct_change()` necesita al menos 2 | Comprobar `len(df) >= 2` antes de calcular |
| Gas REE endpoint da 500 | `apidatos.ree.es/mercados/precio-gas` no es accesible públicamente | Usar `yfinance` con ticker `NG=F` como alternativa robusta |
| POOLred e Infaoliva dan 404 | Cambiaron las URLs de sus páginas de cotizaciones | Usar `oleista.com` como fuente principal de aceite |
| INE devuelve error `0` | El parser no manejaba respuesta vacía ni formato dict/lista | Reescribir parser con manejo explícito de todos los formatos posibles |
| `module not found` en Actions | Paquete nuevo no añadido a `requirements.txt` | Añadir el paquete y hacer commit |
| `.env` commiteado accidentalmente | Falta de `.gitignore` correcto | Añadir `.gitignore`, borrar archivo del repo, rotar credenciales inmediatamente |

---

## Estructura actual del repo

```
ia-indata-agency/
├── CONTEXT.md                         ← este archivo
├── HOWTO.md                           ← guía paso a paso para proyectos nuevos
├── README.md                          ← presentación del repo
├── docs/
│   ├── AGENT.md
│   ├── Workflows.MD
│   ├── ModelContextProtocol.md
│   ├── skill-analytics-engineering.md
│   └── skill-powerbi-visualization.md
├── _template/
│   ├── spec.md
│   ├── app.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── .gitignore
│   ├── backfill.yml.example
│   └── etl/ · sql/ · tests/
├── projects/
│   ├── energia-mercados/
│   └── energia-mercados-hosteleria/
└── .github/workflows/
    ├── energia_mercados.yml
    ├── hosteleria_daily.yml
    └── backfill_hosteleria.yml        ← conservar para futuros rebackfills
```

---


---

## Guía rápida de edición visual (app.py)

Todos los `app.py` tienen comentarios que indican qué editar.
Busca el bloque correspondiente y cambia solo el valor indicado.

### Para cambiar colores globalmente
Edita las variables en `:root` — afectan a toda la app:
```css
--bg:     #080a0f   /* fondo base — más oscuro */
--bg2:    #0f1219   /* cards y paneles */
--teal:   #2dd4bf   /* color principal — logo y acentos */
--purple: #c4b5fd   /* color secundario — tabs, botones, variaciones */
--amber:  #fbbf24   /* advertencia / semáforo NORMAL */
--red:    #f87171   /* alerta / semáforo ALTO */
--text:   #f1f5f9   /* texto principal */
```

### Para cambiar elementos específicos

| Qué quieres cambiar | Dónde buscarlo en app.py |
|---------------------|--------------------------|
| Nombre/color del logo | `/* ── HEADER */` → `.memo-logo` o `.hdr-logo` |
| Tamaño de las tarjetas KPI | `/* ── TARJETAS KPI */` → `.kpi` padding/border-radius |
| Número grande de KPI | `.kpi-value` → font-size |
| Color de pestañas activas | `/* ── PESTAÑAS */` → `[aria-selected="true"]` color |
| Color del botón CSV | `/* ── BOTÓN DE DESCARGA */` → button color |
| Color de semáforos | `/* ── SEMÁFOROS */` → `.sem-bajo/.sem-alto` background y color |
| Fuente tipográfica | `/* FUENTES */` → cambiar nombre en @import y font-family |
| Fondo general | `:root` → `--bg` |
| Borde de cards | `:root` → `--bdr` y `--bdr2` |

### Fuentes tipográficas
- **Título de la app** (`.memo-logo` / `.hdr-logo`): `DM Sans` — legible, moderna
- **Números y valores KPI** (`.kpi-value`): `Space Mono` — se mantiene, es numérico
- **Regla:** nunca usar `Space Mono` para texto largo o títulos principales

### Color --muted
- Valor: `#94a3b8` (era `#475569`, demasiado oscuro en dark mode)
- Usar `#94a3b8` para subtítulos, labels de KPI, texto de footer
- Para texto aún más apagado usar `--dim` (#94a3b8 ya era --dim — ver nota abajo)
- **Nota:** `--dim` y `--muted` se unificaron visualmente; `--muted` subió de tono

### Botón de descarga CSV
- Siempre en la **misma fila que los filtros** (columna `fc3` o `col_dl`)
- Nunca al final de la tabla — el usuario no debe hacer scroll
- **Nombre del archivo:** siempre con formato `seccion_YYYY-MM-DD.csv` usando `csv_nombre("seccion")`
- **Contenido:** siempre ordenado por fecha descendente usando `df_para_csv(df)`
- Helpers disponibles en todos los `app.py`: `csv_nombre()` y `df_para_csv()`

### Tablas históricas
- Usar siempre `tabla_html()` — preserva colores de variación (verde/rojo/violeta)
- **No usar** `st.dataframe()` para tablas con variaciones — pierde los colores
- Orden dentro de la tabla: siempre fecha descendente (`sort_values("fecha", ascending=False)`)

### Modo claro (si quisieras cambiar el tema)
Cambiar en `:root`:
```css
--bg:   #f8fafc   /* fondo blanco */
--bg2:  #ffffff   /* cards blancas */
--bg3:  #f1f5f9   /* hover gris suave */
--text: #0f172a   /* texto oscuro */
--dim:  #475569
--muted:#94a3b8
```

## Próximos pasos

- [ ] Alertas WhatsApp en hostelería (n8n + CallMeBot — gratis sin Twilio)
- [ ] Web de presentación de 1 página para reuniones con clientes en Badajoz
- [ ] Decidir nombre y marca de la agencia
- [ ] Primer post LinkedIn sobre el proceso de construcción de MEMO Hostelería
- [ ] Primer contacto con cliente piloto en Badajoz (hostelería o cooperativa)
- [ ] Revisar MEMO Hostelería — posibles mejoras pendientes
