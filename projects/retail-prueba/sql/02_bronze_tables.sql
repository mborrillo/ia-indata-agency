-- A2: Tablas Bronze con columnas técnicas (_ingested_at, _source_file)

-- Ventas crudas. Grain: una fila por evento/registro de ingesta (puede haber varias por producto/tienda/fecha).
CREATE TABLE IF NOT EXISTS retail_bronze.ventas (
    id               BIGSERIAL PRIMARY KEY,
    producto_id       TEXT NOT NULL,
    tienda_id        TEXT NOT NULL,
    fecha            DATE NOT NULL,
    unidades         NUMERIC(12,2) NOT NULL,
    importe          NUMERIC(14,2) NOT NULL,
    _ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file     TEXT
);
COMMENT ON TABLE retail_bronze.ventas IS 'Bronze: ventas crudas. Grain de ingesta: registro por línea de archivo.';

CREATE TABLE IF NOT EXISTS retail_bronze.stock (
    id               BIGSERIAL PRIMARY KEY,
    producto_id      TEXT NOT NULL,
    tienda_id        TEXT NOT NULL,
    fecha            DATE NOT NULL,
    cantidad         NUMERIC(12,2) NOT NULL,
    _ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file     TEXT
);
COMMENT ON TABLE retail_bronze.stock IS 'Bronze: stock crudo por producto/tienda/fecha.';

CREATE TABLE IF NOT EXISTS retail_bronze.precios (
    id               BIGSERIAL PRIMARY KEY,
    producto_id      TEXT NOT NULL,
    tienda_id        TEXT NOT NULL,
    fecha            DATE NOT NULL,
    precio_local     NUMERIC(14,2) NOT NULL,
    _ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    _source_file     TEXT
);
COMMENT ON TABLE retail_bronze.precios IS 'Bronze: precios locales para KPI oportunidad de venta (vs tendencia mercado).';
