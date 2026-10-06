---

description: "Lista de tareas del módulo de Programación de Citas"
---

# Tareas: Módulo de Programación de Citas

**Entrada**: documentos de diseño en `specs/002-programacion-citas/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: incluidas. La especificación las exige en CE-C08 (superar los 13 CA-C y los 9 CL-C) y
el plan fija su forma en D-C15.

**Organización**: tareas agrupadas por historia de usuario (US1 a US6 = historias de usuario 1 a 6
de [spec.md](spec.md)), para que cada una se implemente y se pruebe por separado.

**Constitución vigente**: v3.2.0.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes).
- **[USn]**: historia de usuario a la que pertenece la tarea.
- Todas las rutas son relativas a la raíz del repositorio.

## Convenciones obligatorias para todas las tareas

- **Idioma (principio I)**: módulos, clases, funciones, variables y mensajes en español, sin tildes
  ni eñes en los identificadores. Vocabulario obligatorio del principio I en su versión 3.2.0:
  **cita**, **especialista**, **especialidad**, **centro**, **agenda**, **hueco** y **franja
  bloqueada** (más paciente, historia clínica, mutua y documento de identidad). No se admiten
  sinónimos: nunca «médico», «doctor», «slot», «turno» ni «sede». Solo se admiten en inglés los
  nombres que impone la biblioteca estándar (`do_GET`, `do_POST`, `setUp`, `tearDown`, prefijo
  `test_`).
- **Trazabilidad (principio III)**: cada módulo, clase, función y método de prueba lleva un
  *docstring* en español que cita los identificadores que implementa o verifica (RF-C, RN-C, CA-C,
  CL-C, PD-C, D-C). Los métodos de prueba incluyen el identificador en su nombre (p. ej.
  `test_cac01_rejilla_de_20_minutos_tiene_12_huecos`).
- **Alcance (principio II)**: no se añade nada que no figure en estas tareas. Ni alta o edición de
  centros, especialidades o especialistas; ni desbloqueo de franjas; ni notificaciones; ni listas
  de espera; ni inicio de sesión; ni dependencias externas (solo biblioteca estándar de Python).
- **Frontera entre módulos (principio II)**: **no se modifica `registro_pacientes/`**. La
  dependencia va en un solo sentido: `programacion_citas` importa de `registro_pacientes`, nunca al
  contrario (D-C03, D-C04). El único archivo existente que se toca es `app.py`, y solo en T005.
- **Datos ficticios (principio IV)**: todos los datos de precarga y de pruebas son inventados.
- **Mensajes**: exactamente los de [contracts/servicio-citas.md](contracts/servicio-citas.md) y
  [contracts/interfaz-web-citas.md](contracts/interfaz-web-citas.md).
- **Momento actual**: ninguna función llama a `datetime.now()` por su cuenta. El momento actual se
  recibe siempre como parámetro `ahora` (D-C10), para que CA-C07, CA-C08 y PD-C11 sean
  deterministas.

---

## Fase 1: Preparación

**Propósito**: crear el paquete del módulo.

- [X] T001 Crear `programacion_citas/__init__.py` con solo un *docstring* en español que describa el paquete como el módulo de programación de citas del HIS y cite las capacidades 4, 5 y 6 del principio II de la constitución (plan.md, «Estructura del proyecto»)

---

## Fase 2: Base común (bloquea todas las historias)

**Propósito**: aritmética temporal, esquema de las cinco tablas, precarga, tipos del servicio,
esqueleto web, arranque y utilidades de prueba.

**⚠️ CRÍTICO**: ninguna historia puede empezar hasta completar esta fase.

- [X] T002 [P] Implementar `programacion_citas/agenda.py` (RN-C03, RN-C04, RN-C07, RN-C12; PD-C03, PD-C06, PD-C10, PD-C12; D-C15) con funciones puras, sin base de datos ni HTTP: `a_minutos(hora)` convierte `"HH:MM"` a minutos desde medianoche; `a_hora(minutos)` hace lo inverso devolviendo `"HH:MM"` con dos dígitos (`"09:00"`, no `"9:00"`); `dia_de_la_semana(fecha)` devuelve el número ISO 1–7 de una fecha `"YYYY-MM-DD"` usando `datetime.date.fromisoformat(...).isoweekday()`; `generar_rejilla(dias_semana, hora_inicio, hora_fin, duracion_minutos, fecha)` devuelve la lista ordenada de horas de inicio `"HH:MM"`: lista vacía si `dia_de_la_semana(fecha)` no está en `dias_semana` (texto de números ISO separados por comas, p. ej. `"1,2,3,4,5"`), y en caso contrario empieza en `hora_inicio` y añade un hueco cada `duracion_minutos` **mientras `inicio + duracion_minutos <= a_minutos(hora_fin)`**, sin generar huecos parciales; `se_solapan(inicio_a, duracion_a, inicio_b, duracion_b)` devuelve `a_ini < b_ini + b_dur and b_ini < a_ini + a_dur` (intervalos semiabiertos, PD-C06); `hueco_en_franja(hueco_inicio, duracion, franja_inicio, franja_fin)` con el mismo criterio semiabierto; `encaja_en_rejilla(hora_cita, rejilla, hora_fin, duracion)` devuelve cierto si `hora_cita` está en `rejilla` y `a_minutos(hora_cita) + duracion <= a_minutos(hora_fin)` (PD-C10). Debe cumplir exactamente: 9:00–13:00 con 20 min → 12 huecos, primero `"09:00"`, último `"12:40"` (CA-C01); con 30 min → 8 huecos, último `"12:30"`; con 50 min → 4 huecos, último `"11:30"` (CL-C05)
- [X] T003 [P] Implementar `programacion_citas/base_datos.py` (RN-C02, RN-C05, RN-C06, RN-C13; PD-C04, PD-C09, PD-C17; D-C02, D-C07, D-C08; data-model.md) con `crear_esquema(conexion)`, que ejecuta exactamente estas cinco tablas con `CREATE TABLE IF NOT EXISTS` y el índice con `CREATE UNIQUE INDEX IF NOT EXISTS`: `centro (id_centro INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE)`; `especialidad (id_especialidad INTEGER PRIMARY KEY, nombre TEXT NOT NULL UNIQUE)`; `especialista (id_especialista INTEGER PRIMARY KEY, nombre TEXT NOT NULL, id_centro INTEGER NOT NULL REFERENCES centro (id_centro), id_especialidad INTEGER NOT NULL REFERENCES especialidad (id_especialidad), dias_semana TEXT NOT NULL, hora_inicio TEXT NOT NULL, hora_fin TEXT NOT NULL, duracion_minutos INTEGER NOT NULL CHECK (duracion_minutos > 0))`; `cita (id_cita INTEGER PRIMARY KEY, codigo_historia TEXT NOT NULL REFERENCES paciente (codigo_historia), id_especialista INTEGER NOT NULL REFERENCES especialista (id_especialista), fecha TEXT NOT NULL, hora_inicio TEXT NOT NULL, estado TEXT NOT NULL CHECK (estado IN ('RESERVADA', 'CANCELADA_PACIENTE', 'CANCELADA_CENTRO')), motivo_cancelacion TEXT, momento_reserva TEXT NOT NULL, CHECK ((estado = 'RESERVADA' AND motivo_cancelacion IS NULL) OR (estado <> 'RESERVADA' AND motivo_cancelacion IS NOT NULL)))`; `franja_bloqueada (id_franja INTEGER PRIMARY KEY, id_especialista INTEGER NOT NULL REFERENCES especialista (id_especialista), fecha_inicio TEXT NOT NULL, fecha_fin TEXT NOT NULL, hora_inicio TEXT NOT NULL, hora_fin TEXT NOT NULL)`; y `CREATE UNIQUE INDEX IF NOT EXISTS hueco_ocupado ON cita (id_especialista, fecha, hora_inicio) WHERE estado = 'RESERVADA'`. Reutilizar `registro_pacientes.base_datos.conectar` para abrir la conexión (misma base de datos, D-C02) y no redefinirla
- [X] T004 [P] Añadir a `programacion_citas/base_datos.py` las consultas, todas con parámetros `?` y devolviendo `sqlite3.Row` o listas de filas (data-model.md; depende de T003): `listar_centros(conexion)` y `listar_especialidades(conexion)` ordenados por nombre; `buscar_especialistas(conexion, especialidad, centro)` que une las tres tablas y filtra por los **dos** nombres (PD-C15); `obtener_especialista(conexion, id_especialista)`; `listar_especialistas(conexion)` con centro y especialidad resueltos; `citas_reservadas_de(conexion, id_especialista, fecha)`; `citas_reservadas_futuras_de(conexion, id_especialista, momento)`; `franjas_de(conexion, id_especialista)`; `insertar_cita(conexion, valores)`; `obtener_cita(conexion, id_cita)`; `citas_de_paciente(conexion, codigo_historia)` ordenadas por fecha y hora; `citas_reservadas_de_paciente(conexion, codigo_historia)`; `actualizar_estado_cita(conexion, id_cita, estado, motivo)`; `trasladar_cita(conexion, id_cita, fecha, hora_inicio, momento_reserva)`; `insertar_franja(conexion, valores)`; `actualizar_duracion(conexion, id_especialista, duracion_minutos)`
- [X] T005 Crear `programacion_citas/datos_iniciales.py` (RN-C01, RN-C02; PD-C19; CA-C13; D-C12; principio IV; depende de T003) con `ESPECIALIDADES`, `CENTROS` y `ESPECIALISTAS` como literales de Python con datos **inventados** (al menos 2 centros, 3 especialidades y 5 especialistas, repartidos de forma que existan combinaciones especialidad+centro sin resultados para poder validar CL-C02, e incluyendo un especialista con horario `"09:00"`–`"13:00"`, `dias_semana="1,2,3,4,5"` y `duracion_minutos=20` para CA-C01), y `precargar(conexion)` que inserta cada tabla **solo si está vacía** (`SELECT COUNT(*)` previo), de modo que arranques repetidos no dupliquen datos ni pisen los existentes (principio V)
- [X] T006 Crear `programacion_citas/servicio.py` con la base del servicio (contracts/servicio-citas.md; depende de T002, T003, T004 y T005): importar `buscar_por_codigo` y `buscar_por_documento` de `registro_pacientes.servicio` (D-C04, sin duplicar la normalización); `@dataclass(frozen=True)` para `Especialista` (`id_especialista`, `nombre`, `centro`, `especialidad`, `dias_semana`, `hora_inicio`, `hora_fin`, `duracion_minutos`), `Hueco` (`hora_inicio`, `duracion_minutos`, `libre`) y `Cita` (`id_cita`, `codigo_historia`, `id_especialista`, `nombre_especialista`, `especialidad`, `centro`, `fecha`, `hora_inicio`, `duracion_minutos`, `estado`, `motivo_cancelacion`, `momento_reserva`); constantes `ESTADO_RESERVADA = "RESERVADA"`, `ESTADO_CANCELADA_PACIENTE = "CANCELADA_PACIENTE"`, `ESTADO_CANCELADA_CENTRO = "CANCELADA_CENTRO"`, `MOTIVO_PACIENTE = "A petición del paciente"`, `MOTIVO_FRANJA = "Franja bloqueada del especialista"`, `MOTIVO_DURACION = "Cambio de la duración de las consultas"` (PD-C09); las ocho excepciones del contrato con sus mensajes exactos (`PacienteNoIdentificado`, `HuecoNoDisponible`, `HuecoPasado`, `CitaSolapada`, `FueraDePlazo`, `CitaYaCancelada`, `CitaNoEncontrada`, `ErrorValidacion`); `MINUTOS_24_HORAS = 24 * 60`; `momento_actual()` que devuelve `datetime.datetime.now()` y es el **único** punto que consulta el reloj (D-C10); e `inicializar_base_datos(ruta_bd)` que conecta, llama a `crear_esquema`, llama a `precargar` y cierra, sin borrar datos
- [X] T007 Crear el esqueleto de `programacion_citas/web.py` (contracts/interfaz-web-citas.md; D-C13, D-C16; depende de T006): clase `ManejadorCitas(registro_pacientes.web.ManejadorPacientes)` que **hereda** del manejador del módulo de registro; `do_GET` y `do_POST` separan ruta y parámetros con `urllib.parse.urlsplit`/`parse_qs(keep_blank_values=True)`, leen el cuerpo POST según `Content-Length`, y enrutan **solo** las 11 rutas del contrato (`/citas`, `/citas/buscar`, `/citas/huecos`, `POST /citas`, `/citas/mias`, `POST /citas/<id>/cancelar`, `GET|POST /citas/<id>/reprogramar` con la expresión `^/citas/([0-9]+)/reprogramar$` y `^/citas/([0-9]+)/cancelar$`, `/agenda`, `POST /agenda/bloquear`, `POST /agenda/duracion`); cualquier ruta que no sea de citas se delega con `super().do_GET()` / `super().do_POST()`, de modo que las 6 rutas del módulo de registro siguen funcionando sin tocarlo; reutilizar `pagina` y `escapar` de `registro_pacientes.web` para que **todo** dato mostrado se escape (D-C16); cada ruta todavía sin implementar responde `404`; y `crear_servidor(ruta_bd, host="127.0.0.1", puerto=8000)` que devuelve un `ThreadingHTTPServer` con `ManejadorCitas` y el atributo `ruta_bd`
- [X] T008 Modificar **solo** `app.py` para que importe `crear_servidor` e `inicializar_base_datos` de `programacion_citas` en lugar de `registro_pacientes` (D-C13; principio V; depende de T006 y T007). `programacion_citas.servicio.inicializar_base_datos` debe llamar también a `registro_pacientes.servicio.inicializar_base_datos` para que la tabla `paciente` siga creándose. No cambiar la lectura de `RUTA_BD`, `PUERTO` ni `HOST`, ni los mensajes de arranque, ni ningún otro archivo del módulo de registro
- [X] T009 [P] Crear `tests/utilidades_citas.py` (principio IV; D-C10, D-C15; depende de T006): `MOMENTO_FIJO = datetime.datetime(2026, 10, 1, 8, 0, 0)` (un jueves, día ISO 4) como momento actual de referencia en las pruebas; `datos_especialista(**cambios)` que devuelve un especialista ficticio con `dias_semana="1,2,3,4,5"`, `hora_inicio="09:00"`, `hora_fin="13:00"` y `duracion_minutos=20`; `fecha_futura(dias=1)` que devuelve una fecha de consulta posterior a `MOMENTO_FIJO`; clase `BaseCitasTestCase(unittest.TestCase)` que en `setUp` crea un `tempfile.TemporaryDirectory`, fija `self.ruta_bd`, llama a `programacion_citas.servicio.inicializar_base_datos`, registra **un paciente ficticio** con `registro_pacientes.servicio.registrar_paciente` reutilizando `tests.utilidades.datos_paciente` y guarda su código en `self.codigo`, y en `tearDown` limpia el directorio; y clase `ServidorCitasTestCase(BaseCitasTestCase)` que arranca `programacion_citas.web.crear_servidor(self.ruta_bd, puerto=0)` en un hilo *daemon*, lo detiene en `tearDown` y ofrece `peticion_get(ruta)` y `peticion_post(ruta, campos)` sin seguir redirecciones. **No modificar `tests/utilidades.py`**
- [X] T010 [P] Crear `tests/test_agenda.py` con las pruebas unitarias de la aritmética, que no tocan base de datos ni HTTP (depende de T002): `test_cac01_rejilla_de_20_minutos_tiene_12_huecos` comprueba 12 huecos con primero `"09:00"` y último `"12:40"`; `test_clc05_rejilla_de_50_minutos_tiene_4_huecos_sin_tramo_parcial` comprueba 4 huecos y último `"11:30"`; `test_clc06_dia_sin_consulta_no_tiene_huecos` comprueba lista vacía para un sábado; `test_pdc06_citas_consecutivas_no_se_solapan` comprueba que 9:00+20 y 9:20+20 no se solapan y que 9:00+30 y 9:20+20 sí; `test_pdc12_hueco_que_acaba_al_fin_de_la_franja_queda_bloqueado` comprueba que con franja 9:00–11:00 y duración 20 quedan bloqueados 9:00, 10:00 y 10:40 y no 11:00 ni 11:20; `test_pdc10_encaje_en_rejilla_de_30_minutos` comprueba que `"09:00"` encaja y `"09:20"` no

**Punto de control**: `python app.py` arranca, sirve las 6 rutas del módulo de registro sin cambios y responde `404` en las rutas de citas; `python -m unittest` pasa, incluido `tests/test_agenda.py`.

---

## Fase 3: Historia de usuario 1 - Reservar una cita (Prioridad: P1) 🎯 MVP

**Objetivo**: que un paciente identificado busque especialista por especialidad y centro, vea los
huecos libres de una fecha y reserve uno (RF-C01 a RF-C04).

**Prueba independiente**: identificar a un paciente precargado, buscar especialistas por
especialidad y centro, comprobar la rejilla de huecos de una fecha, reservar uno y verificar que
desaparece de los libres.

### Pruebas de la historia 1 (escribir primero; deben fallar)

- [X] T011 [P] [US1] Crear `tests/test_reserva.py` con `PruebasReserva(BaseCitasTestCase)` (depende de T009): `test_cac03_busqueda_exige_especialidad_y_centro` comprueba que solo se devuelven los especialistas que cumplen ambos filtros; `test_clc02_busqueda_sin_resultados_devuelve_lista_vacia` sin error; `test_cac01_huecos_de_la_rejilla_completa` comprueba 12 huecos libres; `test_cac02_hueco_reservado_desaparece_de_los_libres` y que los demás siguen libres; `test_clc06_fecha_sin_consulta_no_ofrece_huecos`; `test_clc01_sin_huecos_libres_devuelve_lista_vacia` tras ocupar todos; `test_cac04_identificacion_por_documento_equivale_a_codigo` comprueba que ambas vías devuelven el mismo código de historia clínica; `test_clc09_identificacion_de_paciente_inexistente_lanza_error` sin crear paciente; `test_cac05_reserva_solapada_se_rechaza` con `CitaSolapada`; `test_pdc06_reserva_consecutiva_se_acepta` (una cita a las 9:00 y otra a las 9:20 con duración 20); `test_rnc08_hueco_pasado_se_rechaza` con `HuecoPasado`; `test_clc03_segunda_reserva_del_mismo_hueco_se_rechaza` con `HuecoNoDisponible`. Todas pasan `ahora=MOMENTO_FIJO`

### Implementación de la historia 1

- [X] T012 [US1] Implementar en `programacion_citas/servicio.py` la identificación y la búsqueda (RF-C01, RF-C02; PD-C01, PD-C15; CA-C03, CA-C04, CL-C02, CL-C09; depende de T006): `identificar_paciente(ruta_bd, codigo=None, tipo_documento=None, numero_documento=None)` que, si llega `codigo`, delega en `registro_pacientes.servicio.buscar_por_codigo` y, si llegan tipo y número, en `buscar_por_documento`, devuelve el `codigo_historia` del paciente encontrado y lanza `PacienteNoIdentificado` con el mensaje «No existe ningún paciente con esos datos.» si no existe o si no llega ningún dato; y `buscar_especialistas(ruta_bd, especialidad, centro)` que exige los **dos** filtros y devuelve la lista de `Especialista` que cumplen ambos, vacía si no hay coincidencias. **No crear ni modificar pacientes** (frontera del principio II)
- [X] T013 [US1] Implementar `consultar_huecos(ruta_bd, id_especialista, fecha, ahora)` en `programacion_citas/servicio.py` (RF-C03, RN-C03, RN-C04, RN-C08; PD-C03, PD-C05, PD-C12, PD-C16; CA-C01, CL-C01, CL-C06; depende de T012): obtiene el especialista, genera la rejilla con `agenda.generar_rejilla`, y marca cada hueco como libre solo si (1) no lo ocupa una cita en estado `RESERVADA` de ese especialista, fecha y hora de inicio, (2) no cae en ninguna franja bloqueada del especialista según `agenda.hueco_en_franja` con la fecha dentro de `[fecha_inicio, fecha_fin]` (PD-C12) y (3) su inicio no es anterior a `ahora` (PD-C05). Devuelve solo los huecos libres, lista vacía si no hay ninguno o si la fecha no es día de consulta
- [X] T014 [US1] Implementar `reservar_cita(ruta_bd, codigo_historia, id_especialista, fecha, hora_inicio, ahora)` en `programacion_citas/servicio.py` (RF-C04, RN-C04, RN-C07, RN-C08; PD-C06, PD-C17; CA-C02, CA-C05, CL-C03; D-C08; depende de T013): dentro de `BEGIN IMMEDIATE` comprueba en este orden que la hora es inicio de un hueco de la rejilla vigente (`HuecoNoDisponible`), que no ha pasado (`HuecoPasado`), que no cae en franja bloqueada (`HuecoNoDisponible`), y que el paciente no tiene otra cita `RESERVADA` solapada usando `agenda.se_solapan` con la duración vigente del especialista de **cada** cita (`CitaSolapada`); después inserta con `estado='RESERVADA'`, `motivo_cancelacion=None` y `momento_reserva=ahora`. Captura `sqlite3.IntegrityError` del índice `hueco_ocupado` y la traduce a `HuecoNoDisponible` con el mensaje «Ese hueco ya no está disponible.» (CL-C03). Devuelve la `Cita` creada
- [X] T015 [US1] Implementar en `programacion_citas/web.py` las rutas 1 a 4 del contrato (RF-C01 a RF-C04; PD-C02, PD-C18; depende de T007 y T014): `GET /citas` con los dos formularios de identificación (campo `codigo`; desplegable `tipo_documento` con DNI, NIE y Pasaporte más campo `numero_documento`) y enlace «Ver mis citas»; `GET /citas/buscar` con los desplegables de especialidad y centro rellenados desde la base de datos, que lista los especialistas encontrados con enlace a los huecos, muestra «No hay especialistas de esa especialidad en ese centro.» si no hay ninguno y responde `400` con «No existe ningún paciente con esos datos.» si el paciente no se identifica; `GET /citas/huecos` con un botón de reserva por hueco libre, el aviso «No hay huecos disponibles en esa fecha.» si no hay, y `400` si la fecha está mal formada; `POST /citas` que reserva y redirige con `303` a `/citas/mias?codigo=...&aviso=reservada`, devolviendo `409` con el mensaje exacto de la excepción en `HuecoNoDisponible`, `HuecoPasado` y `CitaSolapada`, y `400` si falta algún campo. Todo dato mostrado se escapa

**Punto de control**: T011 pasa; en el navegador un paciente se identifica, busca especialista, ve 12 huecos y reserva el de las 9:00, que desaparece de los libres.

---

## Fase 4: Historia de usuario 2 - Consultar mis citas y el motivo de una cancelación (Prioridad: P2)

**Objetivo**: que el paciente vea todas sus citas con su estado y, en las canceladas, el motivo
(RF-C05, RN-C13).

**Prueba independiente**: crear citas en los tres estados para un paciente y comprobar que el
listado las muestra con su estado y su motivo.

### Pruebas de la historia 2 (escribir primero; deben fallar)

- [X] T016 [P] [US2] Añadir a `tests/test_reserva.py` la clase `PruebasListado(BaseCitasTestCase)` (depende de T009): `test_rfc05_listado_muestra_estado_de_cada_cita` con una cita en cada uno de los tres estados; `test_pdc14_paciente_sin_citas_devuelve_lista_vacia`; `test_pdc14_cita_pasada_sigue_reservada` comprueba que una cita cuya hora ya pasó se sigue listando en estado `RESERVADA` (no existe estado «atendida»); `test_rnc13_cita_cancelada_incluye_su_motivo`

### Implementación de la historia 2

- [X] T017 [US2] Implementar `consultar_citas(ruta_bd, codigo_historia)` en `programacion_citas/servicio.py` (RF-C05; PD-C14; depende de T012): devuelve todas las citas del paciente, pasadas y futuras, ordenadas por fecha y hora, como objetos `Cita` con el nombre del especialista, su especialidad, su centro y la `duracion_minutos` **vigente** del especialista (PD-C10), con su estado y su `motivo_cancelacion`. Lista vacía si no tiene ninguna. No filtra por fecha ni cambia el estado de las pasadas
- [X] T018 [US2] Implementar la ruta 5 `GET /citas/mias` en `programacion_citas/web.py` (RF-C05; CA-C11; PD-C14, PD-C18; depende de T015 y T017): tabla con especialista, especialidad, centro, fecha, hora, estado y, en las canceladas, el motivo; botón de cancelar y enlace de reprogramar solo en las citas `RESERVADA`; aviso «No tiene ninguna cita.» si la lista está vacía; y los avisos `aviso=reservada`, `aviso=cancelada` y `aviso=reprogramada` cuando lleguen como parámetro. Los estados se muestran en español como «Reservada», «Cancelada por el paciente» y «Cancelada por el centro»

**Punto de control**: T016 pasa; el paciente ve su cita reservada en `/citas/mias`; las pruebas de US1 siguen pasando.

---

## Fase 5: Historia de usuario 3 - Cancelar una cita (Prioridad: P3)

**Objetivo**: que el paciente cancele una cita dentro de plazo, dejándola «cancelada por el
paciente» y liberando su hueco (RF-C06, RN-C09).

**Prueba independiente**: cancelar citas con distintas antelaciones y comprobar el estado
resultante, la liberación del hueco y el rechazo de los casos no permitidos.

### Pruebas de la historia 3 (escribir primero; deben fallar)

- [X] T019 [P] [US3] Crear `tests/test_cancelacion.py` con `PruebasCancelacion(BaseCitasTestCase)` (depende de T009): `test_cac06_cancelacion_con_mas_de_24_horas_libera_el_hueco` comprueba estado `CANCELADA_PACIENTE`, motivo «A petición del paciente» y que el hueco vuelve a ofrecerse libre; `test_cac07_cancelacion_con_menos_de_24_horas_se_rechaza` con `FueraDePlazo`, para una cita reservada hace más de 24 horas; `test_cac08_cita_reservada_hoy_para_dentro_de_3_horas_se_puede_cancelar`; `test_clc07_cancelar_una_cita_ya_cancelada_se_rechaza` con `CitaYaCancelada`; `test_rfc06_cancelar_una_cita_de_otro_paciente_se_rechaza` con `CitaNoEncontrada`. Todas fijan `ahora` y `momento_reserva` de forma explícita

### Implementación de la historia 3

- [X] T020 [US3] Implementar en `programacion_citas/servicio.py` la función auxiliar `_comprobar_plazo(cita, ahora)` (RN-C09; PD-C07; CA-C07, CA-C08; depende de T017): calcula los minutos entre `ahora` y el inicio de la cita (`fecha` + `hora_inicio`); si faltan 24 horas o más, permite; si falta menos, permite **solo** si el intervalo entre `momento_reserva` y el inicio de la cita es inferior a 24 horas; en otro caso lanza `FueraDePlazo` con el mensaje «Solo se puede cancelar o reprogramar hasta 24 horas antes del inicio de la cita.» Documentar en el *docstring* que `momento_reserva` es el de la última reserva o reprogramación (PD-C07, aclaración Q2)
- [X] T021 [US3] Implementar `cancelar_cita(ruta_bd, codigo_historia, id_cita, ahora)` en `programacion_citas/servicio.py` (RF-C06, RN-C06, RN-C13; PD-C04, PD-C09; CA-C06, CL-C07; depende de T020): comprueba que la cita existe y es de ese paciente (`CitaNoEncontrada`), que está en estado `RESERVADA` (`CitaYaCancelada` con «Esa cita ya está cancelada.») y el plazo con `_comprobar_plazo`; después la pasa a `CANCELADA_PACIENTE` con motivo `MOTIVO_PACIENTE`, lo que libera su hueco por el propio índice parcial. Devuelve la `Cita` actualizada
- [X] T022 [US3] Implementar la ruta 6 `POST /citas/<id_cita>/cancelar` en `programacion_citas/web.py` (RF-C06; CA-C06, CA-C07, CL-C07; PD-C18; depende de T018 y T021): redirige con `303` a `/citas/mias?codigo=...&aviso=cancelada` si se cancela; responde `409` con el mensaje exacto en `FueraDePlazo` y `CitaYaCancelada`; y `404` si la cita no existe o no es del paciente

**Punto de control**: T019 pasa; en el navegador se cancela una cita y su hueco vuelve a ofrecerse; las pruebas de US1 y US2 siguen pasando.

---

## Fase 6: Historia de usuario 4 - Reprogramar una cita (Prioridad: P4)

**Objetivo**: trasladar una cita a otro hueco libre del mismo especialista conservando la misma
cita (RF-C07, RN-C10).

**Prueba independiente**: trasladar una cita y comprobar que conserva su identificador, que el
hueco anterior queda libre y que el nuevo queda ocupado.

### Pruebas de la historia 4 (escribir primero; deben fallar)

- [X] T023 [P] [US4] Crear `tests/test_reprogramacion.py` con `PruebasReprogramacion(BaseCitasTestCase)` (depende de T009): `test_cac09_reprogramar_conserva_id_y_especialista_y_libera_el_hueco` comprueba el mismo `id_cita`, el mismo `id_especialista`, el hueco anterior libre y el nuevo ocupado; `test_pdc08_la_propia_cita_no_cuenta_como_solapamiento_consigo_misma`; `test_rnc07_reprogramar_a_un_hueco_solapado_con_otra_cita_se_rechaza` con `CitaSolapada`; `test_clc03_reprogramar_a_un_hueco_ocupado_se_rechaza` con `HuecoNoDisponible`; `test_cac07_reprogramar_fuera_de_plazo_se_rechaza` con `FueraDePlazo`; `test_clc08_reprogramar_una_cita_ya_cancelada_se_rechaza` con `CitaYaCancelada`; `test_pdc07_reprogramar_actualiza_el_momento_de_reserva` comprueba que una cita reservada hace un mes, reprogramada a un hueco de dentro de 3 horas, **puede** cancelarse después

### Implementación de la historia 4

- [X] T024 [US4] Implementar `reprogramar_cita(ruta_bd, codigo_historia, id_cita, fecha, hora_inicio, ahora)` en `programacion_citas/servicio.py` (RF-C07, RN-C07, RN-C10; PD-C07, PD-C08; CA-C09, CL-C08; depende de T014 y T021): comprueba estado y plazo igual que `cancelar_cita`, y el hueco destino igual que `reservar_cita` pero **excluyendo la propia cita** del cálculo de solapamiento (PD-C08) y del hueco ocupado; después hace un `UPDATE` que cambia `fecha`, `hora_inicio` y `momento_reserva = ahora`, conservando `id_cita`, `codigo_historia` e `id_especialista` (RN-C10, PD-C07). Nunca borra e inserta. El hueco anterior queda libre por el propio `UPDATE`. Devuelve la `Cita` actualizada
- [X] T025 [US4] Implementar las rutas 7 y 8 de reprogramación en `programacion_citas/web.py` (RF-C07; CA-C09, CL-C08; PD-C18; depende de T022 y T024): `GET /citas/<id_cita>/reprogramar` muestra los huecos libres **del mismo especialista** para la fecha indicada, cada uno con un botón que envía a la ruta 8, sin ofrecer cambio de especialista, y responde `409` con el mensaje correspondiente si la cita está fuera de plazo o ya cancelada, sin mostrar huecos; `POST /citas/<id_cita>/reprogramar` redirige con `303` a `/citas/mias?codigo=...&aviso=reprogramada` y responde `409` con el mensaje exacto en `HuecoNoDisponible`, `HuecoPasado`, `CitaSolapada`, `FueraDePlazo` y `CitaYaCancelada`

**Punto de control**: T023 pasa; en el navegador se traslada una cita al hueco de las 11:00 y su identificador no cambia; las pruebas de US1 a US3 siguen pasando.

---

## Fase 7: Historia de usuario 5 - Bloquear una franja de un especialista (Prioridad: P5)

**Objetivo**: que el administrativo bloquee una franja de uno o varios días y que las citas futuras
de dentro queden canceladas por el centro (RF-C08, RN-C11).

**Prueba independiente**: bloquear una franja con y sin citas dentro y comprobar qué citas cambian
de estado y qué huecos dejan de ofrecerse.

### Pruebas de la historia 5 (escribir primero; deben fallar)

- [X] T026 [P] [US5] Crear `tests/test_bloqueo.py` con `PruebasBloqueo(BaseCitasTestCase)` (depende de T009): `test_cac10_bloqueo_de_9_a_11_cancela_las_de_dentro_y_conserva_las_de_las_11` con citas a las 9:00, 10:00, 10:40 y 11:00, comprobando que las tres primeras pasan a `CANCELADA_CENTRO` y la de las 11:00 sigue `RESERVADA`; `test_cac11_la_cita_cancelada_se_ve_con_su_motivo_en_el_listado` con motivo «Franja bloqueada del especialista»; `test_rnc11_el_bloqueo_no_respeta_el_plazo_de_24_horas` con una cita que empieza dentro de menos de 24 horas; `test_pdc11_el_bloqueo_no_altera_una_cita_pasada`; `test_clc04_bloqueo_sin_citas_dentro_no_cancela_nada`; `test_pdc12_bloqueo_de_varios_dias_cancela_las_citas_de_todo_el_rango`; `test_rnc04_los_huecos_bloqueados_dejan_de_ofrecerse`

### Implementación de la historia 5

- [X] T027 [US5] Implementar `bloquear_franja(ruta_bd, id_especialista, fecha_inicio, fecha_fin, hora_inicio, hora_fin, ahora)` en `programacion_citas/servicio.py` (RF-C08, RN-C04, RN-C11; PD-C09, PD-C11, PD-C12; CA-C10, CL-C04; depende de T013): valida que las fechas y horas tienen formato correcto, que `fecha_fin` no es anterior a `fecha_inicio` y que `hora_fin` es mayor que `hora_inicio` (`ErrorValidacion`); inserta la franja; y pasa a `CANCELADA_CENTRO` con motivo `MOTIVO_FRANJA` las citas de ese especialista que cumplen **las tres** condiciones: estado `RESERVADA`, fecha dentro de `[fecha_inicio, fecha_fin]` con la hora solapada con el tramo según `agenda.hueco_en_franja`, y **inicio posterior a `ahora`** (PD-C11: una cita pasada no cambia de estado). No aplica el plazo de 24 horas (RN-C11). Devuelve la lista de `Cita` canceladas, vacía si no había ninguna. No implementar ninguna operación de desbloqueo (PD-C13)
- [X] T028 [US5] Implementar las rutas 9 y 10 en `programacion_citas/web.py` (RF-C08; CA-C13; PD-C02, PD-C11, PD-C18; depende de T025 y T027): `GET /agenda` lista los especialistas precargados con su centro, especialidad, horario y duración vigente, y al elegir uno muestra el formulario de bloqueo con `fecha_inicio`, `fecha_fin`, `hora_inicio` y `hora_fin`, **sin** ningún formulario de alta o edición de centros, especialidades o especialistas (CA-C13) y sin identificación de ningún tipo (PD-C02); `POST /agenda/bloquear` responde `200` con la confirmación, el número de citas canceladas por el centro y su listado, indicando que las citas pasadas no se han cancelado (PD-C11), y `400` con el mensaje del dato inválido en `ErrorValidacion`

**Punto de control**: T026 pasa; en el navegador se bloquea la franja de 9:00 a 11:00 y el paciente ve su cita cancelada con el motivo en `/citas/mias`; las pruebas de US1 a US4 siguen pasando.

---

## Fase 8: Historia de usuario 6 - Ajustar la duración de las consultas (Prioridad: P6)

**Objetivo**: que el administrativo cambie la duración de las consultas de un especialista,
recalculando la rejilla y cancelando por el centro las citas futuras que ya no encajan (RF-C09,
RN-C12).

**Prueba independiente**: cambiar la duración con citas en horas que encajan y en horas que no, y
comprobar la nueva rejilla y el estado de cada cita.

### Pruebas de la historia 6 (escribir primero; deben fallar)

- [X] T029 [P] [US6] Crear `tests/test_duracion.py` con `PruebasDuracion(BaseCitasTestCase)` (depende de T009): `test_cac12_al_pasar_de_20_a_30_minutos_la_de_las_9_sigue_y_la_de_las_9_20_se_cancela` comprobando motivo «Cambio de la duración de las consultas»; `test_clc05_al_pasar_a_50_minutos_la_rejilla_tiene_4_huecos`; `test_pdc11_el_cambio_de_duracion_no_altera_una_cita_pasada`; `test_pdc10_la_duracion_de_una_cita_es_la_vigente_del_especialista` comprueba que tras el cambio la misma cita se lista con la nueva duración; `test_pdc20_el_recalculo_no_comprueba_el_solapamiento_del_paciente` documenta la limitación conocida: al alargarse las consultas, dos citas del mismo paciente pueden quedar solapadas y **ambas se conservan**; `test_rfc09_duracion_no_positiva_se_rechaza` con `ErrorValidacion`

### Implementación de la historia 6

- [X] T030 [US6] Implementar `ajustar_duracion(ruta_bd, id_especialista, duracion_minutos, ahora)` en `programacion_citas/servicio.py` (RF-C09, RN-C12; PD-C09, PD-C10, PD-C11, PD-C20; CA-C12; depende de T027): valida que `duracion_minutos` es un entero positivo (`ErrorValidacion`); actualiza `especialista.duracion_minutos`; y para cada fecha con citas `RESERVADA` **futuras** de ese especialista recalcula la rejilla con la nueva duración y pasa a `CANCELADA_CENTRO` con motivo `MOTIVO_DURACION` las que no cumplen `agenda.encaja_en_rejilla` (RN-C12, PD-C10). Las citas cuya hora ya pasó no se tocan (PD-C11). Documentar en el *docstring* que **no** se vuelve a comprobar RN-C07, con referencia a PD-C20. Devuelve la lista de `Cita` canceladas
- [X] T031 [US6] Implementar la ruta 11 `POST /agenda/duracion` en `programacion_citas/web.py` (RF-C09; CA-C12; PD-C18; depende de T028 y T030): añadir al formulario de `GET /agenda` el campo `duracion_minutos`; responder `200` con la confirmación, la nueva rejilla y el listado de citas canceladas por el centro, y `400` con el mensaje del dato inválido si la duración no es un entero positivo

**Punto de control**: T029 pasa; en el navegador se cambia la duración de 20 a 30 minutos, la cita de las 9:00 sigue reservada y la de las 9:20 queda cancelada por el centro; las pruebas de US1 a US5 siguen pasando.

---

## Fase 9: Cierre y aspectos transversales

**Propósito**: cerrar la cobertura de rutas, la documentación y la validación completa.

- [X] T032 [P] Crear `tests/test_web_citas.py` con `PruebasWebCitas(ServidorCitasTestCase)` (CA-C13; PD-C02; depende de T031): una prueba por cada una de las 11 rutas del contrato comprobando su código de estado y un fragmento de su contenido; `test_cac13_no_existe_pantalla_para_gestionar_centros_ni_especialistas` comprueba que `/agenda/especialistas/nuevo`, `/agenda/centros` y `/agenda/especialidades` responden `404`; `test_pdc13_no_existe_ruta_para_desbloquear_una_franja` comprueba `404`; `test_dc13_las_rutas_del_modulo_de_registro_siguen_funcionando` comprueba que `GET /`, `GET /pacientes/nuevo` y `GET /buscar` siguen respondiendo `200` con el manejador combinado; y `test_dc16_los_datos_mostrados_se_escapan` comprueba que un dato con `<b>` aparece escapado
- [X] T033 [P] Añadir al `README.md`, conservando su contenido actual, una sección «Módulo de programación de citas» con las direcciones de los dos flujos (`/citas` y `/agenda`), la advertencia de que la página de inicio todavía no enlaza con ellos (D-C14) y el recordatorio de que no hay control de acceso y no deben introducirse datos reales de personas (D-C16). No modificar las secciones existentes
- [X] T034 Revisar que no se ha modificado ningún archivo de `registro_pacientes/` ni `tests/utilidades.py` (`git diff --name-only`), y que el único archivo preexistente cambiado es `app.py` (T008) más las adiciones de `README.md` (T033). Si aparece cualquier otro, revertirlo (principio III, D-C03)
- [X] T035 Ejecutar `python -m unittest` y comprobar que pasan todas las pruebas de los dos módulos: las 62 preexistentes del módulo de registro **sin modificar ninguna** y las nuevas de este módulo (CE-C08)
- [X] T036 Ejecutar `docker compose up --build` y recorrer [quickstart.md](quickstart.md) de principio a fin, incluida la validación de persistencia (`docker compose down` y `up` conservan las citas) y la comprobación de que la precarga es idempotente y no duplica especialistas al arrancar dos veces (principio V, D-C12)
- [X] T037 Repasar la tabla de «Comprobación de la constitución» de [plan.md](plan.md) contra el código escrito y confirmar cada casilla de la columna «Tras la fase 1»: vocabulario del principio I v3.2.0 sin sinónimos, alcance sin añadidos, trazabilidad en todos los *docstrings*, datos ficticios y arranque en contenedor con un único comando

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Preparación (fase 1)**: sin dependencias.
- **Base común (fase 2)**: depende de la fase 1; bloquea todas las historias.
- **US1 (fase 3)**: depende de la fase 2.
- **US2 (fase 4)**: depende de US1 (usa la identificación y necesita citas que listar).
- **US3 (fase 5)**: depende de US2 (el listado es de donde se cancela) y de US1.
- **US4 (fase 6)**: depende de US3 (reutiliza la comprobación de plazo y estado) y de US1.
- **US5 (fase 7)**: depende de US1 (necesita `consultar_huecos` y citas reservadas); no depende de US3 ni de US4.
- **US6 (fase 8)**: depende de US5 (reutiliza el patrón de cancelación por el centro) y de US1.
- **Cierre (fase 9)**: depende de todas las historias.

```text
Fase 1 → Fase 2 → US1 ─┬→ US2 → US3 → US4
                       └→ US5 → US6
                                   └→ Fase 9 (tras US4 y US6)
```

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar.
- `agenda.py` → `base_datos.py` → `servicio.py` → `web.py`.
- La historia se completa (punto de control) antes de pasar a la siguiente.

### Oportunidades de paralelismo

- Fase 2: T002, T003 y T009 en paralelo (archivos distintos); después T004 → T005 → T006 → T007 → T008. T010 en paralelo con T009 en cuanto T002 esté hecho.
- En cada historia, la tarea de pruebas va a un archivo propio y puede escribirse en paralelo con las pruebas de otra historia: T011, T019, T023, T026 y T029 tocan archivos distintos.
- **US2/US3/US4 y US5/US6 son las dos ramas paralelas** del grafo: una persona puede llevar el flujo del paciente (US2→US3→US4) y otra el de la agenda (US5→US6) en cuanto US1 esté terminada.
- Las tareas de implementación **dentro** de una misma rama no se marcan [P] porque comparten `programacion_citas/servicio.py` y `programacion_citas/web.py`.
- Fase 9: T032 y T033 en paralelo; después T034 → T035 → T036 → T037.

---

## Ejemplo de paralelismo: base común y dos ramas

```text
# Fase 2, a la vez (archivos distintos):
Tarea: "T002 Implementar programacion_citas/agenda.py"
Tarea: "T003 Implementar programacion_citas/base_datos.py"
Tarea: "T009 Crear tests/utilidades_citas.py"

# Tras US1, dos ramas en paralelo:
Rama A (flujo del paciente):      T016 → T017 → T018 → T019 → ... → T025
Rama B (flujo de la agenda):      T026 → T027 → T028 → T029 → T030 → T031
```

---

## Estrategia de implementación

### MVP primero (solo US1)

1. Completar la fase 1: preparación.
2. Completar la fase 2: base común (CRÍTICO, bloquea todas las historias).
3. Completar la fase 3: US1.
4. **PARAR Y VALIDAR**: un paciente se identifica, busca especialista y reserva un hueco. Con eso
   ya está cubierto el objetivo de negocio principal —reservar sin llamar por teléfono— y la
   capacidad 4 del principio II.

### Entrega incremental

1. Base común → cimientos listos.
2. US1 → validar → **MVP** (capacidad 4: reservar una cita).
3. US2 y US3 → validar → el paciente ya consulta y cancela (parte de la capacidad 5).
4. US4 → validar → capacidad 5 completa (cancelar o reprogramar).
5. US5 y US6 → validar → capacidad 6 completa (gestionar la agenda de un especialista).
6. Fase 9 → cierre, cobertura de rutas y validación en contenedor.

Cada historia añade valor sin romper las anteriores: los puntos de control exigen que las pruebas
de las historias previas sigan pasando.

---

## Notas

- Tareas [P] = archivos distintos, sin dependencias pendientes.
- La etiqueta [USn] traza cada tarea a su historia de usuario.
- Verificar que las pruebas fallan antes de implementar.
- Hacer un *commit* por tarea o por grupo lógico.
- Se puede parar en cualquier punto de control para validar la historia por separado.
- Evitar: tareas vagas, conflictos en el mismo archivo y dependencias entre historias que rompan su
  independencia.
- **Punto abierto (D-C14)**: la página `/` del módulo de registro no enlaza con `/citas` ni
  `/agenda`. No hay ninguna tarea que lo cambie, porque significaría modificar el módulo de
  registro y ninguna parte de la especificación lo pide. Si se decide añadir los enlaces, debe
  hacerse como una tarea nueva y explícita, no de pasada.
