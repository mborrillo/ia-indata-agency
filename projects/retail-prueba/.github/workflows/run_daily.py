name: Run Daily ETL - Retail Prueba

on:
  schedule:
    - cron: '0 3 * * *'
  workflow_dispatch:

jobs:
  run-etl:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r projects/retail-prueba/requirements.txt

      - name: Debug - Verificar carpeta data/
        run: |
          echo "=== LISTADO DE CARPETA DATA ==="
          ls -la projects/retail-prueba/data || echo "Carpeta data/ NO ENCONTRADA"
          echo " "
          echo "=== PRIMERAS LÍNEAS DE ventas.csv ==="
          if [ -f projects/retail-prueba/data/ventas.csv ]; then
            head -n 8 projects/retail-prueba/data/ventas.csv
          else
            echo "ventas.csv NO ENCONTRADO"
          fi
          echo " "
          echo "=== PRIMERAS LÍNEAS DE stock.csv ==="
          if [ -f projects/retail-prueba/data/stock.csv ]; then
            head -n 8 projects/retail-prueba/data/stock.csv
          else
            echo "stock.csv NO ENCONTRADO"
          fi

      - name: Run ETL script
        env:
          NEON_DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
        run: python projects/retail-prueba/etl/run_daily.py
