Blindaje de Calidad y Despliegue Automático (CI/CD)

## 1. Filosofía de Operaciones (Reglas de Oro)
Para mitigar el riesgo de la velocidad de la IA, la agencia opera bajo el principio de **Responsabilidad Profesional**: el humano es el único responsable legal del código en producción.
- **Main es Sagrada:** Queda prohibido el push directo a la rama `main`. Toda modificación debe entrar vía **Pull Request (PR)**.
- **Cero Esperanza, Máxima Confianza:** No se asume que el código de la IA funciona; se verifica mediante tests. Código sin tests es deuda técnica por diseño.

## 2. GitHub Actions: El Motor de Automatización
Utilizamos **GitHub Actions** para ejecutar flujos de trabajo en máquinas virtuales cada vez que se detecta un evento en el repositorio.

### Flujo A: Validación de Pull Requests (CI)
Se activa automáticamente en cada PR hacia `main`. El PR se bloquea si falla cualquiera de estos pasos:
1. **Lint & Build:** Verifica que el código (Python/SQL) siga el formato oficial de la agencia definido en `AGENT.md`.
2. **Testing Analítico:** Ejecuta la suite de pruebas (unitarias e integración) para validar que los cálculos de KPIs y la lógica de negocio sigan siendo correctos.
3. **Security Review (Claude Code):** Implementa la acción oficial `claude-code-security-review` de Anthropic para detectar inyecciones SQL, secrets expuestos o lógica insegura generada por la IA.

### Flujo B: Despliegue y Versión (CD)
Tras el merge exitoso en `main`, se activan los procesos de salida:
1. **Deploy Automático:** El código se envía a producción (vía Versel, Supabase o Databricks Jobs) solo si los checks anteriores están en verde.
2. **Release Please (Google):** Automatiza el versionado de la aplicación. Crea un "Release PR" automático que actualiza el historial de cambios.
3. **AI Release Notes:** Un agente de IA resume los cambios técnicos en lenguaje de negocio para el cliente final.

## 3. El Rol del Agente Verificador en el Pipeline
El **Agente Verificador** es el encargado de supervisar estos flujos:
- **Auditoría de PRs:** Antes de la revisión humana, un agente (ej. CodeRabbit) deja comentarios sobre rendimiento y deuda técnica directamente en GitHub.
- **Human in the Loop (HITL):** El paso final de "Merge" siempre requiere la aprobación manual del Arquitecto (Marcos) tras validar los resultados de los agentes de QA.

## 4. Registro de Fallos y Aprendizaje (Engram)
Cualquier error detectado por GitHub Actions o vulnerabilidad bloqueada por Claude debe registrarse en **Engram**:
- **What:** El fallo detectado (ej. Fallo en test de cálculo de ROI).
- **Why:** Causa raíz (ej. La IA usó una división por cero en un caso edge).
- **Where:** Archivo y línea de código.
- **Learned:** Regla nueva para añadir al `agent.md` o `skill-analytics.md` para evitar que se repita.
