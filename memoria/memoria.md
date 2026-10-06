# Memoria · Ejercicio 3: clarificación, análisis y convergencia

**Asignatura**: Ingeniería de Requisitos
**Proyecto**: Sistema de Información de Gestión Hospitalaria (HIS)
**Módulos revisados**: Registro e Identificación de Pacientes (001) y
Programación de Citas (002)
**Fecha de inicio**: 2026-10-06

---

## 1. Objetivo y alcance revisado

Esta práctica no construye ningún módulo nuevo. Parte del proyecto entregado en
el ejercicio 2 y lo somete a tres revisiones distintas con las skills de Spec
Kit: `clarify` para resolver dudas funcionales pendientes, `analyze` para
detectar incoherencias entre especificación, plan y tareas, y `converge` para
contrastar lo definido con lo realmente implementado.

El alcance revisado es el módulo de Programación de Citas y su relación con el
de Registro de Pacientes, en concreto el vínculo entre cita y paciente, la
disponibilidad de huecos, la cancelación, la reprogramación y los bloqueos de
agenda.

Se mantiene fuera de alcance todo lo que ya lo estaba en los ejercicios
anteriores: nuevos módulos del HIS, integraciones reales, autenticación y
control de acceso, y la gestión completa de centros y especialidades.

---

## 2. Estado inicial

El estado previo a cualquier modificación quedó congelado en:

- **Commit**: `947d2e9a142638b90c818b231a4f3cf9e8e5b406`
- **Mensaje**: «feat: contenerización y módulo de programación de citas (SDD completo)»
- **Etiqueta**: `estado-inicial-ejercicio3`

Además se conservó una copia literal de los tres documentos antes de tocarlos,
en `memoria/estado-inicial/`: `spec.md`, `plan.md` y `tasks.md`. Como el
entregable es un ZIP sin historial de git, esa copia permite comparar el estado
inicial y el final abriendo los ficheros, sin necesidad de un `git diff`.

En ese punto de partida, la aplicación arrancaba correctamente con
`docker compose up`, pasaba todas sus pruebas automáticas y tenía sus tareas
marcadas como completadas.

---

## 3. Secuencia de comandos ejecutados

| Orden | Comando | Propósito |
|-------|---------|-----------|
| 1 | `/speckit-clarify` | Resolver ambigüedades funcionales de la especificación de citas |
| 2 | `/speckit-plan` | Alinear plan, modelo de datos y contratos con las decisiones tomadas |
| 3 | `/speckit-tasks` | Regenerar las tareas afectadas |
| 4 | `/speckit-analyze` | Contrastar la coherencia entre spec, plan y tareas |
| 5 | *(correcciones documentales)* | Corregir los hallazgos en sus documentos de origen |
| 6 | `/speckit-analyze` | Repetir el análisis tras las correcciones |
| 7 | `/speckit-converge` | Contrastar la implementación con lo definido |
| 8 | `/speckit-implement` | Completar las tareas correctivas |
| 9 | `/speckit-converge` | Repetir la convergencia y verificar |

Nota: el enunciado escribe los comandos con punto (`/speckit.clarify`); la
instalación utilizada los expone con guion (`/speckit-clarify`), que es la forma
empleada.

---

## 4. Clarify: ambigüedades resueltas

Se formularon **cuatro** preguntas. El informe literal de la sesión, con el
texto de cada pregunta, sus opciones, la respuesta elegida y el cambio aplicado
a la especificación, está en [`informes/clarify.md`](informes/clarify.md). Las
justificaciones de cada decisión se recogen al final de ese mismo documento.

Resumen de las decisiones:

| # | Ambigüedad | Decisión | Dónde queda |
|---|------------|----------|-------------|
| 1 | ¿Se puede cancelar o reprogramar una cita ya pasada? | No, con un motivo propio distinto del de las 24 horas | PD-C07 reescrita, CL-C10 |
| 2 | ¿Qué duraciones de consulta son válidas? | Entero positivo con el que quepa al menos un hueco; si no, se rechaza sin cancelar nada | PD-C21, CL-C11 |
| 3 | ¿Qué ve el administrativo de las citas canceladas? | Número, fecha y hora; ningún dato que identifique al paciente | PD-C22, CE-C10 |
| 4 | ¿Qué franjas se rechazan al bloquear? | Las mal formadas y las que ya han pasado por completo | PD-C23, CL-C12 |

Dos observaciones sobre esta fase:

La decisión 4 **se apartó de la opción recomendada** y, además, modificó una
decisión tomada en el ejercicio 2, donde se había acordado aceptar bloqueos
pasados sin efecto.

Al margen de las cuatro respuestas, la skill detectó tres referencias caducadas
entre documentos que no derivaban de ninguna decisión funcional, y que se
corrigieron por separado.

El resultado más útil de esta fase no fueron las decisiones en sí, sino que
cada una vino acompañada del fichero y la línea exacta del código que pasaba a
incumplir la especificación. Esa lista es el punto de partida de la fase de
convergencia.

---

## 5. Analyze: coherencia documental

Se ejecutó `/speckit-analyze` dos veces: una tras alinear el plan y las tareas
con las aclaraciones, y otra después de aplicar las correcciones. Los dos
informes literales están en [`informes/analyze-inicial.md`](informes/analyze-inicial.md)
y [`informes/analyze-final.md`](informes/analyze-final.md).

### Resultado de las dos pasadas

| | Primera pasada | Segunda pasada |
|---|---|---|
| Críticos | 0 | 0 |
| Altos | 2 | 0 |
| Medios | 8 | 5 |
| Bajos | 5 | 6 |
| **Total** | **15** | **11** |

Los 15 hallazgos de la primera pasada quedaron resueltos y desaparecieron los
dos de severidad alta.

### Naturaleza de los hallazgos

De los 15 iniciales, **14 eran documentales**: frases que conservaban una
redacción anterior, escenarios de aceptación que faltaban, referencias
caducadas entre documentos y recuentos desfasados. Ninguno alteraba el
funcionamiento de la aplicación.

Solo uno, A1, cambiaba un comportamiento ya implementado: un hueco cuyo inicio
coincide exactamente con el momento actual podía reservarse, y esa misma cita
contaba ya como pasada y no se podía cancelar. Reproducía el problema de la
«cita atrapada» que se había resuelto en el ejercicio 2 con otra regla. Se
decidió que un hueco solo es reservable si su inicio es estrictamente posterior
al momento actual, lo que obligó a añadir el caso límite CL-C13 y a propagar la
decisión a cinco documentos y dos tareas nuevas.

**A1 estaba clasificado como severidad media, por debajo de los dos altos**, que
eran frases desalineadas. La severidad que asigna la herramienta mide el riesgo
documental, no el impacto funcional: el único hallazgo que tocaba el
comportamiento iba marcado por debajo de los que solo tocaban texto.

### Por qué quedan 11 hallazgos abiertos

Cuatro de los once de la segunda pasada **los generaron las propias
correcciones**: la de I7 creó I10, y la propagación de CL-C13 dejó sin
actualizar los textos de I11, I12 e I13. Corregir incoherencias genera
incoherencias nuevas, porque cada edición mueve texto que otros documentos
citan. El análisis converge, pero no en una sola iteración.

Por eso el criterio de parada no fue «cero hallazgos», sino que no quedara
ninguno que afectara al comportamiento de la aplicación ni a la ejecución del
trabajo pendiente. Con ese criterio se corrigieron dos más:

- **I10**: `tasks.md` declaraba una dependencia contradictoria entre T042 y
  T044; siguiendo el orden escrito, las pruebas no fallarían antes de su
  implementación, que es lo que exige el método.
- **I11**: la tarea de cierre no incluía la fase 16, de modo que el trabajo de
  CL-C13 se implementaría pero no se verificaría en la batería final.

Los nueve restantes (I12, I13, I14, I15, I16, I17, I18, I19 y U4) son
documentales: recuentos, trazabilidad entre documentos, redacción de dos
mensajes equivalentes, un término del glosario y saltos de línea. Quedan
listados como deuda conocida y no se corrigen.

En total: **15 de 15 hallazgos de la primera pasada y 2 de los 11 de la
segunda**, seleccionados por afectar a la ejecución del trabajo.

## 6. Converge: diferencias con la implementación

Se ejecutó `/speckit-converge` dos veces. Los informes literales están en
[`informes/converge-inicial.md`](informes/converge-inicial.md) y
[`informes/converge-final.md`](informes/converge-final.md).

### Primera pasada (antes de implementar)

La primera ejecución se hizo con las 22 tareas de la actualización aún
pendientes, por lo que seis de sus siete hallazgos se limitaron a confirmar
trabajo ya planificado: las cuatro líneas de código que `clarify` había
señalado, el reloj de las pruebas web y el caso CL-C13 surgido de `analyze`.

Aun así apareció un hallazgo que no tenía tarea asociada:

**F7** — `web.py:598` y `:603` llamaban a `datetime.date.today()` por su
cuenta, cuando la decisión D-C10 del plan establece que
`servicio.momento_actual()` es el único punto que consulta el reloj. Se anexó
como T060.

F7 es relevante porque **ninguna de las dos pasadas de `analyze` podía
detectarlo**: una regla del plan incumplida por el código no produce ninguna
incoherencia entre spec, plan y tareas. Solo la convergencia, que contrasta los
documentos con el código, podía encontrarlo.

Junto con F5 —el mismo D-C10 incumplido en las pruebas— resulta que una sola
decisión del plan se ignoró en dos sitios distintos sin que la revisión
documental lo advirtiera.

El dato que mejor resume esta fase: en el momento de la primera convergencia,
las 167 pruebas pasaban en verde y existían siete diferencias respecto a la
especificación, cinco de severidad alta.

### Segunda pasada (después de implementar)

| | Primera pasada | Segunda pasada |
|---|---|---|
| Críticos | 0 | 0 |
| Altos | 5 | 0 |
| Medios | 1 | 0 |
| Bajos | 1 | 2 |

Alcance revisado en la segunda pasada: 9 requisitos funcionales, 10 criterios
de éxito, 36 escenarios de aceptación, 13 casos límite, 21 decisiones del plan
y los 5 principios de la constitución.

Los cinco comportamientos de la actualización están implementados y probados,
los 13 criterios de aceptación y los 13 casos límite tienen prueba con su
identificador en el nombre, los mensajes coinciden literalmente con el
contrato, el reloj se consulta en un único punto y siguen existiendo
exactamente las 11 rutas.

Los dos hallazgos restantes son de trazabilidad en comentarios del código:

- **T061**: cuatro docstrings cuyo alcance cambió en esta actualización sin que
  su código se modificara. Se corrigen: es un descuido introducido ahora.
- **T062**: quince funciones auxiliares anteriores a la actualización cuyos
  docstrings no citan identificadores. Se deja documentada y sin corregir, por
  el mismo criterio de parada aplicado en `analyze`: no afecta al
  comportamiento ni a la ejecución del trabajo, y la trazabilidad se mantiene a
  nivel de módulo.

## 7. Verificación de las correcciones
Escenarios ejecutados sobre la aplicación en contenedor, con datos ficticios.

> Nota: el contenedor opera en UTC, dos horas por detrás de la hora local. Las
> reglas temporales se evalúan con la hora del contenedor; las horas indicadas
> en estos escenarios son las del contenedor.

### E1 · Reservar para un paciente existente y comprobar su identidad
**Entrada:** _(código de historia clínica usado)_
**Pasos:** _(…)_
**Esperado:** la cita queda asociada a ese código; identificarse por documento
devuelve las mismas citas (CA-C04).
**Observado:**
**Evidencia:**

### E2 · Cancelar y consultar la disponibilidad
**Esperado:** la cita pasa a «cancelada por el paciente» y su hueco vuelve a
ofrecerse (CA-C06).

### E3 · Reprogramar con éxito
**Esperado:** misma cita y mismo especialista, hueco anterior libre y nuevo
ocupado (CA-C09).

### E4 · Reprogramar ante un fallo
**Esperado:** se rechaza con su motivo y la cita original conserva fecha y hora.

### E5 · Bloquear una franja con citas existentes
**Esperado:** las citas futuras de dentro pasan a «cancelada por el centro» con
su motivo; la confirmación muestra número, fecha, hora y motivo, y **ningún
código de historia clínica** (PD-C22).

### E6 · Cita ya pasada (decisión Q1)
**Esperado:** se rechaza con «la cita ya ha pasado», no con el mensaje de las 24
horas (CL-C10).

### E7 · Duración sin huecos posibles (decisión Q2)
**Esperado:** 300 minutos con horario de 9:00 a 13:00 se rechaza, la duración
sigue en 20 y ninguna cita cambia de estado (CL-C11). 240 sí se acepta.

### E8 · Franja ya pasada (decisión Q4)
**Esperado:** bloquear ayer se rechaza; bloquear hoy con el tramo ya terminado
se rechaza; bloquear hoy de 9:00 a 14:00 antes de las 14:00 se acepta (CL-C12).

### E9 · Regresión del módulo de pacientes
**Pasos:** registrar un paciente, buscarlo por documento y por código,
modificar su teléfono.
**Esperado:** las tres operaciones funcionan igual que antes.

### Pruebas automáticas
192 pruebas, todas en verde. Línea base antes de la actualización: 167.

## 8. Comparación del estado inicial y final

**Estado inicial**: commit `947d2e9a142638b90c818b231a4f3cf9e8e5b406`, etiqueta
`estado-inicial-ejercicio3`. Copia literal de los tres documentos en
`memoria/estado-inicial/`.

**Estado final**: commit `c540a19`.

| | Inicial | Final |
|---|---|---|
| Casos límite | 9 | 13 |
| Precisiones derivadas | 20 | 23 |
| Criterios de éxito | 9 | 10 |
| Tareas | 37 | 62 |
| Pruebas automáticas | 167 | 192 |

### Mejoras

- **Cuatro ambigüedades funcionales resueltas** y convertidas en reglas con
  criterio verificable: cita pasada, duración válida, datos en la confirmación
  y franjas rechazables.
- **Dos defectos que no habría detectado ninguna prueba**: las pruebas web
  habrían empezado a fallar el 2026-10-08 por usar una fecha fija y consultar
  el reloj real; y un hueco que empezaba justo en ese instante podía reservarse
  dando lugar a una cita que nacía ya pasada y no se podía cancelar.
- **Un dato personal retirado** de una pantalla sin control de acceso, por
  minimización.
- **17 incoherencias documentales corregidas** entre especificación, plan,
  tareas, contratos y decisiones técnicas.

### Una decisión revisada antes de llegar al código

La decisión Q3 se tomó inicialmente retirando de la confirmación tanto el
código de historia clínica como el motivo de cancelación. Antes de implementarla
se revisó: el motivo no identifica a nadie y sí informa al administrativo de por
qué se canceló cada cita. La minimización se aplica a los datos que identifican
a la persona, no a toda la información de la operación.

La corrección obligó a alinear cinco documentos que ya habían recogido la
redacción anterior. El informe
[`plan-actualizacion.md`](informes/plan-actualizacion.md) conserva a propósito
la redacción original, con una nota posterior, como evidencia del estado
intermedio.

---

## 9. Qué aporta cada skill

Las tres revisiones responden a preguntas distintas y ninguna sustituye a otra.

### Clarify — ¿está decidido?

Busca **dudas funcionales**: situaciones que la especificación no previó. No
hay error en ninguna parte; simplemente nadie se planteó el caso, y el código
hace lo que el documento dice.

*Ejemplo propio:* la especificación permitía cancelar una cita ya celebrada,
porque la excepción redactada para las reservas de última hora también encajaba
con una cita pasada. El código la reproducía fielmente. No era un fallo de
implementación: era una ambigüedad del requisito.

Su mayor aportación no fueron las decisiones, sino que cada una llegó con el
fichero y la línea exacta del código que pasaba a incumplir la especificación.

### Analyze — ¿dicen lo mismo los documentos?

Busca **incoherencias documentales**: contradicciones entre especificación,
plan y tareas. Solo lee documentos, nunca código.

*Ejemplo propio:* tras decidir que se rechazan las franjas ya pasadas, el
apartado de supuestos seguía diciendo que se aceptaban sin efecto. Dos frases
del mismo documento afirmando lo contrario.

Enseñó también algo sobre el propio proceso: **corregir incoherencias genera
incoherencias nuevas**, porque cada edición mueve texto que otros documentos
citan. Cuatro de los once hallazgos de la segunda pasada los habían creado las
correcciones de la primera.

Y que **su severidad mide riesgo documental, no impacto funcional**: el único
hallazgo que cambiaba el comportamiento de la aplicación iba clasificado como
medio, por debajo de dos frases desalineadas marcadas como altas.

### Converge — ¿hace el código lo que dicen los documentos?

Busca **diferencias de implementación**: comportamiento que se aparta de lo
definido, aunque todas las pruebas pasen y todas las tareas estén marcadas.

*Ejemplo propio:* el plan establecía en D-C10 que un único punto del código
consulta el reloj. La interfaz llamaba a `datetime.date.today()` por su cuenta
en dos sitios. Ninguna de las dos pasadas de `analyze` podía detectarlo: no
había ninguna contradicción entre documentos: la contradicción era entre el
plan y el código.

### El resumen de la práctica

En el momento de la primera convergencia, el proyecto tenía **192 pruebas** —167
entonces— **todas en verde, todas las tareas marcadas como completadas, y siete
diferencias respecto a su propia especificación, cinco de severidad alta**.

Esa es la lección: una aplicación que arranca y una batería en verde demuestran
que el código hace lo que las pruebas comprueban, no que cumpla lo que la
especificación define. Hacen falta tres revisiones distintas, porque cada una
mira un plano diferente: `clarify` el requisito consigo mismo, `analyze` los
documentos entre sí, `converge` los documentos contra el código.

---

## 10. Limitaciones pendientes

- **Solapamiento por cambio de duración (PD-C20).** Al alargar las consultas, un
  paciente puede quedar con dos citas solapadas de especialistas distintos y
  ambas se conservan. CE-C03 se acotó para no prometer algo que el sistema no
  cumple. Resolverlo sería comportamiento nuevo, fuera del alcance.
- **Zona horaria del contenedor.** El contenedor opera en UTC, dos horas por
  detrás de la hora local. Las tres reglas temporales se evalúan con esa hora,
  de modo que un hueco puede seguir ofreciéndose después de su hora local. La
  especificación declara que no se tratan zonas horarias, así que no es un
  incumplimiento, pero afecta al uso real.
- **Gestión de citas en nombre del paciente.** Un paciente que cancela por error
  no puede recuperar su cita: el administrativo no puede reservar por él y una
  cita cancelada no vuelve a estado reservada. Requeriría una capacidad nueva.
- **Nueve hallazgos documentales de la segunda pasada de analyze** (I12 a I19 y
  U4): recuentos, trazabilidad entre documentos, redacción de mensajes
  equivalentes, el término «sede» en la definición de Centro y formato de
  párrafos. Documentados y sin corregir.
- **T062**: quince funciones auxiliares sin identificadores en su docstring.
- **Sin control de acceso.** Heredado del alcance de las prácticas anteriores:
  el código de historia clínica basta para ver y operar con las citas de un
  paciente, y el flujo de agenda está abierto. La aplicación no es apta para
  datos reales.
