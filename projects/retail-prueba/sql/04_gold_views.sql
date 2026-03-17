-- A4 + A5: Vistas Gold. KPIs: Rotación (Ventas/Stock prom), Stock Crítico (<7 días venta prevista), Oportunidad.

-- KPI 1: Índice de Rotación = Ventas / Stock promedio (ventana últimos 30 días por producto/tienda)
CREATE OR REPLACE VIEW retail_gold.v_rotacion_inventario AS
WITH ventas_30 AS (
    SELECT
        producto_id,
        tienda_id,
        SUM(unidades) AS total_unidades_vendidas
    FROM retail_silver.ventas
    WHERE fecha >= (SELECT max(fecha) - INTERVAL '30 days' FROM retail_silver.ventas)
    GROUP BY producto_id, tienda_id
),
stock_prom_30 AS (
    SELECT
        producto_id,
        tienda_id,
        AVG(cantidad) AS stock_promedio
    FROM retail_silver.stock
    WHERE fecha >= (SELECT max(fecha) - INTERVAL '30 days' FROM retail_silver.stock)
    GROUP BY producto_id, tienda_id
)
SELECT
    v.producto_id,
    v.tienda_id,
    v.total_unidades_vendidas,
    COALESCE(s.stock_promedio, 0) AS stock_promedio,
    CASE
        WHEN COALESCE(s.stock_promedio, 0) > 0
        THEN v.total_unidades_vendidas / s.stock_promedio
        ELSE NULL
    END AS indice_rotacion
FROM ventas_30 v
LEFT JOIN stock_prom_30 s ON v.producto_id = s.producto_id AND v.tienda_id = s.tienda_id;

COMMENT ON VIEW retail_gold.v_rotacion_inventario IS 'Gold: KPI Índice de Rotación = Ventas / Stock promedio (ventana 30 días). Spec §3.';

-- KPI 2: Stock Crítico. Alerta si stock actual < 7 días de venta prevista (venta prevista = media diaria últimos 7 días)
CREATE OR REPLACE VIEW retail_gold.v_alertas_stock AS
WITH ultima_fecha AS (
    SELECT max(fecha) AS ref_fecha FROM retail_silver.stock
),
venta_media_diaria AS (
    SELECT
        producto_id,
        tienda_id,
        SUM(unidades) / 7.0 AS venta_media_7d
    FROM retail_silver.ventas
    WHERE fecha > (SELECT ref_fecha - INTERVAL '7 days' FROM ultima_fecha)
      AND fecha <= (SELECT ref_fecha FROM ultima_fecha)
    GROUP BY producto_id, tienda_id
),
stock_actual AS (
    SELECT
        s.producto_id,
        s.tienda_id,
        s.cantidad AS stock_actual
    FROM retail_silver.stock s
    INNER JOIN ultima_fecha u ON s.fecha = u.ref_fecha
)
SELECT
    st.producto_id,
    st.tienda_id,
    st.stock_actual,
    COALESCE(v.venta_media_7d, 0) AS venta_media_7d,
    CASE
        WHEN COALESCE(v.venta_media_7d, 0) > 0
        THEN st.stock_actual / v.venta_media_7d
        ELSE NULL
    END AS dias_de_stock,
    (st.stock_actual < 7.0 * COALESCE(v.venta_media_7d, 0)) AS es_stock_critico
FROM stock_actual st
LEFT JOIN venta_media_diaria v ON st.producto_id = v.producto_id AND st.tienda_id = v.tienda_id
WHERE COALESCE(v.venta_media_7d, 0) > 0
  AND st.stock_actual < 7.0 * v.venta_media_7d;

COMMENT ON VIEW retail_gold.v_alertas_stock IS 'Gold: Alerta si stock < 7 días de venta prevista (media 7d). Spec §3.';

-- A5 (opcional): Oportunidad de venta. Placeholder: precio local vs media móvil local (tendencia mercado externa a definir).
CREATE OR REPLACE VIEW retail_gold.v_oportunidad_venta AS
WITH precios_recientes AS (
    SELECT
        producto_id,
        tienda_id,
        fecha,
        precio_local,
        AVG(precio_local) OVER (
            PARTITION BY producto_id, tienda_id
            ORDER BY fecha
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ) AS tendencia_local_7d
    FROM retail_silver.precios
),
ultima_fecha AS (
    SELECT max(fecha) AS ref_fecha FROM retail_silver.precios
)
SELECT
    p.producto_id,
    p.tienda_id,
    p.fecha,
    p.precio_local,
    p.tendencia_local_7d,
    (p.precio_local - p.tendencia_local_7d) AS diff_vs_tendencia,
    CASE
        WHEN p.tendencia_local_7d > 0
        THEN ((p.precio_local - p.tendencia_local_7d) / p.tendencia_local_7d) * 100
        ELSE NULL
    END AS pct_vs_tendencia
FROM precios_recientes p
INNER JOIN ultima_fecha u ON p.fecha = u.ref_fecha;

COMMENT ON VIEW retail_gold.v_oportunidad_venta IS 'Gold: Comparativa precio local vs tendencia (media 7d local; tendencia mercado externa a integrar). Spec §3.;';
