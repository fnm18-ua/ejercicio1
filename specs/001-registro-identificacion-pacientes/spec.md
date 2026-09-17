# Especificación de la funcionalidad: Módulo de Registro e Identificación de Pacientes

**Rama de la funcionalidad**: no se ha creado rama específica (no hay hook de ramas configurado;
se trabaja sobre `master`)

**Creada**: 2026-09-17

**Estado**: Borrador

**Entrada**: Descripción del usuario: «MÓDULO DE REGISTRO E IDENTIFICACIÓN DE PACIENTES»
(enunciado completo con objetivo y contexto de negocio, usuarios, escenarios E-01 a E-05,
requisitos RF-01 a RF-06, reglas RN-01 a RN-11, criterios de aceptación CA-01 a CA-13,
casos límite CL-01 a CL-05 y fuera de alcance).

> **Nota de trazabilidad**: se conservan los identificadores del enunciado (E, RF, RN, CA, CL)
> para que todo elemento del plan, de las tareas y del código pueda rastrearse hasta ellos
> (Constitución, principio III). Los elementos añadidos en esta especificación llevan
> identificadores propios (PD, CE) e indican siempre de qué elemento del enunciado derivan.

## Objetivo y contexto de negocio

Un centro médico de tamaño medio necesita una identidad fiable y única para cada paciente.
Sobre ella se apoya el resto del sistema hospitalario: citas, historia clínica, prescripción y
facturación identifican al paciente por ese mismo dato. Si un paciente se registra dos veces,
su información queda partida entre dos identidades y el resto del sistema deja de ser fiable.

Este módulo resuelve esa pieza: registrar pacientes, asignarles una identidad única y
permanente, localizarlos para reconocer a quien ya existe en lugar de duplicarlo, y mantener
sus datos al día.

**Usuarios**: personal administrativo del centro. Es el único perfil que usa el módulo:
registra a los pacientes en admisión, los localiza cuando vuelven y actualiza sus datos. No hay
inicio de sesión ni distinción de permisos.

## Aclaraciones

### Sesión 2026-09-17

- Q: La búsqueda por documento de identidad, ¿usa solo el número o el tipo y el número? →
  A: Tipo y número (PD-08).
- Q: La comprobación de duplicados, ¿compara el documento normalizado como en RN-08 o
  literalmente? → A: Normalizado (PD-09).
- Q: ¿Qué son «espacios sobrantes»? → A: Los del principio y el final, y los interiores
  repetidos se reducen a uno (PD-10).
- Q: ¿Los pacientes y el contador de códigos se conservan al cerrar y volver a arrancar la
  aplicación? → A: Sí; los datos son persistentes y la secuencia continúa tras reiniciar
  (PD-11).
- Q: ¿Cómo se guarda y se muestra el número de documento tecleado? → A: Normalizado: sin
  espacios extremos, interiores repetidos reducidos a uno y en mayúsculas (PD-12).
- Q: ¿Un dato obligatorio relleno solo con espacios cuenta como dato que falta? → A: Sí; se
  rechaza indicando qué dato falta (PD-13).
- Q: Si dos administrativos modifican a la vez la ficha del mismo paciente, ¿qué pasa al
  guardar? → A: Prevalece el último guardado, sin detección de conflictos (PD-14).

## Escenarios de usuario y pruebas *(obligatorio)*

### Historia de usuario 1 - Registrar un paciente nuevo (Prioridad: P1) · E-01

Llega alguien que nunca ha sido atendido en el centro. El administrativo introduce sus datos y
su cobertura sanitaria. El sistema lo registra y le asigna un código de historia clínica que el
paciente puede apuntar y usar en sus siguientes visitas.

**Por qué esta prioridad**: sin registro no existe identidad del paciente; es la base sobre la
que se apoyan las demás historias y el resto del sistema hospitalario.

**Prueba independiente**: se valida registrando pacientes con distintas combinaciones de datos
y comprobando que se guardan, que reciben un código correcto y que los registros incompletos o
inválidos se rechazan indicando el motivo.

**Escenarios de aceptación**:

1. **Dado** un sistema sin pacientes, **cuando** se registra el primer paciente con todos los
   datos obligatorios, **entonces** su código de historia clínica es exactamente `HC-000001`; y
   **cuando** se registra el siguiente, **entonces** recibe `HC-000002`. *(CA-01)*
2. **Dado** un paciente nuevo sin teléfono, email ni domicilio, **cuando** se registra con el
   resto de datos obligatorios, **entonces** se guarda correctamente y tiene código. *(CA-02)*
3. **Dado** un registro al que le falta cualquier dato obligatorio, **cuando** se intenta
   guardar, **entonces** no se guarda y se indica qué dato falta. *(CA-03)*
4. **Dado** un paciente nuevo con cobertura «sin cobertura», **cuando** se registra,
   **entonces** se guarda correctamente y no tiene número de póliza. *(CA-04)*
5. **Dado** un paciente nuevo con mutua pero sin número de póliza, **cuando** se intenta
   registrar, **entonces** no se guarda y se indica que falta la póliza. *(CA-05)*
6. **Dado** un paciente nuevo con fecha de nacimiento posterior a la fecha actual, **cuando**
   se intenta registrar, **entonces** se rechaza el registro y se indica el motivo. *(CL-03)*

---

### Historia de usuario 2 - Impedir el registro de un duplicado (Prioridad: P2) · E-05

El administrativo registra a alguien que ya existe sin darse cuenta. El sistema lo detecta por
el documento de identidad, no crea el registro y muestra el paciente ya existente.

**Por qué esta prioridad**: evitar que un paciente tenga dos identidades es el objetivo central
del módulo; un duplicado parte su información y deja de ser fiable para el resto del sistema.

**Prueba independiente**: se valida registrando un paciente y volviendo a registrar otro con el
mismo tipo y número de documento, comprobando que no se crea un segundo registro.

**Escenarios de aceptación**:

1. **Dado** un paciente ya registrado con un tipo y número de documento, **cuando** se intenta
   registrar otro paciente con ese mismo tipo y número de documento, **entonces** no se crea un
   registro nuevo, se informa del motivo y se muestra el paciente existente con su código.
   *(CA-08)*
2. **Dado** un paciente registrado con el documento DNI `12345678Z`, **cuando** se intenta
   registrar otro paciente con DNI `12345678z`, **entonces** se detecta como duplicado y no se
   crea el registro. *(CA-08, PD-09)*

---

### Historia de usuario 3 - Localizar y verificar a un paciente que vuelve (Prioridad: P3) · E-02

El administrativo busca por el documento de identidad o por el código de historia clínica. El
sistema muestra la ficha del paciente para verificar que es él, y no se crea un registro nuevo.

**Por qué esta prioridad**: permite reconocer a quien ya existe en lugar de volver a
registrarlo, y es el paso previo a cualquier modificación de datos.

**Prueba independiente**: se valida con pacientes ya registrados, buscándolos por código y por
documento (con variaciones de mayúsculas y espacios) y comprobando que se muestra su ficha
completa, y buscando valores inexistentes.

**Escenarios de aceptación**:

1. **Dado** un paciente registrado con código `HC-000042`, **cuando** se busca ese código,
   **entonces** se devuelve ese paciente y se muestra su ficha completa. *(CA-06)*
2. **Dado** un paciente registrado con el documento DNI `12345678Z`, **cuando** se busca el
   documento DNI `12345678z`, **entonces** se encuentra a ese paciente. *(CA-07, PD-08)*
3. **Dado** un paciente registrado, **cuando** se busca su documento con espacios sobrantes al
   principio o al final o en minúsculas, **entonces** se localiza igualmente. *(CL-02, PD-10)*
4. **Dado** un valor de búsqueda que no corresponde a ningún paciente, **cuando** se busca,
   **entonces** el sistema informa de que no existe ese paciente, sin error. *(CL-01)*
5. **Dado** el buscador del módulo, **cuando** el administrativo va a buscar, **entonces** solo
   puede hacerlo por documento de identidad o por código de historia clínica; no existe
   búsqueda por nombre. *(CA-13)*

---

### Historia de usuario 4 - Actualizar datos que cambian (Prioridad: P4) · E-03

Un paciente ha cambiado de domicilio, teléfono, email o mutua. El administrativo lo localiza y
actualiza esos datos.

**Por qué esta prioridad**: mantiene los datos al día, pero requiere que el paciente ya esté
registrado y pueda localizarse.

**Prueba independiente**: se valida modificando datos de contacto y cobertura de un paciente
registrado y comprobando, al buscarlo de nuevo, que aparecen los valores nuevos.

**Escenarios de aceptación**:

1. **Dado** un paciente registrado, **cuando** se modifica su teléfono, **entonces** al
   buscarlo aparece el teléfono nuevo. *(CA-11)*
2. **Dado** un paciente registrado con mutua y número de póliza, **cuando** se cambia su
   cobertura a «sin cobertura», **entonces** el número de póliza deja de estar presente.
   *(CL-05)*
3. **Dado** un paciente registrado sin teléfono, email o domicilio, **cuando** se rellenan esos
   datos, **entonces** se guardan y aparecen al buscarlo. *(RF-06)*
4. **Dado** cualquier paciente registrado, **cuando** se consulta o modifica su ficha,
   **entonces** no existe ninguna pantalla ni operación que permita editar el código de
   historia clínica. *(CA-12)*

---

### Historia de usuario 5 - Corregir un error en el documento de identidad (Prioridad: P5) · E-04

Al registrar se tecleó mal el número de documento. El administrativo localiza al paciente y lo
corrige, sin que su código de historia clínica cambie.

**Por qué esta prioridad**: corrige errores puntuales de captura; depende de la búsqueda y de
la modificación.

**Prueba independiente**: se valida corrigiendo el documento de un paciente registrado y
comprobando que el código no cambia, y que no se permite asignar un documento de otro paciente.

**Escenarios de aceptación**:

1. **Dado** un paciente registrado, **cuando** se corrige su número de documento, **entonces**
   se guarda con el nuevo valor y su código de historia clínica sigue siendo el mismo.
   *(CA-09)*
2. **Dado** un paciente registrado, **cuando** se corrige su número de documento tecleando
   ` 87654321x `, **entonces** la ficha muestra el documento `87654321X`. *(CA-09, PD-12)*
3. **Dado** dos pacientes registrados, **cuando** se modifica el documento de uno poniéndole el
   tipo y número de documento del otro, **entonces** no se guarda y se informa del motivo.
   *(CA-10)*

---

### Casos límite

- **CL-01** Búsqueda sin coincidencias: el sistema informa de que no existe ese paciente, sin
  error.
- **CL-02** Documento introducido con espacios sobrantes o en minúsculas: se localiza
  igualmente.
- **CL-03** Fecha de nacimiento futura: se rechaza el registro e indica el motivo.
- **CL-04** Agotados los seis dígitos del código (ya asignado `HC-999999`): el sistema no
  repite un código existente y avisa de que no puede registrar.
- **CL-05** Cambiar la cobertura de una mutua a «sin cobertura»: el número de póliza deja de
  estar presente.
- Registro rechazado por cualquier motivo (dato obligatorio ausente, póliza ausente, fecha
  futura, documento duplicado): no consume código de historia clínica *(PD-03)*.
- Modificación que deja vacío un dato obligatorio, indica mutua sin póliza o pone una fecha de
  nacimiento futura: se rechaza igual que en el registro *(PD-01)*.
- Modificación que mantiene el mismo documento del propio paciente: no se considera duplicado
  *(PD-02)*.
- Fecha de nacimiento igual a la fecha actual: se acepta, porque no es posterior *(RN-09)*.
- Reinicio de la aplicación: los pacientes registrados siguen existiendo y el siguiente
  registro recibe el código posterior al último asignado, no `HC-000001` *(PD-11)*.
- Dato obligatorio relleno solo con espacios: se trata como ausente y se rechaza indicando qué
  dato falta *(PD-13)*.
- Dos administrativos modifican a la vez al mismo paciente: prevalece el último guardado, sin
  aviso de conflicto *(PD-14)*.

## Requisitos *(obligatorio)*

### Requisitos funcionales

- **RF-01**: El sistema DEBE permitir registrar un paciente nuevo con sus datos personales, de
  contacto y de cobertura sanitaria.
- **RF-02**: El sistema DEBE asignar automáticamente un código de historia clínica único en el
  momento del registro.
- **RF-03**: El sistema DEBE permitir buscar un paciente por su documento de identidad
  (tipo y número; ver PD-08).
- **RF-04**: El sistema DEBE permitir buscar un paciente por su código de historia clínica.
- **RF-05**: El sistema DEBE mostrar la ficha completa del paciente localizado, para verificar
  su identidad.
- **RF-06**: El sistema DEBE permitir modificar los datos de un paciente ya registrado
  —incluidos el documento de identidad y la cobertura, y rellenando los que quedaron vacíos—
  salvo el código de historia clínica.

### Reglas de negocio

- **RN-01**: Datos del paciente.
  - Obligatorios: nombre, apellidos, fecha de nacimiento, tipo de documento (DNI, NIE o
    pasaporte), número de documento y cobertura sanitaria.
  - Opcionales: teléfono, email y domicilio.
- **RN-02**: La cobertura sanitaria toma uno de dos valores: una mutua junto con su número de
  póliza, o bien «sin cobertura», que significa pago directo del paciente. Con «sin cobertura»
  no se captura número de póliza.
- **RN-03**: Si se indica una mutua, el número de póliza es obligatorio.
- **RN-04**: El código de historia clínica tiene el formato `HC-NNNNNN`: el prefijo `HC-`
  seguido de seis dígitos con ceros a la izquierda.
- **RN-05**: Los códigos se asignan de forma secuencial. El primer paciente registrado recibe
  `HC-000001`.
- **RN-06**: El código es inmutable y nunca se reutiliza. Ninguna operación del sistema permite
  modificarlo.
- **RN-07**: No pueden existir dos pacientes con el mismo tipo y número de documento
  (comparados con la normalización de RN-08; ver PD-09).
- **RN-08**: Las comparaciones de texto en las búsquedas se hacen normalizando: sin distinguir
  mayúsculas y minúsculas, sin tener en cuenta tildes y descartando espacios sobrantes. La
  comparación es del campo completo, nunca de fragmentos. (Alcance de «espacios sobrantes»: ver
  PD-10.)
- **RN-09**: La fecha de nacimiento no puede ser posterior a la fecha actual.
- **RN-10**: El sistema guarda la fecha de registro de cada paciente.
- **RN-11**: Todos los datos del paciente son modificables excepto el código de historia
  clínica. Al modificar el tipo o el número de documento se comprueba la unicidad igual que en
  el registro.

### Precisiones derivadas

Aclaran cómo se aplican los requisitos y reglas anteriores; no añaden capacidades nuevas.

- **PD-01** *(deriva de RN-01, RN-03, RN-09 y RF-06)*: Las reglas de datos obligatorios, de
  póliza obligatoria con mutua y de fecha de nacimiento no futura se aplican también al
  modificar un paciente; una modificación que las incumpla no se guarda e indica el motivo.
- **PD-02** *(deriva de RN-07 y RN-11)*: En la comprobación de unicidad al modificar, el propio
  paciente no cuenta como duplicado de sí mismo.
- **PD-03** *(deriva de RN-05, RN-06 y CA-01)*: Solo un registro que se guarda consume código;
  los registros rechazados no lo consumen, de modo que los códigos asignados son consecutivos.
- **PD-04** *(deriva de RF-02 y RN-07)*: La unicidad del código y del documento se mantiene
  aunque varios administrativos registren o modifiquen pacientes a la vez.
- **PD-05** *(deriva de RF-05 y RN-10)*: La ficha completa muestra el código de historia
  clínica, todos los datos de RN-01, la cobertura sanitaria (mutua y número de póliza, o «sin
  cobertura») y la fecha de registro.
- **PD-06** *(deriva de RF-04 y RN-08)*: La búsqueda por código de historia clínica también se
  normaliza; se exige el código completo (p. ej., `hc-000042` localiza `HC-000042`, pero `42`
  no).
- **PD-07** *(deriva de CA-03, CA-05, CA-08, CA-10, CL-01, CL-03 y CL-04)*: Todos los mensajes
  al usuario están en español e indican el motivo concreto del rechazo o del resultado.
- **PD-08** *(deriva de RF-03 y RN-07; aclaración Q1)*: La búsqueda por documento de identidad
  requiere indicar el tipo (DNI, NIE o pasaporte) y el número; devuelve como máximo un
  paciente.
- **PD-09** *(deriva de RN-07, RN-08 y RN-11; aclaración Q2)*: La comprobación de duplicados,
  tanto al registrar como al modificar, compara el número de documento normalizado según RN-08
  (p. ej., `12345678z` y ` 12345678Z ` son el mismo documento).
- **PD-10** *(deriva de RN-08 y CL-02; aclaración Q3)*: «Descartar espacios sobrantes» significa
  eliminar los espacios del principio y del final y reducir a uno los espacios interiores
  repetidos; un espacio interior simple se conserva (`1234 5678Z` no equivale a `12345678Z`).
- **PD-11** *(deriva de RN-05, RN-06 y RN-10; aclaración de la sesión 2026-09-17)*: Los
  pacientes, sus códigos y fechas de registro se conservan al cerrar y volver a arrancar la
  aplicación; tras un reinicio, el siguiente código continúa la secuencia y nunca repite uno
  ya asignado.
- **PD-12** *(deriva de RN-08, RF-01 y RF-06; aclaración de la sesión 2026-09-17)*: El número
  de documento se guarda y se muestra normalizado, tanto al registrar como al modificar: sin
  espacios al principio ni al final, con los espacios interiores repetidos reducidos a uno y en
  mayúsculas (p. ej., ` 12345678z ` se guarda y se muestra como `12345678Z`).
- **PD-13** *(deriva de RN-01, RN-03, CA-03 y CA-05; aclaración de la sesión 2026-09-17)*: Un
  dato obligatorio (incluidos la mutua y el número de póliza cuando se indica mutua) que
  contenga solo espacios se considera ausente; el registro o la modificación se rechaza
  indicando qué dato falta.
- **PD-14** *(deriva de RF-06, PD-04 y Constitución, principio II; aclaración de la sesión
  2026-09-17)*: Si dos administrativos modifican a la vez al mismo paciente, prevalece el
  último guardado; no se detectan ni se avisan conflictos de edición. Cada guardado sigue
  sometido a las comprobaciones de PD-01 y de unicidad (RN-11).

### Entidades clave

- **Paciente**: persona registrada en el centro. Atributos: código de historia clínica, nombre,
  apellidos, fecha de nacimiento, documento de identidad, cobertura sanitaria, teléfono
  (opcional), email (opcional), domicilio (opcional) y fecha de registro.
- **Código de historia clínica**: identificador único, permanente e inmutable del paciente,
  con formato `HC-NNNNNN`, asignado secuencialmente al registrar. Es el dato por el que el resto
  del sistema hospitalario identifica al paciente.
- **Documento de identidad**: tipo (DNI, NIE o pasaporte) y número, guardado normalizado
  (PD-12). La combinación tipo + número no puede repetirse entre pacientes.
- **Cobertura sanitaria**: o bien una mutua con su número de póliza, o bien «sin cobertura»
  (pago directo del paciente, sin número de póliza).
- **Mutua**: entidad aseguradora o mutua que presta la cobertura sanitaria. Se captura
  únicamente como dato del paciente, sin integración con ella.

## Criterios de éxito *(obligatorio)*

### Resultados medibles

- **CE-01** *(objetivo de negocio; RN-07)*: En ningún momento existen dos pacientes con el
  mismo tipo y número de documento (0 duplicados).
- **CE-02** *(RF-02, RN-04 a RN-06)*: El 100 % de los pacientes registrados tiene un código de
  historia clínica con formato `HC-NNNNNN`, distinto del de cualquier otro paciente, y ningún
  código cambia tras una modificación.
- **CE-03** *(RF-03 a RF-05, RN-08)*: El 100 % de las búsquedas por el código o el documento de
  un paciente registrado lo localiza y muestra su ficha completa, con independencia de
  mayúsculas, tildes y espacios sobrantes; el 100 % de las búsquedas sin coincidencias informa
  de que no existe el paciente sin producir un error.
- **CE-04** *(PD-07)*: El 100 % de las operaciones rechazadas indica al administrativo el motivo
  concreto (dato que falta, póliza que falta, fecha futura, documento ya existente o códigos
  agotados).
- **CE-05** *(sección 6 del enunciado)*: Se superan los 13 criterios de aceptación CA-01 a
  CA-13 y los 5 casos límite CL-01 a CL-05.

## Supuestos

- **Prioridades**: el enunciado no asigna prioridades a los escenarios; se han ordenado
  P1–P5 según su contribución al objetivo de negocio (identidad única) y su dependencia
  funcional (registro → detección de duplicados → búsqueda → modificación → corrección).
- **Sin objetivos de rendimiento**: el enunciado no fija tiempos de respuesta ni volúmenes;
  no se definen métricas de rendimiento para no inventar datos.
- **Sin validación de formato de documentos, teléfono ni email**: el enunciado no exige validar
  la letra de control del DNI/NIE, el formato del pasaporte, del teléfono ni del email. Por el
  principio de alcance mínimo de la constitución no se añaden estas validaciones.
- **Mutua como texto libre**: la mutua se introduce como dato del paciente, sin catálogo de
  entidades, ya que su configuración e integración están fuera de alcance.
- **Campos simples**: apellidos y domicilio se capturan cada uno como un único dato de texto.
- **Duplicado en el registro**: cuando se detecta un duplicado, los datos introducidos no se
  guardan ni se combinan con el paciente existente; la fusión está fuera de alcance.
- **Datos de ejemplo ficticios**: todos los valores de ejemplo de esta especificación
  (`12345678Z`, `HC-000042`, etc.) son inventados (Constitución, principio IV).

### Fuera de alcance

- Los demás módulos del sistema hospitalario: citas, historia clínica, prescripción,
  facturación y notificaciones.
- La configuración de especialidades, centros o permisos.
- Cualquier integración real con aseguradoras o mutuas: la mutua y el número de póliza se
  capturan únicamente como datos del paciente.
- Inicio de sesión y control de acceso por rol.
- El borrado de pacientes.
- La búsqueda por nombre.
- La fusión o el marcado de registros duplicados: el sistema impide crear el duplicado, pero no
  gestiona los que pudieran existir.
