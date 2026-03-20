-- ============================================================
-- MEMO — Monitor de Energía y Mercados
-- Ejecutar UNA VEZ en Neon para crear el schema completo
-- Schema único: memo (bronze + gold en el mismo schema)
-- ============================================================

-- Bronze: Precio luz PVPC (REE)
CREATE TABLE IF NOT EXISTS memo.bronze_energia (
    id            SERIAL PRIMARY KEY,
    fecha         DATE        NOT NULL,
    precio_medio  NUMERIC(8,5) NOT NULL,
    precio_min    NUMERIC(8,5),
    hora_min      SMALLINT,
    precio_max    NUMERIC(8,5),
    hora_max      SMALLINT,
    tramo_mayoria TEXT,
    var_per_prev  NUMERIC(6,2),
    _ingested_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (fecha)
);

-- Bronze: Mercados financieros (Yahoo Finance)
CREATE TABLE IF NOT EXISTS memo.bronze_mercados (
    id            SERIAL PRIMARY KEY,
    fecha         DATE        NOT NULL,
    activo        TEXT        NOT NULL,
    precio_cierre NUMERIC(12,4),
    variacion_p   NUMERIC(6,2),
    categoria     TEXT,
    moneda        TEXT,
    _ingested_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (fecha, activo)
);

-- Bronze: Tipo de cambio EUR/USD (BCE)
CREATE TABLE IF NOT EXISTS memo.bronze_divisa (
    id           SERIAL PRIMARY KEY,
    fecha        DATE        NOT NULL,
    par          TEXT        NOT NULL DEFAULT 'EUR/USD',
    tasa         NUMERIC(8,4) NOT NULL,
    _ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (fecha, par)
);

-- Bronze: Macro España — IPC (INE)
CREATE TABLE IF NOT EXISTS memo.bronze_macro (
    id           SERIAL PRIMARY KEY,
    fecha        DATE        NOT NULL,
    indicador    TEXT        NOT NULL,
    valor        NUMERIC(8,2),
    unidad       TEXT,
    _ingested_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (fecha, indicador)
);

-- Índices para rendimiento
CREATE INDEX IF NOT EXISTS idx_energia_fecha    ON memo.bronze_energia(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_mercados_fecha   ON memo.bronze_mercados(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_mercados_activo  ON memo.bronze_mercados(activo);
CREATE INDEX IF NOT EXISTS idx_divisa_fecha     ON memo.bronze_divisa(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_macro_fecha      ON memo.bronze_macro(fecha DESC);

-- ============================================================
-- VISTAS GOLD — listas para el dashboard
-- ============================================================

-- KPI 1+2: Energía — precio hoy + semáforo vs media 30 días
CREATE OR REPLACE VIEW memo.v_energia_resumen AS
WITH media_30d AS (
    SELECT AVG(precio_medio) AS media
    FROM memo.bronze_energia
    WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
),
hoy AS (
    SELECT * FROM memo.bronze_energia
    ORDER BY fecha DESC
    LIMIT 1
)
SELECT
    h.fecha,
    h.precio_medio,
    h.precio_min,
    h.hora_min,
    h.precio_max,
    h.hora_max,
    h.tramo_mayoria,
    h.var_per_prev,
    m.media AS media_30d,
    CASE
        WHEN h.precio_medio < m.media * 0.85 THEN 'BAJO'
        WHEN h.precio_medio > m.media * 1.15 THEN 'ALTO'
        ELSE 'NORMAL'
    END AS semaforo
FROM hoy h
CROSS JOIN media_30d m;

COMMENT ON VIEW memo.v_energia_resumen IS
'Gold: precio PVPC hoy + semáforo vs media 30d. Spec §3.';

-- KPI 3: Mercados — resumen del último día disponible
CREATE OR REPLACE VIEW memo.v_mercados_resumen AS
WITH ultima_fecha AS (
    SELECT MAX(fecha) AS ref FROM memo.bronze_mercados
)
SELECT
    m.activo,
    m.categoria,
    m.moneda,
    m.precio_cierre,
    m.variacion_p,
    m.fecha,
    CASE
        WHEN m.variacion_p >  2 THEN 'SUBE'
        WHEN m.variacion_p < -2 THEN 'BAJA'
        ELSE 'ESTABLE'
    END AS tendencia
FROM memo.bronze_mercados m
INNER JOIN ultima_fecha u ON m.fecha = u.ref
ORDER BY m.categoria, m.activo;

COMMENT ON VIEW memo.v_mercados_resumen IS
'Gold: últimos precios de mercado con tendencia. Spec §3.';

-- KPI 4+5: Macro — tipo cambio + IPC
CREATE OR REPLACE VIEW memo.v_macro_resumen AS
SELECT
    'EUR/USD'                            AS indicador,
    tasa::TEXT                           AS valor,
    'tasa'                               AS unidad,
    fecha
FROM memo.bronze_divisa
WHERE par = 'EUR/USD'
ORDER BY fecha DESC
LIMIT 1

UNION ALL

SELECT
    indicador,
    valor::TEXT,
    unidad,
    fecha
FROM memo.bronze_macro
ORDER BY fecha DESC
LIMIT 1;

COMMENT ON VIEW memo.v_macro_resumen IS
'Gold: tipo de cambio EUR/USD (BCE) + IPC España (INE). Spec §3.';

-- Vista de serie temporal para gráficos históricos
CREATE OR REPLACE VIEW memo.v_energia_historico AS
SELECT
    fecha,
    precio_medio,
    precio_min,
    precio_max,
    semaforo_dia AS semaforo,
    AVG(precio_medio) OVER (
        ORDER BY fecha
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS media_movil_7d
FROM (
    SELECT *,
        CASE
            WHEN precio_medio < (SELECT AVG(precio_medio) FROM memo.bronze_energia) * 0.85 THEN 'BAJO'
            WHEN precio_medio > (SELECT AVG(precio_medio) FROM memo.bronze_energia) * 1.15 THEN 'ALTO'
            ELSE 'NORMAL'
        END AS semaforo_dia
    FROM memo.bronze_energia
) sub
ORDER BY fecha DESC;

COMMENT ON VIEW memo.v_energia_historico IS
'Gold: serie histórica de energía con media móvil 7d para gráficos.';
