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

*(pendiente)*

## 7. Verificación de las correcciones

*(pendiente)*

## 8. Comparación del estado inicial y final

*(pendiente)*

## 9. Qué aporta cada skill

*(pendiente — se redacta al final, con ejemplos propios de cada categoría)*

---

## 10. Limitaciones pendientes

- **Gestión de citas en nombre del paciente.** Al decidir la pregunta 3 se
  identificó un caso de uso real —un paciente que cancela por error y necesita
  recuperar su cita— que ninguna operación del módulo permite atender: el
  administrativo no puede reservar por un paciente y una cita cancelada no
  vuelve a estado reservada. Resolverlo requeriría una capacidad nueva, fuera
  del alcance de esta práctica.
