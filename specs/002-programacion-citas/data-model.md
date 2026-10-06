# Modelo de datos: Módulo de Programación de Citas

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) ·
**Decisiones**: [research.md](research.md)

Cinco tablas nuevas en la misma base de datos SQLite del proyecto (D-C02). La tabla `paciente`
del módulo de registro **no se modifica**: este módulo solo la consulta a través del servicio de
ese módulo (D-C04). Fechas y horas son texto ISO comparable (D-C09).

## Tabla `centro` · RN-C01, RN-C02

| Columna | Tipo | Restricciones | Requisito |
|---|---|---|---|
| `id_centro` | INTEGER | `PRIMARY KEY` | — |
| `nombre` | TEXT | `NOT NULL`, `UNIQUE` | RN-C02 |

Dato precargado. Sin operaciones de alta, edición ni borrado (RN-C01, PD-C19, CA-C13).

## Tabla `especialidad` · RN-C01, RN-C02

| Columna | Tipo | Restricciones | Requisito |
|---|---|---|---|
| `id_especialidad` | INTEGER | `PRIMARY KEY` | — |
| `nombre` | TEXT | `NOT NULL`, `UNIQUE` | RN-C02 |

Dato precargado, sin alta ni edición (RN-C01, PD-C19).

## Tabla `especialista` · RN-C01, RN-C02, RF-C09

| Columna | Tipo | Restricciones | Requisito |
|---|---|---|---|
| `id_especialista` | INTEGER | `PRIMARY KEY` | — |
| `nombre` | TEXT | `NOT NULL` | RN-C02 |
| `id_centro` | INTEGER | `NOT NULL`, `REFERENCES centro` | RN-C02, RF-C02 |
| `id_especialidad` | INTEGER | `NOT NULL`, `REFERENCES especialidad` | RN-C02, RF-C02 |
| `dias_semana` | TEXT | `NOT NULL`; números ISO separados por comas, p. ej. `1,2,3,4,5` | RN-C02, CL-C06, D-C11 |
| `hora_inicio` | TEXT | `NOT NULL`; `HH:MM` | RN-C02, RN-C03 |
| `hora_fin` | TEXT | `NOT NULL`; `HH:MM`, mayor que `hora_inicio` | RN-C02, RN-C03 |
| `duracion_minutos` | INTEGER | `NOT NULL`, `CHECK (duracion_minutos > 0)` | RN-C02, RF-C09 |

`duracion_minutos` es el **único** campo que la aplicación permite cambiar, mediante RF-C09. El
horario (días y horas) es precargado e inmutable (RN-C01, PD-C19).

**Regla de validación al cambiarla** (PD-C21, CL-C11, D-C18): la nueva duración debe ser un entero
mayor que cero y no superar los minutos entre `hora_inicio` y `hora_fin`, de modo que quepa al
menos un hueco. La comprueba el servicio antes de actualizar; no es un `CHECK` del esquema, que
se queda en `duracion_minutos > 0`. Con horario de 9:00 a 13:00 se aceptan de 1 a 240 minutos y
se rechazan 241 o más.

## Tabla `cita` · RF-C04 a RF-C07, RN-C05, RN-C06, RN-C13

| Columna | Tipo | Restricciones | Requisito |
|---|---|---|---|
| `id_cita` | INTEGER | `PRIMARY KEY` | CA-C09 (no cambia al reprogramar) |
| `codigo_historia` | TEXT | `NOT NULL`, `REFERENCES paciente (codigo_historia)` | RN-C05 |
| `id_especialista` | INTEGER | `NOT NULL`, `REFERENCES especialista` | RN-C10 |
| `fecha` | TEXT | `NOT NULL`; `YYYY-MM-DD` | RF-C03, RF-C04 |
| `hora_inicio` | TEXT | `NOT NULL`; `HH:MM`, inicio de un hueco de la rejilla | RN-C03, RN-C04 |
| `estado` | TEXT | `NOT NULL`, `CHECK (estado IN ('RESERVADA','CANCELADA_PACIENTE','CANCELADA_CENTRO'))` | RN-C06 |
| `motivo_cancelacion` | TEXT | Nulo si y solo si `estado = 'RESERVADA'` (ver invariante) | RN-C13, PD-C09 |
| `momento_reserva` | TEXT | `NOT NULL`; `YYYY-MM-DD HH:MM:SS` | RN-C09, PD-C07 |

La cita **no guarda su duración**: es la `duracion_minutos` vigente de su especialista (D-C06,
PD-C10). Es lo que permite que RN-C12 recalcule la rejilla y decida qué citas encajan.

`momento_reserva` es el momento de la **última** reserva o reprogramación, no el de la reserva
original: reprogramar lo actualiza (PD-C07, aclaración Q2 del 2026-09-28). De él depende la
excepción de RN-C09.

### Restricciones en la base de datos

```sql
-- RN-C13 y PD-C09: toda cancelación registra motivo; una cita reservada no lo tiene.
CHECK (
    (estado = 'RESERVADA' AND motivo_cancelacion IS NULL)
    OR (estado <> 'RESERVADA' AND motivo_cancelacion IS NOT NULL)
)

-- RN-C04, PD-C17 y CL-C03: un hueco no puede tener dos citas reservadas.
-- Es parcial porque las canceladas no ocupan hueco (RN-C06, PD-C04) y ese hueco
-- debe poder reservarse de nuevo.
CREATE UNIQUE INDEX hueco_ocupado
    ON cita (id_especialista, fecha, hora_inicio)
    WHERE estado = 'RESERVADA';
```

Ambas restricciones se han comprobado en SQLite 3.50.4: la segunda reserva del mismo hueco se
rechaza, tras cancelar la primera el hueco vuelve a admitir reserva, y pasar una cita a cancelada
sin motivo es rechazado (D-C07, D-C08).

**Valores de `motivo_cancelacion`** (PD-C09, los genera el sistema, no se teclean):

| Estado | Motivo | Origen |
|---|---|---|
| `CANCELADA_PACIENTE` | A petición del paciente | RF-C06, E-C03 |
| `CANCELADA_CENTRO` | Franja bloqueada del especialista | RN-C11, E-C04 |
| `CANCELADA_CENTRO` | Cambio de la duración de las consultas | RN-C12, E-C05 |

## Tabla `franja_bloqueada` · RF-C08, RN-C04, RN-C11, PD-C12

| Columna | Tipo | Restricciones | Requisito |
|---|---|---|---|
| `id_franja` | INTEGER | `PRIMARY KEY` | — |
| `id_especialista` | INTEGER | `NOT NULL`, `REFERENCES especialista` | RF-C08 |
| `fecha_inicio` | TEXT | `NOT NULL`; `YYYY-MM-DD` | PD-C12 |
| `fecha_fin` | TEXT | `NOT NULL`; `YYYY-MM-DD`, no anterior a `fecha_inicio` | PD-C12 |
| `hora_inicio` | TEXT | `NOT NULL`; `HH:MM` | PD-C12 |
| `hora_fin` | TEXT | `NOT NULL`; `HH:MM`, mayor que `hora_inicio` | PD-C12 |

El tramo horario se aplica a **cada día** del rango, ambas fechas incluidas (PD-C12, aclaración Q1
del 2026-09-28). Así unas vacaciones se bloquean de una vez (E-C04) y CA-C10 es el caso de un solo
día, con `fecha_inicio = fecha_fin`.

No existe operación de desbloqueo: las filas de esta tabla no se borran ni se editan (PD-C13,
RF-C08).

**Reglas de validación al bloquear** (PD-C23, CL-C12, D-C20). El servicio rechaza la franja, sin
insertar la fila ni cancelar ninguna cita, en estos tres casos y solo en ellos:

| Caso | Regla | Ejemplo (ahora = hoy a las 11:00) |
|---|---|---|
| (a) Rango invertido | `fecha_fin` anterior a `fecha_inicio` | del día 20 al día 15 → rechazada |
| (b) Tramo invertido o vacío | `hora_fin` no posterior a `hora_inicio` | de 11:00 a 11:00 → rechazada |
| (c) Franja entera en el pasado | el momento `fecha_fin` + `hora_fin` no es posterior a `ahora` | hoy de 9:00 a 11:00 → rechazada; hoy de 9:00 a 14:00 → aceptada; ayer de 9:00 a 14:00 → rechazada |

El caso (c) depende del momento actual, así que no puede ser una restricción del esquema: una
franja válida al crearse acaba quedando en el pasado sin dejar de ser correcta. Cualquier otra
franja se acepta aunque no tenga efecto (tramo fuera del horario, rango sin días de consulta,
rango que empieza en el pasado y cuyo fin aún no ha llegado).

## Entidad derivada: `hueco` · RN-C03, RN-C04, PD-C03

Un hueco **no se almacena** (D-C05). Se calcula al consultarlo y se describe con especialista,
fecha, hora de inicio y duración vigente.

**Generación de la rejilla** (PD-C03, verificado contra CA-C01 y CL-C05):

1. Si el día de la semana de la fecha no está en `dias_semana`, la rejilla está vacía (CL-C06).
2. El primer hueco empieza en `hora_inicio`; cada siguiente, donde acaba el anterior.
3. Se generan huecos mientras `inicio + duracion_minutos <= hora_fin`. El tiempo sobrante **no**
   forma un hueco parcial.

| Horario | Duración | Huecos | Primero | Último | Criterio |
|---|---|---|---|---|---|
| 9:00–13:00 | 20 min | 12 | 9:00 | 12:40 | CA-C01 |
| 9:00–13:00 | 30 min | 8 | 9:00 | 12:30 | CA-C12 |
| 9:00–13:00 | 50 min | 4 | 9:00 | 11:30 | CL-C05 |

**Disponibilidad de un hueco** (RN-C04). Está libre cuando cumple las tres condiciones:

1. No lo ocupa ninguna cita en estado `RESERVADA` del mismo especialista, fecha y hora de inicio.
2. No cae dentro de ninguna franja bloqueada de ese especialista (ver criterio de extremos abajo).
3. Su inicio es **estrictamente posterior** al momento actual (RN-C08, PD-C05, CL-C13, D-C21). Un
   hueco cuyo inicio coincide con el momento actual ya no está libre ni se puede reservar, de
   modo que ninguna cita nace ya pasada.

## Criterio de extremos en las comparaciones temporales · PD-C06, PD-C12

Todos los intervalos son **semiabiertos**: `[inicio, inicio + duración)`. De ahí se derivan, de
forma uniforme, las tres comparaciones del módulo:

| Comparación | Regla | Consecuencia comprobada |
|---|---|---|
| Solapamiento de dos citas de un paciente (RN-C07, PD-C06) | Se solapan si `a_inicio < b_fin` y `b_inicio < a_fin` | Dos citas consecutivas de 20 min (9:00 y 9:20) **no** se solapan; una de 30 min a las 9:00 y otra a las 9:20 **sí** |
| Hueco dentro de una franja (PD-C12) | Bloqueado si `hueco_inicio < franja_fin` y `franja_inicio < hueco_fin` | Con franja 9:00–11:00 y duración 20: se bloquean 9:00, 10:00 y 10:40 (que acaba justo a las 11:00) y no las de 11:00 en adelante — exactamente CA-C10 |
| Encaje en la rejilla nueva (RN-C12, PD-C10) | Encaja si su hora de inicio es el inicio de un hueco nuevo y `inicio + nueva duración <= hora_fin` | Al pasar de 20 a 30 min, la cita de 9:00 encaja y la de 9:20 no — exactamente CA-C12 |
| Hueco o cita respecto al momento actual (PD-C05, PD-C07, PD-C11; D-C17, D-C21) | Pasado si `inicio <= ahora`; reservable, futuro o cancelable solo si `inicio > ahora` | A las 9:00 en punto, el hueco de las 9:00 no se ofrece ni se puede reservar (CL-C13) y una cita de las 9:00 ya no se puede cancelar (CL-C10); a las 8:59, sí |

## Ciclo de vida de una cita · RN-C06, RN-C09 a RN-C12

```text
                          reservar (RF-C04)
                                 │
                                 ▼
                          ┌──────────────┐
         reprogramar ─────┤  RESERVADA   ├───── cancela el paciente (RF-C06)
        (RF-C07, RN-C10)  └──────┬───────┘                │
        cambia fecha/hora        │                        ▼
        y momento_reserva        │             ┌────────────────────────┐
        (PD-C07); mismo          │             │  CANCELADA_PACIENTE    │
        id_cita y especialista   │             └────────────────────────┘
                                 │
                                 │ bloqueo de franja (RN-C11)
                                 │ o cambio de duración (RN-C12),
                                 │ solo si la cita es futura (PD-C11)
                                 ▼
                     ┌────────────────────────┐
                     │   CANCELADA_CENTRO     │
                     └────────────────────────┘
```

**Transiciones prohibidas**:

- De cualquier estado cancelado a `RESERVADA`: una cita cancelada no revive (CL-C07, CL-C08).
- De `CANCELADA_PACIENTE` a `CANCELADA_CENTRO` ni al contrario.
- `RESERVADA` → cancelada por el paciente fuera del plazo de RN-C09 (CA-C07). El centro no tiene
  ese límite (RN-C11).
- `RESERVADA` → cancelada por el paciente, o reprogramada, cuando la hora de inicio de la cita ya
  ha pasado, aunque se hubiera reservado con menos de 24 horas de antelación (PD-C07, CL-C10,
  aclaración Q1 del 2026-10-06). Una cita pasada conserva su estado, su fecha y su hora.
- Ningún bloqueo ni cambio de duración altera una cita cuya hora ya ha pasado (PD-C11,
  aclaración Q3 del 2026-09-28): es historial, no agenda.

## Invariantes del módulo

Se corresponden con los criterios de éxito de la especificación y son comprobables consultando la
base de datos:

| Invariante | Garantía | Criterio |
|---|---|---|
| Un hueco tiene como máximo una cita `RESERVADA` | Índice único parcial `hueco_ocupado` | CE-C01, CL-C03 |
| Ninguna cita cancelada carece de motivo | `CHECK` de `motivo_cancelacion` | CE-C06, RN-C13 |
| Un paciente no tiene dos citas `RESERVADA` solapadas | Comprobación en el servicio antes de reservar y de reprogramar (PD-C06, PD-C08) | CE-C03, RN-C07 |
| Ninguna cita `RESERVADA` **futura** cae en franja bloqueada ni fuera de la rejilla vigente | Cancelación por el centro al bloquear y al cambiar duración (RN-C11, RN-C12) | CE-C02 |
| Toda cita referencia un paciente existente | `REFERENCES paciente (codigo_historia)` | RN-C05 |
| El identificador de una cita no cambia nunca | Reprogramar es `UPDATE`, nunca borrar e insertar | CE-C05, CA-C09 |
| Todo especialista tiene al menos un hueco en sus días de consulta | Validación de la duración en el servicio antes de actualizarla (D-C18) | PD-C21, CL-C11 |
| Ninguna cita pasada cambia de estado, de fecha ni de hora | El centro solo alcanza a las citas futuras (PD-C11) y el paciente no puede cancelar ni reprogramar una cita pasada (D-C17) | PD-C07, CL-C10 |
| Toda cita recién reservada o reprogramada es futura | El hueco destino solo es reservable si su inicio es estrictamente posterior al momento actual (D-C21) | PD-C05, CL-C13 |

## Ejemplo (datos ficticios) · principio IV

Precarga (D-C12) y una cita de ejemplo. Todos los nombres son inventados:

| Tabla | Fila de ejemplo |
|---|---|
| `centro` | `1`, «Centro Norte» |
| `especialidad` | `1`, «Dermatología» |
| `especialista` | `1`, «Ana Ruiz Delgado», centro `1`, especialidad `1`, `1,2,3,4,5`, `09:00`, `13:00`, `20` |
| `cita` | `1`, `HC-000001`, especialista `1`, `2026-10-05`, `09:00`, `RESERVADA`, `NULL`, `2026-09-28 11:30:00` |
| `franja_bloqueada` | `1`, especialista `1`, `2026-10-12`, `2026-10-23`, `09:00`, `13:00` (dos semanas de vacaciones, E-C04) |

Con esa franja, la cita del ejemplo (5 de octubre) **no** se cancela, porque su fecha queda fuera
del rango; una cita del 15 de octubre a las 10:00 sí quedaría `CANCELADA_CENTRO` con motivo
«Franja bloqueada del especialista».
