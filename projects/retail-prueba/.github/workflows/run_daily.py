name: Run Daily ETL - Retail Prueba

on:
  schedule:
    # Cada día a las 03:00 UTC (ajusta la hora según tu zona)
    - cron: '0 3 * * *'
  workflow_dispatch:  # Permite ejecutar manualmente desde GitHub

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

      - name: Run ETL script
        env:
          NEON_DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
        run: python projects/retail-prueba/etl/run_daily.py

      - name: Commit any changes (if ETL modifies files)
        run: |
          git config --global user.name "GitHub Actions"
          git config --global user.email "actions@github.com"
          git add .
          git commit -m "Auto-commit: ETL daily run" || echo "No changes to commit"
          git push
        continue-on-error: true
