"""
D1: Tests unitarios de fórmulas según spec §3.
- Índice de Rotación = Ventas / Stock promedio
- Stock Crítico = alerta si stock < 7 días de venta prevista
"""
import pytest


def test_indice_rotacion_formula():
    """KPI Rotación: Ventas / Stock promedio."""
    ventas = 100.0
    stock_promedio = 25.0
    indice = ventas / stock_promedio
    assert indice == 4.0


def test_indice_rotacion_stock_cero_devuelve_null_o_inf():
    """Rotación con stock 0: no dividir por cero; tratar como null/inf según lógica negocio."""
    ventas = 10.0
    stock_promedio = 0.0
    # En la vista Gold usamos CASE WHEN stock > 0 THEN ventas/stock ELSE NULL
    indice = ventas / stock_promedio if stock_promedio > 0 else None
    assert indice is None


def test_stock_critico_7_dias():
    """Stock crítico: alerta si stock_actual < 7 * venta_media_diaria."""
    stock_actual = 20.0
    venta_media_7d = 5.0  # 5 unidades/día
    dias_stock = stock_actual / venta_media_7d  # 4 días
    es_critico = stock_actual < 7.0 * venta_media_7d  # 20 < 35
    assert dias_stock == 4.0
    assert es_critico is True


def test_stock_no_critico_suficiente_dias():
    """Si stock >= 7 días de venta, no es crítico."""
    stock_actual = 70.0
    venta_media_7d = 10.0
    assert stock_actual >= 7.0 * venta_media_7d
    assert (stock_actual < 7.0 * venta_media_7d) is False
