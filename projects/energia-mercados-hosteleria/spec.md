# PROJECT SPEC: MEMO Hostelería — Monitor de Costes para Restauración

**Creado:** 2026-03-22
**Autor:** Marcos Borrillo — ia-indata Agency
**Versión:** 1.0

---

## 1. Problema y objetivo

### El problema real
Un grupo de restauración con 3 locales en Badajoz gasta entre 4.000€ y 12.000€ al mes
en energía y materias primas clave (aceite, gas). Toman decisiones de compra y operación
por intuición o costumbre, sin ningún sistema que les avise cuando los costes van a subir
o cuando hay una ventana de ahorro.

El resultado: pagan la luz en las horas más caras, compran aceite cuando está caro,
y se enteran de que el IPC de alimentación ha subido cuando ya han perdido margen.

### La pregunta que debe responder el producto
> "¿Debo actuar hoy, o puedo esperar?"

Esa es la única pregunta que importa. Todo el producto gira alrededor de ella.

### Objetivo
Ser la herramienta que un gerente de grupo de restauración o empresa de catering
consulta cada mañana en 2 minutos para tomar decisiones de coste con datos reales.

### Meta cuantificada
Demostrar que el cliente puede reducir entre 300€ y 1.500€/mes en costes energéticos
y de aprovisionamiento con decisiones basadas en datos.

---

## 2. Público objetivo

### Perfil primario: Grupos de restauración (3+ locales)
- Facturación: 500k€ - 3M€/año
- Estructura: gerente o director de operaciones con poder de decisión
- Dolor principal: tres facturas de luz, compras de volumen, margen apretado
- Capacidad de pago: 150-300€/mes sin problema si ven el ROI

### Perfil secundario: Empresas de catering y colectividades
- Clientes: comedores de colegios, residencias, empresas, catering de eventos
- Estructura: director/a con departamento de compras o administración
- Dolor principal: contratos cerrados a precio fijo con costes variables que suben
- Capacidad de pago: 200-400€/mes — el ahorro justifica el coste 10x

### Geografía inicial
Badajoz ciudad y provincia. Mérida. Cáceres. Expansión nacional vía LinkedIn en fase 2.

---

## 3. Fuentes de datos

| Fuente | Dato | API / URL | Frecuencia | Coste |
|--------|------|-----------|------------|-------|
| REE (PVPC) | Precio luz hora a hora | api.esios.ree.es | Diaria | Gratis |
| Ministerio Agricultura | Precio aceite oliva virgen extra español | realprecioaceite.es o MAPA | Semanal | Gratis |
| REE / ENAGAS | Precio gas natural España | api.esios.ree.es | Diaria | Gratis |
| INE | IPC general + IPC alimentación | servicios.ine.es | Mensual | Gratis |
| BCE | EUR/USD (impacto importaciones) | data-api.ecb.europa.eu | Diaria | Gratis |

**Fuente clave nueva:** Precio del aceite de oliva virgen extra español en €/litro
del mercado nacional — no el futuro de aceite de soja de Chicago.
Esta es la diferencia entre un dato útil y un dato que el cliente ignora.

---

## 4. KPIs — en lenguaje de hostelero, no de analista

| KPI | Pregunta que responde | Fórmula | Alerta |
|-----|----------------------|---------|--------|
| **Semáforo Luz** | ¿Es buen momento para usar equipos? | PVPC hoy vs media 30d | Rojo si >15% sobre media |
| **Hora Valle** | ¿Cuándo enciendo las cámaras? | Hora mínima PVPC del día | Notificación a las 06:00 |
| **Coste Gas Hoy** | ¿Está el gas caro o barato? | Precio gas vs media 30d | Rojo si >10% sobre media |
| **Aceite Oliva** | ¿Compro aceite ahora o espero? | Precio €/litro + tendencia 4 semanas | Alerta si baja >3% |
| **IPC Alimentación** | ¿Están subiendo mis costes más que la inflación? | IPC alimentación vs IPC general | Alerta si spread >2 puntos |
| **Índice Coste Total** | ¿Cómo está mi mes en conjunto? | Promedio ponderado luz+gas+aceite+IPC | Verde / Amarillo / Rojo |

El **Índice de Coste Total** es el KPI diferencial — no existe en ninguna web pública.
Es el único número que resume si el mes está siendo bueno o malo para los costes.

---

## 5. Alertas (el producto real)

El dashboard es la demo. Las alertas son el producto que hace que el cliente
no pueda vivir sin la herramienta.

### Alertas configurables vía n8n
| Alerta | Trigger | Canal | Timing |
|--------|---------|-------|--------|
| Hora valle luz | PVPC mínimo del día | WhatsApp | 06:30 cada día |
| Luz cara mañana | PVPC previsto >20% sobre media | Email | 20:00 día anterior |
| Aceite baja | Precio aceite cae >3% semana | WhatsApp | Lunes 08:00 |
| Gas disparo | Gas sube >10% en 7 días | Email + WhatsApp | Inmediato |
| Resumen semanal | Siempre | Email PDF | Lunes 07:00 |

---

## 6. Stack técnico

- **BD:** Neon.tech → proyecto: `memo-hosteleria`
- **Schema:** `hosteleria` (bronze, gold en schema único)
- **ETL:** Python + GitHub Actions (L-V 07:30 UTC, Lunes incluido para IPC)
- **Dashboard:** Streamlit Community Cloud (demo y uso diario)
- **Alertas:** n8n cloud (WhatsApp via Twilio o CallMeBot, Email via Gmail)
- **Web de presentación:** Lovable o página simple (para reuniones con clientes)

---

## 7. Lo que NO incluye (para no construir de más)

- No incluye precios de proveedores locales específicos (eso es fase 2 con datos del cliente)
- No incluye previsión de ventas ni análisis de ingresos (no tenemos acceso a su TPV)
- No incluye EuroStoxx50, SP500, Aluminio, Cobre — irrelevantes para hostelería
- No incluye comparativa con competidores (no tenemos esos datos)

---

## 8. Estructura del repo

```
projects/memo-hosteleria/
├── spec.md                    ← este archivo
├── app.py                     ← dashboard Streamlit
├── requirements.txt
├── .env.example
├── .gitignore
├── etl/
│   ├── run_daily.py           ← orquestador
│   ├── ingest_pvpc.py         ← luz REE (reutilizar de MEMO)
│   ├── ingest_gas.py          ← gas natural REE
│   ├── ingest_aceite.py       ← aceite oliva MAPA (nuevo)
│   └── ingest_ipc.py          ← IPC alimentación INE (adaptar de MEMO)
├── sql/
│   └── 01_schema_and_gold.sql ← schema hosteleria + vistas
├── n8n/
│   └── alertas_workflow.json  ← workflow exportado de n8n
└── tests/
    └── test_hosteleria.py
```

---

## 9. Entregables

- [ ] ETL automatizado con las 4 fuentes
- [ ] Índice de Coste Total funcionando
- [ ] Dashboard Streamlit con lenguaje de hostelero (sin jerga financiera)
- [ ] Alertas WhatsApp funcionando (mínimo: hora valle + resumen semanal)
- [ ] Web de presentación de 1 página para reuniones con clientes
- [ ] README con instrucciones de setup

---

## 10. QA — no entregar sin esto

- [ ] Un hostelero sin conocimientos técnicos entiende cada KPI en menos de 5 segundos
- [ ] Las alertas de WhatsApp llegan correctamente en horario configurado
- [ ] 0 jerga financiera visible en el dashboard (sin "PVPC", sin "futuros", sin "spread")
- [ ] El Índice de Coste Total coincide con los cálculos manuales del punto 4
- [ ] GitHub Actions ejecuta verde 3 días seguidos
- [ ] App carga en menos de 4 segundos

---

## 11. Propuesta de precio para el cliente

| Paquete | Qué incluye | Precio |
|---------|-------------|--------|
| **Setup** | Configuración completa + formación (2h) | 1.500€ único |
| **Mantenimiento Básico** | Dashboard + alertas email | 99€/mes |
| **Mantenimiento Pro** | Dashboard + alertas WhatsApp + resumen PDF semanal | 199€/mes |

**Oferta piloto para los 3 primeros clientes:** Setup 500€ + 99€/mes
a cambio de testimonial y feedback de producto.
