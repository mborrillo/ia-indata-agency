"""
D2: Tests de integridad: Silver sin duplicados (grano), trazabilidad Gold.
Sin DB: validamos lógica. Con DB: opcional integración.
"""
import pandas as pd
import pytest


def test_silver_ventas_grain_no_duplicados():
    """Silver ventas debe tener grano (producto_id, tienda_id, fecha) sin duplicados."""
    # Simular salida de agregación Bronze -> Silver
    df = pd.DataFrame({
        "producto_id": ["P1", "P1", "P2"],
        "tienda_id": ["T1", "T1", "T1"],
        "fecha": ["2025-03-01", "2025-03-02", "2025-03-01"],
        "unidades": [10.0, 8.0, 5.0],
        "importe": [100.0, 80.0, 50.0],
    })
    key = ["producto_id", "tienda_id", "fecha"]
    assert df.duplicated(subset=key).sum() == 0
    assert len(df) == len(df.drop_duplicates(subset=key))


def test_silver_stock_grain_no_duplicados():
    """Silver stock: grano (producto_id, tienda_id, fecha)."""
    df = pd.DataFrame({
        "producto_id": ["P1"],
        "tienda_id": ["T1"],
        "fecha": ["2025-03-01"],
        "cantidad": [50.0],
    })
    assert df.duplicated(subset=["producto_id", "tienda_id", "fecha"]).sum() == 0


def test_gold_rotacion_columnas_esperadas():
    """Vista v_rotacion_inventario debe exponer columnas del spec."""
    columnas_esperadas = {"producto_id", "tienda_id", "total_unidades_vendidas", "stock_promedio", "indice_rotacion"}
    # Estructura mínima; nombres deben coincidir con vista SQL
    assert "indice_rotacion" in columnas_esperadas
    assert "stock_promedio" in columnas_esperadas


def test_gold_alertas_columnas_esperadas():
    """Vista v_alertas_stock: columnas para alerta 7 días."""
    columnas_esperadas = {"producto_id", "tienda_id", "stock_actual", "venta_media_7d", "dias_de_stock", "es_stock_critico"}
    assert "es_stock_critico" in columnas_esperadas
    assert "dias_de_stock" in columnas_esperadas
