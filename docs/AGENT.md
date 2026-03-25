AGENT.md — Reglas de Operación de la Agencia
1. Perfil y filosofía
Actúa como Senior Analytics Engineer. El objetivo es entregar valor de datos
real a clientes reales en el menor tiempo posible, sin deuda técnica invisible.
Mindset: "El humano define el problema, la IA ejecuta con precisión."
Responsabilidad: La IA genera el código. El humano es el único responsable
profesional del resultado en producción.

2. Stack oficial (lo que realmente usamos)
CapaHerramientaNotasBase de datosNeon.tech (PostgreSQL)Proyectos ilimitados en freeETL + CI/CDGitHub ActionsSchedule L-V, ejecución manual para backfillDashboardStreamlit Community CloudDeploy desde GitHub, gratisAlertasn8n cloudFree tier — pendiente implementar en proyectos
AgroTech Extremadura usa Supabase (proyecto anterior). Los proyectos nuevos
de la agencia usan Neon.tech. No mezclar.

3. Reglas de oro

Spec-first: nunca escribir código sin spec.md completado y validado
Main es sagrada: todo cambio entra por Pull Request, nunca push directo
Backfill por defecto: todo proyecto arranca con mínimo 20 días de histórico
0 credenciales en el repo: siempre variables de entorno o GitHub Secrets
Sin jerga técnica visible: cada KPI entendible en menos de 5 segundos
Tests antes de entregar: pytest tests/ -v debe pasar en verde
CONTEXT.md siempre actualizado: es la memoria de la agencia


4. Flujo de trabajo por proyecto
spec.md validado
    → SQL en Neon (schema + vistas Gold)
    → ETL adaptado + backfill ejecutado
    → Dashboard desplegado
    → Checklist completo (ver HOWTO.md)
    → CONTEXT.md actualizado

5. SQL — arquitectura real
Los proyectos usan un solo archivo SQL por simplicidad:
sql/01_schema_and_gold.sql — tablas de ingesta + vistas Gold directamente.
La separación Bronze/Silver/Gold en archivos distintos está reservada para
proyectos con múltiples fuentes complejas que lo justifiquen.

6. Gestión de contexto entre sesiones
Al iniciar una sesión nueva con Claude u otra IA:

Pegar el contenido de CONTEXT.md
Indicar el proyecto activo
La IA tiene contexto completo sin reexplicar nada

Al terminar la sesión:

Actualizar CONTEXT.md con cambios y decisiones del día
Commit con mensaje descriptivo
