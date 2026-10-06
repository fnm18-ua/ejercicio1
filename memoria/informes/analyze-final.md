## Informe de análisis de la especificación (segunda pasada)

Análisis de solo lectura de `spec.md`, `plan.md` y `tasks.md` contra la constitución v3.2.0. No he modificado ningún archivo y no hay hooks que ejecutar.

**Resultado**: ningún problema crítico ni alto. Quedan 5 hallazgos medios y 6 bajos. Los 15 de la primera pasada están resueltos, pero cuatro de los medios de ahora los introduje yo al corregir aquellos: la corrección de I7 creó I10, y la propagación de CL-C13 dejó sin actualizar los textos de I11, I12 e I13.

Numero los hallazgos a continuación de los de la primera pasada, porque la especificación ya cita «hallazgo I2» y «hallazgo A1» y reutilizar esos identificadores confundiría.

| ID | Categoría | Severidad | Ubicación | Resumen | Recomendación |
|----|-----------|-----------|-----------|---------|---------------|
| I10 | Inconsistencia | MEDIA | tasks.md:L286, L303 | T042 (fase 11) declara que depende de T044, que está en la fase 12. Ejecutando por orden, T042 se hace antes y las pruebas de T044 ya no fallan primero. | Mover las pruebas de T044 al bloque de pruebas de la fase 11, o aceptar que T044 es una prueba de regresión y quitarle el «deben fallar». |
| I11 | Inconsistencia | MEDIA | tasks.md:L367, L370, L374 | El cierre no cubre la fase 16. T054 enumera las pruebas nuevas sin T058, y T057 limita el alcance a «PD-C07 y PD-C21 a PD-C23», lo que deja fuera PD-C05 y CL-C13. | Añadir T058 a T054, y PD-C05 y CL-C13 a T057. |
| I12 | Inconsistencia | MEDIA | plan.md:L8-12, L34-39, L85 | La nota de actualización y el resumen hablan de «cuatro respuestas» y «cuatro reglas». La tabla de cambios recoge cinco, con D-C21, y hubo dos decisiones posteriores al análisis (CE-C03 y PD-C05). | Actualizar la nota, el resumen y la celda del principio III. |
| I13 | Inconsistencia | MEDIA | plan.md:L143, L145, L166, L169 | En «Trazabilidad de la estructura», la fila de `servicio.py` no cita PD-C05, CL-C13 ni D-C21, y PD-C05 figura en `agenda.py`, que no hace esa comprobación. Las anotaciones de `test_reserva.py` y `test_reprogramacion.py` tampoco citan CL-C13. | Completar la fila y las dos anotaciones. |
| I14 | Inconsistencia (terminología) | MEDIA | spec.md:L29, L95, L521; tasks.md:L37 | La entidad Centro se define como «sede del centro médico». `tasks.md` prohíbe «sede», y «centro» designa a la vez la organización y cada sede. La historia 1 dice «dermatólogo». Es anterior a la actualización; no lo vi en la primera pasada. | Redefinir Centro sin «sede» y decidir si «centro médico» se mantiene para la organización. |
| U4 | Subespecificación | BAJA | spec.md:L121-122, L203-205; tasks.md:L389 | CL-C13 no tiene escenario de aceptación en la historia 1 ni en la 4; el escenario 6 de la historia 1 solo cubre el hueco ya pasado. | Añadir un escenario a la historia 1, o dejarlo como caso límite, que ya es comprobable. |
| I15 | Inconsistencia | BAJA | spec.md:L8-9, L413-414 | El estado remite a «Aclaraciones», pero las decisiones sobre CE-C03 y PD-C05 no figuran allí, solo en sus notas de origen. PD-C07 no cita la decisión que cambió su criterio. | Citar la decisión en PD-C07 y ajustar la remisión del estado. |
| I16 | Inconsistencia | BAJA | spec.md:L246-247, L254 | Los escenarios 8 y 10 de la historia 5 describen el mismo rechazo con dos textos: «el rango ya ha pasado» y «la fecha y la hora de fin ya han pasado». El contrato tiene un único mensaje. | Unificar la redacción del escenario 8. |
| I17 | Inconsistencia | BAJA | contracts/interfaz-web-citas.md (ruta 11); quickstart.md:L123 | La fila «Aplicado» de la ruta 11 no menciona el motivo, y los pasos de validación manual de las confirmaciones no lo comprueban. `quickstart.md` no menciona CL-C13. | Añadir el motivo a la fila y a los dos pasos. |
| I18 | Inconsistencia | BAJA | tasks.md:L389 | T058 agrupa dos archivos y una prueba de reprogramación bajo la etiqueta de la historia 1. | Aceptable; si se quiere, separar la prueba de reprogramación en otra tarea. |
| I19 | Estilo | BAJA | spec.md:L422-424, L495-499 | PD-C07 y PD-C22 tienen saltos de línea rotos por las ediciones sucesivas. | Reajustar los párrafos. |

**Resumen de cobertura**

| Requisito | ¿Tiene tarea? | Tareas | Notas |
|-----------|---------------|--------|-------|
| RF-C01, RF-C02, RF-C05 | Sí | T011, T012, T015 a T018 | Completadas |
| RF-C03, RF-C04 | Sí | T013 a T015, T058, T059 | Actualización: PD-C05, CL-C13 |
| RF-C06 | Sí | T019 a T022, T040 a T043 | Actualización: CL-C10 |
| RF-C07 | Sí | T023 a T025, T044 a T046, T058 | Actualización: CL-C10, CL-C13 |
| RF-C08 | Sí | T026 a T028, T047 a T050 | Actualización: PD-C22, PD-C23, CL-C12 |
| RF-C09 | Sí | T029 a T031, T051 a T053 | Actualización: PD-C21, CL-C11 |
| CE-C01, CE-C02 | Sí | T011, T013, T026, T029, T058 | |
| CE-C03 | Sí | T011, T023 | Acotado a reserva y reprogramación |
| CE-C04 a CE-C07 | Sí | T011, T016, T023, T026, T029, T040 a T053 | |
| CE-C08 | Sí | T035, T054, T058 | 13 CA-C y 13 CL-C; T054 no cita T058 (I11) |
| CE-C09 | Sí | T032 | |
| CE-C10 | Sí | T048, T050, T052 | Ya completo: T052 comprueba el motivo |

**Alineación con la constitución**: no veo ninguna infracción de un principio obligatorio. El único punto dudoso es I14: el principio I no admite sinónimos de «centro», y la especificación usa «sede» para definirlo. Lo clasifico como medio y no como crítico porque aparece en la definición del término, no como nombre alternativo en requisitos, código ni mensajes. Con una lectura estricta del principio I sería una infracción, y se elimina cambiando una frase.

**Limitación aceptada que no cuento como hallazgo**: RN-C07 prohíbe los solapamientos sin excepción y PD-C20 admite uno. Lo decidiste expresamente y consta en CE-C03 y en «Supuestos».

**Tareas sin requisito asociado**: ninguna. T038 queda ya recogida en el plan.

**Métricas**

- Requisitos analizados: 19 (9 funcionales y 10 criterios de éxito), con 13 reglas de negocio, 23 precisiones y 13 casos límite de apoyo
- Tareas: 59 (37 completadas, 22 pendientes)
- Cobertura: 100 % (19 de 19)
- Ambigüedades: 0
- Duplicaciones: 0
- Problemas críticos: 0

## Siguientes acciones

Puedes pasar a `/speckit-implement`. Antes conviene corregir los dos que afectan a la ejecución de las tareas:

1. **I10**: tal como está, quien siga el orden de `tasks.md` incumple la dependencia que la propia T042 declara.
2. **I11**: si la fase 16 se hace antes del cierre, T057 daría por fuera de alcance el trabajo de CL-C13.

I12, I13 e I17 son ajustes de texto en `plan.md` y en los artefactos secundarios. I14 es una decisión tuya sobre el vocabulario.

¿Quieres que te proponga las ediciones concretas para los cinco hallazgos medios? No aplicaré ninguna sin tu aprobación.
