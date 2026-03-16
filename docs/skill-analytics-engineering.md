# SKILL: Analytics Engineering & Data Quality Standards

## 1. Triggers (Cuándo activar esta Skill)
- Creación o modificación de pipelines de datos (ETL/ELT).
- Diseño de esquemas en PostgreSQL (Supabase/Neon) o Databricks.
- Redacción de vistas SQL o modelos de transformación.
- Auditorías de calidad de datos y validación de KPIs.

## 2. Arquitectura de Medallón (Estándar de la Agencia)
Toda la información debe fluir siguiendo la estructura de capas para asegurar la trazabilidad, tal como se implementó en los proyectos de Telco y AgroTech:

- **Layer 1: Bronze (Raw)**
    - Ingesta de datos crudos sin transformaciones.
    - Formato inmutable. Columnas técnicas obligatorias: `_ingested_at`, `_source_file`.
- **Layer 2: Silver (Cleansed/Standardized)**
    - Tipado de datos estricto (Dtypes).
    - Eliminación de duplicados y normalización de nombres.
    - Aplicación de lógica de "Append Only" para generar activos históricos.
- **Layer 3: Gold (Business/Curated)**
    - Vistas finales listas para Power BI, Streamlit o Lovable.
    - Lógica de negocio aplicada (KPIs).
    - Nomenclatura sugerida: prefijo `v_` para vistas (ej. `v_rendimiento_riego`).

## 3. Estándares de SQL y Modelado
El agente debe escribir código siguiendo estas reglas para minimizar el uso de tokens y maximizar el rendimiento:

- **Legibilidad:** Uso obligatorio de **CTEs (Common Table Expressions)** en lugar de subconsultas anidadas.
- **Optimización:** Prohibido el uso de `SELECT *`. Definir columnas explícitamente.
- **Documentación:** Cada tabla/vista debe incluir una descripción de su grano (grain) y su propósito de negocio.
- **SQL Dialects:** Priorizar PostgreSQL (Supabase) y SparkSQL (Databricks) según el contexto del proyecto.

## 4. Protocolo de Verificación (QA) - "El Guardián de la Verdad"
Como **Agente Verificador**, antes de considerar una tarea como "Terminada", debes ejecutar los siguientes checks:

1. **Validación de Especificación:** Comparar el output final contra el archivo `spec.md` original. ¿Se cumplen todos los KPIs solicitados?
2. **Integridad Referencial:** Verificar que no haya pérdida de registros en los JOINs (validar recuento de filas).
3. **Null Check:** Auditar columnas críticas de negocio para asegurar que no contengan nulos inesperados.
4. **Pruebas Analíticas:** Generar scripts de validación que comparen los totales agregados contra la fuente Bronze.

## 5. Visualización Narrativa (Power BI / Streamlit / Lovable)
Para que el **Agente Visualizador** aporte valor real:

- **Storytelling:** No crear gráficos aislados. Diseñar flujos: Resumen (KPI Cards) -> Comparativa (Bar/Line charts) -> Detalle (Tables).
- **Consistencia:** Usar paleta de colores corporativa definida en `agent.md`.
- **Performance:** Las interfaces deben conectar a tablas de la capa **Gold**, nunca a la capa Bronze, para garantizar velocidad de respuesta.

## 6. Registro en Memoria (Engram)
Al finalizar cualquier ajuste en el modelo de datos, el agente DEBE registrar el hallazgo en **Engram** con el formato:
- **What:** (Ej. Cambio de lógica en cálculo de Churn).
- **Why:** (Ej. Discrepancia detectada entre CRM y Billing).
- **Where:** (Ej. Esquema `silver`, tabla `t_clientes_activos`).
- **Learned:** (Ej. En Supabase, las funciones de ventana son más eficientes que las subqueries para este volumen).

## 7. Prohibiciones Estrictas
- No editar código directamente en producción sin pasar por un **Pull Request**.
- No exponer credenciales o secretos en los scripts (usar `.env` o Secret Manager).
- No generar modelos de datos que no permitan escalabilidad histórica (evitar el borrado de datos; preferir `is_active` o `valid_to`).
