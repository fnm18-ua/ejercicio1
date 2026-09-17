---

description: "Lista de tareas del Módulo de Registro e Identificación de Pacientes"
---

# Tareas: Módulo de Registro e Identificación de Pacientes

**Entrada**: documentos de diseño en `specs/001-registro-identificacion-pacientes/`

**Requisitos previos**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md),
[data-model.md](data-model.md), [contracts/](contracts/), [quickstart.md](quickstart.md)

**Pruebas**: incluidas. El usuario pidió una prueba automática por CA y CL (research.md, D-02).
Dentro de cada historia, las pruebas se escriben primero y deben fallar antes de implementar.

**Organización**: tareas agrupadas por historia de usuario (US1 a US5 = Historias de usuario 1 a
5 de spec.md), cada una con los requisitos que implementa entre paréntesis.

## Formato: `[ID] [P?] [Historia] Descripción`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin dependencias pendientes).
- **[USn]**: historia de usuario a la que pertenece la tarea.
- Todas las rutas son relativas a la raíz del repositorio.

## Convenciones obligatorias para todas las tareas

- **Idioma (principio I)**: módulos, clases, funciones, variables y mensajes en español, sin
  tildes ni eñes en los identificadores. Solo se admiten en inglés los nombres que impone la
  biblioteca estándar (`do_GET`, `do_POST`, `setUp`, `tearDown`, prefijo `test_`).
- **Trazabilidad (principio III)**: cada módulo, clase, función y método de prueba lleva un
  *docstring* en español que cita los identificadores que implementa o verifica (RF, RN, CA, CL,
  PD). Los métodos de prueba incluyen el identificador en su nombre (p. ej.,
  `test_ca01_primer_codigo_es_hc000001`).
- **Alcance (principio II)**: no se añade nada que no figure en estas tareas: ni rutas, ni
  validaciones de formato, ni borrado, ni listados, ni búsqueda por nombre, ni dependencias
  externas (solo biblioteca estándar de Python).
- **Datos ficticios (principio IV)**: todas las pruebas usan datos inventados, como los de
  `tests/utilidades.py`.
- **Mensajes**: exactamente los de [contracts/servicio-pacientes.md](contracts/servicio-pacientes.md)
  y [contracts/interfaz-web.md](contracts/interfaz-web.md).

---

## Fase 1: Preparación

**Propósito**: estructura del proyecto.

- [X] T001 Crear los paquetes vacíos `registro_pacientes/__init__.py` y `tests/__init__.py`, cada uno solo con un *docstring* en español que describa el paquete (plan.md, «Estructura del proyecto»)
- [X] T002 [P] Añadir a `.gitignore`, conservando su contenido actual, una sección `# Base de datos local (principio IV: no versionar datos introducidos)` con `datos/` y otra `# Archivos generados por Python` con `__pycache__/`

---

## Fase 2: Base común (bloquea todas las historias)

**Propósito**: normalización, esquema, tipos del servicio, esqueleto web, arranque y utilidades de
prueba que usan todas las historias.

**⚠️ CRÍTICO**: ninguna historia puede empezar hasta completar esta fase.

- [X] T003 [P] Implementar `registro_pacientes/normalizacion.py` (RN-08, PD-10, PD-13, D-07) con dos funciones: `recortar(valor)` → devuelve `valor.strip()` o `None` si `valor` es `None` o queda vacío; `normalizar_texto(valor)` → si `valor` es `None` devuelve `""`; si no, (1) quita espacios al principio y al final y reduce a uno los espacios interiores repetidos (`" ".join(valor.split())`), (2) elimina tildes descomponiendo con `unicodedata.normalize("NFD", ...)` y descartando los caracteres de categoría `Mn`, (3) pasa a mayúsculas. Ejemplos que debe cumplir (data-model.md): `12345678z`→`12345678Z`, `  12345678Z  `→`12345678Z`, `1234  5678Z`→`1234 5678Z`, `hc-000042`→`HC-000042`
- [X] T004 [P] Implementar en `registro_pacientes/base_datos.py` (RN-04 a RN-07, RN-10, PD-04, PD-11, D-04) las funciones `conectar(ruta_bd)` → crea la carpeta padre si no existe, abre `sqlite3.connect(ruta_bd, isolation_level=None)` (transacciones explícitas) con `row_factory = sqlite3.Row`; y `crear_esquema(conexion)` → ejecuta exactamente: `CREATE TABLE IF NOT EXISTS paciente (codigo_historia TEXT PRIMARY KEY, nombre TEXT NOT NULL, apellidos TEXT NOT NULL, fecha_nacimiento TEXT NOT NULL, tipo_documento TEXT NOT NULL CHECK (tipo_documento IN ('DNI', 'NIE', 'PASAPORTE')), numero_documento TEXT NOT NULL, tipo_cobertura TEXT NOT NULL CHECK (tipo_cobertura IN ('MUTUA', 'SIN_COBERTURA')), mutua TEXT, numero_poliza TEXT, telefono TEXT, email TEXT, domicilio TEXT, fecha_registro TEXT NOT NULL, UNIQUE (tipo_documento, numero_documento), CHECK ((tipo_cobertura = 'MUTUA' AND mutua IS NOT NULL AND numero_poliza IS NOT NULL) OR (tipo_cobertura = 'SIN_COBERTURA' AND mutua IS NULL AND numero_poliza IS NULL)))`. Añadir también `obtener_por_codigo(conexion, codigo_historia)` y `obtener_por_documento(conexion, tipo_documento, numero_documento)`, que devuelven la fila (`sqlite3.Row`) o `None` usando consultas con parámetros `?`
- [X] T005 Crear `registro_pacientes/servicio.py` con la base del servicio (contracts/servicio-pacientes.md; depende de T003 y T004): constante `TIPOS_DOCUMENTO = ("DNI", "NIE", "PASAPORTE")` y `TIPOS_COBERTURA = ("MUTUA", "SIN_COBERTURA")`; `@dataclass(frozen=True) class Paciente` con los 13 campos en el orden de data-model.md (`codigo_historia`, `nombre`, `apellidos`, `fecha_nacimiento`, `tipo_documento`, `numero_documento`, `tipo_cobertura`, `mutua`, `numero_poliza`, `telefono`, `email`, `domicilio`, `fecha_registro`); excepciones `ErrorValidacion(errores: list[str])`, `PacienteDuplicado(existente: Paciente)`, `CodigosAgotados` (mensaje `No se puede registrar: se han agotado los códigos de historia clínica.`) y `PacienteNoEncontrado(codigo)`; función privada `_fila_a_paciente(fila)`; e `inicializar_base_datos(ruta_bd)`, que conecta, llama a `crear_esquema` y cierra sin borrar datos (PD-11)
- [X] T006 [P] Crear `tests/utilidades.py` (principio IV): función `datos_paciente(**cambios)` que devuelve un diccionario válido y ficticio (`nombre="Lucía"`, `apellidos="Ferrández Olmo"`, `fecha_nacimiento="1987-03-14"`, `tipo_documento="DNI"`, `numero_documento="00000000T"`, `tipo_cobertura="MUTUA"`, `mutua="Mutua Ejemplo Salud"`, `numero_poliza="POL-0000-0001"`, `telefono=""`, `email=""`, `domicilio=""`) sobrescrito con `cambios`; clase `BaseDatosTemporalTestCase(unittest.TestCase)` que en `setUp` crea un `tempfile.TemporaryDirectory`, fija `self.ruta_bd` a un archivo dentro y llama a `servicio.inicializar_base_datos`, y en `tearDown` limpia el directorio; clase `ServidorPruebaTestCase(BaseDatosTemporalTestCase)` que arranca `web.crear_servidor(self.ruta_bd, puerto=0)` en un hilo *daemon*, lo detiene en `tearDown` (`shutdown` + `server_close`) y ofrece `peticion_get(ruta)` y `peticion_post(ruta, campos)` con `http.client.HTTPConnection` (sin seguir redirecciones), que devuelven `(estado, cabeceras, cuerpo)` con el cuerpo decodificado en UTF-8 y el POST codificado como `application/x-www-form-urlencoded`
- [X] T007 Crear el esqueleto de `registro_pacientes/web.py` (contracts/interfaz-web.md; D-03, D-10; depende de T005): función `pagina(titulo, cuerpo)` que genera `<!DOCTYPE html>` con `<html lang="es">`, `<meta charset="utf-8">`, título, enlace de cabecera a `/` y el cuerpo; alias `escapar = html.escape`, que se usa para **todo** dato mostrado; clase `ManejadorPacientes(BaseHTTPRequestHandler)` con `do_GET` y `do_POST` que separan ruta y parámetros con `urllib.parse.urlsplit`/`parse_qs(keep_blank_values=True)` (UTF-8), leen el cuerpo POST según `Content-Length`, y enrutan solo las 6 rutas del contrato (la ruta `/pacientes/<codigo>/editar` con la expresión `^/pacientes/([^/]+)/editar$`); cada ruta todavía no implementada y cualquier otra ruta responde `404` con `pagina("Página no encontrada", ...)`; utilidades `responder_html(estado, contenido)` con `Content-Type: text/html; charset=utf-8` y `redirigir(url)` con estado `303` y cabecera `Location`; y `crear_servidor(ruta_bd, host="127.0.0.1", puerto=8000)` que devuelve un `ThreadingHTTPServer` con el atributo `ruta_bd`
- [X] T008 Crear `app.py` en la raíz (principio V, PD-11; depende de T005 y T007): función `principal()` que calcula `ruta_bd = Path(__file__).resolve().parent / "datos" / "pacientes.db"`, llama a `inicializar_base_datos`, crea el servidor con `crear_servidor`, escribe `Servidor disponible en http://127.0.0.1:8000 (Ctrl+C para detener)` y ejecuta `serve_forever()`; al recibir `KeyboardInterrupt` cierra el servidor y escribe `Servidor detenido.`; bloque `if __name__ == "__main__": principal()`

**Punto de control**: `python app.py` arranca y cualquier ruta responde 404; `python -m unittest` se ejecuta sin pruebas fallidas.

---

## Fase 3: Historia de usuario 1 - Registrar un paciente nuevo (Prioridad: P1) 🎯 MVP

**Objetivo**: registrar un paciente con datos personales, de contacto y cobertura, asignarle el
código `HC-NNNNNN` y mostrar su ficha con el código (E-01; RF-01, RF-02).

**Prueba independiente**: registrar pacientes con distintas combinaciones de datos y comprobar
que se guardan con código correcto y que los registros incompletos o inválidos se rechazan
indicando el motivo.

### Pruebas de la historia 1 (escribir primero; deben fallar)

- [X] T009 [P] [US1] Crear `tests/test_registro.py` con clase `PruebasRegistro(BaseDatosTemporalTestCase)` y los métodos: `test_ca01_primer_codigo_es_hc000001_y_siguiente_hc000002`; `test_ca02_sin_telefono_email_ni_domicilio_se_guarda` (opcionales vacíos → `None` y tiene código); `test_ca03_falta_dato_obligatorio_no_se_guarda` (con `subTest` para cada uno de `nombre`, `apellidos`, `fecha_nacimiento`, `tipo_documento`, `numero_documento`, `tipo_cobertura` vacíos: lanza `ErrorValidacion` cuyo `errores` contiene `Falta el dato obligatorio: <dato>.` con el nombre del contrato, y la tabla sigue vacía); `test_ca04_sin_cobertura_no_tiene_poliza` (aunque se envíen `mutua` y `numero_poliza`, se guardan `None`); `test_ca05_mutua_sin_poliza_no_se_guarda` (mensaje `Falta el número de póliza de la mutua.`); `test_rn03_mutua_sin_nombre_no_se_guarda` (mensaje `Falta el nombre de la mutua.`); `test_cl03_fecha_nacimiento_futura_se_rechaza` (mañana con `date.today() + timedelta(days=1)`; mensaje `La fecha de nacimiento no puede ser posterior a la fecha actual.`); `test_rn09_fecha_nacimiento_hoy_se_acepta`; `test_d08_fecha_no_valida_se_rechaza` (`"1987-13-45"`; mensaje `La fecha de nacimiento no es válida.`); `test_ca03_varios_errores_se_indican_juntos`; `test_pd13_dato_obligatorio_solo_espacios_es_falta`; `test_rn10_guarda_fecha_de_registro_de_hoy`; `test_pd03_registro_rechazado_no_consume_codigo`; `test_cl04_codigos_agotados` (insertar con SQL directo una fila válida con `HC-999999`; registrar lanza `CodigosAgotados` y solo existe esa fila); `test_pd04_registros_simultaneos_reciben_codigos_distintos` (10 hilos con documentos distintos → 10 códigos distintos `HC-000001`..`HC-000010`); `test_pd11_secuencia_continua_tras_reabrir` (registrar, volver a llamar a `inicializar_base_datos` sobre la misma ruta, registrar otro → `HC-000002`); `test_ca12_codigo_en_datos_se_ignora_al_registrar` (`codigo_historia="HC-000500"` en `datos` → recibe `HC-000001`)
- [X] T010 [P] [US1] Crear `tests/test_web.py` con clase `PruebasWebRegistro(ServidorPruebaTestCase)` y los métodos: `test_rf01_formulario_registro_tiene_todos_los_campos` (`GET /pacientes/nuevo` → 200 y el HTML contiene `name="<campo>"` para los 11 campos de entrada del contrato); `test_rf02_registro_redirige_a_ficha_con_codigo` (`POST /pacientes` válido → 303 con `Location: /buscar?codigo=HC-000001&aviso=registrado`; seguir la redirección → 200 con `HC-000001` y `Paciente registrado.`); `test_ca03_registro_invalido_muestra_errores_y_conserva_valores` (sin nombre → 400, contiene `Falta el dato obligatorio: nombre.` y el apellido introducido); `test_cl04_codigos_agotados_responde_409`; `test_d10_datos_se_escapan_en_html` (apellidos `<b>Olmo</b>` → la ficha contiene `&lt;b&gt;Olmo&lt;/b&gt;` y no `<b>Olmo</b>`); `test_inicio_enlaza_registro` (`GET /` → 200 con enlace a `/pacientes/nuevo`); `test_ruta_desconocida_responde_404` (`GET /pacientes` → 404 con `Página no encontrada`)

### Implementación de la historia 1

- [X] T011 [US1] Añadir a `registro_pacientes/base_datos.py` (RN-05, CL-04): `obtener_mayor_codigo(conexion)` → `SELECT MAX(codigo_historia) FROM paciente` (devuelve texto o `None`) e `insertar_paciente(conexion, valores)` → `INSERT` parametrizado con los 13 campos de `valores`
- [X] T012 [US1] Añadir a `registro_pacientes/servicio.py` la función `validar_datos(datos)` (RN-01, RN-02, RN-03, RN-09, PD-01, PD-13, D-08), usada por registro y modificación, que ignora cualquier clave no listada (incluida `codigo_historia`), reúne **todos** los errores y, si hay alguno, lanza `ErrorValidacion`; si no, devuelve el diccionario limpio. Reglas en este orden: `nombre` y `apellidos` con `recortar` (si `None` → `Falta el dato obligatorio: nombre.` / `... apellidos.`); `fecha_nacimiento` recortada (vacía → `Falta el dato obligatorio: fecha de nacimiento.`; no convertible con `date.fromisoformat` → `La fecha de nacimiento no es válida.`; posterior a `date.today()` → `La fecha de nacimiento no puede ser posterior a la fecha actual.`); `tipo_documento` recortado y en mayúsculas debe estar en `TIPOS_DOCUMENTO` (si no → `Falta el dato obligatorio: tipo de documento.`); `numero_documento` con `normalizar_texto` (vacío → `Falta el dato obligatorio: número de documento.`); `tipo_cobertura` recortado debe estar en `TIPOS_COBERTURA` (si no → `Falta el dato obligatorio: cobertura sanitaria.`); si es `MUTUA`: `mutua` con `recortar` (`None` → `Falta el nombre de la mutua.`) y `numero_poliza` con `recortar` (`None` → `Falta el número de póliza de la mutua.`); si es `SIN_COBERTURA`: `mutua` y `numero_poliza` = `None` (RN-02); `telefono`, `email` y `domicilio` con `recortar`, sin validar formato. La fecha se devuelve en formato `AAAA-MM-DD`
- [X] T013 [US1] Añadir a `registro_pacientes/servicio.py` `registrar_paciente(ruta_bd, datos)` (RF-01, RF-02, RN-04, RN-05, RN-06, RN-10, PD-03, PD-04, CL-04, D-06): llama a `validar_datos`; abre conexión; ejecuta `BEGIN IMMEDIATE`; obtiene el mayor código; si es `HC-999999` hace `ROLLBACK` y lanza `CodigosAgotados`; calcula el siguiente como `f"HC-{numero + 1:06d}"` (o `HC-000001` si no hay pacientes); inserta con `fecha_registro = date.today().isoformat()`; `COMMIT`; ante cualquier excepción hace `ROLLBACK` y la relanza; cierra la conexión y devuelve el `Paciente`
- [X] T014 [US1] Añadir a `registro_pacientes/servicio.py` `buscar_por_codigo(ruta_bd, codigo)` (RF-04, PD-06): aplica `normalizar_texto` a `codigo` y devuelve el `Paciente` con ese código exacto o `None` (necesaria para mostrar la ficha tras registrar, E-01)
- [X] T015 [US1] Implementar en `registro_pacientes/web.py` (RF-01, RF-05, PD-05, contracts/interfaz-web.md rutas 1, 2 y 3): `html_ficha(paciente)` que muestra código de historia clínica, nombre, apellidos, fecha de nacimiento, documento (`<tipo> <número>`, con «Pasaporte» para `PASAPORTE`), cobertura (`Mutua: <mutua> · Póliza: <póliza>` o `Sin cobertura`), teléfono, email, domicilio (`—` si faltan) y fecha de registro, todo escapado; `formulario_paciente(accion, valores, errores, titulo, paciente=None)` con los 11 campos, cada uno con `<label>`, obligatorios señalados, `fecha_nacimiento` con `type="date"`, `tipo_documento` como `<select>` (DNI, NIE, Pasaporte) y `tipo_cobertura` como botones de opción («Mutua», «Sin cobertura»), valores rellenos y escapados y la lista de errores arriba; `GET /` con un enlace «Registrar paciente» a `/pacientes/nuevo`; `GET /pacientes/nuevo` → 200 con el formulario vacío que envía a `POST /pacientes`; y `GET /buscar` con parámetro `codigo`: si existe → 200 con `html_ficha` y, si `aviso=registrado`, el texto `Paciente registrado.`; si no existe → 200 con `No existe ningún paciente con el código <código>.`
- [X] T016 [US1] Implementar en `registro_pacientes/web.py` `POST /pacientes` (RF-01, RF-02, contracts/interfaz-web.md ruta 4): llama a `registrar_paciente`; éxito → `redirigir("/buscar?codigo=<código>&aviso=registrado")`; `ErrorValidacion` → 400 con el formulario, los valores introducidos y los errores; `CodigosAgotados` → 409 con el formulario y su mensaje

**Punto de control**: T009 y T010 pasan; en el navegador se registra un paciente y se ve su ficha con `HC-000001`.

---

## Fase 4: Historia de usuario 2 - Impedir el registro de un duplicado (Prioridad: P2)

**Objetivo**: detectar al registrar un documento ya existente, no crear el registro y mostrar el
paciente existente con su código (E-05; RN-07, CA-08).

**Prueba independiente**: registrar un paciente y volver a registrar otro con el mismo tipo y
número de documento (también en minúsculas o con espacios), comprobando que no se crea un segundo
registro.

### Pruebas de la historia 2 (escribir primero; deben fallar)

- [X] T017 [P] [US2] Crear `tests/test_duplicados.py` con clase `PruebasDuplicados(BaseDatosTemporalTestCase)` y los métodos: `test_ca08_duplicado_no_crea_registro_y_devuelve_existente` (segundo registro con DNI `00000000T` lanza `PacienteDuplicado` con `existente.codigo_historia == "HC-000001"`; sigue habiendo un solo paciente); `test_pd09_duplicado_con_documento_normalizado` (segundo registro con `" 00000000t "` también se detecta); `test_rn07_mismo_numero_distinto_tipo_se_permite` (mismo número con `PASAPORTE` → se registra como `HC-000002`); `test_pd03_duplicado_no_consume_codigo` (tras el duplicado, un registro distinto recibe `HC-000002`)
- [X] T018 [P] [US2] Añadir a `tests/test_web.py` la clase `PruebasWebDuplicados(ServidorPruebaTestCase)` con `test_ca08_registro_duplicado_responde_409_con_paciente_existente` (segundo `POST /pacientes` con el mismo documento → 409, contiene `Ya existe un paciente con el documento DNI 00000000T: HC-000001.` y la ficha del paciente existente)

### Implementación de la historia 2

- [X] T019 [US2] Modificar `registrar_paciente` en `registro_pacientes/servicio.py` (RN-07, PD-04, PD-09, CA-08): dentro de la transacción `BEGIN IMMEDIATE` y **antes** de calcular el código, buscar con `obtener_por_documento` el tipo y número ya normalizados; si existe, `ROLLBACK` y lanzar `PacienteDuplicado(existente)`; además, capturar `sqlite3.IntegrityError` en la inserción, hacer `ROLLBACK`, volver a leer el paciente con ese documento y lanzar `PacienteDuplicado`
- [X] T020 [US2] Añadir a `POST /pacientes` en `registro_pacientes/web.py` el caso `PacienteDuplicado` (CA-08, contracts/interfaz-web.md ruta 4): 409 con el mensaje `Ya existe un paciente con el documento <TIPO> <NÚMERO>: <código>.` seguido de `html_ficha(existente)`

**Punto de control**: T017 y T018 pasan; las pruebas de US1 siguen pasando.

---

## Fase 5: Historia de usuario 3 - Localizar y verificar a un paciente que vuelve (Prioridad: P3)

**Objetivo**: buscar por código de historia clínica o por tipo y número de documento y mostrar la
ficha completa para verificar la identidad; sin búsqueda por nombre (E-02; RF-03, RF-04, RF-05).

**Prueba independiente**: con pacientes registrados, buscarlos por código y por documento (con
mayúsculas, minúsculas y espacios), comprobar la ficha completa y buscar valores inexistentes.

### Pruebas de la historia 3 (escribir primero; deben fallar)

- [X] T021 [P] [US3] Crear `tests/test_busqueda.py` con clase `PruebasBusqueda(BaseDatosTemporalTestCase)` y los métodos: `test_ca06_buscar_codigo_hc000042_devuelve_ese_paciente` (registrar 42 pacientes con documentos distintos `f"{i:08d}A"`; `buscar_por_codigo("HC-000042")` devuelve el 42.º con todos sus campos); `test_ca07_documento_en_minusculas_encuentra_paciente` (registrado `12345678Z`, buscar DNI `12345678z`); `test_cl02_documento_con_espacios_extremos_se_localiza` (`"  12345678Z  "`); `test_pd10_espacios_interiores_repetidos_se_reducen` (registrado `"1234 5678Z"`, buscar `"1234   5678Z"` lo encuentra); `test_pd10_espacio_interior_no_equivale_a_sin_espacio` (registrado `12345678Z`, buscar `"1234 5678Z"` → `None`); `test_pd06_codigo_en_minusculas_se_localiza` (`"hc-000001"`); `test_pd06_fragmento_de_codigo_no_se_localiza` (`"000001"` y `"1"` → `None`); `test_pd08_documento_con_otro_tipo_no_se_localiza` (registrado DNI, buscar NIE con el mismo número → `None`); `test_cl01_sin_coincidencias_devuelve_none` (código `HC-000999` y documento inexistente, sin excepciones)
- [X] T022 [P] [US3] Añadir a `tests/test_web.py` la clase `PruebasWebBusqueda(ServidorPruebaTestCase)` con: `test_ca13_inicio_solo_busca_por_codigo_o_documento` (`GET /` contiene `name="codigo"`, `name="tipo_documento"` y `name="numero_documento"` y no contiene `name="nombre"` ni `name="apellidos"`); `test_pd05_ficha_completa` (`GET /buscar?codigo=HC-000001` → 200 con código, nombre, apellidos, fecha de nacimiento, documento, mutua, póliza, `—` en opcionales vacíos y fecha de registro); `test_ca07_buscar_por_documento_en_web` (`GET /buscar?tipo_documento=DNI&numero_documento=00000000t` → 200 con la ficha); `test_cl01_sin_coincidencias_responde_200_con_mensaje` (código y documento inexistentes → 200 con `No existe ningún paciente con el código HC-000999.` y `No existe ningún paciente con el documento DNI 99999999R.`); `test_buscar_sin_parametros_pide_criterio` (`GET /buscar` → 200 con `Indica un código de historia clínica o un documento de identidad.`)

### Implementación de la historia 3

- [X] T023 [US3] Añadir a `registro_pacientes/servicio.py` `buscar_por_documento(ruta_bd, tipo_documento, numero_documento)` (RF-03, RN-08, PD-08, CA-07, CL-02): recorta y pasa a mayúsculas el tipo, aplica `normalizar_texto` al número y devuelve el `Paciente` de `obtener_por_documento` o `None`; si el tipo no está en `TIPOS_DOCUMENTO` o el número queda vacío, devuelve `None`
- [X] T024 [US3] Completar en `registro_pacientes/web.py` (RF-03, RF-04, CA-13, CL-01, contracts/interfaz-web.md rutas 1 y 2): `GET /` con dos formularios `GET /buscar` —uno con el campo `codigo` y otro con el `<select>` `tipo_documento` (DNI, NIE, Pasaporte) y el campo `numero_documento`—, con etiquetas y sin ningún campo de nombre, más el enlace a registrar; `GET /buscar` con `codigo` no vacío → búsqueda por código (ya implementada); con `numero_documento` no vacío → `buscar_por_documento` y, si no hay resultado, 200 con `No existe ningún paciente con el documento <TIPO> <número>.`; sin parámetros o vacíos → 200 con `Indica un código de historia clínica o un documento de identidad.`

**Punto de control**: T021 y T022 pasan; las pruebas de US1 y US2 siguen pasando.

---

## Fase 6: Historia de usuario 4 - Actualizar datos que cambian (Prioridad: P4)

**Objetivo**: modificar datos de contacto, cobertura y cualquier otro dato salvo el código, con
las mismas validaciones que el registro (E-03; RF-06, RN-11, PD-01).

**Prueba independiente**: modificar teléfono, cobertura y datos vacíos de un paciente registrado y
comprobar al buscarlo que aparecen los valores nuevos.

### Pruebas de la historia 4 (escribir primero; deben fallar)

- [X] T025 [P] [US4] Crear `tests/test_modificacion.py` con clase `PruebasModificacion(BaseDatosTemporalTestCase)` y los métodos: `test_ca11_telefono_modificado_aparece_al_buscar` (`telefono="600 000 000"`); `test_cl05_cambiar_a_sin_cobertura_elimina_poliza` (`mutua` y `numero_poliza` quedan `None`); `test_rn03_cambiar_a_mutua_exige_poliza` (paciente sin cobertura pasa a `MUTUA` sin póliza → `ErrorValidacion`); `test_rf06_rellenar_datos_opcionales_vacios` (teléfono, email y domicilio vacíos pasan a tener valor); `test_pd01_modificacion_valida_igual_que_registro` (con `subTest`: nombre vacío, fecha futura → `ErrorValidacion` con el mensaje del contrato y los datos guardados no cambian); `test_ca12_modificar_no_cambia_codigo_ni_fecha_registro` (`codigo_historia="HC-000999"` en `datos` se ignora; código y `fecha_registro` iguales); `test_rf06_modificar_paciente_inexistente` (`HC-000999` → `PacienteNoEncontrado`)
- [X] T026 [P] [US4] Añadir a `tests/test_web.py` la clase `PruebasWebModificacion(ServidorPruebaTestCase)` con: `test_ca12_formulario_edicion_no_permite_editar_codigo` (`GET /pacientes/HC-000001/editar` → 200, contiene `HC-000001` como texto, los valores actuales y **no** contiene `name="codigo_historia"`); `test_ca12_codigo_enviado_en_formulario_se_ignora` (POST con `codigo_historia=HC-000500` → el paciente conserva `HC-000001`); `test_ca11_modificacion_redirige_a_ficha` (POST válido → 303 a `/buscar?codigo=HC-000001&aviso=modificado`; la ficha muestra el teléfono nuevo y `Datos guardados.`); `test_pd01_modificacion_invalida_responde_400`; `test_rf06_editar_paciente_inexistente_responde_404` (GET y POST sobre `HC-000999`); `test_rf06_ficha_enlaza_modificacion` (la ficha contiene el enlace a `/pacientes/HC-000001/editar`)

### Implementación de la historia 4

- [X] T027 [US4] Añadir a `registro_pacientes/base_datos.py` `actualizar_paciente(conexion, codigo_historia, valores)` (RF-06, RN-06, PD-14): `UPDATE paciente SET` solo de los 11 campos editables (`nombre`, `apellidos`, `fecha_nacimiento`, `tipo_documento`, `numero_documento`, `tipo_cobertura`, `mutua`, `numero_poliza`, `telefono`, `email`, `domicilio`) `WHERE codigo_historia = ?`, con parámetros; nunca incluye `codigo_historia` ni `fecha_registro` en el `SET`
- [X] T028 [US4] Añadir a `registro_pacientes/servicio.py` `modificar_paciente(ruta_bd, codigo, datos)` (RF-06, RN-11, PD-01, PD-14): normaliza `codigo`; si no existe → `PacienteNoEncontrado`; valida con `validar_datos`; actualiza con `actualizar_paciente` (el último guardado prevalece, sin detección de conflictos) y devuelve el `Paciente` releído
- [X] T029 [US4] Implementar en `registro_pacientes/web.py` (RF-06, CA-12, contracts/interfaz-web.md rutas 2, 5 y 6): enlace «Modificar datos» a `/pacientes/<código>/editar` en `html_ficha`; aviso `Datos guardados.` en `GET /buscar` cuando `aviso=modificado`; `GET /pacientes/<codigo>/editar` → 200 con `formulario_paciente` relleno que envía a la misma ruta y muestra código de historia clínica y fecha de registro **solo como texto** (sin campo), o 404 con `No existe ningún paciente con el código <código>.`; `POST /pacientes/<codigo>/editar` → `modificar_paciente`; éxito → `redirigir("/buscar?codigo=<código>&aviso=modificado")`; `ErrorValidacion` → 400 con formulario, valores y errores; `PacienteNoEncontrado` → 404 con el mensaje anterior

**Punto de control**: T025 y T026 pasan; las pruebas de US1 a US3 siguen pasando.

---

## Fase 7: Historia de usuario 5 - Corregir un error en el documento de identidad (Prioridad: P5)

**Objetivo**: corregir el documento de un paciente sin cambiar su código y sin permitir que tome
el documento de otro paciente (E-04; RN-11, CA-09, CA-10).

**Prueba independiente**: corregir el documento de un paciente registrado, comprobar que el código
no cambia y que no se permite asignar el documento de otro paciente.

### Pruebas de la historia 5 (escribir primero; deben fallar)

- [X] T030 [P] [US5] Añadir a `tests/test_modificacion.py` la clase `PruebasCorreccionDocumento(BaseDatosTemporalTestCase)` con: `test_ca09_corregir_documento_mantiene_codigo`; `test_pd12_documento_corregido_se_guarda_normalizado` (`" 87654321x "` → `87654321X`); `test_ca10_documento_de_otro_paciente_no_se_guarda` (lanza `PacienteDuplicado`; los datos del paciente modificado no cambian); `test_pd09_documento_de_otro_paciente_normalizado_se_detecta` (`"00000000t"`); `test_pd02_mantener_su_propio_documento_no_es_duplicado`
- [X] T031 [P] [US5] Añadir a `tests/test_web.py` la clase `PruebasWebCorreccionDocumento(ServidorPruebaTestCase)` con `test_ca10_documento_de_otro_paciente_responde_409` (POST de edición con el documento de otro paciente → 409 con `El documento DNI 00000000T ya pertenece a otro paciente.`)

### Implementación de la historia 5

- [X] T032 [US5] Modificar `modificar_paciente` en `registro_pacientes/servicio.py` (RN-11, PD-02, PD-09, CA-10): tras validar, dentro de `BEGIN IMMEDIATE`, buscar con `obtener_por_documento` el tipo y número normalizados; si existe y su `codigo_historia` es distinto del paciente modificado → `ROLLBACK` y `PacienteDuplicado(existente)`; capturar también `sqlite3.IntegrityError` en la actualización con `ROLLBACK` y `PacienteDuplicado`; `COMMIT` al terminar
- [X] T033 [US5] Añadir a `POST /pacientes/<codigo>/editar` en `registro_pacientes/web.py` el caso `PacienteDuplicado` (CA-10, contracts/interfaz-web.md ruta 6): 409 con el formulario, los valores introducidos y el error `El documento <TIPO> <NÚMERO> ya pertenece a otro paciente.` (sin mostrar los datos del otro paciente)

**Punto de control**: T030 y T031 pasan; todas las pruebas pasan.

---

## Fase 8: Cierre y aspectos transversales

**Propósito**: documentación de uso y validación final.

- [X] T034 [P] Crear `README.md` en la raíz, en español (principios I, IV y V): qué es el módulo (resumen de spec.md), requisitos (Python 3.10+), arranque con `python app.py`, pruebas con `python -m unittest`, enlaces a `specs/001-registro-identificacion-pacientes/` (spec, plan, tasks, quickstart) y aviso de que todos los datos de ejemplo son ficticios
- [X] T035 Revisar el código de `app.py`, `registro_pacientes/` y `tests/` contra las «Convenciones obligatorias» (principios I, II y III): identificadores sin tildes ni eñes, *docstrings* con identificadores de requisitos, solo las 6 rutas del contrato, ninguna dependencia externa, ningún dato real; corregir lo que no cumpla
- [X] T036 Ejecutar `python -m unittest` desde la raíz sobre `tests/` y confirmar que todas las pruebas pasan (CE-05)
- [X] T037 Seguir los 17 pasos de validación manual de `specs/001-registro-identificacion-pacientes/quickstart.md` con la base de datos vacía y anotar cualquier discrepancia (CE-01 a CE-05)

---

## Dependencias y orden de ejecución

### Dependencias entre fases

- **Preparación (fase 1)**: sin dependencias.
- **Base común (fase 2)**: depende de la fase 1; bloquea todas las historias.
- **US1 (fase 3)**: depende de la fase 2.
- **US2 (fase 4)**: depende de US1 (amplía `registrar_paciente` y `POST /pacientes`).
- **US3 (fase 5)**: depende de US1 (usa `buscar_por_codigo`, `html_ficha` y `GET /buscar`); no depende de US2.
- **US4 (fase 6)**: depende de US1 (usa `validar_datos`, `formulario_paciente` y la ficha); no depende de US2 ni de US3.
- **US5 (fase 7)**: depende de US4 (amplía `modificar_paciente` y la ruta de edición).
- **Cierre (fase 8)**: depende de todas las historias.

```text
Fase 1 → Fase 2 → US1 ─┬→ US2
                       ├→ US3
                       └→ US4 → US5
                                   └→ Fase 8 (tras US2, US3 y US5)
```

### Dentro de cada historia

- Las pruebas se escriben primero y deben fallar.
- `base_datos.py` → `servicio.py` → `web.py`.
- La historia se completa (punto de control) antes de pasar a la siguiente.

### Oportunidades de paralelismo

- Fase 1: T002 en paralelo con T001.
- Fase 2: T003, T004 y T006 en paralelo; después T005 → T007 → T008.
- En cada historia, las dos tareas de prueba van a archivos distintos y pueden hacerse en paralelo (T009/T010, T017/T018, T021/T022, T025/T026, T030/T031).
- Tras US1, US2, US3 y US4 tocan funciones distintas, pero comparten `servicio.py`, `web.py` y `tests/test_web.py`; por eso sus tareas de implementación no se marcan [P] entre historias.
- Fase 8: T034 en paralelo con T035.

---

## Ejemplo de paralelismo: historia de usuario 1

```text
# Pruebas de US1 a la vez:
Tarea: "T009 Crear tests/test_registro.py con PruebasRegistro"
Tarea: "T010 Crear tests/test_web.py con PruebasWebRegistro"

# Base común a la vez:
Tarea: "T003 Implementar registro_pacientes/normalizacion.py"
Tarea: "T004 Implementar esquema y consultas en registro_pacientes/base_datos.py"
Tarea: "T006 Crear tests/utilidades.py"
```

---

## Estrategia de implementación

### Primero el MVP (solo historia 1)

1. Fase 1: Preparación.
2. Fase 2: Base común.
3. Fase 3: US1.
4. **Parar y validar**: pasos 1 a 5 de quickstart.md y `python -m unittest`.

### Entrega incremental

1. Preparación + base común → aplicación arrancable.
2. US1 → registro con código (MVP).
3. US2 → identidad única garantizada frente a duplicados.
4. US3 → búsqueda y verificación de pacientes que vuelven.
5. US4 → actualización de datos.
6. US5 → corrección de documento sin perder la identidad.
7. Cierre → README, revisión de principios y validación completa.

---

## Notas

- [P] = archivos distintos y sin dependencias pendientes.
- La etiqueta [USn] traza la tarea a su historia; los identificadores entre paréntesis la trazan a RF, RN, CA, CL o PD.
- Hacer un commit al terminar cada tarea o grupo lógico.
- Si durante la implementación aparece una ambigüedad no resuelta en spec.md, se pregunta antes de decidir (principio III).
