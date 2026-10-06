# Contrato: interfaz web del módulo de citas (`programacion_citas/web.py`)

**Funcionalidad**: [spec.md](../spec.md) · **Servicio**: [servicio-citas.md](servicio-citas.md)

El manejador de citas **hereda** del manejador del módulo de registro y atiende primero estas
rutas; cualquier otra se delega a la clase base, que conserva sus 6 rutas intactas (D-C13). Un
solo servidor y un solo puerto (`PUERTO`, 8000 por defecto).

Páginas HTML en español, codificadas en UTF-8, sin JavaScript. Todo dato mostrado se escapa
(D-C16). Los mensajes son los del contrato del servicio.

Dos flujos separados por prefijo, sin inicio de sesión (PD-C02, D-C14): `/citas` para el paciente
y `/agenda` para el personal administrativo.

Existen **exactamente** estas rutas nuevas; cualquier otra devuelve `404`:

| # | Método y ruta | Flujo | Propósito | Trazabilidad |
|---|---|---|---|---|
| 1 | `GET /citas` | Paciente | Identificarse por código o por documento | RF-C01 |
| 2 | `GET /citas/buscar` | Paciente | Elegir especialidad y centro; listar especialistas | RF-C02 |
| 3 | `GET /citas/huecos` | Paciente | Huecos libres de un especialista en una fecha | RF-C03 |
| 4 | `POST /citas` | Paciente | Reservar el hueco elegido | RF-C04 |
| 5 | `GET /citas/mias` | Paciente | Listado de sus citas con estado y motivo | RF-C05 |
| 6 | `POST /citas/<id_cita>/cancelar` | Paciente | Cancelar | RF-C06 |
| 7 | `GET /citas/<id_cita>/reprogramar` | Paciente | Elegir el hueco destino | RF-C07 |
| 8 | `POST /citas/<id_cita>/reprogramar` | Paciente | Guardar el traslado | RF-C07 |
| 9 | `GET /agenda` | Administrativo | Elegir especialista y ver sus dos operaciones | RF-C08, RF-C09 |
| 10 | `POST /agenda/bloquear` | Administrativo | Bloquear una franja | RF-C08 |
| 11 | `POST /agenda/duracion` | Administrativo | Ajustar la duración de las consultas | RF-C09 |

**No existe** ninguna ruta para crear, editar o borrar centros, especialidades ni especialistas
(CA-C13, RN-C01, PD-C19), ni para desbloquear una franja (PD-C13), ni de notificaciones, listas de
espera o facturación (fuera de alcance).

## Identificación en los dos flujos · PD-C01, PD-C02

El paciente se identifica en la ruta 1 y su código de historia clínica viaja como parámetro
`codigo` en las rutas siguientes. No hay contraseña ni sesión: es la consecuencia directa de no
haber control de acceso (PD-C02), declarada como limitación en D-C16.

Si falta el parámetro `codigo` o no corresponde a ningún paciente, se responde `400` con el
mensaje «No existe ningún paciente con esos datos.» y un enlace a la ruta 1 (CL-C09).

## 1 · `GET /citas`

Dos formularios que envían a `GET /citas/buscar`:

- **Por código de historia clínica**: campo `codigo`.
- **Por documento de identidad**: desplegable `tipo_documento` (DNI, NIE, Pasaporte) y campo
  `numero_documento` (PD-C01, coherente con el módulo de registro).

Enlace «Ver mis citas» a la ruta 5.

## 2 · `GET /citas/buscar`

Parámetros: `codigo`, **o bien** `tipo_documento` + `numero_documento`; opcionalmente
`especialidad` y `centro`.

| Caso | Estado | Contenido |
|---|---|---|
| Sin filtros | `200` | Desplegables de especialidad y de centro, con los valores precargados |
| Con filtros y resultados | `200` | Especialistas que cumplen **ambos** filtros (CA-C03, PD-C15), cada uno con enlace a la ruta 3 |
| Con filtros sin resultados | `200` | Aviso «No hay especialistas de esa especialidad en ese centro.», sin error (CL-C02) |
| Paciente no identificado | `400` | Mensaje de identificación (CL-C09) |

## 3 · `GET /citas/huecos`

Parámetros: `codigo`, `id_especialista`, `fecha` (`YYYY-MM-DD`).

| Caso | Estado | Contenido |
|---|---|---|
| Con huecos libres | `200` | Datos del especialista y un botón de reserva por hueco libre, que envía a la ruta 4 (CA-C01, CA-C02) |
| Sin huecos libres | `200` | Aviso «No hay huecos disponibles en esa fecha.» (CL-C01) |
| Día sin consulta | `200` | El mismo aviso; no se ofrece ningún hueco (CL-C06) |
| Fecha mal formada | `400` | Mensaje de dato inválido (PD-C18) |

Los huecos ya pasados no se muestran (RN-C08, PD-C05). Solo se pide una fecha, nunca un rango
(PD-C16).

## 4 · `POST /citas`

Campos: `codigo`, `id_especialista`, `fecha`, `hora_inicio`.

| Caso | Estado | Contenido |
|---|---|---|
| Reservada | `303` | Redirección a la ruta 5 con `aviso=reservada` |
| Hueco ocupado o bloqueado | `409` | «Ese hueco ya no está disponible.» (CL-C03) |
| Hueco pasado | `409` | «No se puede reservar un hueco cuya hora ya ha pasado.» (RN-C08) |
| Solapamiento | `409` | «Ya tiene otra cita reservada a esa hora.» (CA-C05) |
| Datos incompletos | `400` | Mensaje del dato que falta (PD-C18) |

## 5 · `GET /citas/mias`

Parámetro: `codigo`. Con `aviso=reservada`, `aviso=cancelada` o `aviso=reprogramada`, muestra
además el aviso correspondiente.

| Caso | Estado | Contenido |
|---|---|---|
| Con citas | `200` | Tabla con especialista, especialidad, centro, fecha, hora, estado y, en las canceladas, el motivo (RF-C05, CA-C11, RN-C13). Las reservadas llevan botón de cancelar (ruta 6) y enlace de reprogramar (ruta 7) |
| Sin citas | `200` | Aviso «No tiene ninguna cita.» (PD-C14) |

Se listan las pasadas y las futuras; una cita pasada sigue apareciendo como reservada (PD-C14).

## 6 · `POST /citas/<id_cita>/cancelar`

Campo: `codigo`.

| Caso | Estado | Contenido |
|---|---|---|
| Cancelada | `303` | Redirección a la ruta 5 con `aviso=cancelada` (CA-C06, CA-C08) |
| Fuera de plazo | `409` | «Solo se puede cancelar o reprogramar hasta 24 horas antes del inicio de la cita.» (CA-C07) |
| Cita pasada | `409` | «No se puede cancelar ni reprogramar una cita cuya hora ya ha pasado.» (CL-C10, PD-C07) |
| Ya cancelada | `409` | «Esa cita ya está cancelada.» (CL-C07) |
| No es del paciente o no existe | `404` | Página de cita no encontrada |

## 7 · `GET /citas/<id_cita>/reprogramar`

Parámetros: `codigo`, opcionalmente `fecha`. Muestra los huecos libres **del mismo especialista**
(RN-C10) para la fecha elegida, cada uno con un botón que envía a la ruta 8. No permite cambiar de
especialista.

Si la cita está fuera de plazo, ya cancelada o ya pasada, responde `409` con el mensaje
correspondiente, sin mostrar huecos (CA-C07, CL-C08, CL-C10).

## 8 · `POST /citas/<id_cita>/reprogramar`

Campos: `codigo`, `fecha`, `hora_inicio`.

| Caso | Estado | Contenido |
|---|---|---|
| Reprogramada | `303` | Redirección a la ruta 5 con `aviso=reprogramada`; el identificador de la cita no cambia (CA-C09) |
| Hueco no disponible, pasado o solapado | `409` | El mensaje correspondiente (CL-C03, RN-C07, RN-C08) |
| Fuera de plazo, ya cancelada o ya pasada | `409` | El mensaje correspondiente (CA-C07, CL-C08, CL-C10) |

## 9 · `GET /agenda`

Flujo del personal administrativo. Sin identificación de ningún tipo (PD-C02).

Lista los especialistas precargados con su centro, especialidad, horario y duración vigente. Al
elegir uno, muestra sus dos formularios:

- **Bloquear franja** (ruta 10): `id_especialista`, `fecha_inicio`, `fecha_fin`, `hora_inicio`,
  `hora_fin` (PD-C12).
- **Ajustar duración** (ruta 11): `id_especialista`, `duracion_minutos` (RF-C09).

No hay ningún formulario de alta o edición de especialistas, centros o especialidades (CA-C13).

## 10 · `POST /agenda/bloquear`

| Caso | Estado | Contenido |
|---|---|---|
| Aplicado | `200` | Confirmación con el número de citas canceladas por el centro y, de cada una, la fecha, la hora y el motivo de cancelación (CA-C10, PD-C22) |
| Aplicado sin citas dentro | `200` | Confirmación indicando que no se canceló ninguna cita (CL-C04) |
| Rango u horas inválidas | `400` | Mensaje del dato inválido (PD-C18, PD-C23, CL-C12) |
| Franja entera en el pasado | `400` | «No se puede bloquear una franja cuya fecha y hora de fin ya han pasado.» (PD-C23, CL-C12) |

Las citas pasadas no se cancelan y se indica en la confirmación (PD-C11).

**Contenido de la confirmación** (PD-C22, CE-C10, D-C19): de cada cita cancelada se muestran la
fecha, la hora y el motivo de cancelación, con la forma «{fecha} a las {hora} · motivo: {motivo}».
El motivo se conserva porque no identifica al paciente y confirma al administrativo por qué se
canceló cada cita. La página **no** contiene el código de historia clínica, el documento de
identidad ni ningún otro dato de los pacientes afectados. Lo mismo aplica a la ruta 11.

## 11 · `POST /agenda/duracion`

| Caso | Estado | Contenido |
|---|---|---|
| Aplicado | `200` | Confirmación con la nueva rejilla, el número de citas canceladas por el centro y la fecha y la hora de cada una, sin datos de los pacientes (CA-C12, PD-C22) |
| Duración no positiva o no numérica | `400` | Mensaje del dato inválido (PD-C18, PD-C21) |
| Duración con la que no cabe ningún hueco | `400` | «Con esa duración no cabe ningún hueco en el horario del especialista.»; la duración no cambia y no se cancela ninguna cita (PD-C21, CL-C11) |

## Respuestas de error comunes

| Estado | Cuándo |
|---|---|
| `303` | Operación correcta que redirige, para no repetir el envío del formulario |
| `400` | Dato ausente o mal formado; paciente no identificado (CL-C09); duración sin hueco posible (CL-C11); franja mal formada o entera en el pasado (CL-C12) |
| `404` | Ruta inexistente, o cita que no existe o no es del paciente (CA-C13) |
| `409` | Regla de negocio incumplida: hueco no disponible o pasado, solapamiento, fuera de plazo, cita ya pasada (CL-C10), cita ya cancelada |

Ningún error se presenta como fallo genérico: todos indican el motivo concreto (PD-C18).
