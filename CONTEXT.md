# CONTEXT.md — Estado de la Agencia ia-indata

> Este archivo es tu memoria persistente. Actualízalo al terminar cada sesión de trabajo.
> Pégalo al inicio de cada conversación con Claude, Gemini o cualquier IA.

## Última actualización
**Fecha:** 2026-03-20  
**Cambio:** Setup inicial del template

## Stack oficial (no cambiar sin buena razón)
- BD: Neon.tech (PostgreSQL)
- ETL: Python + GitHub Actions
- App: Streamlit Community Cloud
- Alertas: n8n cloud (cuando aplique)

## Proyectos activos
| Proyecto | Sector | BD Neon | App URL | Estado |
|----------|--------|---------|---------|--------|
| retail-prueba | Retail (prueba) | pendiente | pendiente | setup |

## Decisiones técnicas ya tomadas
- Patrón ETL: un script por fuente de datos (ingest_precios.py, ingest_clima.py...)
- Vistas SQL: siempre prefijo `v_` en capa Gold
- Columnas técnicas obligatorias en Bronze: `_ingested_at`, `_source`
- App: `@st.cache_data(ttl=3600)` en todas las queries
- Secretos: siempre en `.env` local o GitHub Actions Secrets (nunca en el repo)

## Errores ya resueltos (no repetir)
- `.env` commiteado accidentalmente → resuelto con .gitignore actualizado

## Próximo paso
Crear `projects/retailtech-monitor/` como primer proyecto de prueba con datos reales.
