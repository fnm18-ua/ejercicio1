## Informe de análisis de la especificación

Análisis de solo lectura de `spec.md`, `plan.md` y `tasks.md` del módulo de programación de citas, contra la constitución v3.2.0. No he modificado ningún archivo y no hay hooks que ejecutar.

**Resultado**: ningún problema crítico. Hay 2 hallazgos altos, 8 medios y 5 bajos. Casi todos están en `spec.md`: son frases que quedaron con la redacción anterior tras tus dos correcciones (franja pasada y motivo de cancelación).

| ID | Categoría | Severidad | Ubicación | Resumen | Recomendación |
|----|-----------|-----------|-----------|---------|---------------|
| I1 | Inconsistencia | ALTA | spec.md:L578-581 frente a L480-492 | El supuesto «Bloqueos sobre fechas pasadas» dice que un rango que «acaba hoy o después sí se acepta». PD-C23 y CL-C12 rechazan el bloqueo de hoy cuyo tramo ya terminó. | Reescribir el supuesto con el criterio de PD-C23: fecha y hora de fin ya pasadas. |
| I2 | Inconsistencia | ALTA | spec.md:L539-540 frente a L458-461 y L582-584 | CE-C03 exige 0 solapamientos «en ningún momento», pero PD-C20 admite que un cambio de duración deje dos citas del mismo paciente solapadas, y hay una prueba que lo comprueba. Es anterior a esta actualización. | Acotar CE-C03 a reservas y reprogramaciones, con la excepción de PD-C20, o resolver PD-C20. |
| I3 | Inconsistencia | MEDIA | spec.md:L81-84, L452-453, L518-523 | Tres frases conservan el criterio «solo por fecha»: la entrada de la pregunta 4, PD-C18 («rango ya pasado») y la entidad «Franja bloqueada». | Alinearlas con PD-C23. |
| I4 | Inconsistencia | MEDIA | spec.md:L77-80, L469-474 | La entrada de la pregunta 3 dice «número, fecha y hora». PD-C22 añade el motivo y cita esa pregunta como origen, pero ninguna entrada recoge tu decisión de conservarlo (principio III). | Añadir a «Aclaraciones» la decisión del 2026-10-06 y citarla en PD-C22. |
| U1 | Subespecificación | MEDIA | spec.md:L239-241; tasks.md:L323 | El escenario 8 de la historia 5 solo cubre la fecha de fin anterior a hoy. T047 prueba además el bloqueo de hoy ya terminado y el de hoy sin terminar, sin escenario de aceptación detrás. | Añadir los dos escenarios a la historia 5. |
| U2 | Subespecificación | MEDIA | spec.md:L236-238, L278-280 | El escenario 7 de la historia 5 y el 6 de la historia 6 no comprueban el motivo que PD-C22 y CE-C10 exigen mostrar. | Añadir el motivo a los dos escenarios. |
| U3 | Subespecificación | MEDIA | spec.md:L229-231 | El escenario 4 de la historia 5 bloquea «una franja que cubre» una cita pasada. Si la franja está entera en el pasado, PD-C23 la rechaza y el escenario no se puede ejecutar. | Precisar que la fecha y hora de fin de la franja aún no han llegado. |
| A1 | Ambigüedad | MEDIA | spec.md:L384-386, L393-394, L418-419 | PD-C07 llama «el mismo criterio» a PD-C05 y PD-C11, pero difieren en el instante exacto del inicio. Un hueco que empieza justo ahora se puede reservar (`servicio.py:368`), y esa cita ya cuenta como pasada y no se puede cancelar. | Fijar en PD-C05 qué ocurre cuando el inicio coincide con el momento actual. |
| C1 | Cobertura | MEDIA | tasks.md:L348; plan.md:L196 | CE-C10 exige el motivo en las dos confirmaciones. T048 lo comprueba en el bloqueo, pero T052 no lo comprueba en el cambio de duración, y la fila de pruebas del plan tampoco lo menciona. | Añadir a T052 la comprobación del motivo «Cambio de la duración de las consultas». |
| I5 | Inconsistencia | MEDIA | plan.md:L175-212; tasks.md:L259 | T038 modifica `tests/utilidades_citas.py` para fijar el reloj, pero «Cambios respecto al plan implementado» no recoge ni ese archivo ni el fallo previsto para el 2026-10-08. | Añadir una fila al plan con el cambio y su motivo (D-C10). |
| I6 | Inconsistencia | BAJA | tasks.md:L390-404 frente a L324, L348 | El grafo presenta las historias 5 y 6 como rama independiente de la 3 y la 4, pero T048 depende de T045 y T052 de T048 por compartir `tests/test_web_citas.py`. | Aclarar que es una dependencia de archivo, no funcional. |
| I7 | Inconsistencia | BAJA | tasks.md:L298-300 | La fase 12 dice que sus pruebas «deben fallar», pero si T044 se escribe después de T042 ya pasa, porque el servicio es compartido. | Indicar que T044 debe escribirse antes de T042. |
| I8 | Inconsistencia | BAJA | tasks.md:L50 | Las convenciones dicen que `app.py` se toca «solo en T005»; la tarea que lo modifica es T008. Es anterior a esta actualización. | Corregir la referencia. |
| I9 | Inconsistencia | BAJA | spec.md:L8 | El estado sigue siendo «Borrador», con el módulo implementado y dos sesiones de aclaraciones cerradas. | Actualizar el estado. |
| C2 | Cobertura | BAJA | tasks.md:L323 | Los casos de franja mal formada de CL-C12 los verifican pruebas existentes llamadas `test_rfc08_…`, sin el identificador CL-C12 que pide la convención de nombres. | Citar CL-C12 en sus *docstrings* dentro de T047, sin renombrarlas. |

**Resumen de cobertura**

| Requisito | ¿Tiene tarea? | Tareas | Notas |
|-----------|---------------|--------|-------|
| RF-C01 a RF-C05 | Sí | T011 a T018 | Completadas; sin cambios en la actualización |
| RF-C06 | Sí | T019 a T022, T040 a T043 | Actualización: cita pasada (CL-C10) |
| RF-C07 | Sí | T023 a T025, T044 a T046 | Actualización: cita pasada (CL-C10) |
| RF-C08 | Sí | T026 a T028, T047 a T050 | Actualización: PD-C22, PD-C23, CL-C12 |
| RF-C09 | Sí | T029 a T031, T051 a T053 | Actualización: PD-C21, CL-C11 |
| CE-C01, CE-C02 | Sí | T011, T013, T026, T029 | |
| CE-C03 | Sí | T011, T023 | En conflicto con PD-C20 (I2) |
| CE-C04 a CE-C07 | Sí | T011, T016, T023, T026, T029, T040 a T052 | |
| CE-C08 | Sí | T035, T054 | 13 CA-C y 12 CL-C |
| CE-C09 | Sí | T032 | |
| CE-C10 | Parcial | T048, T050, T052 | Falta comprobar el motivo en la ruta 11 (C1) |

**Alineación con la constitución**: no hay ninguna infracción de un principio obligatorio. I1 e I4 rozan el principio III (trazabilidad): el diseño sigue una decisión tuya explícita, pero la especificación conserva texto que dice otra cosa.

**Tareas sin requisito asociado**: T038, que fija el reloj de las pruebas web. Se apoya en la decisión D-C10 del plan y en CE-C08, no en un requisito propio; está justificada, pero el plan no la recoge (I5).

**Métricas**

- Requisitos analizados: 19 (9 funcionales y 10 criterios de éxito), con 13 reglas de negocio, 23 precisiones y 12 casos límite de apoyo
- Tareas: 57 (37 completadas, 20 pendientes)
- Cobertura: 100 % (19 de 19 con al menos una tarea; CE-C10 parcial)
- Ambigüedades: 1
- Duplicaciones: 0
- Problemas críticos: 0

## Siguientes acciones

Puedes pasar a `/speckit-implement`: las tareas siguen PD-C23 y PD-C22, que son las redacciones que tú fijaste. Antes conviene:

1. **Corregir `spec.md`** a mano (I1, I3, I4, U1, U2, U3). Son las frases que ya te había señalado dos veces, más las del motivo.
2. **Ampliar T052** en `tasks.md` para comprobar el motivo en el cambio de duración (C1).
3. **Añadir a `plan.md`** la fila de T038 (I5).

I2 y A1 son decisiones tuyas: cómo acotar CE-C03 frente a PD-C20, y qué ocurre en el instante exacto del inicio de una cita.

¿Quieres que te proponga las ediciones concretas para los hallazgos altos y medios? No aplicaré ninguna sin tu aprobación.
