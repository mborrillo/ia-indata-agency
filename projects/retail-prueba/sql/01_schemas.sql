-- A1: Esquemas Medallón para SIMIR (Neon/PostgreSQL)
-- Grain: producto_id, tienda_id, fecha donde aplique.

CREATE SCHEMA IF NOT EXISTS retail_bronze;
CREATE SCHEMA IF NOT EXISTS retail_silver;
CREATE SCHEMA IF NOT EXISTS retail_gold;

COMMENT ON SCHEMA retail_bronze IS 'Capa Bronze: datos crudos, inmutable. Columnas _ingested_at, _source_file.';
COMMENT ON SCHEMA retail_silver IS 'Capa Silver: datos limpios, tipado y grano (producto_id, tienda_id, fecha).';
COMMENT ON SCHEMA retail_gold IS 'Capa Gold: vistas de negocio para Streamlit (KPIs: rotación, alertas, oportunidad).';
