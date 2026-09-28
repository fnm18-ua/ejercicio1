# Contrato: servicio de citas (`programacion_citas/servicio.py`)

**Funcionalidad**: [spec.md](../spec.md) · **Modelo de datos**: [data-model.md](../data-model.md) ·
**Interfaz**: [interfaz-web-citas.md](interfaz-web-citas.md)

Toda la lógica de negocio del módulo. La interfaz web y las pruebas usan estas funciones; las
pruebas de CA-C y CL-C no dependen del HTML (D-C15). Los textos son en español (principio I) y
todas las consultas van parametrizadas (D-C16).

## Aritmética temporal (`programacion_citas/agenda.py`)

Funciones puras, sin base de datos, para poder probar por separado las afirmaciones numéricas del
enunciado (D-C15).

### `generar_rejilla(dias_semana, hora_inicio, hora_fin, duracion_minutos, fecha) -> list[str]`

Horas de inicio de los huecos de esa fecha, en orden (RN-C03, PD-C03). Lista vacía si la fecha no
es un día de consulta (CL-C06). No genera huecos parciales (CL-C05).

### `se_solapan(inicio_a, duracion_a, inicio_b, duracion_b) -> bool`

Intervalos semiabiertos (RN-C07, PD-C06). Dos citas que se tocan en el extremo no se solapan.

### `hueco_en_franja(hueco_inicio, duracion, franja_inicio, franja_fin) -> bool`

Si el hueco cae dentro del tramo horario de una franja, con el mismo criterio de extremos
(PD-C12).

### `encaja_en_rejilla(hora_cita, rejilla, hora_fin, duracion) -> bool`

Si la hora de la cita es el inicio de un hueco de la rejilla y cabe entera en el horario (RN-C12,
PD-C10).

## Tipos

### `Cita` (inmutable)

`id_cita`, `codigo_historia`, `id_especialista`, `nombre_especialista`, `especialidad`, `centro`,
`fecha`, `hora_inicio`, `duracion_minutos`, `estado`, `motivo_cancelacion`, `momento_reserva`.

La duración es la vigente del especialista, no un dato de la cita (D-C06, PD-C10).

### `Especialista` (inmutable)

`id_especialista`, `nombre`, `centro`, `especialidad`, `dias_semana`, `hora_inicio`, `hora_fin`,
`duracion_minutos`.

### `Hueco` (inmutable)

`hora_inicio`, `duracion_minutos`, `libre` (bool). Derivado, nunca almacenado (D-C05).

### Errores

| Excepción | Cuándo | Requisito |
|---|---|---|
| `PacienteNoIdentificado` | El código o el documento no corresponde a ningún paciente | RF-C01, CL-C09 |
| `HuecoNoDisponible` | El hueco está ocupado, bloqueado o no existe en la rejilla | RN-C04, CL-C03 |
| `HuecoPasado` | La hora de inicio del hueco ya ha pasado | RN-C08, PD-C05 |
| `CitaSolapada` | El paciente ya tiene otra cita reservada que se solapa | RN-C07, CA-C05 |
| `FueraDePlazo` | Fuera del plazo de 24 horas de RN-C09 | CA-C07 |
| `CitaYaCancelada` | La cita no está en estado reservada | CL-C07, CL-C08 |
| `CitaNoEncontrada` | No existe cita con ese identificador para ese paciente | RF-C06, RF-C07 |
| `ErrorValidacion` | Datos de entrada ausentes o mal formados (fecha, hora, duración) | PD-C18 |

Todos los errores llevan un mensaje concreto (PD-C18): ningún rechazo es genérico.

## Funciones

### `inicializar_base_datos(ruta_bd) -> None`

Crea las cinco tablas si no existen y el índice único parcial, y precarga centros, especialidades
y especialistas **solo si las tablas están vacías** (D-C12). Idempotente: arranques repetidos no
duplican datos ni pisan los existentes (principio V).

### `identificar_paciente(ruta_bd, codigo=None, tipo_documento=None, numero_documento=None) -> str`

Devuelve el código de historia clínica del paciente. Delega en `registro_pacientes.servicio`
(D-C04), por lo que la comparación es normalizada y las dos vías llevan al mismo paciente
(PD-C01, CA-C04). Lanza `PacienteNoIdentificado` si no existe (CL-C09). **No crea pacientes**
(frontera del principio II).

### `buscar_especialistas(ruta_bd, especialidad, centro) -> list[Especialista]` · RF-C02

Exige los dos filtros y devuelve solo quienes cumplen ambos (CA-C03, PD-C15). Lista vacía si no
hay coincidencias, que la interfaz presenta como aviso y no como error (CL-C02).

### `consultar_huecos(ruta_bd, id_especialista, fecha, ahora) -> list[Hueco]` · RF-C03

Rejilla de esa fecha con su disponibilidad (RN-C03, RN-C04). Excluye los huecos ocupados por citas
reservadas, los que caen en franja bloqueada y los ya pasados (PD-C05). Lista vacía si el
especialista no pasa consulta ese día (CL-C06); todos ocupados es un caso normal, no un error
(CL-C01).

### `reservar_cita(ruta_bd, codigo_historia, id_especialista, fecha, hora_inicio, ahora) -> Cita` · RF-C04

En una transacción `BEGIN IMMEDIATE` (D-C08):

1. Comprueba que la hora es inicio de un hueco de la rejilla vigente, o `HuecoNoDisponible`.
2. Comprueba que no ha pasado (RN-C08), o `HuecoPasado`.
3. Comprueba que no cae en franja bloqueada (RN-C04), o `HuecoNoDisponible`.
4. Comprueba que el paciente no tiene otra cita reservada solapada (RN-C07, PD-C06), o
   `CitaSolapada`.
5. Inserta con estado `RESERVADA`, `motivo_cancelacion` nulo y `momento_reserva = ahora`.

Si el índice único parcial rechaza la inserción porque otra persona acaba de ocupar el hueco, se
traduce a `HuecoNoDisponible` (CL-C03, PD-C17).

### `consultar_citas(ruta_bd, codigo_historia) -> list[Cita]` · RF-C05

Todas las citas del paciente, pasadas y futuras, con estado y motivo (PD-C14). Lista vacía si no
tiene ninguna. No existe estado «atendida»: una cita pasada sigue `RESERVADA` (PD-C14).

### `cancelar_cita(ruta_bd, codigo_historia, id_cita, ahora) -> Cita` · RF-C06

Comprueba que la cita es de ese paciente (`CitaNoEncontrada`), que está reservada
(`CitaYaCancelada`, CL-C07) y que se cumple el plazo de RN-C09 (`FueraDePlazo`, CA-C07). Pasa a
`CANCELADA_PACIENTE` con motivo «A petición del paciente» y libera el hueco (CA-C06, PD-C04).

**Plazo de RN-C09**: se permite si faltan 24 horas o más para el inicio; si falta menos, solo si
`momento_reserva` está a menos de 24 horas del inicio (CA-C08).

### `reprogramar_cita(ruta_bd, codigo_historia, id_cita, fecha, hora_inicio, ahora) -> Cita` · RF-C07

Mismas comprobaciones de plazo y estado que cancelar, más las del hueco destino de
`reservar_cita`. Es un `UPDATE`: conserva `id_cita`, `codigo_historia` e `id_especialista`; cambia
`fecha`, `hora_inicio` y `momento_reserva = ahora` (RN-C10, PD-C07, PD-C08, CA-C09). Al comprobar
RN-C07, la propia cita no se cuenta contra sí misma (PD-C08). El hueco anterior queda libre por el
propio `UPDATE`.

### `bloquear_franja(ruta_bd, id_especialista, fecha_inicio, fecha_fin, hora_inicio, hora_fin, ahora) -> list[Cita]` · RF-C08

Inserta la franja (PD-C12) y devuelve las citas canceladas. Pasa a `CANCELADA_CENTRO`, con motivo
«Franja bloqueada del especialista», las citas de ese especialista que cumplen **las tres**
condiciones:

1. Estado `RESERVADA`.
2. Fecha dentro del rango y hora solapada con el tramo (PD-C12) — así CA-C10 cancela las de 9:00,
   10:00 y 10:40 y conserva las de 11:00 en adelante.
3. **Son futuras** respecto a `ahora` (PD-C11): una cita ya pasada no cambia de estado.

No está sujeto al plazo de 24 horas (RN-C11). Si no hay citas dentro, la franja se aplica y no se
cancela nada (CL-C04). No existe operación de desbloqueo (PD-C13).

### `ajustar_duracion(ruta_bd, id_especialista, duracion_minutos, ahora) -> list[Cita]` · RF-C09

Actualiza `duracion_minutos` y devuelve las citas canceladas. Recalcula la rejilla y pasa a
`CANCELADA_CENTRO`, con motivo «Cambio de la duración de las consultas», las citas **futuras**
reservadas que ya no encajan (RN-C12, PD-C10, PD-C11): la de 9:00 sobrevive y la de 9:20 no al
pasar de 20 a 30 minutos (CA-C12). Las citas pasadas no se tocan (PD-C11).

**Limitación declarada** (PD-C20): no vuelve a comprobar RN-C07, de modo que al alargarse las
consultas dos citas de un mismo paciente podrían quedar solapadas. Es una limitación conocida y
documentada, no un defecto silencioso.

## Mensajes (español, PD-C18)

| Situación | Mensaje | Requisito |
|---|---|---|
| Paciente no encontrado | «No existe ningún paciente con esos datos.» | CL-C09 |
| Hueco ocupado o bloqueado | «Ese hueco ya no está disponible.» | CL-C03, RN-C04 |
| Hueco pasado | «No se puede reservar un hueco cuya hora ya ha pasado.» | RN-C08 |
| Solapamiento | «Ya tiene otra cita reservada a esa hora.» | CA-C05, RN-C07 |
| Fuera de plazo | «Solo se puede cancelar o reprogramar hasta 24 horas antes del inicio de la cita.» | CA-C07, RN-C09 |
| Cita ya cancelada | «Esa cita ya está cancelada.» | CL-C07, CL-C08 |
| Sin especialistas | «No hay especialistas de esa especialidad en ese centro.» | CL-C02 |
| Sin huecos | «No hay huecos disponibles en esa fecha.» | CL-C01, CL-C06 |
| Sin citas | «No tiene ninguna cita.» | PD-C14 |
| Cancelada por el paciente | «A petición del paciente» | PD-C09 |
| Cancelada por bloqueo | «Franja bloqueada del especialista» | PD-C09, RN-C11 |
| Cancelada por duración | «Cambio de la duración de las consultas» | PD-C09, RN-C12 |
