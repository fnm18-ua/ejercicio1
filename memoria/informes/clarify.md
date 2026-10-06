# Informe de la sesión de aclaraciones (`/speckit-clarify`)

**Fecha**: 2026-10-06

**Funcionalidad**: Módulo de Programación de Citas

**Especificación modificada**: `specs/002-programacion-citas/spec.md`

**Preguntas hechas y respondidas**: 4

> **Nota sobre el número de preguntas**: el flujo `/speckit-clarify` admite un máximo de cinco
> preguntas por sesión, pero en esta sesión solo se formularon **cuatro**. La quinta no llegó a
> hacerse porque las ambigüedades restantes eran de bajo impacto. Este informe recoge las cuatro
> que existieron; no se añade una quinta que no se preguntó.

Para cada pregunta se recoge, tal como se presentó: el texto de la pregunta, por qué importaba,
el contexto que la motivó, la recomendación, las opciones, la respuesta elegida y el cambio
aplicado a la especificación, con el texto anterior y el nuevo.

Dos elementos de la especificación se modificaron en más de una pregunta (PD-C18 y CE-C08). En
cada pregunta se muestra el estado en que quedaron tras esa respuesta concreta.

---

## Pregunta 1

### Texto de la pregunta

¿Puede el paciente cancelar o reprogramar una cita cuya hora de inicio ya ha pasado? (RN-C09,
PD-C07)

### Por qué importa

Una cita pasada sigue en estado «reservada» (PD-C14), y hoy la especificación deja cancelarla
después de celebrada si se reservó con menos de 24 horas de antelación.

### Contexto

El origen es la redacción de PD-C07: «si falta menos [de 24 horas], solo se permite cuando la
cita se reservó a menos de 24 horas de su inicio». Una cita ya pasada también cumple «falta
menos», así que la excepción la deja pasar. El código lo reproduce tal cual
(`programacion_citas/servicio.py:452-456`) y ninguna prueba cubre el caso.

### Recomendación

Opción A. RN-C09 dice «hasta su inicio», es coherente con PD-C11 (no reescribir el historial) y
PD-C18 exige un motivo concreto; el mensaje de las 24 horas sería engañoso para una cita ya
celebrada.

### Opciones

| Opción | Descripción |
|--------|-------------|
| A | No se permite. Se rechaza con un motivo propio («la cita ya ha pasado»), que se añade a la lista de PD-C18 y como caso límite nuevo. |
| B | No se permite. Se rechaza con el motivo ya existente de «fuera del plazo de 24 horas», sin añadir uno nuevo. |
| C | Se permite cuando la cita se reservó con menos de 24 horas de antelación (lectura literal actual de PD-C07). |
| Breve | Otra respuesta corta (<=5 palabras). |

### Respuesta

**A**

### Cambio aplicado a la especificación

**1. Sección «Aclaraciones»: subsección nueva «Sesión 2026-10-06» con esta entrada**

```text
### Sesión 2026-10-06

- Q: ¿Puede el paciente cancelar o reprogramar una cita cuya hora de inicio ya ha pasado? → A: No;
  se rechaza con un motivo propio, «la cita ya ha pasado», distinto del de las 24 horas (PD-C07,
  PD-C18, CL-C10).
```

**2. Historia de usuario 3 (Cancelar una cita): escenario de aceptación 5, añadido**

```text
5. **Given** una cita reservada cuya hora de inicio ya ha pasado y que se reservó con menos de 24
   horas de antelación, **When** el paciente intenta cancelarla, **Then** se rechaza e informa de
   que la cita ya ha pasado, y sigue en estado reservada (CL-C10, RN-C09, PD-C07).
```

**3. Historia de usuario 4 (Reprogramar una cita): escenario de aceptación 5, añadido**

```text
5. **Given** una cita reservada cuya hora de inicio ya ha pasado, **When** el paciente intenta
   reprogramarla, **Then** se rechaza e informa de que la cita ya ha pasado, y conserva su fecha
   y su hora (CL-C10, RN-C09, PD-C07).
```

**4. Casos límite: CL-C10, añadido**

```text
- **CL-C10** *(deriva de RN-C09; aclaración Q1 de la sesión 2026-10-06)*: intentar cancelar o
  reprogramar una cita reservada cuya hora de inicio ya ha pasado: se rechaza e informa de que la
  cita ya ha pasado, aunque se hubiera reservado con menos de 24 horas de antelación (PD-C07).
```

**5. Precisiones derivadas: PD-C07, reescrita**

Antes:

```text
- **PD-C07** *(deriva de RN-C09; aclaración Q2 de la sesión 2026-09-28)*: El límite de RN-C09 se
  evalúa comparando el momento actual con el inicio de la cita: si faltan 24 horas o más, se
  permite cancelar y reprogramar; si falta menos, solo se permite cuando la cita se reservó a
  menos de 24 horas de su inicio. **Reprogramar actualiza ese momento de referencia**: tras un
  traslado, la antelación se mide desde el instante de la reprogramación, no desde la reserva
  original. Así, una cita reservada hace un mes y reprogramada hoy a un hueco de dentro de 3
  horas puede después cancelarse, porque su reserva efectiva es de hace minutos.
```

Después:

```text
- **PD-C07** *(deriva de RN-C09; aclaración Q2 de la sesión 2026-09-28 y aclaración Q1 de la
  sesión 2026-10-06)*: El límite de RN-C09 se evalúa comparando el momento actual con el inicio
  de la cita. **Una cita cuya hora de inicio ya ha pasado no se puede cancelar ni reprogramar en
  ningún caso** («hasta su inicio», RN-C09), con el mismo criterio de PD-C05 y PD-C11; el rechazo
  indica que la cita ya ha pasado, no que está fuera del plazo de 24 horas (PD-C18). Para una
  cita futura: si faltan 24 horas o más, se permite cancelar y reprogramar; si falta menos, solo
  se permite cuando la cita se reservó a menos de 24 horas de su inicio. **Reprogramar actualiza
  ese momento de referencia**: tras un
  traslado, la antelación se mide desde el instante de la reprogramación, no desde la reserva
  original. Así, una cita reservada hace un mes y reprogramada hoy a un hueco de dentro de 3
  horas puede después cancelarse, porque su reserva efectiva es de hace minutos.
```

**6. Precisiones derivadas: PD-C18, modificada (se añade el motivo «cita ya pasada»)**

Antes:

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04 y CL-C07)*: Toda operación rechazada
  indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento con otra cita del
  paciente, fuera del plazo de 24 horas, cita ya cancelada o paciente no encontrado. Ningún
  rechazo se presenta como error genérico.
```

Después de esta pregunta:

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04, CL-C07 y CL-C10)*: Toda operación
  rechazada indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento con otra
  cita del paciente, fuera del plazo de 24 horas, cita ya pasada, cita ya cancelada o paciente no
  encontrado. Ningún rechazo se presenta como error genérico.
```

**7. Criterios de éxito: CE-C08, modificado**

Antes:

```text
  CA-C13 y los 9 casos límite CL-C01 a CL-C09.
```

Después de esta pregunta:

```text
  CA-C13 y los 10 casos límite CL-C01 a CL-C10.
```

---

## Pregunta 2

### Texto de la pregunta

¿Qué valores se aceptan como nueva duración de las consultas cuando ni un solo hueco de esa
duración cabe en el horario del especialista? (RF-C09, RN-C12)

### Por qué importa

Con horario de 9:00 a 13:00, teclear 300 en vez de 30 deja al especialista sin huecos y cancela
por el centro todas sus citas futuras, y una cita cancelada no vuelve a reservada (CL-C08).

### Contexto

La especificación no dice qué duraciones son válidas. El código solo exige un entero mayor que
cero (`programacion_citas/servicio.py:603-605`) y lo traza a PD-C18, que no recoge ese rechazo.
En cualquiera de las opciones quedará escrito en la especificación que la duración es un número
entero de minutos mayor que cero.

### Recomendación

Opción A. Un especialista sin ningún hueco contradice el objetivo de negocio del módulo, y el
efecto es irreversible. La opción B es la más simple y no exige tocar el código, pero deja ese
error de tecleo sin red.

### Opciones

| Opción | Descripción |
|--------|-------------|
| A | Entero mayor que cero y que permita al menos un hueco en el horario. Si no cabe ninguno, se rechaza con su motivo y no se cancela ninguna cita. |
| B | Cualquier entero mayor que cero. Si no cabe ningún hueco, el especialista se queda sin huecos y se cancelan todas sus citas futuras (comportamiento actual). |
| Breve | Otra respuesta corta (<=5 palabras). |

### Respuesta

**A**

### Cambio aplicado a la especificación

**1. Sección «Aclaraciones», sesión 2026-10-06: entrada añadida**

```text
- Q: ¿Qué valores se aceptan como nueva duración de las consultas cuando ni un solo hueco de esa
  duración cabe en el horario del especialista? → A: Solo un número entero de minutos mayor que
  cero que permita al menos un hueco en el horario; si no cabe ninguno, se rechaza con su motivo
  y no se cancela ninguna cita (PD-C21, PD-C18, CL-C11).
```

**2. Historia de usuario 6 (Ajustar la duración de las consultas): escenario de aceptación 5,
añadido**

```text
5. **Given** un especialista con horario de 9:00 a 13:00, consultas de 20 minutos y citas futuras
   reservadas, **When** el administrativo intenta pasar la duración a 300 minutos, **Then** el
   cambio se rechaza e informa de que no cabe ningún hueco en el horario, la duración sigue
   siendo de 20 minutos y ninguna cita cambia de estado (CL-C11, PD-C21).
```

**3. Casos límite: CL-C11, añadido**

```text
- **CL-C11** *(deriva de RF-C09 y RN-C03; aclaración Q2 de la sesión 2026-10-06)*: intentar
  ajustar la duración de las consultas a un valor que no es un número entero de minutos mayor
  que cero, o con el que no cabe ningún hueco en el horario del especialista: se rechaza e
  informa del motivo, sin cambiar la duración y sin cancelar ninguna cita (PD-C21).
```

**4. Precisiones derivadas: PD-C21, añadida**

```text
- **PD-C21** *(deriva de RF-C09, RN-C02 y RN-C03; aclaración Q2 de la sesión 2026-10-06)*: La
  nueva duración de consulta DEBE ser un número entero de minutos mayor que cero y DEBE permitir
  al menos un hueco en el horario del especialista, es decir, no superar el tiempo entre su hora
  de inicio y su hora de fin (PD-C03). Un valor que no lo cumple se rechaza indicando el motivo
  (PD-C18): la duración vigente no cambia, la rejilla no se recalcula y ninguna cita se cancela.
  Así un error al teclear no deja al especialista sin huecos ni cancela todas sus citas futuras,
  efecto que no podría deshacerse (CL-C08).
```

**5. Precisiones derivadas: PD-C18, modificada (se añade el motivo «duración de consulta no
válida»)**

Antes de esta pregunta:

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04, CL-C07 y CL-C10)*: Toda operación
  rechazada indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento con otra
  cita del paciente, fuera del plazo de 24 horas, cita ya pasada, cita ya cancelada o paciente no
  encontrado. Ningún rechazo se presenta como error genérico.
```

Después de esta pregunta:

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04, CL-C07, CL-C10 y CL-C11)*: Toda
  operación rechazada indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento
  con otra cita del paciente, fuera del plazo de 24 horas, cita ya pasada, cita ya cancelada,
  paciente no encontrado o duración de consulta no válida. Ningún rechazo se presenta como error
  genérico.
```

**6. Entidades clave: «Especialista», modificada**

Antes:

```text
  La duración es el único atributo que la aplicación permite cambiar (RF-C09).
```

Después:

```text
  La duración es el único atributo que la aplicación permite cambiar (RF-C09); es un número
  entero de minutos mayor que cero con el que cabe al menos un hueco en el horario (PD-C21).
```

**7. Criterios de éxito: CE-C08, modificado**

Antes de esta pregunta:

```text
  CA-C13 y los 10 casos límite CL-C01 a CL-C10.
```

Después de esta pregunta:

```text
  CA-C13 y los 11 casos límite CL-C01 a CL-C11.
```

---

## Pregunta 3

### Texto de la pregunta

Tras bloquear una franja o cambiar la duración de las consultas, ¿qué información de las citas
canceladas debe ver el administrativo en la confirmación? (RF-C08, RF-C09)

### Por qué importa

La especificación no dice qué ve el administrativo, y la pantalla actual le enseña el código de
historia clínica de cada paciente afectado, que es justo el dato que basta para ver y cancelar
sus citas (PD-C02).

### Contexto

Hoy la confirmación lista fecha, hora, código de historia clínica y motivo de cada cita cancelada
(`programacion_citas/web.py:527-531`). Lo decidió el contrato de la interfaz, sin requisito
detrás. Además, el flujo administrativo está abierto a cualquiera que entre en la aplicación.

### Recomendación

Opción A. Sin notificaciones ni reasignación de citas, el administrativo no tiene nada que hacer
con la identidad del paciente, así que mostrarla incumple la minimización de datos (RGPD
art. 5.1.c, competencia CESI2). El número y las fechas bastan para comprobar el efecto del
cambio.

### Opciones

| Opción | Descripción |
|--------|-------------|
| A | El número de citas canceladas y la fecha y hora de cada una, sin ningún dato que identifique al paciente. |
| B | El número de citas canceladas y, de cada una, fecha, hora y código de historia clínica del paciente (comportamiento actual). |
| C | Solo la confirmación de la operación y el número de citas canceladas, sin listado. |
| Breve | Otra respuesta corta (<=5 palabras). |

### Respuesta

**A**

### Cambio aplicado a la especificación

**1. Sección «Aclaraciones», sesión 2026-10-06: entrada añadida**

```text
- Q: Tras bloquear una franja o cambiar la duración de las consultas, ¿qué información de las
  citas canceladas debe ver el administrativo en la confirmación? → A: El número de citas
  canceladas y la fecha y hora de cada una, sin ningún dato que identifique al paciente (PD-C22,
  CE-C10).
```

**2. Historia de usuario 5 (Bloquear una franja de un especialista): escenario de aceptación 7,
añadido**

```text
7. **Given** un bloqueo que cancela dos citas futuras, **When** el administrativo recibe la
   confirmación, **Then** ve que se han cancelado 2 citas y la fecha y la hora de cada una, y no
   ve el código de historia clínica ni ningún otro dato de los pacientes (PD-C22).
```

**3. Historia de usuario 6 (Ajustar la duración de las consultas): escenario de aceptación 6,
añadido**

```text
6. **Given** un cambio de duración que cancela una cita futura, **When** el administrativo recibe
   la confirmación, **Then** ve que se ha cancelado 1 cita y su fecha y su hora, y no ve el
   código de historia clínica ni ningún otro dato del paciente (PD-C22).
```

**4. Precisiones derivadas: PD-C22, añadida**

```text
- **PD-C22** *(deriva de RF-C08, RF-C09, RN-C11, RN-C12 y PD-C02; aclaración Q3 de la sesión
  2026-10-06)*: Al bloquear una franja o ajustar la duración, el sistema confirma la operación al
  administrativo indicando el número de citas canceladas por el centro y la fecha y la hora de
  cada una; si no se cancela ninguna, lo indica (CL-C04). La confirmación NO muestra el código de
  historia clínica, el documento de identidad ni ningún otro dato que identifique a los
  pacientes afectados: el administrativo no tiene ninguna operación que hacer con esa identidad
  —no hay notificaciones ni reasignación de citas— y, sin control de acceso, el código de
  historia clínica basta para ver y operar con las citas de un paciente (PD-C02). Es la
  aplicación del principio de minimización de datos (RGPD, art. 5.1.c).
```

**5. Criterios de éxito: CE-C10, añadido**

```text
- **CE-C10** *(PD-C22, PD-C02)*: El 100 % de las confirmaciones de bloqueo de franja y de cambio
  de duración indica el número de citas canceladas y la fecha y la hora de cada una, y muestra 0
  datos que identifiquen a un paciente (ni código de historia clínica ni documento de identidad).
```

---

## Pregunta 4

### Texto de la pregunta

¿Qué franjas debe rechazar el sistema cuando el administrativo intenta bloquearlas? (RF-C08,
PD-C12)

### Por qué importa

La especificación no recoge ningún rechazo al bloquear, pero el código ya rechaza dos casos sin
requisito que lo respalde, y un bloqueo no se puede deshacer (PD-C13).

### Contexto

Hoy se rechazan la fecha de fin anterior a la de inicio y la hora de fin que no es posterior a la
de inicio (`programacion_citas/servicio.py:545-547`). Se acepta cualquier otra franja, también
las que no tienen efecto: sobre fechas pasadas (ya recogido en «Supuestos»), fuera del horario
del especialista o en días en que no pasa consulta.

### Recomendación

Opción A. Es la más simple (principio II), coincide con el supuesto ya escrito sobre fechas
pasadas y no exige tocar el código. Una franja sin efecto no cancela nada ni oculta huecos, así
que aceptarla es inocuo.

### Opciones

| Opción | Descripción |
|--------|-------------|
| A | Solo las mal formadas: fecha de fin anterior a la de inicio, u hora de fin no posterior a la de inicio. Las que no tienen efecto se aceptan (comportamiento actual). |
| B | Las mal formadas y además las que no pueden tener ningún efecto: rango entero en el pasado, tramo fuera del horario del especialista o rango sin ningún día de consulta. |
| C | Las mal formadas y además las que tienen el rango entero en el pasado; esto sustituiría al supuesto actual sobre fechas pasadas. |
| Breve | Otra respuesta corta (<=5 palabras). |

### Respuesta

**C** (distinta de la recomendada, que era la A)

### Interpretación aplicada, pendiente de confirmar

«El rango entero en el pasado» se ha escrito en PD-C23 como **fecha de fin anterior a la fecha
actual del sistema**, porque la especificación usa «rango» para las fechas (PD-C12). Con esa
lectura, un bloqueo para hoy cuyo tramo horario ya ha terminado se acepta, sin efecto. Esta
lectura es una interpretación de quien redactó el cambio, no una respuesta explícita: queda
pendiente de que la persona responsable la confirme o pida cambiarla a «fecha y hora de fin ya
pasadas».

### Cambio aplicado a la especificación

**1. Sección «Aclaraciones», sesión 2026-10-06: entrada añadida**

```text
- Q: ¿Qué franjas debe rechazar el sistema cuando el administrativo intenta bloquearlas? → A: Las
  mal formadas (fecha de fin anterior a la de inicio, u hora de fin no posterior a la de inicio)
  y las que tienen el rango de fechas entero en el pasado; las demás se aceptan aunque no tengan
  efecto (PD-C23, PD-C18, CL-C12).
```

**2. Historia de usuario 5 (Bloquear una franja de un especialista): escenarios de aceptación 8
y 9, añadidos**

```text
8. **Given** un especialista cualquiera, **When** el administrativo intenta bloquear una franja
   cuya fecha de fin es anterior a la fecha actual, **Then** el bloqueo se rechaza e informa de
   que el rango ya ha pasado, y no se registra ninguna franja (CL-C12, PD-C23).
9. **Given** un especialista cualquiera, **When** el administrativo intenta bloquear una franja
   con la fecha de fin anterior a la de inicio, o con la hora de fin no posterior a la de inicio,
   **Then** el bloqueo se rechaza e informa del dato incorrecto, y no se registra ninguna franja
   ni se cancela ninguna cita (CL-C12, PD-C23).
```

**3. Casos límite: CL-C12, añadido**

```text
- **CL-C12** *(deriva de RF-C08 y PD-C12; aclaración Q4 de la sesión 2026-10-06)*: intentar
  bloquear una franja mal formada (fecha de fin anterior a la de inicio, u hora de fin no
  posterior a la de inicio) o con el rango de fechas entero en el pasado: se rechaza e informa
  del motivo, sin registrar la franja y sin cancelar ninguna cita (PD-C23).
```

**4. Precisiones derivadas: PD-C23, añadida**

```text
- **PD-C23** *(deriva de RF-C08 y PD-C12; aclaración Q4 de la sesión 2026-10-06)*: El sistema
  rechaza el bloqueo de una franja, indicando el motivo (PD-C18) y sin registrarla ni cancelar
  ninguna cita, en estos tres casos y solo en ellos: (a) la fecha de fin es anterior a la fecha
  de inicio; (b) la hora de fin no es posterior a la hora de inicio; (c) el rango de fechas está
  entero en el pasado, es decir, la fecha de fin es anterior a la fecha actual del sistema.
  Cualquier otra franja se acepta, aunque no tenga efecto: un rango que empieza en el pasado y
  acaba hoy o después, un tramo horario fuera del horario del especialista o un rango sin ningún
  día en que pase consulta. Como un bloqueo no se puede deshacer (PD-C13), rechazar el rango ya
  pasado evita registrar franjas que nunca podrían afectar a la agenda.
```

**5. Precisiones derivadas: PD-C18, modificada (se añade el motivo «franja no válida»)**

Antes de esta pregunta:

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04, CL-C07, CL-C10 y CL-C11)*: Toda
  operación rechazada indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento
  con otra cita del paciente, fuera del plazo de 24 horas, cita ya pasada, cita ya cancelada,
  paciente no encontrado o duración de consulta no válida. Ningún rechazo se presenta como error
  genérico.
```

Después de esta pregunta (texto final):

```text
- **PD-C18** *(deriva de CA-C05, CA-C07, CL-C01 a CL-C04, CL-C07 y CL-C10 a CL-C12)*: Toda
  operación rechazada indica el motivo concreto: hueco no disponible, hueco pasado, solapamiento
  con otra cita del paciente, fuera del plazo de 24 horas, cita ya pasada, cita ya cancelada,
  paciente no encontrado, duración de consulta no válida o franja no válida (mal formada o con
  el rango ya pasado). Ningún rechazo se presenta como error genérico.
```

**6. Entidades clave: «Franja bloqueada», modificada**

Antes:

```text
  horario se aplica a cada día del rango, ambas fechas incluidas (PD-C12). Mientras esté vigente,
```

Después:

```text
  horario se aplica a cada día del rango, ambas fechas incluidas (PD-C12). La fecha de fin no es
  anterior a la de inicio ni a la fecha en que se bloquea, y la hora de fin es posterior a la de
  inicio (PD-C23). Mientras esté vigente,
```

**7. Supuestos: «Bloqueos sobre fechas pasadas», sustituido**

Antes:

```text
- **Bloqueos sobre fechas pasadas**: no se prohíben, pero no tienen ningún efecto sobre las citas
  ya celebradas (PD-C11). El enunciado no pide validar que el rango sea futuro y no se añade esa
  restricción.
```

Después:

```text
- **Bloqueos sobre fechas pasadas**: se rechaza la franja cuyo rango de fechas está entero en el
  pasado (PD-C23, aclaración Q4 de la sesión 2026-10-06). Un rango que empieza en el pasado y
  acaba hoy o después sí se acepta, y su parte ya pasada no tiene ningún efecto sobre las citas
  ya celebradas (PD-C11).
```

**8. Criterios de éxito: CE-C08, modificado**

Antes de esta pregunta:

```text
  CA-C13 y los 11 casos límite CL-C01 a CL-C11.
```

Después de esta pregunta (texto final):

```text
  CA-C13 y los 12 casos límite CL-C01 a CL-C12.
```

---

## Justificación de las decisiones

Las respuestas las tomó el responsable del producto. La skill registra qué se
eligió, no por qué; esta sección recoge el motivo de cada decisión y su
clasificación.

### Q1 · Cita ya pasada — opción A (motivo propio)

Las opciones A y B rechazan igual; la diferencia está en el mensaje. Con la B,
quien intenta cancelar una consulta celebrada la semana pasada lee «solo se
puede cancelar hasta 24 horas antes del inicio»: es cierto, pero sugiere un
problema de plazos y no que la cita ya se celebró. Se elige el motivo propio
porque un mensaje que no describe lo ocurrido confunde aunque sea técnicamente
correcto. El coste —un motivo más en PD-C18, un caso límite y una prueba— es
precisión sobre algo que ya existía, no funcionalidad nueva, así que no choca
con el principio de alcance mínimo.

**Clasificación: duda funcional.** El código hacía exactamente lo que decía la
especificación; lo que faltaba era que la especificación previera el caso.

### Q2 · Duración sin huecos posibles — opción A (rechazar)

La duración de una consulta no puede ser mayor que la jornada del especialista,
porque entonces no existiría ningún hueco donde atenderla. El límite exacto no
es «la jornada» sino «que quepa un hueco entero», que es el mismo criterio que
RN-C03 ya aplica al generar la rejilla: no se inventa una regla nueva, se aplica
la existente también al cambiar la duración. Se valida porque el error es
irreversible: un dedazo cancela todas las citas futuras del especialista y una
cita cancelada no vuelve a reservada (CL-C08).

**Clasificación: duda funcional.** La especificación nunca dijo qué duraciones
eran válidas y el código eligió la validación mínima.

### Q3 · Datos en la confirmación al administrativo — opción A (sin identidad)

Se valoró mantener el comportamiento actual con el argumento de que un
administrativo real tiene acceso a los datos de los pacientes del centro. El
argumento no se sostiene en esta aplicación: no hay control de acceso, el flujo
de agenda está abierto a cualquiera que escriba la dirección, y el código de
historia clínica es suficiente para ver y cancelar las citas de un paciente.

Se buscó entonces un caso de uso que justificara el dato —un paciente que
necesita recuperar una cita cancelada por error— y se comprobó que ninguna
operación del módulo permite atenderlo: el administrativo no puede reservar en
nombre de un paciente y una cita cancelada no vuelve a reservada. Al no
habilitar ninguna acción posible, el dato se elimina por minimización
(RGPD, art. 5.1.c).

**Clasificación: decisión tomada por el contrato de la interfaz sin requisito
que la respaldara.** El código mostraba un dato que ningún documento pedía.

**Limitación pendiente detectada:** la gestión de citas por parte del
administrativo en nombre de un paciente sería una capacidad nueva, fuera del
alcance de este ejercicio.

### Q4 · Franjas que se rechazan — opción C (distinta de la recomendada)

Se descartó la opción A recomendada. Bloquear significa «no atenderé en ese
rato», y un rato que ya terminó no se puede dejar de atender: un bloqueo sobre
el pasado no puede tener efecto nunca. Las otras dos franjas sin efecto —fuera
del horario, o en días sin consulta— sí se aceptan, porque el horario del
especialista puede cambiar y entonces cobrarían sentido; el pasado no cambia.

Es el mismo criterio de la Q1: el usuario debe enterarse de lo que realmente
ocurre en lugar de recibir una confirmación falsa.

**Esta respuesta modifica una decisión del ejercicio 2**, donde se acordó
permitir bloqueos pasados sin efecto. El supuesto correspondiente queda
sustituido.

**Clasificación: duda funcional,** con revisión de una decisión previa.

## Correcciones de texto obsoleto

Durante la sesión, clarify detectó tres referencias caducadas que no derivaban
de ninguna respuesta y se corrigieron aparte:

- La especificación citaba la constitución v3.1.0, vigente la v3.2.0.
- El supuesto «Vocabulario pendiente en la constitución» ya no era cierto: la
  v3.2.0 incorporó los términos del módulo de citas.
- Las notas de la lista de comprobación hablaban de 7 casos límite y de
  PD-C01 a PD-C20, cifras desfasadas.

Clasificación: incoherencia documental. Ningún comportamiento de la aplicación
cambia; son documentos que se referencian entre sí con datos caducados.
