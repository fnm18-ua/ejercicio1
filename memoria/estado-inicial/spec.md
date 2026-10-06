# Especificación de la funcionalidad: Módulo de Programación de Citas

**Rama de la funcionalidad**: no se ha creado rama específica (no hay hook de ramas configurado;
se trabaja sobre `master`)

**Creada**: 2026-09-28

**Estado**: Borrador — sin ambigüedades pendientes (ver «Aclaraciones»)

**Entrada**: Descripción del usuario: «MÓDULO DE PROGRAMACIÓN DE CITAS» (enunciado completo con
objetivo y contexto de negocio, usuarios, escenarios E-C01 a E-C06, requisitos RF-C01 a RF-C09,
reglas RN-C01 a RN-C13, criterios de aceptación CA-C01 a CA-C13, casos límite CL-C01 a CL-C07 y
fuera de alcance).

> **Nota de trazabilidad**: se conservan los identificadores del enunciado (E-C, RF-C, RN-C,
> CA-C, CL-C) para que todo elemento del plan, de las tareas y del código pueda rastrearse hasta
> ellos (Constitución, principio III). Los elementos añadidos en esta especificación llevan
> identificadores propios (PD-C, CE-C) e indican siempre de qué elemento del enunciado derivan.
> El sufijo `-C` distingue los identificadores de este módulo de los del módulo de registro
> (`specs/001-registro-identificacion-pacientes/`), cuyos `RF-01`, `RN-01`… son distintos.

> **Encaje en la constitución**: este módulo es el segundo de los dos que cubre el proyecto y
> aporta las capacidades 4, 5 y 6 del principio II (reservar una cita; cancelar o reprogramar;
> gestionar la agenda de un especialista), en su versión 3.1.0.

## Objetivo y contexto de negocio

Un centro médico de tamaño medio necesita que sus pacientes puedan reservar cita con un
especialista sin llamar por teléfono, y que la disponibilidad que ven sea siempre real. Para el
centro el riesgo es el simétrico: que la agenda publicada no refleje la situación del
especialista —vacaciones, baja, formación— y se acumulen citas imposibles de atender.

Este módulo resuelve esa pieza: permite a un paciente ya registrado buscar especialista por
especialidad y centro, reservar un hueco libre, y cancelar o reprogramar su cita; y permite al
personal administrativo mantener la agenda de cada especialista bloqueando franjas y ajustando
la duración de sus consultas.

El módulo se apoya en la identidad que produce el módulo de registro: cada cita referencia al
paciente por su código de historia clínica, que es único e inmutable (RN-C05). Este módulo no
crea, modifica ni borra pacientes.

**Usuarios**:

- **Paciente**: ya registrado en el centro. Se identifica introduciendo su código de historia
  clínica o su documento de identidad. Reserva, consulta, cancela y reprograma sus propias
  citas.
- **Personal administrativo**: mantiene la agenda de los especialistas, bloqueando franjas y
  ajustando la duración de las consultas.

No hay inicio de sesión ni control de acceso: la aplicación ofrece dos flujos separados, uno
para cada perfil (PD-C02).

## Aclaraciones

### Sesión 2026-09-28

- Q: El escenario E-C04 habla de vacaciones, que duran varios días, pero CA-C10 bloquea «de 9:00
  a 11:00», que es un tramo de un solo día. ¿Qué alcance temporal tiene una franja bloqueada? →
  A: Rango de fechas más un tramo horario que se aplica a cada día del rango; CA-C10 es el caso
  de un solo día (PD-C12).
- Q: RN-C09 usa el momento en que la cita «se reservó». ¿Reprogramar actualiza ese momento? →
  A: Sí; tras reprogramar, la referencia de las 24 horas es el momento de la reprogramación
  (PD-C07, PD-C08).
- Q: ¿El bloqueo de una franja (RN-C11) y el cambio de duración (RN-C12) cancelan también las
  citas cuya hora ya ha pasado? → A: No; solo alcanzan a las citas futuras, para no reescribir
  el historial del paciente (PD-C11).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 - Reservar una cita (Prioridad: P1) · E-C01

Un paciente necesita ir al dermatólogo. Se identifica con su código de historia clínica o su
documento de identidad, elige la especialidad y el centro, ve los especialistas que encajan y
los huecos libres de una fecha, y reserva uno.

**Por qué esta prioridad**: es el objetivo de negocio del módulo —reservar sin llamar por
teléfono— y la única historia que crea citas. Sin ella las demás no tienen sobre qué operar.

**Prueba independiente**: se valida identificando a un paciente precargado, buscando
especialistas por especialidad y centro, comprobando la rejilla de huecos de una fecha,
reservando uno y verificando que desaparece de los libres.

**Escenarios de aceptación**:

1. **Given** un especialista con horario de 9:00 a 13:00 y consultas de 20 minutos, **When** el
   paciente consulta sus huecos de una fecha en la que pasa consulta, **Then** se ofrecen 12
   huecos, el primero a las 9:00 y el último a las 12:40 (CA-C01).
2. **Given** la rejilla anterior, **When** el paciente reserva el hueco de las 9:00, **Then** ese
   hueco deja de aparecer entre los libres y los demás siguen disponibles (CA-C02).
3. **Given** varios especialistas en varios centros, **When** el paciente busca una especialidad
   en un centro, **Then** se listan solo los especialistas que cumplen ambos filtros (CA-C03).
4. **Given** un paciente con una cita reservada a las 10:00, **When** intenta reservar otra cita
   que se solapa con esa hora, aunque sea de otro especialista, **Then** la reserva se rechaza e
   informa del motivo (CA-C05, RN-C07).
5. **Given** un paciente registrado, **When** se identifica por su documento de identidad,
   **Then** accede a las mismas citas que identificándose por su código de historia clínica
   (CA-C04).
6. **Given** un hueco cuya hora de inicio ya ha pasado, **When** el paciente consulta los huecos
   de hoy, **Then** ese hueco no se ofrece y no puede reservarse (RN-C08).

---

### Historia de usuario 2 - Consultar mis citas y el motivo de una cancelación (Prioridad: P2) · E-C06

El paciente se identifica y consulta su listado de citas con el estado de cada una. Si el centro
ha cancelado alguna, la ve como cancelada por el centro, con el motivo.

**Por qué esta prioridad**: es la vía por la que el paciente localiza una cita para cancelarla o
reprogramarla (P3 y P4 dependen de ella) y, al no haber notificaciones de ningún tipo, es el
único canal por el que se entera de una cancelación del centro.

**Prueba independiente**: se valida creando citas en los tres estados para un paciente y
comprobando que el listado las muestra con su estado y, en las canceladas, con su motivo.

**Escenarios de aceptación**:

1. **Given** un paciente con citas en varios estados, **When** consulta su listado, **Then** ve
   cada cita con su especialista, fecha, hora y estado (RF-C05).
2. **Given** una cita cancelada por el centro tras un bloqueo, **When** el paciente consulta su
   listado, **Then** la ve como cancelada por el centro con el motivo indicado (CA-C11, RN-C13).
3. **Given** un paciente sin ninguna cita, **When** consulta su listado, **Then** se informa de
   que no tiene citas, sin error (PD-C14).

---

### Historia de usuario 3 - Cancelar una cita (Prioridad: P3) · E-C03

El paciente ya no necesita la consulta y cancela la cita, que queda registrada como cancelada
por él y libera su hueco.

**Por qué esta prioridad**: es la operación de mantenimiento más simple sobre una cita existente
y la que devuelve disponibilidad real al resto de pacientes, que es el objetivo del módulo.

**Prueba independiente**: se valida cancelando citas con distintas antelaciones y comprobando el
estado resultante, la liberación del hueco y el rechazo de los casos no permitidos.

**Escenarios de aceptación**:

1. **Given** una cita reservada que empieza dentro de más de 24 horas, **When** el paciente la
   cancela, **Then** queda en estado «cancelada por el paciente» y su hueco vuelve a estar libre
   (CA-C06).
2. **Given** una cita que empieza dentro de menos de 24 horas y que se reservó hace más de 24
   horas, **When** el paciente intenta cancelarla, **Then** se rechaza e informa del motivo
   (CA-C07, RN-C09).
3. **Given** una cita reservada hoy para dentro de 3 horas, **When** el paciente la cancela,
   **Then** la cancelación se acepta (CA-C08, RN-C09).
4. **Given** una cita ya cancelada, **When** el paciente intenta cancelarla otra vez, **Then** se
   rechaza e informa (CL-C07).

---

### Historia de usuario 4 - Reprogramar una cita (Prioridad: P4) · E-C02

Al paciente le ha surgido un imprevisto. Localiza su cita, elige otro hueco libre del mismo
especialista y la cita se traslada, sin repetir la búsqueda y sin perder la reserva.

**Por qué esta prioridad**: aporta valor sobre P3 —evita perder la plaza con el especialista—
pero requiere la identificación, el listado y la rejilla de huecos de las historias anteriores.

**Prueba independiente**: se valida trasladando una cita a otro hueco del mismo especialista y
comprobando que conserva su identificador, que el hueco anterior queda libre y que el nuevo
queda ocupado.

**Escenarios de aceptación**:

1. **Given** una cita reservada a las 9:00 y el hueco de las 11:00 libre del mismo especialista,
   **When** el paciente la reprograma a las 11:00, **Then** la cita mantiene su identificador y
   su especialista, el hueco de las 9:00 queda libre y el de las 11:00 ocupado (CA-C09, RN-C10).
2. **Given** una cita reservada, **When** el paciente intenta reprogramarla a un hueco que ya
   está ocupado, **Then** se rechaza e informa de que no está disponible (RN-C04, CL-C03).
3. **Given** una cita que empieza dentro de menos de 24 horas y que se reservó hace más de 24
   horas, **When** el paciente intenta reprogramarla, **Then** se rechaza e informa del motivo
   (RN-C09).
4. **Given** una cita reservada, **When** el paciente intenta reprogramarla a un hueco que se
   solapa con otra cita reservada suya, **Then** se rechaza e informa del motivo (RN-C07,
   PD-C08).

---

### Historia de usuario 5 - Bloquear una franja de un especialista (Prioridad: P5) · E-C04

El especialista se va de vacaciones. El administrativo bloquea la franja correspondiente, que
puede abarcar varios días seguidos (PD-C12). Las citas futuras reservadas que había dentro
quedan canceladas por el centro, y esos huecos dejan de ofrecerse.

**Por qué esta prioridad**: cubre el riesgo que el enunciado atribuye al centro —una agenda que
no refleja la situación del especialista— pero solo es observable cuando ya existen citas y una
rejilla de huecos (P1).

**Prueba independiente**: se valida bloqueando una franja con y sin citas dentro y comprobando
qué citas cambian de estado y qué huecos dejan de ofrecerse.

**Escenarios de aceptación**:

1. **Given** un especialista con citas futuras reservadas a las 9:00, a las 10:00 y a las 11:00
   de una fecha, **When** el administrativo bloquea la franja de 9:00 a 11:00 de esa fecha,
   **Then** las de las 9:00 y las 10:00 pasan a «cancelada por el centro» y la de las 11:00 sigue
   reservada (CA-C10, PD-C12).
2. **Given** un especialista con citas futuras en varios días seguidos, **When** el administrativo
   bloquea una franja cuyo rango abarca esos días, **Then** se cancelan por el centro las citas
   de todos los días del rango que caen en el tramo horario, con un solo bloqueo (E-C04, PD-C12).
3. **Given** una cita futura que empieza dentro de menos de 24 horas, **When** el bloqueo la
   alcanza, **Then** se cancela igualmente: la regla de las 24 horas no limita al centro
   (RN-C11).
4. **Given** una cita del mismo especialista cuya hora ya ha pasado, **When** el administrativo
   bloquea una franja que la cubre, **Then** esa cita NO cambia de estado y sigue reservada
   (PD-C11).
5. **Given** una franja sin ninguna cita futura dentro, **When** el administrativo la bloquea,
   **Then** el bloqueo se aplica sin cancelar ninguna cita (CL-C04).
6. **Given** una franja bloqueada, **When** un paciente consulta los huecos de una fecha del
   rango, **Then** los huecos que cubre el tramo horario no se ofrecen como libres (RN-C04).

---

### Historia de usuario 6 - Ajustar la duración de las consultas (Prioridad: P6) · E-C05

El administrativo cambia las consultas de un especialista de 20 a 30 minutos. Los huecos se
recalculan sobre la nueva duración y las citas que ya no encajan quedan canceladas por el
centro.

**Por qué esta prioridad**: es la operación de agenda de efecto más amplio y la que más depende
de las demás (rejilla de huecos y citas existentes), por lo que se aborda al final.

**Prueba independiente**: se valida cambiando la duración de un especialista con citas en horas
que encajan y en horas que no, y comprobando la nueva rejilla y el estado de cada cita.

**Escenarios de aceptación**:

1. **Given** un especialista con consultas de 20 minutos y citas futuras a las 9:00 y a las 9:20,
   **When** el administrativo pasa la duración a 30 minutos, **Then** la cita de las 9:00 sigue
   reservada y la de las 9:20 queda cancelada por el centro (CA-C12, RN-C12).
2. **Given** un especialista con horario de 9:00 a 13:00, **When** su duración de consulta pasa
   a 50 minutos, **Then** se ofrecen 4 huecos y el tiempo sobrante no forma un hueco parcial
   (CL-C05, RN-C03).
3. **Given** una cita cancelada por un cambio de duración, **When** el paciente consulta su
   listado, **Then** la ve como cancelada por el centro con el motivo indicado (RN-C13).
4. **Given** una cita pasada a las 9:20 que no encaja en la nueva rejilla, **When** el
   administrativo cambia la duración, **Then** esa cita NO cambia de estado: el recálculo solo
   alcanza a las citas futuras (PD-C11).

---

### Casos límite

- **CL-C01**: un especialista sin huecos libres en una fecha (todos ocupados o bloqueados): se
  informa de que no hay disponibilidad, sin error.
- **CL-C02**: una búsqueda de especialidad y centro sin resultados: se informa, sin error.
- **CL-C03**: intentar reservar un hueco que otra persona acaba de ocupar: se rechaza e informa
  de que ya no está disponible (PD-C17).
- **CL-C04**: bloquear una franja que no contiene ninguna cita: se aplica sin cancelar nada.
- **CL-C05**: un horario de 9:00 a 13:00 con consultas de 50 minutos genera 4 huecos; el tiempo
  sobrante no forma un hueco parcial.
- **CL-C06**: reservar en una fecha en la que el especialista no pasa consulta: no se ofrece
  ningún hueco.
- **CL-C07**: intentar cancelar una cita ya cancelada: se rechaza e informa.
- **CL-C08** *(deriva de CL-C07 y RN-C10)*: intentar reprogramar una cita ya cancelada: se
  rechaza e informa. Una cita cancelada no vuelve al estado reservada.
- **CL-C09** *(deriva de RF-C01)*: identificarse con un código o un documento que no corresponde
  a ningún paciente: se informa de que no existe el paciente, sin crear ninguno y sin error.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-C01**: El sistema DEBE identificar al paciente por su código de historia clínica o por su
  documento de identidad antes de operar con sus citas.
- **RF-C02**: El sistema DEBE permitir buscar especialistas filtrando por especialidad y por
  centro.
- **RF-C03**: El sistema DEBE mostrar los huecos libres de un especialista en una fecha concreta.
- **RF-C04**: El sistema DEBE permitir reservar un hueco libre para el paciente identificado.
- **RF-C05**: El sistema DEBE permitir consultar las citas del paciente identificado, con su
  estado.
- **RF-C06**: El sistema DEBE permitir cancelar una cita reservada.
- **RF-C07**: El sistema DEBE permitir reprogramar una cita a otro hueco libre del mismo
  especialista, conservando la misma cita.
- **RF-C08**: El sistema DEBE permitir bloquear una franja horaria de un especialista.
- **RF-C09**: El sistema DEBE permitir ajustar la duración de las consultas de un especialista.

### Reglas de negocio

- **RN-C01**: Los centros, las especialidades y los especialistas son datos precargados. La
  aplicación NO permite crearlos, editarlos ni eliminarlos.
- **RN-C02**: Cada especialista pertenece a un centro, tiene una especialidad, un horario de
  consulta (días de la semana y hora de inicio y fin) y una duración de consulta en minutos.
- **RN-C03**: Los huecos de un especialista se generan a partir de su horario y su duración de
  consulta: consecutivos, sin solaparse, desde la hora de inicio y hasta donde quepa un hueco
  entero.
- **RN-C04**: Un hueco está libre si no lo ocupa ninguna cita reservada y no cae dentro de una
  franja bloqueada.
- **RN-C05**: Cada cita referencia al paciente por su código de historia clínica.
- **RN-C06**: Una cita tiene uno de estos estados: reservada, cancelada por el paciente o
  cancelada por el centro. Las canceladas no ocupan hueco.
- **RN-C07**: Un paciente NO puede tener dos citas reservadas que se solapen en el tiempo,
  aunque sean de especialistas distintos.
- **RN-C08**: No hay antelación mínima para reservar: se puede reservar para el mismo día. NO se
  puede reservar un hueco cuya hora ya ha pasado.
- **RN-C09**: Un paciente puede cancelar o reprogramar hasta 24 horas antes del inicio de la
  cita. Si la cita se reservó con menos de 24 horas de antelación, puede cancelarla o
  reprogramarla hasta su inicio.
- **RN-C10**: Reprogramar conserva la misma cita y el mismo especialista: solo cambian la fecha
  y la hora. El hueco anterior queda libre.
- **RN-C11**: Al bloquear una franja, las citas reservadas que caen dentro quedan canceladas por
  el centro, sin límite de antelación. Esta cancelación NO está sujeta a la regla de las 24
  horas.
- **RN-C12**: Al cambiar la duración de las consultas, los huecos se recalculan. Una cita encaja
  si su hora de inicio coincide con el inicio de un hueco nuevo y cabe entera en el horario; las
  que no encajan quedan canceladas por el centro.
- **RN-C13**: Toda cancelación registra su motivo y queda visible para el paciente.

### Precisiones derivadas

- **PD-C01** *(deriva de RF-C01, RN-C05 y CA-C04)*: La identificación del paciente reutiliza la
  identidad del módulo de registro: se acepta el código de historia clínica con formato
  `HC-NNNNNN` o la combinación tipo + número de documento de identidad, comparada de forma
  normalizada igual que en ese módulo (sin distinguir mayúsculas, tildes ni espacios sobrantes).
  Ambas vías dan acceso exactamente al mismo paciente y a las mismas citas.
- **PD-C02** *(deriva de la sección 2 del enunciado)*: Al no haber inicio de sesión ni control de
  acceso, conocer el código de historia clínica o el documento de un paciente basta para ver y
  operar con sus citas, y el flujo administrativo está abierto a cualquiera que acceda a la
  aplicación. Es una limitación asumida y consciente del alcance académico, no un descuido: se
  documenta como riesgo en «Supuestos» y en ningún caso debe entenderse como apta para un
  entorno real con datos de pacientes.
- **PD-C03** *(deriva de RN-C03 y CL-C05)*: La rejilla de huecos de una fecha se genera así:
  si la fecha no está entre los días de la semana del horario del especialista, no hay ningún
  hueco (CL-C06); en caso contrario, el primer hueco empieza a la hora de inicio y cada hueco
  siguiente empieza donde acaba el anterior, mientras el fin del hueco (inicio + duración) no
  supere la hora de fin del horario. El tiempo sobrante no forma un hueco parcial.
- **PD-C04** *(deriva de RN-C04 y RN-C06)*: Un hueco solo lo ocupan las citas en estado
  reservada. Cancelar una cita —por el paciente o por el centro— libera su hueco de inmediato.
- **PD-C05** *(deriva de RN-C08)*: «Un hueco cuya hora ya ha pasado» se evalúa comparando la
  fecha y la hora de inicio del hueco con la fecha y la hora actuales del sistema. Los huecos ya
  pasados no se ofrecen entre los libres ni pueden reservarse.
- **PD-C06** *(deriva de RN-C07)*: Dos citas se solapan cuando sus intervalos
  [inicio, inicio + duración) se intersecan. Dos citas consecutivas que se tocan en el extremo
  (una acaba a las 9:20 y la otra empieza a las 9:20) NO se solapan. Solo se tienen en cuenta
  las citas en estado reservada del mismo paciente.
- **PD-C07** *(deriva de RN-C09; aclaración Q2 de la sesión 2026-09-28)*: El límite de RN-C09 se
  evalúa comparando el momento actual con el inicio de la cita: si faltan 24 horas o más, se
  permite cancelar y reprogramar; si falta menos, solo se permite cuando la cita se reservó a
  menos de 24 horas de su inicio. **Reprogramar actualiza ese momento de referencia**: tras un
  traslado, la antelación se mide desde el instante de la reprogramación, no desde la reserva
  original. Así, una cita reservada hace un mes y reprogramada hoy a un hueco de dentro de 3
  horas puede después cancelarse, porque su reserva efectiva es de hace minutos.
- **PD-C08** *(deriva de RF-C07, RN-C07 y RN-C10; aclaración Q2 de la sesión 2026-09-28)*:
  Reprogramar conserva el identificador de la cita, su paciente y su especialista; solo cambian
  la fecha, la hora y el momento de referencia de las 24 horas (PD-C07). El hueco destino DEBE
  estar libre (RN-C04) y no pasado (RN-C08), y al comprobar el solapamiento del paciente
  (RN-C07) la propia cita que se traslada NO se cuenta contra sí misma.
- **PD-C09** *(deriva de RN-C06, RN-C11, RN-C12 y RN-C13)*: El motivo de cancelación lo genera el
  sistema a partir de la causa, con tres valores posibles: cancelación a petición del paciente,
  cancelación por franja bloqueada del especialista y cancelación por cambio de la duración de
  las consultas. El administrativo no redacta texto libre, porque el enunciado no lo pide.
- **PD-C10** *(deriva de RN-C02, RN-C03 y RN-C12)*: La duración de una cita es la duración de
  consulta vigente de su especialista; no se congela al reservar. Es lo que hace que RN-C12
  pueda recalcular la rejilla y decidir qué citas encajan. «Cabe entera en el horario» significa
  que el inicio de la cita coincide con el inicio de un hueco nuevo y que inicio + nueva
  duración no supera la hora de fin del horario.
- **PD-C11** *(deriva de RN-C11 y RN-C12; aclaración Q3 de la sesión 2026-09-28)*: Las
  cancelaciones automáticas por bloqueo de franja y por cambio de duración recaen **solo sobre
  las citas futuras** en estado reservada del especialista afectado: aquellas cuya hora de inicio
  es posterior al momento actual, con el mismo criterio de PD-C05. Una cita cuya hora ya ha
  pasado NO cambia de estado, para no reescribir el historial del paciente con consultas
  «canceladas por el centro» a las que sí acudió. Que RN-C11 sea «sin límite de antelación»
  significa que la regla de las 24 horas no protege al paciente frente al centro, no que el
  bloqueo alcance al pasado.
- **PD-C12** *(deriva de RF-C08, RN-C04, E-C04 y CA-C10; aclaración Q1 de la sesión 2026-09-28)*:
  Una franja bloqueada se define sobre un especialista con una **fecha de inicio, una fecha de
  fin y un tramo horario (hora de inicio y hora de fin) que se aplica a cada día del rango**,
  ambas fechas incluidas. Unas vacaciones se bloquean de una vez (E-C04) y CA-C10 es el caso de
  un solo día, con la misma fecha de inicio y de fin. Un hueco no está libre cuando su fecha cae
  dentro del rango y su intervalo se solapa con el tramo horario, con el criterio de extremos de
  PD-C06: un hueco que acaba justo a la hora de fin de la franja sí queda bloqueado, y uno que
  empieza justo a esa hora no. La franja no distingue días de la semana: se aplica a todos los
  días del rango en que el especialista pasa consulta.
- **PD-C13** *(deriva de RF-C08)*: No existe la operación de desbloquear una franja: los
  requisitos funcionales solo recogen bloquear (RF-C08). Por el principio de alcance mínimo de
  la constitución no se añade.
- **PD-C14** *(deriva de RF-C05 y RN-C06)*: El listado del paciente muestra todas sus citas,
  pasadas y futuras, con su estado y, en las canceladas, su motivo. No existe un estado
  «atendida» —la asistencia está fuera de alcance—, por lo que una cita pasada permanece en
  estado reservada. Un paciente sin citas recibe un aviso, no un error.
- **PD-C15** *(deriva de RF-C02, CA-C03 y CL-C02)*: La búsqueda de especialistas exige los dos
  filtros, especialidad y centro, y devuelve solo los especialistas que cumplen ambos. Sin
  coincidencias se informa, sin error.
- **PD-C16** *(deriva de RF-C03)*: Los huecos se consultan para una fecha concreta, un único
  día; no se ofrece una vista de rango de fechas ni de semana.
- **PD-C17** *(deriva de CL-C03 y RN-C04)*: La comprobación de que el hueco sigue libre y la
  reserva se resuelven de forma que dos intentos simultáneos sobre el mismo hueco no puedan
  confirmarse los dos: el segundo se rechaza informando de que ya no está disponible. La misma
  garantía aplica al hueco destino de una reprogramación.
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04 y CL-C07)*: Toda operación rechazada
  indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento con otra cita del
  paciente, fuera del plazo de 24 horas, cita ya cancelada o paciente no encontrado. Ningún
  rechazo se presenta como error genérico.
- **PD-C19** *(deriva de RN-C01 y CA-C13)*: Los centros, las especialidades y los especialistas
  se cargan como datos iniciales de la aplicación. No existe ninguna pantalla ni operación de
  alta, edición o borrado de esas tres entidades, ni del horario de un especialista más allá de
  la duración de consulta que permite ajustar RF-C09.
- **PD-C20** *(deriva de RN-C12 y RN-C07)*: El recálculo por cambio de duración solo decide qué
  citas encajan en la nueva rejilla; no vuelve a comprobar RN-C07. Si al alargarse las consultas
  dos citas de un mismo paciente pasaran a solaparse, ambas se conservan. Se documenta como
  limitación conocida en «Supuestos» para no ampliar el alcance por iniciativa propia.

### Entidades clave

- **Centro**: sede del centro médico donde pasa consulta un especialista. Dato precargado.
  Atributos: nombre.
- **Especialidad**: disciplina médica por la que el paciente busca (p. ej. dermatología). Dato
  precargado. Atributos: nombre.
- **Especialista**: profesional que atiende las citas. Dato precargado. Atributos: nombre,
  centro al que pertenece, especialidad, horario de consulta y duración de consulta en minutos.
  La duración es el único atributo que la aplicación permite cambiar (RF-C09).
- **Horario de consulta**: días de la semana en que el especialista pasa consulta y hora de
  inicio y de fin dentro de esos días.
- **Hueco**: tramo de tiempo de un especialista en una fecha, calculado a partir de su horario y
  su duración de consulta (PD-C03). No es un dato que se guarde: se deriva en cada consulta, y
  su disponibilidad depende de las citas reservadas y de las franjas bloqueadas.
- **Cita**: reserva de un hueco por un paciente. Atributos: identificador propio, código de
  historia clínica del paciente, especialista, fecha, hora de inicio, estado, motivo de
  cancelación (solo si está cancelada) y momento de la última reserva o reprogramación, que es el
  que usa la regla de las 24 horas (RN-C09, PD-C07). El identificador no cambia al reprogramar
  (RN-C10).
- **Estado de la cita**: reservada, cancelada por el paciente o cancelada por el centro
  (RN-C06). Solo «reservada» ocupa hueco.
- **Motivo de cancelación**: causa registrada al cancelar, visible para el paciente (RN-C13),
  con los tres valores de PD-C09.
- **Franja bloqueada**: periodo en que un especialista no atiende (vacaciones, baja, formación).
  Atributos: especialista, fecha de inicio, fecha de fin, hora de inicio y hora de fin; el tramo
  horario se aplica a cada día del rango, ambas fechas incluidas (PD-C12). Mientras esté vigente,
  los huecos que cubre no están libres (RN-C04). No se puede desbloquear (PD-C13).
- **Paciente**: entidad del módulo de registro, referenciada aquí por su código de historia
  clínica (RN-C05). Este módulo no la crea, la modifica ni la borra.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **CE-C01** *(objetivo de negocio; RF-C03, RN-C04)*: El 100 % de los huecos que la aplicación
  ofrece como libres son reservables en ese momento: ninguno está ocupado por una cita
  reservada, dentro de una franja bloqueada o ya pasado. La disponibilidad que ve el paciente es
  siempre real.
- **CE-C02** *(objetivo de negocio; RN-C11, RN-C12, PD-C11)*: Tras bloquear una franja o cambiar
  la duración de las consultas, quedan 0 citas **futuras** reservadas que el especialista no
  pueda atender (ninguna dentro de una franja bloqueada, ninguna fuera de la rejilla vigente).
  Las citas ya pasadas se conservan tal como estaban: son historial, no agenda.
- **CE-C03** *(RN-C07)*: En ningún momento un paciente tiene dos citas reservadas que se solapen
  en el tiempo (0 solapamientos), con independencia del especialista.
- **CE-C04** *(RF-C01, CA-C04)*: El 100 % de los pacientes registrados accede a sus citas tanto
  por su código de historia clínica como por su documento de identidad, obteniendo el mismo
  listado por las dos vías.
- **CE-C05** *(RF-C07, RN-C10, CA-C09)*: El 100 % de las reprogramaciones aceptadas conserva el
  identificador de la cita y su especialista, libera el hueco anterior y ocupa el nuevo; 0
  reprogramaciones crean una cita distinta.
- **CE-C06** *(RN-C13, CA-C11)*: El 100 % de las citas canceladas muestra al paciente su estado
  y el motivo de la cancelación en su listado, sin depender de ninguna notificación externa.
- **CE-C07** *(PD-C18)*: El 100 % de las operaciones rechazadas indica el motivo concreto del
  rechazo.
- **CE-C08** *(sección 6 y 7 del enunciado)*: Se superan los 13 criterios de aceptación CA-C01 a
  CA-C13 y los 9 casos límite CL-C01 a CL-C09.
- **CE-C09** *(RN-C01, CA-C13)*: La aplicación no ofrece ninguna vía para crear, editar o borrar
  centros, especialidades ni especialistas (0 pantallas y 0 operaciones de ese tipo).

## Supuestos

- **Prioridades**: el enunciado no asigna prioridades a los escenarios; se han ordenado P1–P6
  según su contribución al objetivo de negocio y su dependencia funcional (reservar → consultar
  → cancelar → reprogramar → bloquear franja → ajustar duración).
- **Dependencia del módulo de registro**: este módulo presupone pacientes ya registrados y
  reutiliza su código de historia clínica como referencia (RN-C05). No crea ni modifica
  pacientes; si el paciente no existe, se informa y no se le da de alta (CL-C09).
- **Vocabulario pendiente en la constitución**: el principio I de la constitución (v3.1.0) fija
  un vocabulario cerrado de cuatro términos —paciente, historia clínica, mutua y documento de
  identidad— que no cubre el dominio de citas. Esta especificación usa de forma consistente
  *cita*, *especialista*, *agenda*, *hueco* y *franja bloqueada*, y queda pendiente la enmienda
  del principio I que los incorpore. Se señala en vez de darlo por hecho (principio III).
- **Sin objetivos de rendimiento**: el enunciado no fija tiempos de respuesta ni volúmenes; no
  se definen métricas de rendimiento para no inventar datos.
- **Reloj del sistema**: las reglas temporales (RN-C08, RN-C09) se evalúan con la fecha y hora
  locales del sistema. El enunciado no menciona zonas horarias ni centros en husos distintos, y
  no se introduce ese tratamiento.
- **Sin notificaciones**: al estar fuera de alcance, el listado de citas del paciente es el único
  canal por el que conoce una cancelación del centro (E-C06, CE-C06).
- **Motivo de cancelación predefinido**: el sistema genera el motivo a partir de la causa
  (PD-C09); el administrativo no escribe texto libre, porque el enunciado no lo pide.
- **Sin desbloqueo de franjas**: solo se bloquea (RF-C08, PD-C13).
- **Bloqueos sobre fechas pasadas**: no se prohíben, pero no tienen ningún efecto sobre las citas
  ya celebradas (PD-C11). El enunciado no pide validar que el rango sea futuro y no se añade esa
  restricción.
- **Limitación conocida del recálculo**: un cambio de duración puede dejar dos citas de un mismo
  paciente solapadas sin que el sistema lo impida (PD-C20). El enunciado no regula este caso y
  no se amplía el alcance para resolverlo.
- **Duración y horario**: la aplicación solo permite cambiar la duración de consulta (RF-C09); el
  horario del especialista (días y horas) es dato precargado e inmutable (RN-C01, PD-C19).
- **Datos de ejemplo ficticios**: todos los valores de ejemplo de esta especificación
  (horarios, horas de cita, especialidades) son inventados (Constitución, principio IV).

### Fuera de alcance

- El alta y la edición de centros, especialidades y especialistas.
- Las notificaciones de cualquier tipo: el paciente consulta el estado de sus citas en la
  aplicación.
- Los demás módulos del sistema hospitalario: historia clínica, prescripción y facturación.
- Inicio de sesión y control de acceso por rol.
- El registro de asistencia del paciente a la cita y el resultado de la consulta.
- Las listas de espera y las citas recurrentes.
- El cobro o la facturación de la cita.
- El desbloqueo de una franja previamente bloqueada (PD-C13).
- La fusión, el traslado de citas entre especialistas y la reasignación automática de las citas
  canceladas por el centro: el paciente reserva de nuevo por su cuenta.
