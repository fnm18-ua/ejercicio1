# Contrato: interfaz web (`registro_pacientes/web.py`)

**Funcionalidad**: [spec.md](../spec.md) · **Servicio**: [servicio-pacientes.md](servicio-pacientes.md)

Servidor local en `http://127.0.0.1:8000`. Páginas HTML en español, codificadas en UTF-8, sin
JavaScript. Todo dato mostrado se escapa (D-10). Los mensajes son los del contrato del servicio.

Existen **exactamente** estas rutas; cualquier otra devuelve `404` con la página
«Página no encontrada».

| # | Método y ruta | Propósito | Trazabilidad |
|---|---|---|---|
| 1 | `GET /` | Inicio: formulario de búsqueda y enlace para registrar | RF-03, RF-04, CA-13 |
| 2 | `GET /buscar` | Buscar y mostrar la ficha | RF-03, RF-04, RF-05 |
| 3 | `GET /pacientes/nuevo` | Formulario de registro | RF-01 |
| 4 | `POST /pacientes` | Registrar | RF-01, RF-02 |
| 5 | `GET /pacientes/<codigo>/editar` | Formulario de modificación | RF-06 |
| 6 | `POST /pacientes/<codigo>/editar` | Guardar la modificación | RF-06 |

No existen rutas para borrar pacientes, listar pacientes, buscar por nombre ni editar el código
de historia clínica (fuera de alcance, CA-12, CA-13).

## 1 · `GET /`

Dos formularios que envían a `GET /buscar`:

- **Por código de historia clínica**: campo `codigo`.
- **Por documento de identidad**: desplegable `tipo_documento` (DNI, NIE, Pasaporte) y campo
  `numero_documento` (PD-08).

No hay ningún campo de búsqueda por nombre (CA-13). Enlace «Registrar paciente» a
`/pacientes/nuevo`.

## 2 · `GET /buscar`

Parámetros: `codigo`, **o bien** `tipo_documento` + `numero_documento`.

| Caso | Estado | Contenido |
|---|---|---|
| Encontrado | `200` | Ficha completa (PD-05): código, nombre, apellidos, fecha de nacimiento, documento, cobertura (mutua y póliza, o «Sin cobertura»), teléfono, email, domicilio (o «—» si falta) y fecha de registro. Enlace «Modificar datos» a la ruta 5. Si llega `aviso=registrado` o `aviso=modificado`, muestra además «Paciente registrado.» o «Datos guardados.». |
| Sin coincidencias | `200` | `No existe ningún paciente con el código <código>.` o `No existe ningún paciente con el documento <TIPO> <número>.` (CL-01) |
| Sin parámetros o vacíos | `200` | `Indica un código de historia clínica o un documento de identidad.` |

## 3 · `GET /pacientes/nuevo`

Formulario con los campos de entrada del servicio: `nombre`, `apellidos`, `fecha_nacimiento`
(`type="date"`), `tipo_documento`, `numero_documento`, `tipo_cobertura` (opciones «Mutua» y
«Sin cobertura»), `mutua`, `numero_poliza`, `telefono`, `email`, `domicilio`. Cada campo tiene su
etiqueta. Los obligatorios se señalan como tales.

## 4 · `POST /pacientes`

Cuerpo `application/x-www-form-urlencoded` con los campos de la ruta 3.

| Resultado del servicio | Estado | Respuesta |
|---|---|---|
| Registrado | `303` | Redirección a `/buscar?codigo=<código>&aviso=registrado` |
| `ErrorValidacion` | `400` | Formulario de registro con los valores introducidos y la lista de errores (CA-03, CA-05, CL-03) |
| `PacienteDuplicado` | `409` | Mensaje de duplicado y ficha del paciente existente con su código (CA-08) |
| `CodigosAgotados` | `409` | Formulario con el mensaje de códigos agotados (CL-04) |

## 5 · `GET /pacientes/<codigo>/editar`

| Caso | Estado | Contenido |
|---|---|---|
| Existe | `200` | Formulario con los mismos campos que la ruta 3, rellenos con los datos actuales. El código de historia clínica y la fecha de registro se muestran como texto, **nunca como campo editable** (CA-12). |
| No existe | `404` | `No existe ningún paciente con el código <código>.` |

## 6 · `POST /pacientes/<codigo>/editar`

Cuerpo con los campos de la ruta 3. Un campo `codigo_historia` en el cuerpo se ignora (CA-12).

| Resultado del servicio | Estado | Respuesta |
|---|---|---|
| Modificado | `303` | Redirección a `/buscar?codigo=<código>&aviso=modificado` (CA-11) |
| `ErrorValidacion` | `400` | Formulario de modificación con los valores introducidos y los errores (PD-01) |
| `PacienteDuplicado` | `409` | Formulario con `El documento <TIPO> <NÚMERO> ya pertenece a otro paciente.` (CA-10) |
| `PacienteNoEncontrado` | `404` | `No existe ningún paciente con el código <código>.` |
