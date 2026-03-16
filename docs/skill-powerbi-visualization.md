# SKILL: Power BI Visualization & Data Storytelling

## 1. Triggers (Cuándo activar esta Skill)
- Diseño o modificación de tableros en **Power BI**.
- Redacción de fórmulas **DAX** o transformaciones en **Power Query (M)**.
- Definición de maquetas (wireframes) para reportes directivos.
- Auditoría de usabilidad y consistencia visual en entregables analíticos.

## 2. Filosofía de Diseño: El Estándar de los 5 Segundos
El objetivo principal es que cualquier stakeholder entienda el KPI principal y la salud del negocio en un vistazo rápido.
- **Jerarquía Visual:** Los KPIs más críticos (tarjetas) deben situarse en la parte superior izquierda.
- **Narrativa de Datos (Storytelling):** Seguir el flujo: **Resumen** (Cards/Gauges) -> **Tendencia/Comparación** (Line/Bar charts) -> **Detalle** (Tablas/Matrices).
- **Uso Crítico de la IA:** Emplear la función de **"Preguntas y Respuestas" (Q&A)** de Power BI para permitir que el cliente interactúe con los datos en lenguaje natural.

## 3. Estándares Técnicos (DAX y Modelado)
El agente debe seguir estas directrices para garantizar la trazabilidad y el rendimiento [7]:
- **Separación de Lógica:** Las transformaciones pesadas se realizan en **Power Query (M)** o en la capa **Gold** de la base de datos para no sobrecargar el motor DAX.
- **DAX Limpio:** 
    - Uso obligatorio de variables (`VAR`/`RETURN`) para mejorar la legibilidad y el rendimiento.
    - Medidas organizadas en tablas de carpetas específicas (ej. "Medidas Base", "Medidas de Tiempo").
- **Modelo en Estrella:** Priorizar esquemas de estrella (hechos y dimensiones) para optimizar la velocidad de filtrado.

## 4. Protocolo de Verificación (QA Visual)
Como **Agente Verificador**, debes auditar el reporte punta a punta antes de la entrega final:
- **Precisión Analítica:** ¿Coincide el total de la tarjeta con la suma de la tabla de detalles?
- **Consistencia Visual:** ¿Se respeta la paleta de colores y tipografía definida en el `AGENT.md`?
- **Accesibilidad:** ¿Los contrastes son adecuados y los títulos de los ejes son descriptivos?
- **Interactividad:** Validar que todos los *slicers* (filtros) afecten correctamente a los visuales relacionados.

## 5. Registro de Aprendizaje (Engram)
Cada decisión de diseño o solución a un error de cálculo DAX debe registrarse en **Engram**:
- **What:** (Ej. Implementación de cálculo de *Year-to-Date* dinámico).
- **Why:** (Ej. El cliente necesita comparar el rendimiento agrícola contra el año anterior).
- **Where:** (Ej. Archivo `.pbix` de AgroTech, Tabla de Medidas).
- **Learned:** (Ej. Usar `TOTALYTD` es más eficiente que filtros manuales para este volumen de datos).

## 6. Prohibiciones Estrictas
- **No usar gráficos circulares (Pie Charts)** para más de tres categorías.
- **Prohibido el "Chartjunk":** Eliminar líneas de cuadrícula y bordes innecesarios que distraigan de la información.
- **No exponer datos sensibles:** Asegurar que los filtros de seguridad a nivel de fila (RLS) estén activos si el proyecto lo requiere.
