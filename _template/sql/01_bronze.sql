-- ============================================================
-- CAPA BRONZE: Ingesta cruda
-- Ejecutar UNA VEZ al crear el proyecto en Neon
-- ============================================================

CREATE TABLE IF NOT EXISTS bronze_datos (
    id            SERIAL PRIMARY KEY,
    fecha         DATE        NOT NULL,
    valor         NUMERIC,
    categoria     TEXT,
    fuente        TEXT,
    _ingested_at  TIMESTAMPTZ DEFAULT NOW(),
    _source       TEXT,

    -- Evitar duplicados exactos
    UNIQUE (fecha, valor, fuente)
);

CREATE INDEX IF NOT EXISTS idx_bronze_fecha    ON bronze_datos(fecha DESC);
CREATE INDEX IF NOT EXISTS idx_bronze_fuente   ON bronze_datos(fuente);
