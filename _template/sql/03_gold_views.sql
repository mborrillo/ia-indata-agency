-- ============================================================
-- CAPA GOLD: Vistas listas para el dashboard
-- Nomenclatura obligatoria: prefijo v_
-- ============================================================

-- KPI resumen (tarjetas del dashboard)
CREATE OR REPLACE VIEW v_resumen_kpi AS
SELECT
    DATE_TRUNC('month', fecha)  AS mes,
    categoria,
    AVG(valor)                  AS promedio,
    MAX(valor)                  AS maximo,
    MIN(valor)                  AS minimo,
    COUNT(*)                    AS n_registros
FROM silver_datos
GROUP BY 1, 2
ORDER BY 1 DESC, 2;

-- Serie temporal (gráfico de línea)
CREATE OR REPLACE VIEW v_serie_temporal AS
SELECT
    fecha,
    categoria,
    valor,
    AVG(valor) OVER (
        PARTITION BY categoria
        ORDER BY fecha
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS media_movil_7d
FROM silver_datos
ORDER BY fecha DESC;
