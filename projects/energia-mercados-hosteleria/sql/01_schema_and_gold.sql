-- ============================================================
-- MEMO Hostelería — Schema y Vistas Gold
-- Ejecutar UNA VEZ en Neon (proyecto: memo-hosteleria)
-- Schema: hosteleria
-- ============================================================

CREATE SCHEMA IF NOT EXISTS hosteleria;

-- ── BRONZE ────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS hosteleria.bronze_pvpc (
    id            SERIAL PRIMARY KEY,
    fecha         DATE         NOT NULL,
    precio_medio  NUMERIC(8,5) NOT NULL,
    precio_min    NUMERIC(8,5),
    hora_min      SMALLINT,
    precio_max    NUMERIC(8,5),
    hora_max      SMALLINT,
    tramo_mayoria TEXT,
    var_per_prev  NUMERIC(6,2),
    _ingested_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (fecha)
);

CREATE TABLE IF NOT EXISTS hosteleria.bronze_gas (
    id            SERIAL PRIMARY KEY,
    fecha         DATE         NOT NULL,
    precio_mwh    NUMERIC(10,4),
    unidad        TEXT         DEFAULT 'EUR/MWh',
    var_per_prev  NUMERIC(6,2),
    _ingested_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (fecha)
);

CREATE TABLE IF NOT EXISTS hosteleria.bronze_aceite (
    id            SERIAL PRIMARY KEY,
    fecha         DATE         NOT NULL,
    tipo          TEXT         NOT NULL,
    precio_kg     NUMERIC(8,4) NOT NULL,
    variacion_sem NUMERIC(6,2),
    fuente        TEXT         DEFAULT 'MAPA',
    _ingested_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (fecha, tipo)
);

CREATE TABLE IF NOT EXISTS hosteleria.bronze_ipc (
    id            SERIAL PRIMARY KEY,
    fecha         DATE         NOT NULL,
    indicador     TEXT         NOT NULL,
    valor         NUMERIC(8,2) NOT NULL,
    unidad        TEXT         DEFAULT 'tasa_variacion_anual_%',
    _ingested_at  TIMESTAMPTZ  DEFAULT NOW(),
    UNIQUE (fecha, indicador)
);

CREATE INDEX IF NOT EXISTS idx_h_pvpc_fecha   ON hosteleria.bronze_pvpc(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_h_gas_fecha    ON hosteleria.bronze_gas(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_h_aceite_fecha ON hosteleria.bronze_aceite(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_h_ipc_fecha    ON hosteleria.bronze_ipc(fecha DESC);

-- ── GOLD ──────────────────────────────────────────────────────

CREATE OR REPLACE VIEW hosteleria.v_luz_hoy AS
WITH media_30d AS (
    SELECT AVG(precio_medio) AS media
    FROM hosteleria.bronze_pvpc
    WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
),
hoy AS (
    SELECT * FROM hosteleria.bronze_pvpc ORDER BY fecha DESC LIMIT 1
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
    ROUND((h.precio_medio - m.media) / m.media * 100, 1) AS pct_vs_media,
    CASE
        WHEN h.precio_medio < m.media * 0.85 THEN 'BAJO'
        WHEN h.precio_medio > m.media * 1.15 THEN 'ALTO'
        ELSE 'NORMAL'
    END AS semaforo,
    CASE
        WHEN h.precio_medio < m.media * 0.85 THEN 'Buen momento para encender equipos de alto consumo'
        WHEN h.precio_medio > m.media * 1.15 THEN 'Evita equipos de alto consumo ahora'
        ELSE 'Consumo normal — sin restricciones especiales'
    END AS recomendacion
FROM hoy h CROSS JOIN media_30d m;

CREATE OR REPLACE VIEW hosteleria.v_hora_valle AS
SELECT
    fecha,
    hora_min AS mejor_hora,
    precio_min AS precio_en_mejor_hora,
    precio_max AS precio_en_peor_hora,
    ROUND((precio_max - precio_min) / precio_min * 100, 1) AS ahorro_potencial_pct,
    CASE
        WHEN hora_min BETWEEN 0  AND 7  THEN 'Madrugada'
        WHEN hora_min BETWEEN 8  AND 13 THEN 'Mañana'
        WHEN hora_min BETWEEN 14 AND 17 THEN 'Tarde'
        ELSE 'Noche'
    END AS franja
FROM hosteleria.bronze_pvpc
ORDER BY fecha DESC LIMIT 1;

CREATE OR REPLACE VIEW hosteleria.v_aceite_estado AS
WITH ultimas AS (
    SELECT * FROM hosteleria.bronze_aceite
    WHERE tipo = 'AOVE' ORDER BY fecha DESC LIMIT 4
),
calc AS (
    SELECT
        MAX(fecha) AS fecha,
        MAX(precio_kg) AS precio_actual,
        AVG(precio_kg) AS precio_medio_4sem,
        CASE
            WHEN MAX(precio_kg) < AVG(precio_kg)        THEN 'BAJANDO'
            WHEN MAX(precio_kg) > AVG(precio_kg) * 1.03 THEN 'SUBIENDO'
            ELSE 'ESTABLE'
        END AS tendencia
    FROM ultimas
)
SELECT
    fecha, precio_actual, precio_medio_4sem, tendencia,
    ROUND(precio_actual - precio_medio_4sem, 3) AS diff_vs_media_4sem,
    CASE
        WHEN tendencia = 'BAJANDO'  THEN 'Espera antes de comprar — el precio está bajando'
        WHEN tendencia = 'SUBIENDO' THEN 'Considera comprar ahora — el precio está subiendo'
        ELSE 'Precio estable — compra según tu consumo habitual'
    END AS recomendacion_compra
FROM calc;

CREATE OR REPLACE VIEW hosteleria.v_gas_estado AS
WITH media_30d AS (
    SELECT AVG(precio_mwh) AS media
    FROM hosteleria.bronze_gas
    WHERE fecha >= CURRENT_DATE - INTERVAL '30 days'
),
hoy AS (SELECT * FROM hosteleria.bronze_gas ORDER BY fecha DESC LIMIT 1)
SELECT
    h.fecha, h.precio_mwh, m.media AS media_30d, h.var_per_prev,
    ROUND((h.precio_mwh - m.media) / m.media * 100, 1) AS pct_vs_media,
    CASE
        WHEN h.precio_mwh < m.media * 0.90 THEN 'BAJO'
        WHEN h.precio_mwh > m.media * 1.10 THEN 'ALTO'
        ELSE 'NORMAL'
    END AS semaforo
FROM hoy h CROSS JOIN media_30d m;

CREATE OR REPLACE VIEW hosteleria.v_ipc_spread AS
WITH ipc AS (
    SELECT
        MAX(CASE WHEN indicador = 'IPC_GENERAL'      THEN valor END) AS ipc_general,
        MAX(CASE WHEN indicador = 'IPC_ALIMENTACION' THEN valor END) AS ipc_alimentacion,
        MAX(fecha) AS fecha
    FROM hosteleria.bronze_ipc
    WHERE fecha = (SELECT MAX(fecha) FROM hosteleria.bronze_ipc)
)
SELECT
    fecha, ipc_general, ipc_alimentacion,
    ROUND(ipc_alimentacion - ipc_general, 2) AS spread,
    CASE
        WHEN ipc_alimentacion - ipc_general > 2
            THEN 'TUS COSTES SUBEN MÁS QUE LA INFLACIÓN — revisa los precios de la carta'
        WHEN ipc_alimentacion - ipc_general > 0
            THEN 'Costes algo por encima de la inflación — vigila tus márgenes'
        ELSE 'Costes bajo control — inflación alimentaria por debajo de la general'
    END AS alerta_margen
FROM ipc;

-- KPI diferencial: Índice de Coste Total ponderado
CREATE OR REPLACE VIEW hosteleria.v_indice_coste AS
WITH
    luz    AS (SELECT semaforo, pct_vs_media FROM hosteleria.v_luz_hoy),
    gas    AS (SELECT semaforo, pct_vs_media FROM hosteleria.v_gas_estado),
    aceite AS (SELECT tendencia FROM hosteleria.v_aceite_estado),
    ipc    AS (SELECT spread FROM hosteleria.v_ipc_spread),
    puntos AS (
        SELECT
            CASE WHEN l.semaforo='BAJO' THEN -1 WHEN l.semaforo='ALTO' THEN 1 ELSE 0 END * 0.40 +
            CASE WHEN g.semaforo='BAJO' THEN -1 WHEN g.semaforo='ALTO' THEN 1 ELSE 0 END * 0.30 +
            CASE WHEN a.tendencia='BAJANDO' THEN -1 WHEN a.tendencia='SUBIENDO' THEN 1 ELSE 0 END * 0.20 +
            CASE WHEN i.spread > 2 THEN 1 WHEN i.spread < 0 THEN -1 ELSE 0 END * 0.10
            AS score,
            l.semaforo AS luz, g.semaforo AS gas,
            a.tendencia AS aceite, i.spread AS spread_ipc
        FROM luz l, gas g, aceite a, ipc i
    )
SELECT
    ROUND(score::NUMERIC, 2) AS indice,
    CASE
        WHEN score < -0.2 THEN 'VERDE'
        WHEN score >  0.2 THEN 'ROJO'
        ELSE 'AMARILLO'
    END AS semaforo_global,
    luz, gas, aceite, spread_ipc
FROM puntos;

-- Histórico luz para gráficos
CREATE OR REPLACE VIEW hosteleria.v_luz_historico AS
SELECT
    fecha, precio_medio, precio_min, precio_max, hora_min,
    AVG(precio_medio) OVER (
        ORDER BY fecha
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS media_movil_7d,
    CASE
        WHEN precio_medio < AVG(precio_medio) OVER () * 0.85 THEN 'BAJO'
        WHEN precio_medio > AVG(precio_medio) OVER () * 1.15 THEN 'ALTO'
        ELSE 'NORMAL'
    END AS semaforo_dia
FROM hosteleria.bronze_pvpc
ORDER BY fecha DESC;
