# Plan de implementación: Módulo de Registro e Identificación de Pacientes

**Rama**: `001-registro-identificacion-pacientes` (carpeta de la funcionalidad; se trabaja sobre
`master`) | **Fecha**: 2026-09-17 | **Especificación**: [spec.md](spec.md)

**Entrada**: especificación de la funcionalidad en
`specs/001-registro-identificacion-pacientes/spec.md`

## Resumen

El módulo registra pacientes, les asigna un código de historia clínica único, secuencial e
inmutable (`HC-NNNNNN`), permite localizarlos por código o por documento de identidad para
verificar su identidad sin duplicarlos, y permite modificar sus datos salvo el código
(RF-01 a RF-06).

Enfoque técnico ([research.md](research.md)): aplicación web local escrita en Python usando solo
la biblioteca estándar (`http.server` + `sqlite3`), con páginas HTML generadas en el servidor y
persistencia en un archivo SQLite. Se arranca con `python app.py`. El código de historia clínica
es la clave primaria y la identidad que reutilizarían los demás módulos del HIS. Las reglas de
negocio se concentran en un servicio que ejercitan tanto la interfaz web como las pruebas
automáticas (una por CA y CL).

## Contexto técnico

**Lenguaje/Versión**: Python 3.10 o superior (entorno de desarrollo: Python 3.14.0) — D-01

**Dependencias principales**: ninguna externa; biblioteca estándar: `http.server`, `sqlite3`,
`html`, `urllib.parse`, `unicodedata`, `datetime`, `dataclasses` — D-01

**Almacenamiento**: SQLite en `datos/pacientes.db`, creado en el primer arranque y excluido de git
— D-04

**Pruebas**: `unittest` (`python -m unittest`), una prueba por CA-01 a CA-13 y CL-01 a CL-05, más
las precisiones PD verificables — D-02

**Plataforma objetivo**: puesto local (Windows, Linux o macOS) con navegador; servidor en
`127.0.0.1:8000` — D-03, D-10

**Tipo de proyecto**: aplicación web local (servidor y páginas HTML en un único proyecto)

**Objetivos de rendimiento**: no definidos; la especificación no fija tiempos ni volúmenes
(Supuestos de spec.md)

**Restricciones**: arranque con un único comando y sin servicios externos (principio V); sin
JavaScript; código y textos en español (principio I); datos ficticios (principio IV)

**Escala/Alcance**: un centro médico de tamaño medio; como máximo 999 999 pacientes (RN-04,
CL-04); 6 rutas web y 1 tabla

## Comprobación de la constitución

*PUERTA: debe superarse antes de la fase 0 y volver a comprobarse tras la fase 1.*

| Principio | Comprobación | Antes de la fase 0 | Tras la fase 1 |
|---|---|---|---|
| I. Idioma | Interfaz, mensajes y documentación en español; módulos, funciones, variables, tabla y campos en español sin tildes ni eñes (`codigo_historia`, `numero_poliza`, `normalizar_texto`). Vocabulario: paciente, historia clínica, mutua, documento de identidad. | ✅ | ✅ Los únicos nombres en inglés son los que impone la biblioteca estándar y no se pueden renombrar (`do_GET`, `do_POST`, `setUp`, el prefijo `test_` que exige `unittest`). |
| II. Alcance mínimo | Solo las tres capacidades. Sin borrado, listados, búsqueda por nombre, API para otros sistemas, inicio de sesión ni validaciones de formato no pedidas. Sin dependencias externas. | ✅ | ✅ 6 rutas, 1 tabla y 4 módulos, todos trazados abajo; en cada decisión de research.md se eligió la alternativa más simple. |
| III. Trazabilidad | Cada elemento del plan remite a RF, RN, CA, CL o PD. Las ambigüedades se preguntaron (7 aclaraciones en spec.md y 2 decisiones técnicas del usuario). | ✅ | ✅ Ver «Trazabilidad de la estructura». Sin ambigüedades abiertas. |
| IV. Datos ficticios | Ejemplos y pruebas con datos inventados; `datos/` excluida de git. | ✅ | ✅ data-model.md y quickstart.md usan solo datos ficticios. |
| V. Ejecución local | `python app.py`, sin instalar paquetes ni crear cuentas. | ✅ | ✅ |

**Resultado**: la puerta se supera sin violaciones; la sección «Seguimiento de complejidad» no
aplica.

## Estructura del proyecto

### Documentación (esta funcionalidad)

```text
specs/001-registro-identificacion-pacientes/
├── spec.md              # Especificación (/speckit-specify, /speckit-clarify)
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0: decisiones técnicas D-01 a D-10
├── data-model.md        # Fase 1: tabla paciente, normalización, ciclo de vida
├── quickstart.md        # Fase 1: arranque, pruebas y validación manual
├── contracts/
│   ├── servicio-pacientes.md   # Funciones, errores y mensajes del servicio
│   └── interfaz-web.md         # Rutas, parámetros y respuestas
├── checklists/
│   └── requirements.md  # Calidad de la especificación
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea /speckit-plan)
```

### Código fuente (raíz del repositorio)

```text
app.py                       # Punto de entrada: crea la base de datos y arranca el servidor
registro_pacientes/
├── __init__.py
├── normalizacion.py         # normalizar_texto, recortar
├── base_datos.py            # Conexión, esquema y consultas SQL parametrizadas
├── servicio.py              # Paciente, errores, validación, registrar/buscar/modificar
└── web.py                   # Manejador HTTP, rutas y páginas HTML
tests/
├── __init__.py
├── utilidades.py            # Base de datos temporal y datos ficticios de prueba
├── test_registro.py         # CA-01..CA-05, CL-03, CL-04, PD-03, PD-04, PD-11, PD-13
├── test_duplicados.py       # CA-08, PD-09
├── test_busqueda.py         # CA-06, CA-07, CL-01, CL-02, PD-06, PD-08, PD-10
├── test_modificacion.py     # CA-09, CA-10, CA-11, CL-05, PD-01, PD-02, PD-12
└── test_web.py              # CA-12, CA-13, PD-05 y respuestas de las rutas
datos/                       # Creada en ejecución; excluida en .gitignore
```

**Decisión de estructura**: un único proyecto en la raíz del repositorio. La separación en
cuatro módulos responde a tres motivos concretos: `normalizacion.py` aísla la regla RN-08 que se
usa al guardar y al buscar; `servicio.py` concentra las reglas de negocio para que las pruebas de
CA y CL no dependan del HTML; `base_datos.py` contiene todo el SQL; `web.py` solo traduce entre
peticiones HTTP y el servicio.

### Trazabilidad de la estructura

| Elemento | Requisitos que implementa |
|---|---|
| `app.py` | Principio V; PD-11 (usa `datos/pacientes.db` persistente) |
| `normalizacion.py` | RN-08, PD-06, PD-09, PD-10, PD-12, PD-13 |
| `base_datos.py` | RN-04 a RN-07, RN-10, PD-03, PD-04, PD-11, PD-14 (esquema y consultas; data-model.md) |
| `servicio.py` | RF-01 a RF-06, RN-01 a RN-03, RN-09, RN-11, CL-04, PD-01, PD-02, PD-07, PD-08 |
| `web.py` | RF-01, RF-03 a RF-06, CA-12, CA-13, CL-01, PD-05, PD-07 |
| `tests/` | CE-05: CA-01 a CA-13, CL-01 a CL-05 y PD verificables |
| `.gitignore` (`datos/`) | Principio IV |

## Seguimiento de complejidad

No aplica: la comprobación de la constitución no muestra violaciones.
