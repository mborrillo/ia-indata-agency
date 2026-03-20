-- ============================================================
-- CAPA SILVER: Datos limpios y tipados
-- Vista materializable o tabla con refresh diario
-- ============================================================

CREATE OR REPLACE VIEW silver_datos AS
SELECT
    fecha,
    valor::NUMERIC(12,4)   AS valor,
    LOWER(TRIM(categoria)) AS categoria,
    fuente,
    _ingested_at
FROM bronze_datos
WHERE valor IS NOT NULL
  AND fecha >= CURRENT_DATE - INTERVAL '2 years'
ORDER BY fecha DESC;
