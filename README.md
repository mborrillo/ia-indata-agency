# 🏢 IA-Indata Agency

**Agencia de datos con IA.** Proyectos de inteligencia de datos replicables
a cualquier sector empresarial, construidos sobre un stack 100% freemium.

Autor: **Marcos Borrillo** · Badajoz, Extremadura
[Web](https://marcos-borrillo.lovable.app/) ·
[LinkedIn](https://www.linkedin.com/in/marcos-borrillo/) ·
[AgroTech Extremadura](https://github.com/mborrillo/agro-tech-es)

---

## Proyectos en producción

| Proyecto | Sector | App |
|----------|--------|-----|
| [energia-mercados](projects/energia-mercados/) | Energía y mercados financieros | [energia-mercados.streamlit.app](https://energia-mercados.streamlit.app) |
| [energia-mercados-hosteleria](projects/energia-mercados-hosteleria/) | Monitor de costes para restauración | [mercados-hosteleria.streamlit.app](https://mercados-hosteleria.streamlit.app) |

---

## Cómo crear un proyecto nuevo

Ver **[HOWTO.md](HOWTO.md)** para la guía completa paso a paso.

Resumen:
1. Copia `_template/` → `projects/nombre-cliente/`
2. Rellena `spec.md` — problema, KPIs, fuentes de datos
3. Crea proyecto en [Neon.tech](https://neon.tech) y ejecuta el SQL
4. Adapta los scripts ETL en `etl/`
5. Ejecuta el backfill — histórico desde el día 1
6. Despliega en [Streamlit Community Cloud](https://share.streamlit.io)

---

## Stack oficial (freemium)

| Capa | Herramienta |
|------|-------------|
| Base de datos | Neon.tech (PostgreSQL) |
| ETL + automatización | GitHub Actions |
| Dashboard | Streamlit Community Cloud |
| Alertas | n8n cloud |

---

## Estructura

```
ia-indata-agency/
├── CONTEXT.md        ← memoria de la agencia — actualizar tras cada sesión
├── HOWTO.md          ← guía paso a paso para proyectos nuevos
├── docs/             ← filosofía y reglas de la agencia
├── _template/        ← punto de partida para cada proyecto nuevo
└── projects/         ← un directorio por proyecto
```

---

## Filosofía

- **Spec-first:** nunca escribir código sin `spec.md` validado
- **Backfill por defecto:** todo proyecto arranca con histórico desde el día 1
- **Sin jerga técnica:** el cliente entiende cada KPI en menos de 5 segundos
- **0 credenciales en el repo:** siempre variables de entorno o GitHub Secrets
