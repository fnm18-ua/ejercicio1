# Contrato: servicio de pacientes (`registro_pacientes/servicio.py`)

**Funcionalidad**: [spec.md](../spec.md) · **Modelo**: [data-model.md](../data-model.md)

Interfaz interna que usa la interfaz web y que ejercitan las pruebas. Es también el punto por el
que otro módulo del HIS reconocería a un paciente (identidad reutilizable). Todas las funciones
reciben la ruta del archivo de base de datos para que las pruebas usen una base temporal.

## Tipos

### `Paciente` (inmutable)

Campos, con los mismos nombres que [data-model.md](../data-model.md): `codigo_historia`,
`nombre`, `apellidos`, `fecha_nacimiento`, `tipo_documento`, `numero_documento`,
`tipo_cobertura`, `mutua`, `numero_poliza`, `telefono`, `email`, `domicilio`,
`fecha_registro`. Los opcionales ausentes valen `None`.

### Datos de entrada (`datos`: diccionario de textos)

Claves: `nombre`, `apellidos`, `fecha_nacimiento` (`AAAA-MM-DD`), `tipo_documento`
(`DNI` | `NIE` | `PASAPORTE`), `numero_documento`, `tipo_cobertura` (`MUTUA` | `SIN_COBERTURA`),
`mutua`, `numero_poliza`, `telefono`, `email`, `domicilio`. Una clave ausente equivale a un
valor vacío. **Cualquier otra clave, incluida `codigo_historia`, se ignora** (RN-06, CA-12).

### Errores

| Error | Cuándo | Contenido | Origen |
|---|---|---|---|
| `ErrorValidacion` | Faltan datos obligatorios, falta mutua o póliza con `MUTUA`, fecha no válida o futura. | `errores`: lista de mensajes en español, uno por problema. | CA-03, CA-05, CL-03, PD-01, PD-13 |
| `PacienteDuplicado` | Ya existe otro paciente con el mismo tipo y número de documento normalizado. | `existente`: el `Paciente` que ya tiene ese documento. | CA-08, CA-10, PD-09 |
| `CodigosAgotados` | Ya se asignó `HC-999999`. | Mensaje en español. | CL-04 |
| `PacienteNoEncontrado` | Se intenta modificar un código que no existe. | Código buscado. | RF-06 |

## Funciones

### `inicializar_base_datos(ruta_bd) -> None`

Crea la tabla `paciente` con sus restricciones si no existe. No borra datos existentes (PD-11).

### `registrar_paciente(ruta_bd, datos) -> Paciente` · RF-01, RF-02

1. Valida `datos` (D-08). Si hay errores → `ErrorValidacion`.
2. En una transacción exclusiva: si existe un paciente con el mismo tipo y número normalizado →
   `PacienteDuplicado` con ese paciente; si el mayor código es `HC-999999` →
   `CodigosAgotados`; en otro caso asigna el siguiente código y la fecha de registro de hoy e
   inserta.
3. Devuelve el `Paciente` guardado.

Si se lanza un error, no se guarda nada ni se consume código (PD-03).

### `buscar_por_codigo(ruta_bd, codigo) -> Paciente | None` · RF-04, RF-05

Normaliza `codigo` (PD-06) y devuelve el paciente con ese código exacto, o `None` (CL-01).

### `buscar_por_documento(ruta_bd, tipo_documento, numero_documento) -> Paciente | None` · RF-03, RF-05

Normaliza `numero_documento` y devuelve el paciente con ese tipo y número, o `None`
(CA-07, CL-01, CL-02, PD-08). Nunca devuelve más de un paciente.

### `modificar_paciente(ruta_bd, codigo, datos) -> Paciente` · RF-06

1. Si no existe el paciente → `PacienteNoEncontrado`.
2. Valida `datos` igual que el registro (PD-01). Si hay errores → `ErrorValidacion`.
3. Si otro paciente (no él mismo, PD-02) tiene el mismo tipo y número normalizado →
   `PacienteDuplicado`.
4. Actualiza todos los campos de `datos`; con `SIN_COBERTURA` deja `mutua` y `numero_poliza`
   nulos (CL-05). Nunca cambia `codigo_historia` ni `fecha_registro` (RN-06, CA-09, CA-12).
5. Devuelve el `Paciente` actualizado. El último guardado prevalece (PD-14).

## Mensajes (español, PD-07)

| Situación | Mensaje |
|---|---|
| Falta un dato obligatorio | `Falta el dato obligatorio: <dato>.` (p. ej., `nombre`, `apellidos`, `fecha de nacimiento`, `tipo de documento`, `número de documento`, `cobertura sanitaria`) |
| Mutua sin nombre | `Falta el nombre de la mutua.` |
| Mutua sin póliza | `Falta el número de póliza de la mutua.` |
| Fecha no válida | `La fecha de nacimiento no es válida.` |
| Fecha futura | `La fecha de nacimiento no puede ser posterior a la fecha actual.` |
| Duplicado al registrar | `Ya existe un paciente con el documento <TIPO> <NÚMERO>: <código>.` |
| Documento de otro paciente al modificar | `El documento <TIPO> <NÚMERO> ya pertenece a otro paciente.` |
| Códigos agotados | `No se puede registrar: se han agotado los códigos de historia clínica.` |
