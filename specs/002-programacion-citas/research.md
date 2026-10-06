# Investigación y decisiones técnicas: Módulo de Programación de Citas

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Fecha**: 2026-09-28 ·
**Actualizada**: 2026-10-06 (D-C17 a D-C20, tras la segunda sesión de aclaraciones; D-C21, tras
`/speckit-analyze`)

Cada decisión indica qué requisito, regla o precisión de la especificación resuelve (principio
III de la constitución) y qué alternativas se descartaron. Las decisiones se numeran `D-C01`…
para no colisionar con las `D-01`…`D-10` del módulo de registro.

No queda ninguna `NEEDS CLARIFICATION`: las tres ambigüedades de la especificación se cerraron en
la sesión de aclaraciones del 2026-09-28 (PD-C07, PD-C11, PD-C12) y las cuatro de la sesión del
2026-10-06, en PD-C07 y PD-C21 a PD-C23. Las decisiones D-C17 a D-C20 llevan esas cuatro
respuestas al diseño; D-C01 a D-C16 no cambian salvo las dos notas que se indican en D-C15 y
D-C16. D-C21 recoge la decisión de la persona responsable sobre el hallazgo A1 de
`/speckit-analyze` (PD-C05, CL-C13).

## D-C01 · Tecnología: reutilizar el stack del módulo de registro

- **Decisión**: Python 3 con solo la biblioteca estándar, igual que el módulo de registro
  (`http.server`, `sqlite3`, `html`, `urllib.parse`, `datetime`, `dataclasses`). Ninguna
  dependencia nueva.
- **Justificación**: el principio V exige arrancar con `docker compose up` sin servicios de pago
  ni cuentas externas, y el módulo de registro ya demuestra que la biblioteca estándar basta. El
  principio II obliga a elegir la opción más simple: introducir un marco web o un ORM añadiría
  dependencias sin resolver ningún requisito de RF-C01 a RF-C09.
- **Alternativas descartadas**: Flask o FastAPI (dependencias externas, sin ventaja para 9
  requisitos funcionales); SQLAlchemy (el SQL de este módulo son consultas simples y
  parametrizadas); una segunda tecnología para el módulo de citas (dos stacks en un proyecto
  académico de dos módulos es complejidad injustificada).

## D-C02 · Persistencia: la misma base de datos SQLite, con tablas nuevas

- **Decisión**: las tablas de este módulo viven en el **mismo archivo** SQLite que ya usa el
  módulo de registro (`datos/pacientes.db` por defecto, configurable con `RUTA_BD`). Se añaden
  cinco tablas: `centro`, `especialidad`, `especialista`, `cita` y `franja_bloqueada`. No se
  modifica la tabla `paciente`.
- **Justificación**: RN-C05 obliga a que cada cita referencie al paciente por su código de
  historia clínica, y CA-C04 exige identificar al paciente por su documento. Con una sola base de
  datos esa consulta es directa, la integridad referencial es comprobable y todo queda en el único
  volumen que define el principio V. Dos archivos obligarían a abrir dos conexiones y harían
  imposible una transacción conjunta.
- **Alternativas descartadas**: un archivo `datos/citas.db` separado (rompe la integridad con
  `paciente` y duplica la configuración); **renombrar** el archivo a algo como `his.db` para
  reflejar que ya no guarda solo pacientes (obligaría a tocar `app.py`, el `Dockerfile`, el
  `docker-compose.yml` y el README del módulo de registro por un motivo puramente cosmético, en
  contra del principio II). Se asume el nombre heredado y se documenta que es la base de datos
  única del proyecto.

## D-C03 · Estructura: un paquete nuevo `programacion_citas/`, sin tocar el módulo de registro

- **Decisión**: el código vive en un paquete nuevo, hermano de `registro_pacientes/`, con cinco
  módulos: `base_datos.py` (esquema y SQL), `agenda.py` (aritmética temporal pura),
  `servicio.py` (reglas de negocio), `datos_iniciales.py` (precarga) y `web.py` (rutas y HTML).
- **Justificación**: el principio III prohíbe implementar lo que no está en la especificación, y
  la especificación del módulo de citas no pide ningún cambio en el de registro. Un paquete
  separado hace que la frontera entre los dos módulos del principio II sea física y verificable.
  `agenda.py` se separa porque la generación de huecos (RN-C03, PD-C03), el solapamiento (RN-C07,
  PD-C06) y el encaje en la rejilla (RN-C12, PD-C10) son el corazón de CA-C01, CA-C12 y CL-C05 y
  deben poder probarse sin base de datos ni HTTP.
- **Alternativas descartadas**: añadir las citas dentro de `registro_pacientes/` (mezcla dos
  módulos con alcances distintos y contradice la regla de frontera del principio II); un único
  módulo `citas.py` con todo (impide probar la aritmética aislada, que es lo más delicado).

## D-C04 · Identificación del paciente: se reutiliza el módulo de registro, no se duplica

- **Decisión**: `programacion_citas.servicio` importa `buscar_por_codigo` y
  `buscar_por_documento` de `registro_pacientes.servicio` para resolver RF-C01. La dependencia es
  en un solo sentido: citas → registro. El módulo de registro no importa nada de citas.
- **Justificación**: PD-C01 exige que las dos vías de identificación lleven al mismo paciente y
  que la comparación sea normalizada igual que en el módulo de registro. Reimplementar la
  normalización garantizaría divergencias y rompería CA-C04. Es también el punto donde este
  proyecto integra dos piezas de TIC sobre un proceso de negocio único (competencia CESI1): la
  identidad que produce un módulo es la que consume el otro.
- **Alternativas descartadas**: copiar `normalizar_texto` al paquete de citas (duplicidad que
  divergirá); consultar la tabla `paciente` con SQL propio desde citas (salta la lógica de
  normalización y volvería a implementar PD-C01).

## D-C05 · Los huecos se derivan, nunca se almacenan

- **Decisión**: no existe tabla de huecos. La rejilla de un especialista en una fecha se calcula
  en cada consulta a partir de su horario y su duración vigente (PD-C03), y la disponibilidad se
  obtiene restando las citas reservadas y las franjas bloqueadas (RN-C04).
- **Justificación**: RN-C12 permite cambiar la duración de las consultas, lo que redefine la
  rejilla completa. Con huecos almacenados, cada cambio de duración exigiría regenerar filas y
  el sistema podría quedar en un estado inconsistente; derivándolos, la rejilla es siempre la
  vigente por construcción. Es además la opción más simple (principio II).
- **Alternativas descartadas**: materializar los huecos de cada día (obliga a decidir hasta qué
  fecha generarlos y a regenerarlos en cada cambio de duración, sin resolver ningún requisito).

## D-C06 · La duración de una cita no se congela al reservar

- **Decisión**: la tabla `cita` guarda solo `fecha` y `hora_inicio`. La duración de una cita es
  siempre la `duracion_minutos` vigente de su especialista.
- **Justificación**: es lo que hace posible RN-C12 y CA-C12. Si cada cita guardara su duración,
  cambiar la del especialista no podría decidir qué citas «encajan» en la nueva rejilla, porque
  las citas conservarían la rejilla antigua.
- **Consecuencia documentada**: PD-C20 y el supuesto correspondiente de la especificación. Al
  alargarse las consultas, dos citas de un mismo paciente podrían pasar a solaparse; RN-C12 solo
  decide el encaje y no vuelve a comprobar RN-C07. No se amplía el alcance para resolverlo.
- **Alternativas descartadas**: `duracion_minutos` en cada cita (contradice RN-C12).

## D-C07 · Estado y motivo de cancelación como restricciones del esquema

- **Decisión**: `cita.estado` admite exactamente `RESERVADA`, `CANCELADA_PACIENTE` y
  `CANCELADA_CENTRO` mediante `CHECK ... IN (...)`, con el mismo estilo que el módulo de registro.
  Un segundo `CHECK` obliga a que `motivo_cancelacion` sea nulo si y solo si el estado es
  `RESERVADA`. El motivo toma uno de los tres valores predefinidos de PD-C09.
- **Justificación**: RN-C06 fija tres estados y RN-C13 exige que toda cancelación registre su
  motivo. Llevar ambas reglas al esquema las hace inviolables, incluso ante un error de
  programación, en lugar de depender de que el código las respete.
- **Verificado**: un `UPDATE` que pasa una cita a `CANCELADA_CENTRO` sin motivo es rechazado por
  el `CHECK`.
- **Alternativas descartadas**: validar solo en el servicio (una regla de negocio no verificada
  por el almacén); texto libre como motivo (PD-C09: el enunciado no lo pide).

## D-C08 · Unicidad del hueco: índice único parcial, que resuelve CL-C03

- **Decisión**: `CREATE UNIQUE INDEX ... ON cita (id_especialista, fecha, hora_inicio) WHERE
  estado = 'RESERVADA'`. La reserva y la reprogramación se ejecutan dentro de una transacción
  `BEGIN IMMEDIATE`, igual que la asignación de códigos del módulo de registro (D-06).
- **Justificación**: RN-C04 y CL-C03 exigen que dos personas no puedan ocupar el mismo hueco. Un
  índice parcial lo garantiza en la base de datos: la segunda reserva falla con `IntegrityError`,
  que el servicio traduce al mensaje «ese hueco ya no está disponible» (PD-C17). Es parcial
  porque las citas canceladas no ocupan hueco (RN-C06, PD-C04) y debe poder reservarse de nuevo
  el mismo hueco tras una cancelación.
- **Verificado en SQLite 3.50.4**: la primera reserva de las 9:00 entra, la segunda se rechaza y,
  tras cancelar la primera, el hueco vuelve a admitir una reserva.
- **Alternativas descartadas**: comprobar disponibilidad con un `SELECT` previo y luego insertar
  (deja una ventana de carrera, que es exactamente lo que CL-C03 describe); bloquear toda la base
  de datos por operación (innecesario, el índice basta).

## D-C09 · Fechas y horas como texto ISO comparable

- **Decisión**: `fecha` como `YYYY-MM-DD`, `hora_inicio`/`hora_fin` como `HH:MM` y
  `momento_reserva` como `YYYY-MM-DD HH:MM:SS`, todos en TEXT, igual que `fecha_nacimiento` y
  `fecha_registro` del módulo de registro. La aritmética temporal se hace convirtiendo la hora a
  minutos desde medianoche.
- **Justificación**: en ese formato el orden lexicográfico coincide con el cronológico, de modo
  que las comparaciones de RN-C08 (hueco pasado), RN-C09 (24 horas) y PD-C12 (rango de fechas) se
  pueden hacer en SQL y en Python sin conversiones. Mantiene la coherencia con el módulo ya
  escrito.
- **Alternativas descartadas**: enteros epoch (ilegibles al inspeccionar la base de datos y
  dependientes de zona horaria); tipos de fecha nativos (SQLite no los tiene).

## D-C10 · Reloj del sistema como única fuente de «ahora»

- **Decisión**: una sola función devuelve el momento actual y todas las reglas temporales
  (RN-C08, RN-C09, PD-C05, PD-C11) la usan. En las pruebas se sustituye por un momento fijo.
- **Justificación**: RN-C08, RN-C09 y PD-C11 dependen del instante actual; CA-C07, CA-C08 y los
  escenarios de citas pasadas solo son verificables de forma determinista si «ahora» se puede
  fijar. Concentrarlo en un punto evita llamadas dispersas a `datetime.now()` imposibles de probar.
- **Alcance**: se usa la hora local del sistema, sin husos horarios (supuesto de la
  especificación: el enunciado no menciona centros en husos distintos).

## D-C11 · Días de la semana del horario como texto de números ISO

- **Decisión**: `especialista.dias_semana` es un texto con los números de día separados por
  comas, en convenio ISO (1 = lunes … 7 = domingo); por ejemplo `1,2,3,4,5`.
- **Justificación**: RN-C02 define el horario con días de la semana, y RN-C01 los hace datos
  precargados e inmutables. Al no existir ninguna operación de alta o edición de horarios
  (PD-C19), una tabla adicional de días solo añadiría un `JOIN` sin habilitar ningún requisito.
  Es la opción más simple (principio II) y CL-C06 se resuelve comprobando la pertenencia del día
  de la fecha consultada.
- **Alternativas descartadas**: tabla `dia_horario` (normalización sin caso de uso que la pida);
  siete columnas booleanas (más rígido y verboso).

## D-C12 · Datos precargados en el arranque, sin ninguna vía de alta o edición

- **Decisión**: `datos_iniciales.py` contiene centros, especialidades y especialistas ficticios
  como literales de Python y los inserta al arrancar **solo si las tablas están vacías**. La
  aplicación no expone ninguna ruta de creación, edición ni borrado de esas tres entidades.
- **Justificación**: RN-C01 y PD-C19 los declaran precargados y CA-C13 exige comprobar que no
  existe ninguna pantalla para gestionarlos. Insertar solo con las tablas vacías hace el arranque
  idempotente, lo que el principio V necesita: `docker compose up` repetido no duplica datos ni
  pisa lo que haya.
- **Nota del principio IV**: todos los nombres de centros, especialidades y especialistas son
  inventados.
- **Alternativas descartadas**: un archivo JSON o CSV externo (un archivo más que cargar y
  validar, sin requisito que lo pida); insertar en cada arranque (duplicaría filas).

## D-C13 · Un solo servidor y un solo puerto: el manejador de citas extiende el de registro

- **Decisión**: `programacion_citas.web` define un manejador HTTP que **hereda** del manejador del
  módulo de registro y atiende primero las rutas de citas; cualquier otra ruta se delega a la
  clase base. `app.py` crea el servidor con ese manejador combinado. El módulo de registro no se
  modifica.
- **Justificación**: el principio V exige que todo arranque con un único `docker compose up`, lo
  que descarta un segundo proceso o un segundo puerto. La herencia consigue un único servidor en
  `PUERTO` sirviendo los dos módulos sin tocar una línea del módulo de registro, que es lo que
  pide el principio III.
- **Alternativas descartadas**: modificar el manejador del módulo de registro para que delegue
  (cambia código que ninguna parte de esta especificación pide); un segundo servidor en otro
  puerto (dos puertos a publicar y a documentar, contra el principio V); un despachador nuevo que
  reimplemente el enrutado de los dos módulos (duplica lógica ya escrita).

## D-C14 · Dos flujos separados, cada uno con su página de entrada

- **Decisión**: el flujo del paciente empieza en `GET /citas` y el del personal administrativo en
  `GET /agenda`. Son páginas de entrada independientes, sin inicio de sesión (PD-C02).
- **Justificación**: la sección 2 de la especificación pide «dos flujos separados, uno para cada
  perfil» y descarta expresamente el control de acceso. Separarlos por prefijo de ruta hace la
  frontera evidente y encaja con D-C13.
- **Punto abierto que se señala en vez de resolver** (principio III): la página de inicio del
  módulo de registro (`GET /`) no enlaza con `/citas` ni con `/agenda`, porque añadir esos enlaces
  significaría modificar el módulo de registro y ninguna parte de esta especificación lo pide.
  Mientras no se decida, los dos flujos se alcanzan escribiendo su dirección, que es lo que
  documenta [quickstart.md](quickstart.md). Es una decisión de usabilidad para la persona
  responsable del proyecto, no una ambigüedad de requisitos.

## D-C15 · Pruebas: una por criterio de aceptación y caso límite, más la aritmética aislada

- **Decisión**: `unittest` (`python -m unittest`), con archivos nuevos en `tests/` y un módulo
  propio de utilidades (`utilidades_citas.py`) que crea una base de datos temporal con datos
  ficticios y permite fijar el momento actual (D-C10). No se modifica ninguna prueba existente.
- **Justificación**: CE-C08 exige superar los 13 CA-C y los 13 CL-C (eran 9 hasta el 2026-10-06:
  la sesión de aclaraciones añadió CL-C10 a CL-C12 y la decisión sobre el hallazgo A1 de
  `/speckit-analyze` añadió CL-C13), y el módulo de registro ya
  fijó esta forma de trazar pruebas a requisitos (D-02). La aritmética de `agenda.py` se prueba
  además de forma unitaria, porque CA-C01, CA-C12 y CL-C05 son afirmaciones numéricas exactas.
- **Comprobación previa ya realizada**: los tres predicados temporales reproducen los criterios
  del enunciado — rejilla de 20 minutos entre 9:00 y 13:00 → 12 huecos de 9:00 a 12:40 (CA-C01);
  de 50 minutos → 4 huecos sin tramo parcial (CL-C05); franja 9:00–11:00 → se cancelan las citas
  de 9:00, 10:00 y 10:40 y sobreviven las de 11:00 en adelante (CA-C10); rejilla nueva de 30
  minutos → encaja la cita de 9:00 y no la de 9:20 (CA-C12).
- **Alternativas descartadas**: `pytest` (dependencia externa, principio V); probar solo por la
  interfaz web (haría ilegibles los fallos de aritmética).

## D-C16 · Seguridad y normativa aplicable (vinculación con CESI2)

- **Decisión**: dentro del alcance fijado se aplican solo las medidas que no añaden
  funcionalidad: todo dato mostrado se escapa antes de insertarlo en el HTML, todas las consultas
  van parametrizadas, no se registran datos reales de personas (principio IV) y el módulo no
  expone ningún dato clínico —solo quién tiene cita con qué especialista y cuándo—.
- **Limitación declarada, no un descuido**: al no haber inicio de sesión ni control de acceso
  (PD-C02), el código de historia clínica funciona de hecho como única credencial: quien lo
  conozca puede ver, cancelar y reprogramar las citas de ese paciente, y el flujo administrativo
  está abierto a cualquiera que alcance `/agenda`.
- **Lectura normativa**: una cita con un especialista revela una sospecha diagnóstica, de modo
  que estos datos son datos relativos a la salud, categoría especial del artículo 9 del RGPD. Un
  despliegue real exigiría, como mínimo, autenticación de paciente y de personal, control de
  acceso por rol, registro de accesos y minimización de los datos mostrados; el ENS lo situaría
  en categoría media o alta. Nada de eso se implementa porque está fuera de alcance, y por eso la
  aplicación **no es apta para datos reales de pacientes**: se deja constancia explícita en lugar
  de dar por hecha una seguridad que no existe.
- **Alternativas descartadas**: implementar autenticación (fuera de alcance, contra el principio
  II); no documentar la limitación (dejaría el riesgo invisible, que es lo contrario de CESI2).
- **Medida añadida el 2026-10-06**: las confirmaciones del flujo administrativo dejan de mostrar
  el código de historia clínica de los pacientes afectados (PD-C22, D-C19). Es la única
  minimización de datos que cabe dentro del alcance y cierra la vía por la que `/agenda`
  entregaba la credencial de hecho de un paciente a quien no la tenía.

## D-C17 · Cita pasada: comprobación previa al plazo y error propio

- **Decisión**: la comprobación de plazo de cancelar y reprogramar evalúa primero si la cita ya
  ha pasado y, en ese caso, lanza un error nuevo, `CitaPasada`, con el mensaje «No se puede
  cancelar ni reprogramar una cita cuya hora ya ha pasado.». El orden de comprobaciones queda:
  cita del paciente → estado reservada → **no pasada** → plazo de 24 horas. Una cita está pasada
  cuando su inicio no es posterior a `ahora`, el mismo criterio con el que PD-C11 separa las
  citas futuras.
- **Justificación**: PD-C07 (aclaración Q1 del 2026-10-06) prohíbe cancelar o reprogramar una
  cita pasada «en ningún caso» y exige que el rechazo diga que la cita ya ha pasado, no que está
  fuera de plazo (PD-C18, CL-C10). Hasta ahora la excepción de las reservas con menos de 24 horas
  dejaba pasar justo ese caso, porque a una cita pasada también le «falta menos de 24 horas».
  Comprobarlo antes del plazo corrige el defecto sin tocar la regla de RN-C09 para las citas
  futuras.
- **Alternativas descartadas**: reutilizar `FueraDePlazo` (contradice PD-C18: el mensaje de las
  24 horas es falso para una cita ya celebrada); impedirlo solo en la interfaz ocultando los
  botones (la regla quedaría sin proteger en el servicio y sin prueba posible de CL-C10);
  añadir un estado «atendida» (fuera de alcance, PD-C14).

## D-C18 · Duración válida: comparación con la amplitud del horario, en el servicio

- **Decisión**: `ajustar_duracion` rechaza con `ErrorValidacion` y el mensaje «Con esa duración
  no cabe ningún hueco en el horario del especialista.» cuando la duración supera los minutos
  entre la hora de inicio y la hora de fin del horario. La comprobación se hace dentro de la
  transacción, después de leer el especialista y **antes** de actualizar la duración, de modo que
  el rechazo no cambia nada. Las dos validaciones existentes (entero, mayor que cero) se
  conservan.
- **Justificación**: PD-C21 y CL-C11 exigen que un valor sin hueco posible se rechace sin
  cambiar la duración, sin recalcular la rejilla y sin cancelar citas. Comparar con la amplitud
  del horario es la traducción directa de «cabe al menos un hueco» (PD-C03) y no depende de
  ninguna fecha.
- **Alternativas descartadas**: generar la rejilla de una fecha y comprobar si sale vacía
  (depende de elegir un día de consulta, cuando el resultado no depende del día); un `CHECK` en
  la tabla `especialista` (compararía un entero con horas guardadas como texto y obligaría a
  recrear una tabla ya desplegada, sin requisito que lo pida); pedir confirmación al
  administrativo antes de aplicar (un paso nuevo de interfaz que la especificación no recoge).

## D-C19 · Confirmación al administrativo: número, fecha, hora y motivo, sin datos del paciente

- **Decisión**: la página de confirmación de bloquear franja y de ajustar duración muestra el
  número de citas canceladas y, de cada una, la fecha, la hora y el motivo de cancelación. Se
  retira únicamente el código de historia clínica, y no se muestra ningún otro dato que
  identifique al paciente. El servicio sigue devolviendo la lista de citas canceladas; es la
  interfaz la que no muestra la identidad.
- **Justificación**: PD-C22 y CE-C10 fijan qué ve el administrativo y prohíben cualquier dato que
  identifique al paciente. Sin control de acceso (PD-C02), el código de historia clínica es la
  credencial de hecho, y `/agenda` está abierta a cualquiera: es el punto de D-C16 donde la
  minimización de datos (RGPD, art. 5.1.c; competencia CESI2) sí es aplicable sin ampliar el
  alcance. El motivo se conserva porque no identifica al paciente y confirma al administrativo
  por qué se canceló cada cita.
- **Revisión del 2026-10-06**: la primera redacción de esta decisión retiraba también el motivo
  por línea. La persona responsable decidió conservarlo, y PD-C22 y CE-C10 lo recogen así.
- **Alternativas descartadas**: retirar también el motivo por línea (descartada por la persona
  responsable: es información útil para el administrativo y no es un dato del paciente); que el
  servicio deje de devolver las citas y devuelva solo pares de fecha y hora (obliga a reescribir
  las pruebas que comprueban el estado de las citas canceladas, sin que la especificación lo
  exija: lo que PD-C22 regula es lo que se muestra); enmascarar el código (sigue siendo un dato
  del paciente que el administrativo no necesita).

## D-C20 · Franja pasada: comparación de la fecha y hora de fin con `ahora`, en el servicio

- **Decisión**: `bloquear_franja` rechaza con `ErrorValidacion` y el mensaje «No se puede
  bloquear una franja cuya fecha y hora de fin ya han pasado.» cuando el momento formado por
  `fecha_fin` y `hora_fin` no es posterior a `ahora`. Se evalúa después de las dos validaciones
  de forma ya existentes y antes de abrir la transacción: no se registra la franja ni se cancela
  ninguna cita. Un bloqueo de hoy de 9:00 a 14:00 solicitado a las 11:00 se acepta; uno de hoy
  de 9:00 a 11:00 solicitado a las 15:00 se rechaza.
- **Justificación**: PD-C23 y CL-C12, en la redacción que la persona responsable fijó el
  2026-10-06: «fecha y hora de fin ya pasadas», no solo la fecha. `ahora` ya llega como
  parámetro (D-C10), así que la regla es determinista en las pruebas.
- **Por qué no es una restricción del esquema**: una condición que depende del momento actual no
  se puede expresar como `CHECK`, y además una franja válida al crearse pasa a estar en el pasado
  con el tiempo sin dejar de ser correcta.
- **Consecuencia sobre lo ya construido**: PD-C11 (un bloqueo no altera una cita pasada) deja de
  poder probarse con una franja entera en el pasado, que ahora se rechaza. Se prueba con una
  franja que empieza en el pasado y cuyo fin aún no ha llegado.
- **Discrepancia ya resuelta** (principio III): varios puntos de la especificación conservaban la
  redacción anterior, solo por fecha (el supuesto «Bloqueos sobre fechas pasadas», la entidad
  «Franja bloqueada», PD-C18 y la entrada de la pregunta 4 en «Aclaraciones»). Se alinearon con
  PD-C23 el 2026-10-06, tras `/speckit-analyze`, y la historia 5 ganó los escenarios 10 y 11.
- **Alternativas descartadas**: comparar solo la fecha de fin (era la lectura inicial y fue
  corregida); rechazar también las franjas sin efecto, como un tramo fuera del horario (PD-C23
  las acepta expresamente).

## D-C21 · Hueco reservable solo si su inicio es estrictamente posterior a `ahora`

- **Decisión**: un hueco se trata como pasado cuando su inicio **no es estrictamente posterior**
  a `ahora`, es decir, también cuando coincide con él. Cambia la comparación en los dos puntos
  del servicio que deciden si un hueco ha pasado: la consulta de huecos libres y la comprobación
  del hueco al reservar y al reprogramar, que comparten criterio. Se reutiliza el error
  `HuecoPasado` con su mensaje actual, «No se puede reservar un hueco cuya hora ya ha pasado.»;
  no hay error ni mensaje nuevos.
- **Justificación**: PD-C05 y CL-C13, por decisión de la persona responsable del 2026-10-06
  sobre el hallazgo A1 de `/speckit-analyze`. Hasta ahora un hueco cuyo inicio coincidía con el
  momento actual se podía reservar, y la cita resultante nacía ya pasada: no era futura para
  PD-C11 ni se podía cancelar según PD-C07. Con la comparación estricta, PD-C05 (hueco
  reservable), PD-C07 (cita pasada) y PD-C11 (cita futura) usan un único criterio, y toda cita
  recién reservada o reprogramada es futura.
- **Comprobado el 2026-10-06**: simulando la comparación estricta en esos dos puntos, las 167
  pruebas existentes siguen pasando; ninguna reserva un hueco en el instante exacto de su inicio.
- **Sin cambios en el esquema ni en la interfaz**: la regla depende del momento actual, así que
  no puede ser una restricción de la base de datos, y la interfaz ya responde `409` con el
  mensaje de `HuecoPasado`.
- **Alternativas descartadas**: mantener reservable el hueco que empieza justo ahora y permitir
  cancelar la cita en su instante inicial (contradice PD-C07, que da por pasada la cita cuyo
  inicio coincide con el momento actual); exigir una antelación mínima para reservar (RN-C08
  dice expresamente que no la hay).
