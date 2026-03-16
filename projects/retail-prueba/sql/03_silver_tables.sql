-- A3: Tablas Silver. Grano: (producto_id, tienda_id, fecha). Tipado estricto, sin duplicados.

CREATE TABLE IF NOT EXISTS retail_silver.ventas (
    producto_id   TEXT NOT NULL,
    tienda_id     TEXT NOT NULL,
    fecha         DATE NOT NULL,
    unidades      NUMERIC(12,2) NOT NULL,
    importe       NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (producto_id, tienda_id, fecha)
);
COMMENT ON TABLE retail_silver.ventas IS 'Silver: ventas limpias. Grain: (producto_id, tienda_id, fecha).';

CREATE TABLE IF NOT EXISTS retail_silver.stock (
    producto_id   TEXT NOT NULL,
    tienda_id     TEXT NOT NULL,
    fecha         DATE NOT NULL,
    cantidad      NUMERIC(12,2) NOT NULL,
    PRIMARY KEY (producto_id, tienda_id, fecha)
);
COMMENT ON TABLE retail_silver.stock IS 'Silver: stock limpio. Grain: (producto_id, tienda_id, fecha).';

CREATE TABLE IF NOT EXISTS retail_silver.precios (
    producto_id   TEXT NOT NULL,
    tienda_id     TEXT NOT NULL,
    fecha         DATE NOT NULL,
    precio_local  NUMERIC(14,2) NOT NULL,
    PRIMARY KEY (producto_id, tienda_id, fecha)
);
COMMENT ON TABLE retail_silver.precios IS 'Silver: precios locales. Grain: (producto_id, tienda_id, fecha).';
