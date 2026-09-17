# Modelo de datos: Módulo de Registro e Identificación de Pacientes

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md) · **Fecha**: 2026-09-17

## Entidad `paciente`

Una única tabla. El documento de identidad y la cobertura sanitaria son grupos de columnas del
paciente, no entidades con identidad propia (Entidades clave de la especificación).

| Campo | Tipo | Obligatorio | Reglas | Origen |
|---|---|---|---|---|
| `codigo_historia` | texto | Sí (lo asigna el sistema) | Clave primaria. Formato `HC-NNNNNN`. Secuencial desde `HC-000001`. Inmutable: ninguna operación lo actualiza. | RF-02, RN-04, RN-05, RN-06, D-05, D-06 |
| `nombre` | texto | Sí | Recortado de espacios extremos; vacío tras recortar = falta. | RN-01, PD-13 |
| `apellidos` | texto | Sí | Igual que `nombre`. Un único dato de texto. | RN-01, PD-13, Supuestos |
| `fecha_nacimiento` | texto `AAAA-MM-DD` | Sí | Fecha válida no posterior a la fecha actual (hoy se acepta). | RN-01, RN-09, CL-03 |
| `tipo_documento` | texto | Sí | Uno de: `DNI`, `NIE`, `PASAPORTE`. | RN-01 |
| `numero_documento` | texto | Sí | Guardado normalizado (`normalizar_texto`). Vacío tras normalizar = falta. | RN-01, PD-12, PD-13, D-07 |
| `tipo_cobertura` | texto | Sí | Uno de: `MUTUA`, `SIN_COBERTURA`. | RN-01, RN-02 |
| `mutua` | texto | Solo si `tipo_cobertura = MUTUA` | Recortado. Con `SIN_COBERTURA` se guarda nulo. | RN-02, RN-03, PD-13 |
| `numero_poliza` | texto | Solo si `tipo_cobertura = MUTUA` | Recortado. Con `SIN_COBERTURA` se guarda nulo. | RN-02, RN-03, CA-04, CA-05, CL-05 |
| `telefono` | texto | No | Recortado; vacío se guarda nulo. Sin validación de formato. | RN-01, Supuestos |
| `email` | texto | No | Igual que `telefono`. | RN-01, Supuestos |
| `domicilio` | texto | No | Igual que `telefono`. Un único dato de texto. | RN-01, Supuestos |
| `fecha_registro` | texto `AAAA-MM-DD` | Sí (lo asigna el sistema) | Fecha del día en que se registra. No se modifica. | RN-10 |

### Restricciones en la base de datos

- `PRIMARY KEY (codigo_historia)` → unicidad del código (RF-02).
- `UNIQUE (tipo_documento, numero_documento)` → no hay dos pacientes con el mismo documento; como
  el número se guarda normalizado, la comparación es la de PD-09 (RN-07, RN-11, PD-04).
- `CHECK (tipo_documento IN ('DNI', 'NIE', 'PASAPORTE'))` (RN-01).
- `CHECK (tipo_cobertura IN ('MUTUA', 'SIN_COBERTURA'))` (RN-02).
- `CHECK` de coherencia de la cobertura: con `MUTUA`, `mutua` y `numero_poliza` no nulos; con
  `SIN_COBERTURA`, ambos nulos (RN-02, RN-03).

Las restricciones replican en la base de datos las reglas que ya valida el servicio; son la
garantía final ante escrituras simultáneas (PD-04), no una segunda validación con mensajes
propios.

## Normalización (`normalizar_texto`)

Aplicada al número de documento (al guardar y al buscar) y al código introducido en la búsqueda
(D-07):

1. Quitar espacios al principio y al final.
2. Reducir a uno los espacios interiores repetidos.
3. Eliminar tildes.
4. Pasar a mayúsculas.

| Entrada | Resultado | Referencia |
|---|---|---|
| `12345678z` | `12345678Z` | CA-07 |
| `  12345678Z  ` | `12345678Z` | CL-02 |
| `1234  5678Z` | `1234 5678Z` | PD-10 |
| `1234 5678Z` | `1234 5678Z` (no equivale a `12345678Z`) | PD-10 |
| `hc-000042` | `HC-000042` | PD-06 |

## Ciclo de vida

```text
(no existe) ──registrar──▶ REGISTRADO ──modificar──▶ REGISTRADO
```

- **Registrar** (RF-01, RF-02): valida (D-08), comprueba duplicado (RN-07), asigna código y fecha
  de registro. Si falla cualquier paso, no se crea nada ni se consume código (PD-03).
- **Modificar** (RF-06, RN-11): valida igual que el registro (PD-01), comprueba que el documento
  no pertenece a otro paciente (PD-02, PD-09) y actualiza todos los campos salvo
  `codigo_historia` y `fecha_registro`. El último guardado prevalece (PD-14).
- No hay borrado (fuera de alcance): un paciente registrado existe para siempre y su código nunca
  se libera (RN-06).

## Identidad reutilizable por otros módulos del HIS

El resto del HIS (citas, historia clínica, prescripción, facturación) debe referenciar al
paciente únicamente por `codigo_historia`:

- es la clave primaria y no cambia nunca, ni al corregir el documento (CA-09);
- tiene un formato fijo y verificable (`HC-NNNNNN`);
- se puede resolver a la ficha completa con `buscar_por_codigo` (ver
  [contracts/servicio-pacientes.md](contracts/servicio-pacientes.md)).

El documento de identidad **no** sirve como referencia entre módulos, porque puede corregirse
(E-04).

## Ejemplo (datos ficticios)

| Campo | Valor |
|---|---|
| `codigo_historia` | `HC-000001` |
| `nombre` | Lucía |
| `apellidos` | Ferrández Olmo |
| `fecha_nacimiento` | 1987-03-14 |
| `tipo_documento` | DNI |
| `numero_documento` | 00000000T |
| `tipo_cobertura` | MUTUA |
| `mutua` | Mutua Ejemplo Salud |
| `numero_poliza` | POL-0000-0001 |
| `telefono` | 600 000 000 |
| `email` | lucia.ejemplo@example.com |
| `domicilio` | Calle Inventada 1, 00000 Ciudad Ficticia |
| `fecha_registro` | 2026-09-17 |
