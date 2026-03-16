# PLAN SDD: retail-prueba — SIMIR (Sistema de Inteligencia para Gestión de Inventarios Retail)

**Rol:** Senior Architect (AGENT.md + .cursorrules)  
**Pipeline:** Explorer → Proposer → Arquitecto (plan) → Task Planner  
**Rama objetivo:** `feature/retail-prueba-inicial`  
**Estado:** Plan para aprobación — sin código aún.

---

## FASE 1 — EXPLORER

### 1.1 Análisis del template (repositorio ia-indata-agency)

- **Filosofía:** "Tony Stark tiene la visión, Jarvis ejecuta con precisión." Repo como template de Agencia de Datos IA, replicable a retail/salud/logística.
- **Stack obligatorio (freemium):** Neon.tech (Postgres), Python + GitHub Actions, Streamlit. No Supabase/Lovable/Databricks en este proyecto.
- **Estructura relevante:**
  - `/docs/`: AGENT.md, Workflows.MD, Spec.MD (ejemplo AgroTech), ModelContextProtocol.md, skills (analytics-engineering, powerbi-visualization).
  - `.cursorrules`: Pipeline SDD, main sagrada, tests + spec, env vars para secrets, Neon + Streamlit.
  - Proyectos por cliente en `/projects/<nombre>/` con su propio `spec.md`.
- **Reglas sagradas:** Main solo vía PR; tests y validación contra spec; cero API keys en código; DATABASE_URL desde secrets; app en Streamlit (`app.py`).

### 1.2 Análisis de docs/

| Documento | Hallazgos para retail-prueba |
|-----------|------------------------------|
| **AGENT.md** | Pipeline: Explorer → Proposer → Arquitecto → Task Planner → Implementer → Verificador. Spec-driven, plan antes de cambios grandes, seguridad nativa. |
| **Workflows.MD** | CI en PR: Lint & Build, tests analíticos, security review (claude-code). CD post-merge. HITL en merge. |
| **Spec.MD** | Plantilla de spec (AgroTech): Contexto, equipo SDD, stack, KPIs, protocolo verificador, entregables. |
| **skill-analytics-engineering.md** | Medallón: Bronze (raw, `_ingested_at`, `_source_file`), Silver (cleansed, append-only), Gold (vistas `v_*`, KPIs). SQL con CTEs, sin `SELECT *`, PostgreSQL. |
| **skill-powerbi-visualization.md** | Narrativa: Resumen → Comparativa → Detalle. Aquí aplicamos equivalente en Streamlit. |
| **ModelContextProtocol.md** | DATABASE_URL para Neon; GitHub para ramas/PRs; sin push a main. |

### 1.3 Estado actual de retail-prueba

- **Único artefacto:** `projects/retail-prueba/spec.md` (especificación ya redactada).
- **Sin:** Código, esquema SQL, ETL, app Streamlit, tests ni rama de trabajo aún.

### 1.4 Resumen Explorer

- Template y docs alineados con SDD y stack Neon + Python + Streamlit.
- spec.md de retail-prueba define objetivos, KPIs (Rotación, Stock Crítico, Oportunidad de Venta), vistas Gold y protocolo verificador.
- No hay conflicto con .cursorrules (stack freemium respetado).
- Fuentes de datos concretas (archivos, APIs, tablas) no están definidas en spec; el Implementer deberá asumir o pedir datos de ejemplo/estructura.

---

## FASE 2 — PROPOSER

### 2.1 Estrategia técnica propuesta

1. **Data Warehouse (Neon):**
   - Un esquema `retail` (o por capas: `retail_bronze`, `retail_silver`, `retail_gold`) en la misma instancia Neon del repo.
   - Crear tablas/vistas con nomenclatura estándar de la agencia.

2. **Arquitectura de Medallón:**
   - **Bronze:** Tablas de ingesta cruda (ej. ventas, stock, precios). Columnas técnicas: `_ingested_at`, `_source_file`.
   - **Silver:** Tablas limpias, tipado fijo, sin duplicados, grano claro (por producto/tienda/fecha según spec).
   - **Gold:** Solo vistas: `v_rotacion_inventario`, `v_alertas_stock`; si aplica, una vista para oportunidad de venta (precio local vs tendencia).

3. **ETL:**
   - Scripts Python (Pandas) en `/projects/retail-prueba/` (o en raíz con target retail): lectura de fuentes → carga Bronze → transformación a Silver → materialización de Gold (vistas ya en DB; opcionalmente tablas materializadas si Neon lo soporta).
   - Pipeline ETL "diario" ejecutable vía GitHub Actions (schedule o manual), leyendo desde env (DATABASE_URL, rutas o URLs de datos si aplica).

4. **Lógica de negocio (alineada a spec):**
   - **Índice de Rotación:** Ventas / Stock promedio (por producto/tienda y ventana temporal definida).
   - **Stock Crítico:** Alerta si stock < 7 días de venta prevista (venta prevista = proyección basada en historial reciente).
   - **Oportunidad de Venta:** Comparativa precio local vs tendencia mercado (requiere definir fuente de "tendencia mercado"; si no hay datos, dejar estructura preparada y KPI documentado).

5. **App Streamlit:**
   - Una sola app (`app.py`) para el gerente de tienda: conectarse solo a vistas Gold; storytelling Resumen (KPI cards) → Comparativa (gráficos) → Detalle (tablas).
   - Despliegue fuera de este plan (solo código en repo).

6. **Alertas:**
   - GitHub Actions + email/WhatsApp "futuro": en esta fase solo dejar preparado un job que exponga alertas (ej. leyendo `v_alertas_stock`) y opcionalmente envíe por email; WhatsApp como extensión posterior.

7. **Calidad y seguridad:**
   - Tests (Python/pytest) que validen fórmulas de KPIs contra spec y comprobaciones de integridad (sin duplicados en Silver, trazabilidad Gold).
   - Security review (claude-code-security-review) en CI; cero secrets en código.

### 2.2 Decisiones y riesgos

- **Datos de entrada:** Si el spec no define CSV/API concretos, proponer estructura mínima (ej. `ventas`, `stock`, `precios`) y datos de ejemplo o seeds para que el pipeline sea ejecutable y testeable.
- **Oportunidad de Venta:** Si no hay fuente de "tendencia mercado", implementar vista con placeholder o lógica simplificada (ej. comparar con media móvil local) y documentar en spec o en código.
- **Reporte ejecutivo:** Entregable "Reporte ejecutivo" puede ser una página en Streamlit (resumen) o un documento estático generado; dejarlo como página/ficha en la app en esta fase.

---

## FASE 3 — PLAN DETALLADO (ARQUITECTO)

### 3.1 Esquema de base de datos (Neon, PostgreSQL)

- **Bronze:**
  - `retail_bronze.ventas` (id, producto_id, tienda_id, fecha, unidades, importe, _ingested_at, _source_file).
  - `retail_bronze.stock` (id, producto_id, tienda_id, fecha, cantidad, _ingested_at, _source_file).
  - Opcional: `retail_bronze.precios` si aplica para oportunidad de venta.
- **Silver:**
  - `retail_silver.ventas`: limpieza, tipos, dedup, grano (producto_id, tienda_id, fecha).
  - `retail_silver.stock`: mismo criterio.
  - `retail_silver.precios` (si aplica).
- **Gold (vistas):**
  - `v_rotacion_inventario`: Ventas / Stock promedio por producto/tienda y ventana (fórmula exacta según spec).
  - `v_alertas_stock`: filas donde stock < 7 días de venta prevista (con definición explícita de "venta prevista").
  - Opcional: `v_oportunidad_venta` (precio local vs tendencia; estructura definida, lógica según datos disponibles).

### 3.2 Pipeline ETL

- **Orden:** Ingesta → Bronze → Silver → Gold (vistas definidas en SQL en DB; ETL solo escribe Bronze y Silver).
- **Herramientas:** Python 3.x, Pandas, psycopg2 o SQLAlchemy, env (DATABASE_URL).
- **Ubicación:** Por ejemplo `projects/retail-prueba/etl/` con `run.py` o `run_daily.py` invocable por GitHub Actions.
- **Idempotencia:** Ingesta append con clave/ventana para evitar duplicados; Silver recalculable o por ventana.

### 3.3 App Streamlit

- **Una app:** `projects/retail-prueba/app.py` (o en raíz apuntando a esquema retail).
- **Secciones:** (1) Resumen KPIs (rotación, alertas de stock, oportunidad si existe). (2) Comparativas (gráficos por producto/tienda). (3) Detalle (tablas filtrables desde Gold).
- **Conexión:** Solo lectura a vistas Gold; DATABASE_URL desde env.

### 3.4 Automatización y CI

- **GitHub Actions:**
  - Workflow de CI en PR: lint (Python), tests (pytest), security review.
  - Workflow opcional: ETL diario (schedule) o manual, que ejecute el script ETL y (futuro) envíe alertas.
- **Tests:** Unitarios para fórmulas (rotación, días de stock, venta prevista); integración opcional contra DB de prueba con datos fijos.

### 3.5 Protocolo verificador (checklist)

- Trazabilidad: cada métrica de la app proviene de una vista Gold.
- Tests de cálculo exactos según fórmulas del spec.
- Security review sin API keys ni secrets en repo.
- Sin duplicados en Silver tras ingesta (test o revisión manual).

---

## FASE 4 — TASK PLANNER (TAREAS ATÓMICAS)

Las tareas se ejecutan en rama `feature/retail-prueba-inicial`; no se genera código hasta tu aprobación.

### Bloque A — Infraestructura y esquema

| ID | Tarea atómica | Dependencias |
|----|----------------|--------------|
| A1 | Crear esquemas en Neon: `retail_bronze`, `retail_silver`, `retail_gold` (o equivalente) | — |
| A2 | Crear tablas Bronze: `ventas`, `stock` (y `precios` si aplica) con columnas técnicas | A1 |
| A3 | Crear tablas Silver: `ventas`, `stock` (y `precios`) con tipado y grano definido | A2 |
| A4 | Definir vistas Gold: `v_rotacion_inventario` (fórmula spec), `v_alertas_stock` (7 días venta prevista) | A3 |
| A5 | (Opcional) Vista Gold `v_oportunidad_venta` con lógica documentada | A3 |

### Bloque B — ETL

| ID | Tarea atómica | Dependencias |
|----|----------------|--------------|
| B1 | Crear estructura de carpetas y módulo ETL (ej. `projects/retail-prueba/etl/`) | — |
| B2 | Implementar carga a Bronze (ventas, stock) desde fuentes definidas o seeds | A2, B1 |
| B3 | Implementar transformación Bronze → Silver (dedup, tipos, grano) | A3, B2 |
| B4 | Garantizar que las vistas Gold se alimenten desde Silver (solo DDL; sin script de "carga" Gold si son vistas) | A4, B3 |
| B5 | Script invocable para pipeline completo (ej. `run_daily.py`) y uso de DATABASE_URL | B2, B3 |

### Bloque C — App y reporte

| ID | Tarea atómica | Dependencias |
|----|----------------|--------------|
| C1 | Crear `app.py` Streamlit con conexión a Neon (solo lectura, vistas Gold) | A4 |
| C2 | Sección Resumen: KPI cards (rotación, alertas, oportunidad si existe) | C1 |
| C3 | Sección Comparativa: gráficos por producto/tienda desde Gold | C1 |
| C4 | Sección Detalle: tablas filtrables desde Gold | C1 |
| C5 | Incluir "Reporte ejecutivo" como página o sección en la app | C2–C4 |

### Bloque D — Calidad y CI

| ID | Tarea atómica | Dependencias |
|----|----------------|--------------|
| D1 | Añadir tests unitarios de fórmulas (rotación, stock crítico, venta prevista) | A4 |
| D2 | Añadir test de integridad Silver (sin duplicados) y trazabilidad Gold | B3, A4 |
| D3 | Configurar workflow GitHub Actions: lint, tests, security review en PR | D1, D2 |
| D4 | (Opcional) Workflow ETL diario o manual y documentación de alertas futuras | B5 |

### Bloque E — Documentación y cierre

| ID | Tarea atómica | Dependencias |
|----|----------------|--------------|
| E1 | Actualizar README o doc del proyecto con cómo ejecutar ETL y app | B5, C1 |
| E2 | Verificación final contra spec.md y checklist del protocolo verificador | A–D |

---

## Resumen para aprobación

- **Explorer:** Template y docs coherentes con SDD; spec de retail-prueba claro; sin código aún.
- **Proposer:** Neon + Medallón + Python ETL + Streamlit + GitHub Actions; alertas en fase preparatoria.
- **Plan:** Esquema Bronze/Silver/Gold, vistas `v_rotacion_inventario` y `v_alertas_stock`, ETL en Python, app única Streamlit, CI con tests y security.
- **Tareas:** 5 bloques (A: esquema, B: ETL, C: app, D: tests/CI, E: docs y verificación); dependencias indicadas.
- **Rama:** `feature/retail-prueba-inicial` creada para implementación posterior.

Si apruebas este plan, el siguiente paso será que el Implementer ejecute las tareas atómicas en esta rama (sin tocar `main`).
