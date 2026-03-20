# PROJECT SPEC: Monitor de Energía y Mercados (MEMO)

**Creado:** 2026-03-21
**Autor:** Marcos Borrillo — ia-indata Agency
**Sector:** Transversal (válido para retail, industria, hostelería, logística)
**Propósito:** Prueba técnica del template ia-indata-agency + contenido LinkedIn

---

## 1. Problema y objetivo

- **Problema:** Las empresas españolas no tienen visibilidad unificada sobre los
  dos costes externos que más impactan su margen: la energía (PVPC) y los
  mercados de materias primas / divisas (Yahoo Finance, BCE).
- **Meta:** Demostrar que en ~10 días se puede construir un monitor
  automatizado, gratuito y replicable a cualquier sector, usando el template
  ia-indata-agency como base.

---

## 2. Fuentes de datos

| Fuente | URL / API | Frecuencia | Gratuita |
|--------|-----------|------------|----------|
| REE (PVPC) | `https://api.esios.ree.es/archives/70/download_json` | Diaria | Sí |
| Yahoo Finance | `yfinance` (Python) | Diaria | Sí |
| BCE (EUR/USD) | `https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A` | Diaria | Sí |
| INE / Eurostat | `https://servicios.ine.es/wstempus/js/ES/DATOS_SERIE/IPC206449` | Mensual | Sí |

---

## 3. KPIs (5 máximo)

| KPI | Fórmula | Capa | Vista Gold |
|-----|---------|------|-----------|
| Precio luz hoy | `precio_medio` del día (€/kWh) | Gold | `v_energia_resumen` |
| Semáforo energía | `BAJO / NORMAL / ALTO` vs media 30d | Gold | `v_energia_resumen` |
| Variación mercados | `((cierre_hoy - cierre_ayer) / cierre_ayer) * 100` | Gold | `v_mercados_resumen` |
| Tipo cambio EUR/USD | Último valor BCE | Gold | `v_macro_resumen` |
| IPC España (último) | Último dato mensual INE | Gold | `v_macro_resumen` |

---

## 4. Stack del proyecto

- **BD:** Neon.tech → proyecto: `memo-energia-mercados`
- **Schema:** `memo` (bronze, silver, gold en un solo schema por simplicidad)
- **ETL:** GitHub Actions — 4 scripts independientes, schedule `0 8 * * 1-5`
- **App:** Streamlit Community Cloud
- **Alertas:** No (fase 1)

---

## 5. Entregables

- [ ] 4 scripts ETL (energia, mercados, divisa, macro)
- [ ] SQL: tablas Bronze + vistas Gold
- [ ] App Streamlit desplegada
- [ ] GitHub Actions ejecutando en verde
- [ ] README con instrucciones de setup
- [ ] Post LinkedIn con demo

---

## 6. QA — no entregar sin esto

- [ ] KPIs coinciden con fórmulas del punto 3
- [ ] 0 duplicados en BD (upsert por fecha + clave natural)
- [ ] 0 API keys en el código (solo variables de entorno)
- [ ] GitHub Actions ejecuta verde al menos 3 días seguidos
- [ ] App carga en menos de 5 segundos
- [ ] `pytest tests/` pasa sin errores
