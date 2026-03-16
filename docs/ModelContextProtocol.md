Inventario y Guía de Conectividad de la Agencia
Este documento define los servidores del Model Context Protocol que permiten a los agentes de la agencia (Data Engineer, Analyst, Verificador) interactuar con herramientas externas de forma segura y en tiempo real
.
1. Servidor MCP: PostgreSQL (Supabase / Neon)
Este conector es el "ojo" del agente dentro de tus bases de datos. Permite explorar esquemas, ver tipos de datos y relaciones de tablas sin intervención manual
.
Configuración Técnica:
Servidor: postgres (oficial de MCP).
Variables Requeridas: DATABASE_URL (URL de conexión de Supabase).
Capacidades del Agente:
list_tables: Listar tablas de las capas Bronze, Silver y Gold.
describe_table: Ver tipos de columnas y claves primarias/foráneas.
execute_query: Validar queries SQL antes de implementarlas en el código. Usar comentarios y buenas practicas en el código.
Uso Estratégico: Evita que el agente invente nombres de columnas inexistentes
.
2. Servidor MCP: Databricks (SparkSQL & Catalog)
Permite que el Agente Arquitecto gestione la infraestructura de Big Data y la Arquitectura de Medallón directamente desde el entorno de desarrollo
.
Configuración Técnica:
Conector: SQLAlchemy / Databricks SQL
.
Autenticación: Token de Acceso Personal (PAT) guardado como secreto de entorno
.
Capacidades del Agente:
Explorar el Unity Catalog para identificar activos de datos.
Monitorear el estado de los clusters y la ejecución de los jobs de procesamiento
.
Validar la integridad de los datos en la transición de capa Silver a Gold.
3. Servidor MCP: GitHub (Automatización de Ingeniería)
Este servidor es el motor del Agente Verificador y del flujo CI/CD. Permite que la IA gestione el ciclo de vida del código de forma autónoma pero supervisada
.
Configuración Técnica:
Servidor: github (oficial).
Variables Requeridas: GITHUB_PERSONAL_ACCESS_TOKEN.
Capacidades del Agente:
create_branch: Crear ramas de trabajo aisladas (Worktrees)
.
create_pull_request: Abrir peticiones de revisión con resúmenes generados por IA
.
get_issue: Leer requerimientos del cliente registrados como issues
.
search_code: Buscar patrones de código o errores en repositorios históricos de la agencia
.
4. Guía de Instalación (Gentle AI Stack)
Para que los agentes no sufran amnesia y reconozcan estas conexiones en cada sesión, sigue estos pasos:
Instalación del Bridge: Utiliza el instalador Gentle AI Stack para configurar el binario en tu sistema
.
Registro de Servidores: Añade las configuraciones anteriores en tu archivo de configuración del IDE (ej. cursor.json o configuración de Claude Code)
.
Vinculación con Engram: Asegura que el servidor MCP de Engram esté activo para que los hallazgos detectados en Supabase o GitHub se guarden en la memoria persistente del agente
.
5. Reglas de Seguridad (Mandatorio)
Prohibición de Push Directo: El agente nunca tiene permiso para hacer push a main; todo debe pasar por un Pull Request gestionado vía MCP
.
Gestión de Secretos: Ninguna API Key debe estar escrita en este archivo. Deben ser inyectadas como variables de entorno seguras
.
