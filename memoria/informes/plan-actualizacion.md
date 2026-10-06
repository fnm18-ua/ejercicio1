# Informe de la actualización del plan (`/speckit-plan`)

**Fecha**: 2026-10-06

**Funcionalidad**: Módulo de Programación de Citas

**Rama**: `002-programacion-citas` (carpeta de la funcionalidad; se trabaja sobre `master`)

**Plan**: `specs/002-programacion-citas/plan.md`

## Resumen de la actualización

El plan ya existía y estaba implementado, así que se actualizó en vez de regenerarse. La
actualización lleva al diseño las cuatro respuestas de la sesión de aclaraciones del 2026-10-06
(PD-C07 reescrita, PD-C21 a PD-C23, CL-C10 a CL-C12 y CE-C10).

No cambian la tecnología, la estructura del proyecto ni el esquema de datos: las cuatro reglas
nuevas van al servicio y a la interfaz, sin migración. En esta ejecución no se tocó código ni
pruebas. No existe `.specify/extensions.yml`, así que no había hooks que ejecutar. La puerta de
la constitución (v3.2.0) se supera antes de la fase 0 y tras la fase 1, sin violaciones.

## Artefactos actualizados

Todos están en `specs/002-programacion-citas/`.

| Artefacto | Qué cambia |
|---|---|
| `plan.md` | Nota de actualización, puerta de la constitución revisada (se supera), trazabilidad ampliada y sección nueva «Cambios respecto al plan implementado» |
| `research.md` | Cuatro decisiones nuevas, D-C17 a D-C20 |
| `data-model.md` | Reglas de validación de la duración y de la franja, una transición prohibida más y dos invariantes nuevos |
| `contracts/servicio-citas.md` | Error nuevo `CitaPasada`, orden de comprobaciones, validaciones previas y tres mensajes nuevos |
| `contracts/interfaz-web-citas.md` | Respuestas nuevas en las rutas 6, 7, 8, 10 y 11, y contenido de la confirmación al administrativo |
| `quickstart.md` | Pasos de validación manual para CL-C10 a CL-C12 y PD-C22 |

No se modificaron `spec.md`, `tasks.md` ni `checklists/requirements.md`.

## Decisiones de diseño tomadas

| Decisión | Contenido | Requisito |
|---|---|---|
| D-C17 · Cita pasada | Se comprueba antes que el plazo de 24 horas y responde `409` con «No se puede cancelar ni reprogramar una cita cuya hora ya ha pasado.». | PD-C07, CL-C10 |
| D-C18 · Duración válida | Se rechaza con `400` si supera los minutos del horario. Con horario de 9:00 a 13:00 se aceptan de 1 a 240 minutos. | PD-C21, CL-C11 |
| D-C19 · Confirmación al administrativo | Muestra solo número, fecha y hora. Además del código de historia clínica se retira el motivo de cada línea, porque la especificación no pide mostrarlo. | PD-C22, CE-C10 |
| D-C20 · Franja pasada | Se rechaza con `400` cuando su fecha y hora de fin no son posteriores al momento actual. | PD-C23, CL-C12 |

La retirada del motivo por línea (D-C19) es una decisión del plan, no una respuesta de la sesión
de aclaraciones: queda pendiente de que la persona responsable la confirme o pida conservarlo.

## Sección «Cambios respecto al plan implementado» del plan

Copia literal de la sección de `specs/002-programacion-citas/plan.md`.

---

## Cambios respecto al plan implementado

Lo que la actualización del 2026-10-06 obliga a modificar en lo ya construido. No se crea ningún
archivo de código ni de pruebas, no cambia el esquema y no hace falta migrar datos.

| Archivo | Cambio | Requisito | Decisión |
|---|---|---|---|
| `programacion_citas/servicio.py` | Error nuevo `CitaPasada`; la comprobación de plazo rechaza primero la cita cuyo inicio no es posterior a `ahora`. Afecta a cancelar y a reprogramar. | PD-C07, CL-C10, PD-C18 | D-C17 |
| `programacion_citas/servicio.py` | `ajustar_duracion` rechaza la duración que supera la amplitud del horario, antes de actualizar. | PD-C21, CL-C11 | D-C18 |
| `programacion_citas/servicio.py` | `bloquear_franja` rechaza la franja cuya fecha y hora de fin no son posteriores a `ahora`. Las dos validaciones de forma ya existían y pasan a estar trazadas. | PD-C23, CL-C12 | D-C20 |
| `programacion_citas/web.py` | Las rutas 6, 7 y 8 responden `409` con el mensaje de cita pasada. | CL-C10 | D-C17 |
| `programacion_citas/web.py` | La confirmación de las rutas 10 y 11 muestra solo número, fecha y hora: se retiran el código de historia clínica y el motivo por línea. | PD-C22, CE-C10 | D-C19 |

**Pruebas nuevas**, en los archivos existentes:

| Archivo | Prueba | Verifica |
|---|---|---|
| `tests/test_cancelacion.py` | Cancelar una cita pasada reservada con menos de 24 horas de antelación se rechaza con `CitaPasada` y la cita sigue reservada | CL-C10, PD-C07 |
| `tests/test_reprogramacion.py` | Reprogramar una cita pasada se rechaza con `CitaPasada` y conserva fecha y hora | CL-C10, PD-C07 |
| `tests/test_duracion.py` | 300 minutos en un horario de 9:00 a 13:00 se rechaza, la duración sigue en 20 y ninguna cita se cancela; 240 minutos se acepta | CL-C11, PD-C21 |
| `tests/test_bloqueo.py` | Franja con fecha de fin anterior a hoy se rechaza; franja de hoy con el tramo ya terminado se rechaza; franja de hoy de 9:00 a 14:00 a las 11:00 se acepta; en los rechazos no se registra la franja | CL-C12, PD-C23 |
| `tests/test_web_citas.py` | La confirmación de las rutas 10 y 11 contiene el número, la fecha y la hora, y no contiene el código de historia clínica del paciente | PD-C22, CE-C10 |
| `tests/test_web_citas.py` | Las rutas 6 y 8 responden `409` ante una cita pasada; las rutas 10 y 11 responden `400` ante la franja pasada y la duración sin hueco | CL-C10, CL-C11, CL-C12 |

**Pruebas existentes que dejan de ser válidas** y hay que adaptar:

- `tests/test_bloqueo.py::test_pdc11_el_bloqueo_no_altera_una_cita_pasada` bloquea una franja
  entera en el pasado, que ahora se rechaza (PD-C23). Debe usar una franja que cubra la cita
  pasada y cuyo fin aún no haya llegado.
- `tests/test_web_citas.py::test_ruta10_bloquear_confirma_las_canceladas` comprueba que la
  confirmación contiene el motivo de cancelación, que deja de mostrarse (D-C19).

Puede haber alguna más que bloquee franjas pasadas; se detectará al ejecutar la batería completa.
