# Informe de la actualización de tareas (`/speckit-tasks`)

**Fecha**: 2026-10-06

**Funcionalidad**: Módulo de Programación de Citas

**Archivo de tareas**: `specs/002-programacion-citas/tasks.md`

## Resumen de la actualización

`tasks.md` ya existía con 37 tareas (T001 a T037), todas completadas. Se conservan como
historial y se añadieron 20 tareas nuevas, T038 a T057, en las fases 10 a 15. Llevan al código
las cuatro respuestas de la sesión de aclaraciones del 2026-10-06, según la sección «Cambios
respecto al plan implementado» de `plan.md`.

En esta ejecución no se tocó código ni pruebas. No existe `.specify/extensions.yml`, así que no
había hooks que ejecutar.

| Dato | Valor |
|---|---|
| Tareas completadas que se conservan | 37 (T001 a T037) |
| Tareas nuevas, pendientes | 20 (T038 a T057) |
| Total | 57 |
| Formato | Las 57 cumplen el formato de lista: casilla, identificador, marcas `[P]` y `[USn]` donde corresponde, y ruta de archivo |

## Tareas añadidas

### Por fase

| Fase | Contenido | Tareas | Número |
|---|---|---|---|
| 10 · Base de la actualización | Reloj fijo en las pruebas web y error nuevo `CitaPasada` | T038, T039 | 2 |
| 11 · Historia de usuario 3 | Una cita pasada no se cancela | T040 a T043 | 4 |
| 12 · Historia de usuario 4 | Una cita pasada no se reprograma | T044 a T046 | 3 |
| 13 · Historia de usuario 5 | Franjas válidas y confirmación sin datos del paciente | T047 a T050 | 4 |
| 14 · Historia de usuario 6 | Duración de consulta válida | T051 a T053 | 3 |
| 15 · Cierre de la actualización | Batería completa, alcance, contenedor y constitución | T054 a T057 | 4 |

Las historias de usuario 1 y 2 no tienen tareas nuevas, porque las aclaraciones del 2026-10-06 no
las afectan.

### Una por una

| Tarea | Marcas | Archivo | Qué hace | Requisito |
|---|---|---|---|---|
| T038 | [P] | `tests/utilidades_citas.py` | Fija el momento actual en las pruebas web sustituyendo `servicio.momento_actual` por `MOMENTO_FIJO` | D-C10, D-C15 |
| T039 | [P] | `programacion_citas/servicio.py` | Define la excepción `CitaPasada` con su mensaje; todavía no la lanza nadie | PD-C07, PD-C18, CL-C10 |
| T040 | [P] [US3] | `tests/test_cancelacion.py` | Cuatro pruebas: cita pasada reservada con menos de 24 horas, cita pasada reservada con antelación, justo a la hora de inicio y un minuto antes | CL-C10, PD-C07 |
| T041 | [US3] | `tests/test_web_citas.py` | Prueba de que la ruta 6 responde `409` ante una cita pasada | CL-C10 |
| T042 | [US3] | `programacion_citas/servicio.py` | `_comprobar_plazo` lanza `CitaPasada` antes de cualquier otra comprobación | PD-C07, CL-C10, D-C17 |
| T043 | [US3] | `programacion_citas/web.py` | La ruta 6 responde `409` con el mensaje de cita pasada | CL-C10, PD-C18 |
| T044 | [P] [US4] | `tests/test_reprogramacion.py` | Dos pruebas: reprogramar una cita pasada se rechaza y conserva fecha y hora; el rechazo por cita pasada precede al de plazo | CL-C10, PD-C07 |
| T045 | [US4] | `tests/test_web_citas.py` | Pruebas de que las rutas 7 y 8 responden `409` ante una cita pasada | CL-C10 |
| T046 | [US4] | `programacion_citas/web.py` | Las rutas 7 y 8 responden `409` con el mensaje de cita pasada | CL-C10, PD-C18 |
| T047 | [P] [US5] | `tests/test_bloqueo.py` | Adapta `test_pdc11_el_bloqueo_no_altera_una_cita_pasada` y añade seis pruebas de franjas rechazadas y aceptadas | PD-C23, CL-C12, D-C20 |
| T048 | [US5] | `tests/test_web_citas.py` | Adapta `test_ruta10_bloquear_confirma_las_canceladas` y añade la prueba de franja pasada con `400` | PD-C22, CE-C10, CL-C12 |
| T049 | [US5] | `programacion_citas/servicio.py` | `bloquear_franja` rechaza la franja cuya fecha y hora de fin no son posteriores a `ahora` | PD-C23, CL-C12, D-C20 |
| T050 | [US5] | `programacion_citas/web.py` | `_confirmar_canceladas` muestra solo fecha y hora de cada cita; vale para las rutas 10 y 11 | PD-C22, CE-C10, D-C19 |
| T051 | [P] [US6] | `tests/test_duracion.py` | Tres pruebas: 300 minutos se rechaza sin cambiar nada, 241 se rechaza y 240 se acepta | PD-C21, CL-C11, D-C18 |
| T052 | [US6] | `tests/test_web_citas.py` | Pruebas de que la ruta 11 responde `400` sin hueco posible y de que su confirmación no muestra datos del paciente | PD-C21, PD-C22, CL-C11, CE-C10 |
| T053 | [US6] | `programacion_citas/servicio.py` | `ajustar_duracion` rechaza la duración que supera la amplitud del horario, antes de actualizar | PD-C21, CL-C11, D-C18 |
| T054 | — | — | Ejecutar `python -m unittest` y comprobar que pasa entera | CE-C08, CE-C10 |
| T055 | — | — | Revisar con `git diff --name-only` que solo se han tocado los ocho archivos permitidos | Principio III, D-C03 |
| T056 | — | — | `docker compose up --build` y recorrer los pasos nuevos de `quickstart.md` | CL-C10 a CL-C12, PD-C22, PD-C23 |
| T057 | — | — | Repasar la tabla de comprobación de la constitución contra los cambios | Constitución v3.2.0 |

En cada historia, las tareas de pruebas van antes que las de implementación.

### Dependencias y paralelismo

```text
Fase 10 ─┬→ US3 (fase 11) → US4 (fase 12) ─┐
         └→ US5 (fase 13) → US6 (fase 14) ─┴→ Fase 15
```

- La fase 10 bloquea las fases 11 a 14.
- La historia 4 depende de la 3, porque reprogramar reutiliza la comprobación que cambia T042.
- La historia 6 depende de T050 de la historia 5 solo para la prueba de la confirmación (T052),
  porque las rutas 10 y 11 comparten `_confirmar_canceladas`.
- T038 y T039 pueden hacerse a la vez.
- Las cuatro tareas de pruebas del servicio (T040, T044, T047 y T051) tocan archivos distintos y
  pueden escribirse a la vez tras la fase 10.
- Las tareas de pruebas web (T041, T045, T048 y T052) no se marcan `[P]`: todas editan
  `tests/test_web_citas.py`. Las de implementación tampoco: comparten `servicio.py` y `web.py`.

### Orden de entrega sugerido

El MVP original (historia 1) y las seis historias ya están entregados. De la actualización:

1. Fase 10: las pruebas web dejan de depender de la fecha real. Es lo más urgente.
2. Historias 3 y 4: se corrige el defecto que permitía cancelar o reprogramar una cita ya
   celebrada. Es el primer incremento con valor propio.
3. Historia 5: el administrativo deja de ver el código de historia clínica y las franjas pasadas
   se rechazan.
4. Historia 6: una duración imposible ya no cancela todas las citas.
5. Fase 15: cierre y validación en contenedor.

## Hallazgo: las pruebas web dependen del reloj real

Este hallazgo no viene de la sesión de aclaraciones. Apareció al preparar las tareas.

### Qué ocurre

- `programacion_citas/web.py` consulta el reloj real en cada ruta, con
  `servicio.momento_actual()` (líneas 257, 294, 354, 382, 404, 438, 551 y 570).
- Las pruebas de `tests/test_web_citas.py` usan `fecha_futura()`, que se calcula a partir de la
  constante `MOMENTO_FIJO = datetime.datetime(2026, 10, 1, 8, 0, 0)` más siete días: la fecha
  fija **2026-10-08**.
- Las pruebas del servicio no tienen el problema, porque pasan `ahora=MOMENTO_FIJO` como
  parámetro. Las pruebas web no fijan el momento actual, en contra de lo que decide D-C10 («en
  las pruebas se sustituye por un momento fijo»).

Mientras la fecha real sea anterior al 2026-10-08, esa fecha es futura y las pruebas pasan. Cuando
deje de serlo, los huecos y las citas de esas pruebas estarán en el pasado.

### Evidencia

**1. Estado de partida, con el reloj real (2026-10-06)**

```text
python -m unittest
Ran 167 tests in 38.983s
OK
```

**2. Simulación del 9 de octubre de 2026 a las 10:00**

Se ejecutó `tests.test_web_citas` sustituyendo `servicio.momento_actual` por una función que
devuelve `datetime.datetime(2026, 10, 9, 10, 0, 0)`, sin modificar ningún archivo:

```python
import datetime, unittest
from unittest import mock
from programacion_citas import servicio
with mock.patch.object(servicio, 'momento_actual',
                       return_value=datetime.datetime(2026, 10, 9, 10, 0, 0)):
    suite = unittest.defaultTestLoader.loadTestsFromName('tests.test_web_citas')
    r = unittest.TextTestRunner(verbosity=0).run(suite)
    print('FALLOS:', [t.id().split('.')[-1] for t, _ in r.failures + r.errors])
```

Resultado:

```text
Ran 29 tests in 22.303s
FAILED (failures=8, errors=2)
```

Las 10 pruebas que fallan, de las 29 del archivo:

| # | Prueba | Tipo |
|---|---|---|
| 1 | `test_ruta10_bloquear_confirma_las_canceladas` | Fallo |
| 2 | `test_ruta3_huecos_muestra_la_rejilla` | Fallo |
| 3 | `test_ruta4_hueco_ocupado_responde_409` | Fallo |
| 4 | `test_ruta4_reservar_redirige_al_listado` | Fallo |
| 5 | `test_ruta6_cancelar_cita_ya_cancelada_responde_409` | Fallo |
| 6 | `test_ruta6_cancelar_redirige_al_listado` | Fallo |
| 7 | `test_ruta7_reprogramar_ofrece_huecos_del_mismo_especialista` | Fallo |
| 8 | `test_ruta8_reprogramar_redirige_y_conserva_el_identificador` | Fallo |
| 9 | `test_ruta5_listado_muestra_estado_y_motivo` | Error |
| 10 | `test_ruta7_reprogramar_cita_cancelada_responde_409` | Error |

El último fallo que mostró la salida fue `AssertionError: 409 != 303`: una operación que debía
redirigir se rechaza como regla de negocio incumplida, que es lo esperable cuando el hueco o la
cita ya han pasado. La salida se recortó a las últimas líneas, así que no consta el mensaje de
cada una de las diez.

**3. Comprobación de la corrección propuesta en T038**

Se ejecutó el mismo archivo sustituyendo `servicio.momento_actual` por una función que devuelve
`MOMENTO_FIJO`:

```text
T038 con reloj fijo -> ejecutadas 29 fallos 0
```

Con el reloj fijado, las 29 pruebas web siguen pasando sin tocar ninguna.

### Alcance de la evidencia

- Lo comprobado es el **9 de octubre a las 10:00**. Que la batería empiece a fallar el
  2026-10-08 es una deducción a partir de que `fecha_futura()` vale 2026-10-08; no se simuló ese
  día ni la hora exacta en que empieza cada fallo.
- Solo se simuló `tests.test_web_citas`. Los demás archivos de pruebas del módulo pasan el momento
  actual como parámetro y no deberían verse afectados, pero no se ejecutaron con el reloj
  adelantado.

### Cómo queda recogido en las tareas

T038 fija el momento actual en `ServidorCitasTestCase.setUp` con
`unittest.mock.patch.object(servicio, "momento_actual", return_value=MOMENTO_FIJO)`. Es la primera
tarea de la actualización y bloquea las fases 11 a 14, porque las pruebas web nuevas (T041, T045,
T048 y T052) también dependen de un momento actual conocido.

## Pruebas independientes de cada historia

Cada historia de la actualización se puede validar por separado:

| Historia | Prueba independiente | Resultado esperado |
|---|---|---|
| 3 · Una cita pasada no se cancela | Reservar una cita con menos de 24 horas de antelación, situar el momento actual después de su inicio e intentar cancelarla | Se rechaza con el motivo propio («No se puede cancelar ni reprogramar una cita cuya hora ya ha pasado.») y la cita sigue reservada |
| 4 · Una cita pasada no se reprograma | Con una cita cuya hora ya ha pasado, intentar trasladarla a un hueco libre | Se rechaza con el mismo motivo y la cita conserva su fecha y su hora |
| 5 · Franjas válidas y confirmación sin datos del paciente | Intentar bloquear una franja de ayer, una de hoy ya terminada y una de hoy aún sin terminar; bloquear una franja con una cita dentro | Las dos primeras se rechazan y la tercera se acepta; la confirmación indica el número de citas canceladas y la fecha y la hora de cada una, y no contiene el código de historia clínica del paciente |
| 6 · Duración de consulta válida | Con un especialista de horario de 9:00 a 13:00 y una cita futura, intentar pasar la duración a 300 minutos; después probar con 240 | Con 300 se rechaza, la duración sigue en 20 y la cita sigue reservada; con 240 se acepta, porque cabe un hueco |

Puntos de control que fija `tasks.md` al final de cada fase:

- **Fase 10**: `python -m unittest` pasa entera, igual que antes de la actualización (167
  pruebas).
- **Fase 11**: pasan T040 y T041; las pruebas anteriores de cancelación (CA-C06, CA-C07, CA-C08,
  CL-C07) siguen pasando sin modificarlas.
- **Fase 12**: pasan T044 y T045; las pruebas anteriores de reprogramación siguen pasando sin
  modificarlas.
- **Fase 13**: pasan T047 y T048; las demás pruebas de bloqueo (CA-C10, CA-C11, CL-C04, PD-C12,
  RN-C04, RN-C11) siguen pasando sin modificarlas.
- **Fase 14**: pasan T051 y T052; las demás pruebas de duración (CA-C12, CL-C05, PD-C10, PD-C11,
  PD-C20) siguen pasando sin modificarlas.

## Pendiente de decisión de la persona responsable

- **Motivo por línea en la confirmación al administrativo** (D-C19): T050 lo retira junto con el
  código de historia clínica. Retirar el código lo exige PD-C22; retirar el motivo es una decisión
  del plan. Si se prefiere conservarlo, hay que ajustar T048 y T050 antes de implementarlas.
- **Redacción anterior de la franja pasada en `spec.md`** (D-C20): cuatro frases siguen diciendo
  «solo por fecha» (el supuesto «Bloqueos sobre fechas pasadas», la entrada de la pregunta 4 en
  «Aclaraciones», la entidad «Franja bloqueada» y el escenario 8 de la historia 5). Las tareas
  siguen PD-C23 y CL-C12. No hay ninguna tarea que corrija esas frases, porque es un cambio de la
  especificación y no del código.
