# PROJECT SPEC: [NOMBRE DEL PROYECTO]

**Creado:** YYYY-MM-DD  
**Cliente:** [nombre]  
**Sector:** [sector]

---

## 1. Problema y objetivo
- **Problema:** [qué no puede ver o hacer el cliente hoy]
- **Meta cuantificada:** [ej: reducir coste X en 15%]

## 2. Fuentes de datos
| Fuente | URL / API | Frecuencia | Gratuita |
|--------|-----------|------------|----------|
|        |           | diaria     | sí/no    |

## 3. KPIs (máximo 5)
| KPI | Fórmula | Capa |
|-----|---------|------|
|     |         | Gold |

## 4. Stack del proyecto
- **BD:** Neon.tech → proyecto: `[pendiente-crear]`
- **ETL:** GitHub Actions (schedule: `0 7 * * *`)
- **App:** Streamlit Community Cloud
- **Alertas:** n8n (si/no)

## 5. Entregables
- [ ] ETL automatizado (ingesta diaria)
- [ ] Vistas Gold en SQL
- [ ] App Streamlit desplegada en producción
- [ ] README del proyecto actualizado

## 6. QA — no entregar sin esto
- [ ] KPIs coinciden exactamente con fórmulas del punto 3
- [ ] 0 duplicados en BD tras ingesta
- [ ] 0 API keys en el código
- [ ] GitHub Actions ejecuta verde
- [ ] App carga en menos de 5 segundos
```

Commit: `"fix: remove exposed API keys, clean spec template"`

---

### Fix 2 — Crear `_template/.env.example` (nuevo archivo)
```
# ── Base de datos ──────────────────────────────────────────────
NEON_DATABASE_URL=postgresql://user:pass@ep-xxx.eu-west-2.aws.neon.tech/dbname?sslmode=require

# ── APIs externas (añade las que uses para este proyecto) ──────
# AEMET_API_KEY= SECRETS AEMET_API_KEY
# OPENWEATHER_API_KEY= SECRETS OPENWEATHER_API_KEY
# YAHOO_FINANCE no requiere key

# ── Notificaciones (opcional) ──────────────────────────────────
# N8N_WEBHOOK_URL=
```

---

### Fix 3 — Crear `_template/requirements.txt` (nuevo archivo)
```
streamlit>=1.32.0
plotly>=5.20.0
pandas>=2.2.0
psycopg2-binary>=2.9.9
python-dotenv>=1.0.0
sqlalchemy>=2.0.0
requests>=2.31.0
```

---

### Fix 4 — Crear `_template/.gitignore` (nuevo archivo)
```
.env
.env.*
*.env
.streamlit/secrets.toml
__pycache__/
*.pyc
.venv/
venv/
data/raw/
data/processed/
*.csv
*.xlsx
.DS_Store
