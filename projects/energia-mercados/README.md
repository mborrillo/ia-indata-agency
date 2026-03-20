# ⚡ MEMO — Monitor de Energía y Mercados

> Proyecto de la [ia-indata Agency](https://github.com/mborrillo/ia-indata-agency).
> Demuestra que en ~10 días se construye un monitor automatizado, gratuito y
> replicable a cualquier sector empresarial español.

**Stack:** Neon · Python · GitHub Actions · Streamlit · 0 € / mes

---

## ¿Qué monitoriza?

| Panel | Fuente | Frecuencia |
|-------|--------|------------|
| Precio luz PVPC + semáforo | Red Eléctrica de España (REE) | Diaria |
| Futuros, índices, divisas | Yahoo Finance (yfinance) | Diaria (L–V) |
| Tipo de cambio EUR/USD | Banco Central Europeo (BCE) | Diaria |
| IPC España | INE | Mensual |

---

## Setup en 5 pasos

### 1. Crea el proyecto en Neon

Entra a [console.neon.tech](https://console.neon.tech) → New Project →
nombre: `memo-energia-mercados`. Copia la connection string.

### 2. Crea el schema en Neon

En el SQL Editor de Neon, ejecuta el contenido de `sql/01_schema_and_gold.sql`.

### 3. Configura variables de entorno

```bash
cp .env.example .env
# Edita .env y pega tu NEON_DATABASE_URL
```

### 4. Instala dependencias y prueba el ETL localmente

```bash
pip install -r requirements.txt
python -m etl.run_daily
```

### 5. Despliega

**GitHub Actions (ETL automático):**
- Copia `workflow_memo_daily.yml` a `.github/workflows/` en la raíz del repo
- En GitHub → Settings → Secrets → New secret:
  - Nombre: `MEMO_NEON_URL`
  - Valor: tu connection string de Neon

**Streamlit Community Cloud (dashboard):**
- Ve a [share.streamlit.io](https://share.streamlit.io) → New app
- Repo: `ia-indata-agency` · Branch: `main`
- Main file: `projects/energia-mercados/app.py`
- En Advanced settings → Secrets: añade `NEON_DATABASE_URL = "tu_url"`

---

## Estructura

```
energia-mercados/
├── spec.md                    ← Definición del proyecto
├── app.py                     ← Dashboard Streamlit
├── requirements.txt
├── .env.example
├── .gitignore
├── workflow_memo_daily.yml    ← Copiar a .github/workflows/
├── etl/
│   ├── run_daily.py           ← Orquestador (GitHub Actions llama a este)
│   ├── ingest_energia.py      ← PVPC (REE)
│   ├── ingest_mercados.py     ← Yahoo Finance
│   └── ingest_macro.py        ← BCE + INE
├── sql/
│   └── 01_schema_and_gold.sql ← Ejecutar una vez en Neon
└── tests/
    └── test_memo.py           ← pytest tests/
```

---

## Arquitectura de datos

```
REE API ──▶ ingest_energia.py ──▶ memo.bronze_energia ──▶ v_energia_resumen
Yahoo   ──▶ ingest_mercados.py──▶ memo.bronze_mercados──▶ v_mercados_resumen ──▶ app.py
BCE     ──▶ ingest_macro.py   ──▶ memo.bronze_divisa  ──┐
INE     ──▶ ingest_macro.py   ──▶ memo.bronze_macro   ──┴▶ v_macro_resumen
```

---

Hecho por **Marcos Borrillo** · [LinkedIn](https://www.linkedin.com/in/marcos-borrillo/) ·
[ia-indata Agency](https://github.com/mborrillo/ia-indata-agency)
