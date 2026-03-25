Workflows.MD — Automatización y CI/CD
1. Filosofía
Main es sagrada. Todo cambio entra por Pull Request. El humano aprueba
el merge tras revisar que los checks están en verde.
Cero deuda técnica invisible. Código sin tests es deuda por diseño.
Todo proyecto entrega con pytest tests/ -v en verde.

2. Workflows activos en el repo
ArchivoProyectoQué haceScheduleenergia_mercados.ymlenergia-mercadosETL diario (PVPC + macro + mercados)L-V 07:00 UTCenergia_mercados_hosteleria.ymlenergia-mercados-hosteleriaETL diario (PVPC + gas + aceite + IPC)L-V 07:30 UTCbackfill.ymlenergia-mercadosCarga histórica manualmanualbackfill_hosteleria.ymlenergia-mercados-hosteleriaCarga histórica manualmanual

3. Crear un workflow nuevo
Copiar _template/backfill.yml.example y reemplazar los tres placeholders:

[NOMBRE PROYECTO] → nombre descriptivo
[NOMBRE-CARPETA] → nombre exacto de la carpeta en projects/
[NOMBRE_SECRET] → nombre del secret en GitHub Settings

Regla: nombres de archivo .yml sin espacios ni caracteres especiales.
Los nombres con guiones largos o caracteres raros causan que GitHub Actions
no detecte cambios correctamente.

4. Errores frecuentes en Actions
SíntomaCausaSoluciónETL ejecuta código viejoCaché de pipActions → Caches → borrar todospytest no encuentra tests/working-directory globalPoner working-directory por paso individualWorkflow no se activaNombre .yml con caracteres especialesRenombrar con nombre simplemodule not foundPaquete no en requirements.txtAñadir y hacer commit

5. Proceso de Pull Request

Crear rama desde main con nombre descriptivo (fix/etl-energia, feat/kpi-margen)
Hacer los cambios
Abrir PR hacia main
Revisar que el ETL ejecuta en verde (si aplica)
Merge — solo el autor del proyecto (Marcos)

No hay CI automático implementado aún. La revisión es manual en esta fase.
Cuando haya 3+ proyectos activos, evaluar añadir checks automáticos de lint y tests.

6. Registro de decisiones técnicas
Cualquier decisión técnica relevante (cambio de fuente de datos, nuevo patrón ETL,
error resuelto) se documenta en CONTEXT.md en la sección "Errores resueltos"
o "Decisiones técnicas consolidadas". No en este archivo.
