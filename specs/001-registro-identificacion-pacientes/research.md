# Investigación (fase 0): Módulo de Registro e Identificación de Pacientes

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Fecha**: 2026-09-17

Cada decisión indica el requisito o principio del que parte. Las decisiones D-01 y D-02 las tomó
el usuario el 2026-09-17; el resto se derivan de la especificación y la constitución.

## D-01 · Tecnología: Python con solo la biblioteca estándar

- **Decisión**: Python 3 sin dependencias externas. Servidor web con `http.server`
  (`ThreadingHTTPServer`), base de datos con `sqlite3`, HTML generado en el servidor y escapado
  con `html.escape`, normalización de tildes con `unicodedata`.
- **Justificación**: la constitución (principio V) exige arrancar en local con un único comando
  y sin servicios externos: `python app.py` funciona sin instalar nada más que Python. El
  principio II pide la opción más simple: no hay gestor de dependencias ni *framework*.
- **Alternativas consideradas**:
  - Python + Flask + SQLite: código web más cómodo, pero exige `pip install` antes del primer
    arranque.
  - Node.js sin dependencias (`node:http` + `node:sqlite`): equivalente, pero `node:sqlite`
    sigue marcado como experimental.
  - Java Spring Boot + H2: más pesado y con más estructura de la necesaria.

## D-02 · Pruebas: una prueba automática por criterio de aceptación y caso límite

- **Decisión**: pruebas con `unittest` (biblioteca estándar), ejecutables con
  `python -m unittest`. Cada método de prueba nombra el CA, CL o PD que verifica
  (p. ej., `test_ca01_primer_codigo_es_hc000001`).
- **Justificación**: CE-05 exige superar CA-01 a CA-13 y CL-01 a CL-05, y la práctica se evalúa
  por la cobertura de los criterios de aceptación. Las pruebas son artefactos de verificación
  trazables, no funcionalidad nueva (principios II y III).
- **Alternativas consideradas**: `pytest` (dependencia externa, descartada por D-01);
  validación solo manual (descartada por el usuario).

## D-03 · Interfaz: aplicación web local con páginas HTML y formularios

- **Decisión**: el administrativo usa el navegador contra `http://localhost:8000`. Páginas
  generadas en el servidor con formularios HTML estándar, sin JavaScript.
- **Justificación**: la especificación habla de «ficha» y «pantalla» (RF-05, CA-12); una página
  web es la interfaz más simple que no exige instalar nada en el puesto. Sin JavaScript no hay
  lógica duplicada entre cliente y servidor.
- **Presentación** (petición del usuario, 2026-09-17): cada página lleva embebida una hoja de
  estilos mínima (`ESTILOS` en `registro_pacientes/web.py`) y la etiqueta `viewport` para
  pantallas estrechas: tipografía del sistema, contenido centrado de ancho limitado, campos y
  botones uniformes y colores sobrios. Sin archivos externos, CDN, JavaScript ni dependencias.
  No cambia rutas, campos, mensajes ni reglas de negocio.
- **Alternativas consideradas**: interfaz de línea de comandos (poco adecuada para un puesto de
  admisión y para «mostrar la ficha»); aplicación de escritorio con `tkinter` (más código de
  interfaz y más difícil de probar automáticamente).

## D-04 · Persistencia: SQLite en un archivo local

- **Decisión**: una base de datos SQLite en `datos/pacientes.db`, creada automáticamente en el
  primer arranque. La carpeta `datos/` se excluye del control de versiones.
- **Justificación**: PD-11 exige conservar pacientes y secuencia entre reinicios. SQLite viene
  con Python, no necesita servidor y ofrece restricciones `UNIQUE` y transacciones, que resuelven
  RN-07 y PD-04 sin código adicional. Excluir `datos/` evita publicar datos introducidos durante
  las pruebas manuales (principio IV).
- **Alternativas consideradas**: archivo JSON (sin transacciones ni unicidad garantizada con
  varios administrativos a la vez); base de datos en memoria (incumple PD-11).

## D-05 · Identidad del paciente: el código de historia clínica es la clave primaria

- **Decisión**: la columna `codigo_historia` (texto con formato `HC-NNNNNN`) es la clave primaria
  de la tabla `paciente`. No existe ningún otro identificador interno.
- **Justificación**: RF-02 y RN-04 a RN-06 definen el código como la identidad única y
  permanente; el enunciado de la práctica pide que esa identidad sea reutilizable por otros
  módulos del HIS (citas, historia clínica, facturación). Usar el propio código como clave evita
  que convivan dos identificadores y es lo que otros módulos guardarían como referencia.
- **Alternativas consideradas**: clave numérica interna autoincremental más código visible
  (dos identificadores para un mismo concepto; descartado por simplicidad).

## D-06 · Asignación secuencial del código

- **Decisión**: dentro de una transacción `BEGIN IMMEDIATE` se lee el mayor código existente, se
  calcula el siguiente y se inserta el paciente. Si el mayor es `HC-999999`, se rechaza el
  registro (CL-04). Si no hay pacientes, el siguiente es `HC-000001` (RN-05, CA-01).
- **Justificación**: `BEGIN IMMEDIATE` bloquea las escrituras concurrentes, así que dos
  administrativos no pueden obtener el mismo código (PD-04). Como no se borran pacientes (fuera de
  alcance) y los registros rechazados no insertan nada, el mayor código más uno nunca reutiliza
  un código y los códigos quedan consecutivos (RN-06, PD-03). El ceroizado a seis dígitos hace que
  el orden alfabético coincida con el numérico.
- **Alternativas consideradas**: tabla de contador separada (un elemento más que mantener sin
  aportar nada mientras no haya borrado); `AUTOINCREMENT` de SQLite (no permite el formato
  `HC-NNNNNN` como clave ni controlar el límite de CL-04 de forma directa).

## D-07 · Normalización de textos y del documento de identidad

- **Decisión**: una única función `normalizar_texto` que (1) quita espacios al principio y al
  final, (2) reduce a uno los espacios interiores repetidos, (3) elimina tildes y (4) pasa a
  mayúsculas. Se aplica:
  - al número de documento antes de guardarlo y antes de compararlo (PD-09, PD-12);
  - al código de historia clínica introducido en la búsqueda (PD-06).
  El resto de datos de texto (nombre, apellidos, mutua, póliza, teléfono, email, domicilio) solo
  se recortan de espacios al principio y al final; un valor que queda vacío se trata como ausente
  (PD-13) y, si es opcional, se guarda vacío (nulo).
- **Justificación**: al guardar el documento ya normalizado, la restricción
  `UNIQUE (tipo_documento, numero_documento)` compara exactamente como exigen RN-07 y PD-09, y la
  búsqueda por documento es una igualdad directa (RN-08, CA-07, CL-02). Los números de DNI, NIE y
  pasaporte no llevan tildes, así que eliminarlas no cambia ningún documento real y mantiene una
  sola regla de normalización (RN-08).
- **Alternativas consideradas**: guardar el documento tal como se teclea y normalizar solo al
  comparar (descartado por el usuario en la aclaración de PD-12); columna adicional con el
  documento normalizado (dato duplicado sin necesidad).

## D-08 · Validación y mensajes

- **Decisión**: la validación de registro y modificación es la misma función (PD-01). Reúne
  todos los errores del formulario y los devuelve juntos, cada uno con el dato concreto
  (CA-03, CA-05, CL-03, PD-07). No se valida el formato del documento, del teléfono ni del email
  (supuesto de la especificación). La fecha de nacimiento debe ser una fecha válida `AAAA-MM-DD`
  no posterior a hoy (RN-09).
- **Justificación**: una sola validación garantiza que registro y modificación aplican las mismas
  reglas; mostrar todos los errores a la vez evita reintentos.
- **Alternativas consideradas**: detenerse en el primer error (obliga a varios intentos para un
  formulario con varios fallos).

## D-09 · Ediciones simultáneas

- **Decisión**: la modificación es una actualización directa de la fila del paciente; el último
  guardado prevalece y no se detectan conflictos (PD-14). La unicidad del documento la sigue
  garantizando la restricción `UNIQUE` (RN-11).
- **Alternativas consideradas**: control de versiones optimista (descartado por el usuario).

## D-10 · Seguridad y normativa aplicable (vinculación con CESI2)

- **Decisión**: dentro del alcance fijado se aplican solo medidas que no añaden funcionalidad:
  todo dato mostrado en HTML se escapa (evita inyección de código en páginas), las consultas SQL
  usan parámetros (evita inyección SQL), el servidor escucha solo en `127.0.0.1`, la base de datos
  local no se versiona y todos los datos de ejemplo y de prueba son ficticios (principio IV).
- **Justificación**: los datos de salud son categoría especial en el RGPD; aunque el inicio de
  sesión y el control de acceso están fuera de alcance por decisión del enunciado, el módulo no
  debe exponer datos más allá del puesto local ni facilitar ataques triviales.
- **Pendiente fuera de este módulo**: control de acceso, registro de accesos y demás medidas del
  RGPD/LOPDGDD y del ENS corresponden a otros módulos o a una versión posterior (fuera de alcance
  según la especificación).
