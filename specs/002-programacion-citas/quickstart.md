# Guía de validación: Módulo de Programación de Citas

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) ·
**Contratos**: [servicio-citas.md](contracts/servicio-citas.md),
[interfaz-web-citas.md](contracts/interfaz-web-citas.md)

Guía para arrancar el módulo, ejecutar sus pruebas y validar a mano los escenarios del enunciado.
Todos los datos que aparecen son **ficticios** (principio IV).

## Requisitos previos

- Docker con Docker Compose v2 (forma recomendada), **o** Python 3.10 o superior para la ejecución
  sin contenedor.
- Al menos un paciente registrado: este módulo no da de alta pacientes (frontera del principio II).
  Si la base de datos está vacía, regístralo primero en el flujo del módulo de registro
  (`/pacientes/nuevo`) y apunta su código de historia clínica.

## Arranque

```bash
docker compose up
```

No hay ningún paso manual: el esquema de las cinco tablas y la precarga de centros, especialidades
y especialistas se aplican en el propio arranque, y es idempotente (D-C12), así que repetir el
comando no duplica datos.

Sin contenedor:

```bash
python app.py
```

Direcciones de los dos flujos (D-C14):

| Flujo | Dirección |
|---|---|
| Paciente | `http://127.0.0.1:8000/citas` |
| Personal administrativo | `http://127.0.0.1:8000/agenda` |
| Módulo de registro (sin cambios) | `http://127.0.0.1:8000/` |

> La página de inicio `/` todavía no enlaza con los dos flujos anteriores: hay que escribir la
> dirección. Es el punto abierto de D-C14, pendiente de decisión y ajeno a los requisitos.

## Pruebas automáticas

```bash
python -m unittest
```

Ejecuta las pruebas de los dos módulos. Para ver solo las de este:

```bash
python -m unittest tests.test_agenda tests.test_reserva tests.test_cancelacion \
                   tests.test_reprogramacion tests.test_bloqueo tests.test_duracion \
                   tests.test_web_citas
```

Cada prueba indica en su nombre el criterio de aceptación (CA-C), caso límite (CL-C) o precisión
(PD-C) que verifica. La correspondencia completa está en la tabla de trazabilidad de
[plan.md](plan.md).

Las pruebas fijan el momento actual (D-C10), sin lo cual CA-C07, CA-C08 y los escenarios de citas
pasadas no serían deterministas.

## Validación manual de los escenarios

Los datos precargados usados abajo son de ejemplo; ajusta nombres y fechas a lo que muestre tu
instalación. Usa siempre fechas **futuras** en un día en que el especialista pase consulta.

### E-C01 · Reservar · CA-C01, CA-C02, CA-C03, CA-C04

1. Abre `/citas` e identifícate con el código de historia clínica del paciente.
2. Elige una especialidad y un centro. **Comprueba** que solo aparecen los especialistas que
   cumplen los dos filtros (CA-C03).
3. Elige un especialista con horario de 9:00 a 13:00 y consultas de 20 minutos, y una fecha futura
   de consulta. **Comprueba** que se ofrecen 12 huecos, de 9:00 a 12:40 (CA-C01).
4. Reserva el de las 9:00. **Comprueba** que desaparece de los libres y que los demás siguen
   (CA-C02).
5. Vuelve a `/citas` e identifícate ahora por tipo y número de documento. **Comprueba** que ves la
   misma cita (CA-C04).

### E-C01 · Solapamiento · CA-C05

1. Con el mismo paciente, busca **otro** especialista, de otro centro si quieres.
2. Intenta reservar un hueco que se solape con la cita de las 9:00 ya reservada.
3. **Comprueba** que se rechaza con «Ya tiene otra cita reservada a esa hora.» (CA-C05, RN-C07).
4. Reserva ahora un hueco que empiece justo cuando acaba la otra (9:20 si duran 20 minutos).
   **Comprueba** que **sí** se acepta: tocarse en el extremo no es solaparse (PD-C06).

### E-C03 · Cancelar · CA-C06, CA-C07, CA-C08, CL-C07

1. En `/citas/mias`, cancela una cita cuyo inicio esté a más de 24 horas. **Comprueba** que queda
   «cancelada por el paciente» y que su hueco vuelve a ofrecerse (CA-C06).
2. Intenta cancelar una cita que empiece dentro de menos de 24 horas y que reservaste hace más de
   24 horas. **Comprueba** que se rechaza indicando el plazo (CA-C07).
3. Reserva una cita para dentro de unas 3 horas de hoy y cancélala de inmediato. **Comprueba** que
   se acepta (CA-C08).
4. Intenta cancelar una cita ya cancelada. **Comprueba** que se rechaza (CL-C07).
5. Reserva una cita para dentro de unos minutos, espera a que pase su hora de inicio e intenta
   cancelarla y después reprogramarla. **Comprueba** que las dos se rechazan con «No se puede
   cancelar ni reprogramar una cita cuya hora ya ha pasado.» —no con el mensaje de las 24 horas— y
   que la cita sigue reservada (CL-C10, PD-C07). La vía fiable son las pruebas automáticas, que
   fijan el momento actual.

### E-C02 · Reprogramar · CA-C09, PD-C07

1. En `/citas/mias`, reprograma una cita reservada al hueco de las 11:00 del mismo especialista.
2. **Comprueba** que el identificador de la cita **no cambia**, que el especialista es el mismo,
   que el hueco anterior vuelve a estar libre y que el de las 11:00 pasa a estar ocupado (CA-C09).
3. **Comprueba** que no se ofrece cambiar de especialista (RN-C10).
4. Reprograma una cita antigua a un hueco de dentro de unas 3 horas y, acto seguido, cancélala.
   **Comprueba** que se permite: reprogramar actualiza la referencia de las 24 horas (PD-C07).

### E-C04 · Bloquear una franja · CA-C10, CA-C11, CL-C04

1. Reserva tres citas del mismo especialista y misma fecha, a las 9:00, 10:00 y 11:00.
2. En `/agenda`, elige ese especialista y bloquea la franja de 9:00 a 11:00 de esa fecha
   (`fecha_inicio` = `fecha_fin` = esa fecha).
3. **Comprueba** que las de 9:00 y 10:00 pasan a «cancelada por el centro» y que la de 11:00 sigue
   reservada (CA-C10). En la página de confirmación, **comprueba** que se indica que se han
   cancelado 2 citas, con la fecha y la hora de cada una, y que **no** aparece el código de
   historia clínica ni ningún otro dato del paciente (PD-C22, CE-C10).
4. Entra en `/citas/mias` con ese paciente. **Comprueba** que ve las canceladas con el motivo
   «Franja bloqueada del especialista» (CA-C11, RN-C13).
5. Vuelve a `/citas/huecos` de esa fecha. **Comprueba** que los huecos de 9:00 a 11:00 ya no se
   ofrecen (RN-C04).
6. Bloquea una franja de una fecha sin citas. **Comprueba** que se aplica sin cancelar nada
   (CL-C04).
7. Bloquea una franja con un rango de **varios días** (vacaciones). **Comprueba** que se cancelan
   las citas de todos los días del rango en ese tramo, con un solo bloqueo (E-C04, PD-C12).
8. Intenta bloquear una franja mal formada: con la fecha de fin anterior a la de inicio y, después,
   con la hora de fin igual o anterior a la de inicio. **Comprueba** que las dos se rechazan
   indicando el dato incorrecto (CL-C12, PD-C23).
9. Intenta bloquear una franja de ayer y, después, una de **hoy** cuyo tramo horario ya haya
   terminado. **Comprueba** que las dos se rechazan con «No se puede bloquear una franja cuya
   fecha y hora de fin ya han pasado.» (CL-C12, PD-C23).
10. Bloquea una franja de **hoy** que ya haya empezado pero cuya hora de fin aún no haya llegado
    (por ejemplo, de 9:00 a 14:00 si son las 11:00). **Comprueba** que **sí** se acepta (PD-C23).

### E-C05 · Ajustar la duración · CA-C12, CL-C05

1. Con un especialista de consultas de 20 minutos, reserva citas futuras a las 9:00 y a las 9:20.
2. En `/agenda`, cambia su duración a 30 minutos.
3. **Comprueba** que la de 9:00 sigue reservada y la de 9:20 queda «cancelada por el centro» con
   motivo «Cambio de la duración de las consultas» (CA-C12).
4. Consulta los huecos: **comprueba** que la rejilla es ahora de 8 huecos, de 9:00 a 12:30.
5. Cambia la duración a 50 minutos. **Comprueba** que se ofrecen 4 huecos (9:00, 9:50, 10:40 y
   11:30) y que el tiempo restante no forma un hueco parcial (CL-C05).
6. Con un especialista de horario de 9:00 a 13:00 y citas futuras reservadas, intenta cambiar la
   duración a 300 minutos. **Comprueba** que se rechaza con «Con esa duración no cabe ningún hueco
   en el horario del especialista.», que la duración no ha cambiado y que ninguna cita se ha
   cancelado (CL-C11, PD-C21). **Comprueba** también que 240 minutos sí se acepta: cabe un hueco.
7. En la confirmación de un cambio que cancele citas, **comprueba** que aparecen el número de
   citas canceladas y la fecha y la hora de cada una, sin ningún dato del paciente (PD-C22).

### E-C06 · Revisar mis citas · PD-C14

1. En `/citas/mias`, **comprueba** que se listan las citas pasadas y futuras, cada una con su
   estado y, si está cancelada, su motivo.
2. **Comprueba** que una cita cuya hora ya pasó sigue apareciendo como reservada: no existe estado
   «atendida» (PD-C14).
3. Con un paciente sin citas, **comprueba** que se muestra «No tiene ninguna cita.» y no un error.

### Casos límite restantes

| Caso | Cómo comprobarlo | Esperado |
|---|---|---|
| CL-C01 | Consulta huecos de una fecha con todos ocupados o bloqueados | Aviso de sin disponibilidad, sin error |
| CL-C02 | Busca una especialidad que no exista en el centro elegido | Aviso de sin resultados, sin error |
| CL-C03 | Abre la misma página de huecos en dos pestañas y reserva el mismo hueco en las dos | La segunda: «Ese hueco ya no está disponible.» |
| CL-C06 | Consulta huecos en un día en que el especialista no pasa consulta (p. ej. domingo) | Ningún hueco ofrecido |
| CL-C08 | Intenta reprogramar una cita ya cancelada | Se rechaza indicando que ya está cancelada |
| CL-C09 | Identifícate con un código inventado | «No existe ningún paciente con esos datos.», sin crear paciente |
| CL-C10 | Paso 5 de «E-C03 · Cancelar» | Se rechaza indicando que la cita ya ha pasado |
| CL-C11 | Paso 6 de «E-C05 · Ajustar la duración» | Se rechaza; ni cambia la duración ni se cancelan citas |
| CL-C12 | Pasos 8 y 9 de «E-C04 · Bloquear una franja» | Se rechaza; no se registra la franja |

### CA-C13 · No hay gestión de centros, especialidades ni especialistas

1. Recorre `/citas` y `/agenda`. **Comprueba** que no existe ningún formulario ni enlace para
   crear, editar o borrar centros, especialidades o especialistas.
2. Prueba direcciones inventadas como `/agenda/especialistas/nuevo` o `/agenda/centros`.
   **Comprueba** que responden `404` (CA-C13, RN-C01).
3. **Comprueba** que tampoco hay forma de desbloquear una franja ya creada (PD-C13).

### PD-C11 · Las citas pasadas no se tocan

Requiere una cita cuya hora ya haya pasado (o fijar el momento actual en las pruebas
automáticas, que es la vía fiable):

1. Con una cita pasada en estado reservada, bloquea una franja que la cubra y cuya fecha y hora de
   fin **aún no hayan llegado** (por ejemplo, un rango que empiece el día de la cita y acabe
   mañana). Una franja entera en el pasado se rechaza y no sirve para esta comprobación (PD-C23).
2. **Comprueba** que la cita **no** cambia de estado (PD-C11).
3. Repite cambiando la duración de las consultas del especialista. **Comprueba** el mismo
   resultado.

## Persistencia y contenedor · principio V

1. Reserva una cita.
2. `docker compose down` y después `docker compose up`.
3. **Comprueba** que la cita sigue ahí: el fichero SQLite vive en el volumen `datos_pacientes`.
4. `docker compose down -v` borra el volumen y, con él, pacientes y citas.

## Nota de seguridad · D-C16, PD-C02

No hay inicio de sesión ni control de acceso: basta conocer el código de historia clínica de un
paciente para ver y operar con sus citas, y `/agenda` está abierta a cualquiera. Es una limitación
declarada del alcance académico. **No introduzcas datos reales de personas**: una cita con un
especialista revela una sospecha diagnóstica y es dato de salud, categoría especial del artículo 9
del RGPD.
