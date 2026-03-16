# PROJECT SPECIFICATION: Sistema de Inteligencia para Gestión de Inventarios Retail (SIMIR)

## 1. Contexto y Objetivos
Transformar datos de ventas y stock en alertas proactivas para reducir stockout y exceso de inventario.

- **Problema**: Sin visibilidad de rotación real ni tendencias de demanda.
- **Meta**: Reducir 12% el stock inmovilizado y aumentar 8% las ventas mediante alertas.

## 2. Requerimientos Técnicos
- Data Warehouse: Neon.tech (esquema retail)
- Modelado: Arquitectura de Medallón (Bronze, Silver, Gold)
- Visualización: App Streamlit
- Alertas: GitHub Actions + email/WhatsApp futuro

## 3. KPIs y Lógica de Negocio
1. **Índice de Rotación**: Ventas / Stock promedio
2. **Stock Crítico**: Alerta si stock < 7 días de venta prevista
3. **Oportunidad de Venta**: Comparativa precio local vs tendencia mercado

## 4. Entregables
- Pipeline ETL diario
- Vistas Gold: `v_rotacion_inventario`, `v_alertas_stock`
- App Streamlit para el gerente de tienda
- Reporte ejecutivo

## 5. Protocolo Verificador
- Trazabilidad desde Gold
- Tests de cálculo exactos
- Security review