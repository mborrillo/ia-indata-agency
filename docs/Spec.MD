# PROJECT SPECIFICATION:

## 1. Contexto y Objetivos de Negocio
Este proyecto escala la PoC de AgroTech Extremadura para una Cooperativa Agrícola. El objetivo es transformar datos pasivos en inteligencia proactiva para optimizar el uso de recursos y la comercialización.
- **Problema:** Los agricultores carecen de visibilidad sobre la necesidad hídrica real y las tendencias de precio de mercado global.
- **Meta:** Reducción del 15% en costes energéticos de riego y aumento del 10% en el precio de venta final mediante alertas de oportunidad [Conversation History].

## 2. Equipo de Agentes y Pipeline SDD
Se delega la ejecución en la "Legión" bajo la supervisión del Arquitecto (Human in the Loop):
- **Explorer:** Mapeo de esquemas en Supabase / Neon y endpoints de Apis ("Definir Apis del Proyecto").
- **Proposer:** Definición de la estrategia técnica de ingesta y modelado.
- **Arquitecto & Analista:** Implementación de la lógica de negocio en SQL y Python.
- **Verificador (QA):** Auditoría punta a punta contra esta especificación.
- **Documentador:** Registro histórico en Engram, Notion [Conversation History]. O bien, generar un Memori.md simplificado, que contenga (Proyecto, Qué (What), Por qué (Why), Dónde (Where), Aprendizaje (Learned)).

## 3. Requerimientos Técnicos (Stack)
- **Data Warehouse:** PostgreSQL en **Supabase / Neon** (esquema primario) [4, 5].
- **Modelado:** Arquitectura de Medallón (Bronze, Silver, Gold) en **Databricks** [6, 7].
- **Ingestión:** Scripts de Python (Pandas/PySpark) automatizados por **GitHub Actions** [4, 8].
- **Visualización:** Interfaz proactiva en **Streamlit** y Dashboards en **Lovable** [Conversation History].
- **Automatización:** Flujos de alertas en **n8n** (WhatsApp/Email) [9, 10].

## 4. Definición de KPIs y Lógica de Negocio
1. **INR (Índice de Necesidad de Riego):** Lógica basada en `(Evapotranspiración - Lluvia Prevista) * Coeficiente de Cultivo`.
2. **MVM (Margen de Ventaja de Mercado):** Comparativa entre `Precio Local` y `Futuros de Commodities` [Conversation History].
3. **Alerta de Helada:** Disparo de notificación si `Temperatura < 2°C` y `Humedad > 80%`.

## 5. Protocolo del Agente Verificador (Checklist de Calidad)
El despliegue a `main` será bloqueado si no se cumple lo siguiente [11, 12]:
- **Trazabilidad:** Cada métrica del dashboard debe nacer de una vista en la capa **Gold** [Turn 12].
- **Integridad:** Validación de que no hay duplicados en la capa Silver tras la ingesta de AEMET.
- **Seguridad:** Verificación con `claude-code-security-review` de que no hay API Keys expuestas [13, 14].
- **Consistencia:** Los cálculos en SQL deben coincidir exactamente con las fórmulas del punto 4 de este spec.

## 6. Entregables
- [ ] Pipeline ETL automatizado (sync diario).
- [ ] Vistas Gold (`v_indicadores_riego`, `v_oportunidades_mercado`).
- [ ] Data App en Streamlit para el técnico de campo.
- [ ] Reporte Ejecutivo en Lovable para la directiva de la cooperativa.
