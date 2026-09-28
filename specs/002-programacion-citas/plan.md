# Plan de implementación: Módulo de Programación de Citas

**Rama**: `002-programacion-citas` (carpeta de la funcionalidad; se trabaja sobre `master`) |
**Fecha**: 2026-09-28 | **Especificación**: [spec.md](spec.md)

**Entrada**: especificación de la funcionalidad en `specs/002-programacion-citas/spec.md`

## Resumen

El módulo permite a un paciente ya registrado identificarse, buscar especialista por especialidad
y centro, ver los huecos libres de una fecha y reservar uno, así como consultar, cancelar y
reprogramar sus citas; y permite al personal administrativo bloquear franjas de un especialista y
ajustar la duración de sus consultas, cancelando por el centro las citas futuras que dejan de ser
atendibles (RF-C01 a RF-C09).

Enfoque técnico ([research.md](research.md)): se reutiliza el stack del módulo de registro
—Python con solo la biblioteca estándar, `http.server` y `sqlite3`— en un paquete nuevo
`programacion_citas/`, sin modificar ni una línea del módulo de registro (D-C03). Las cinco
tablas nuevas viven en la misma base de datos SQLite, de modo que la identidad del paciente se
consulta directamente (D-C02, D-C04). Los huecos no se almacenan: se derivan en cada consulta del
horario y de la duración vigente del especialista, que es lo que permite recalcular la rejilla al
cambiar la duración (D-C05, D-C06). La imposibilidad de que dos personas ocupen el mismo hueco se
garantiza con un índice único parcial en la base de datos, no con una comprobación previa
(D-C08). La aritmética temporal se aísla en `agenda.py` para poder probar por separado las
afirmaciones numéricas exactas de CA-C01, CA-C12 y CL-C05 (D-C15). El servidor sigue siendo uno y
el puerto sigue siendo uno: el manejador de citas hereda del de registro (D-C13).

## Contexto técnico

**Lenguaje/Versión**: Python 3.10 o superior (imagen del contenedor: `python:3.12-slim`) — D-C01

**Dependencias principales**: ninguna externa; biblioteca estándar: `http.server`, `sqlite3`,
`html`, `urllib.parse`, `datetime`, `dataclasses` — D-C01

**Almacenamiento**: el mismo SQLite del proyecto (`datos/pacientes.db` por defecto, variable
`RUTA_BD`), con cinco tablas nuevas: `centro`, `especialidad`, `especialista`, `cita` y
`franja_bloqueada` — D-C02

**Pruebas**: `unittest` (`python -m unittest`), una prueba por CA-C01 a CA-C13 y CL-C01 a CL-C09,
más pruebas unitarias de la aritmética de `agenda.py` y de las precisiones PD-C verificables —
D-C15

**Plataforma objetivo**: contenedor levantado con `docker compose up`; navegador contra el puerto
publicado (`PUERTO`, 8000 por defecto). También ejecutable en local con `python app.py` — principio
V

**Tipo de proyecto**: aplicación web local servida por el servidor ya existente del proyecto, al
que este módulo añade sus rutas (D-C13)

**Objetivos de rendimiento**: no definidos; la especificación no fija tiempos ni volúmenes
(Supuestos de spec.md)

**Restricciones**: arranque con un único comando, datos en volumen y configuración por variables
de entorno (principio V); sin JavaScript; código, interfaz y textos en español con el vocabulario
del principio I (cita, especialista, especialidad, centro, agenda, hueco, franja bloqueada); datos
ficticios (principio IV); no se modifica el módulo de registro (principio III, D-C03)

**Escala/Alcance**: un centro médico de tamaño medio; 5 tablas nuevas, 11 rutas nuevas, 2 flujos
sin control de acceso (PD-C02)

## Comprobación de la constitución

*PUERTA: debe superarse antes de la fase 0 y volver a comprobarse tras la fase 1.*

Constitución vigente: **v3.2.0**.

| Principio | Comprobación | Antes de la fase 0 | Tras la fase 1 |
|---|---|---|---|
| I. Idioma | Interfaz, mensajes y documentación en español; paquete, módulos, tablas y campos en español sin tildes ni eñes (`franja_bloqueada`, `dias_semana`, `duracion_minutos`, `motivo_cancelacion`). Vocabulario del principio I en su versión 3.2.0: cita, especialista, especialidad, centro, agenda, hueco y franja bloqueada. | ✅ | ✅ Los 7 términos nuevos del principio I son los que usan `data-model.md` y los contratos. Los únicos nombres en inglés son los que impone la biblioteca estándar y no se pueden renombrar (`do_GET`, `do_POST`, `setUp`, el prefijo `test_`). |
| II. Alcance mínimo | Solo las tres capacidades del módulo de citas (capacidades 4, 5 y 6 del principio II). Sin alta ni edición de centros, especialidades o especialistas; sin notificaciones, sin listas de espera, sin desbloqueo de franjas, sin inicio de sesión. Sin dependencias nuevas. | ✅ | ✅ 11 rutas y 5 tablas, todas trazadas abajo. En cada decisión de research.md se eligió la alternativa más simple, incluido no renombrar la base de datos (D-C02) y no materializar los huecos (D-C05). |
| II. Frontera entre módulos | Ninguna capacidad de citas absorbe trabajo del módulo de registro: este módulo no crea, modifica ni borra pacientes; solo los identifica. | ✅ | ✅ La dependencia es en un solo sentido (citas → registro, D-C04) y el módulo de registro no se modifica (D-C03, D-C13). |
| III. Trazabilidad | Cada elemento del plan remite a RF-C, RN-C, CA-C, CL-C o PD-C. Las tres ambigüedades detectadas se preguntaron al usuario en vez de suponerlas (sesión de aclaraciones 2026-09-28). | ✅ | ✅ Ver «Trazabilidad de la estructura». Sin ambigüedades abiertas. El único punto abierto (enlace desde `/` a los dos flujos) se señala como decisión pendiente en D-C14, no se resuelve inventando. |
| IV. Datos ficticios | Centros, especialidades, especialistas y citas de ejemplo inventados, tanto en la precarga como en las pruebas y la documentación. | ✅ | ✅ `datos_iniciales.py` y los ejemplos de `data-model.md` y `quickstart.md` usan solo datos inventados (D-C12). |
| V. Ejecución local en contenedores | No se añade ningún servicio ni dependencia: el módulo entra en el contenedor existente, con la misma base de datos en el mismo volumen y la misma configuración por variables de entorno. Un solo `docker compose up`. | ✅ | ✅ Un único servidor y un único puerto (D-C13); precarga idempotente para que arranques repetidos no dupliquen datos (D-C12). |

**Resultado**: la puerta se supera antes de la fase 0 y tras la fase 1, sin violaciones. La sección
«Seguimiento de complejidad» no aplica.

**Vinculación con las competencias de la asignatura**:

- **CESI1**: el módulo integra dos piezas de TIC sobre un proceso de negocio único —la identidad
  que produce el módulo de registro es la que consume el de citas (D-C04)— y ataca el objetivo de
  negocio declarado: reservar sin llamar por teléfono con disponibilidad real (CE-C01, CE-C02).
- **CESI2**: D-C16 recoge las medidas aplicadas (escapado de salida, SQL parametrizado, datos
  ficticios) y declara de forma explícita la limitación de no tener control de acceso (PD-C02),
  con su lectura bajo el artículo 9 del RGPD y el ENS. La aplicación no es apta para datos reales
  de pacientes, y se deja constancia en vez de darlo por supuesto.

## Estructura del proyecto

### Documentación (esta funcionalidad)

```text
specs/002-programacion-citas/
├── spec.md              # Especificación (/speckit-specify + aclaraciones 2026-09-28)
├── plan.md              # Este archivo (/speckit-plan)
├── research.md          # Fase 0: decisiones técnicas D-C01 a D-C16
├── data-model.md        # Fase 1: 5 tablas, invariantes, ciclo de vida de la cita
├── quickstart.md        # Fase 1: arranque, pruebas y validación manual
├── contracts/
│   ├── servicio-citas.md       # Funciones, errores y mensajes del servicio
│   └── interfaz-web-citas.md   # Rutas, parámetros y respuestas
├── checklists/
│   └── requirements.md  # Calidad de la especificación (16/16)
└── tasks.md             # Fase 2 (/speckit-tasks; no lo crea /speckit-plan)
```

### Código fuente (raíz del repositorio)

Se añade el paquete `programacion_citas/` y archivos nuevos en `tests/`. Lo marcado como
`(sin cambios)` no se toca.

```text
app.py                          # Se modifica solo para crear el servidor combinado (D-C13)
registro_pacientes/             # (sin cambios) módulo de registro, del que este importa
├── servicio.py                 #   buscar_por_codigo, buscar_por_documento (D-C04)
└── web.py                      #   ManejadorPacientes, clase base del manejador de citas
programacion_citas/
├── __init__.py
├── agenda.py                   # Aritmética temporal pura: rejilla, solapamiento, encaje, bloqueo
├── base_datos.py               # Esquema de las 5 tablas, índice único parcial y SQL parametrizado
├── datos_iniciales.py          # Precarga idempotente de centros, especialidades y especialistas
├── servicio.py                 # Reglas de negocio: reservar, cancelar, reprogramar, agenda
└── web.py                      # Manejador que hereda del de registro; rutas y páginas HTML
tests/
├── utilidades_citas.py         # Base de datos temporal, datos ficticios y momento actual fijable
├── test_agenda.py              # CA-C01, CL-C05, PD-C03, PD-C06, PD-C10, PD-C12 (sin base de datos)
├── test_reserva.py             # CA-C02, CA-C03, CA-C04, CA-C05, CL-C01, CL-C02, CL-C03, CL-C06, CL-C09
├── test_cancelacion.py         # CA-C06, CA-C07, CA-C08, CL-C07
├── test_reprogramacion.py      # CA-C09, CL-C08, PD-C07, PD-C08
├── test_bloqueo.py             # CA-C10, CA-C11, CL-C04, PD-C11, PD-C12
├── test_duracion.py            # CA-C12, PD-C10, PD-C11, PD-C20
└── test_web_citas.py           # CA-C13 y respuestas de las 11 rutas
datos/                          # (sin cambios) creada en ejecución; persistida en el volumen
```

**Decisión de estructura**: un paquete nuevo hermano de `registro_pacientes/`, en la raíz del
repositorio. La separación en cinco módulos responde a motivos concretos: `agenda.py` aísla la
aritmética temporal, que es donde están las afirmaciones numéricas exactas del enunciado y debe
poder probarse sin base de datos ni HTTP; `base_datos.py` contiene todo el SQL y las restricciones
que hacen inviolables RN-C06, RN-C13 y la unicidad del hueco; `servicio.py` concentra las reglas
de negocio para que las pruebas de CA-C y CL-C no dependan del HTML; `datos_iniciales.py` separa
la precarga de RN-C01 del esquema; `web.py` solo traduce entre peticiones HTTP y el servicio. El
único archivo existente que se modifica es `app.py`, y solo para construir el servidor combinado
(D-C13).

### Trazabilidad de la estructura

| Elemento | Requisitos que implementa |
|---|---|
| `agenda.py` | RN-C03, RN-C04, RN-C07, RN-C12; PD-C03, PD-C05, PD-C06, PD-C10, PD-C12; CA-C01, CA-C12, CL-C05, CL-C06 |
| `base_datos.py` | RN-C02, RN-C05, RN-C06, RN-C13; PD-C04, PD-C09, PD-C17; CL-C03 (esquema, `CHECK` e índice único parcial; ver data-model.md) |
| `datos_iniciales.py` | RN-C01, RN-C02; PD-C19; CA-C13; principio IV |
| `servicio.py` | RF-C01 a RF-C09; RN-C07 a RN-C12; PD-C01, PD-C07, PD-C08, PD-C11, PD-C14, PD-C15, PD-C18 |
| `web.py` | RF-C01 a RF-C09; PD-C02, PD-C16, PD-C18; CA-C13; D-C13, D-C14 |
| `app.py` (cambio mínimo) | D-C13; principio V |
| Importación de `registro_pacientes.servicio` | RF-C01, RN-C05, CA-C04; PD-C01; D-C04 |
| `tests/` | CE-C08: CA-C01 a CA-C13, CL-C01 a CL-C09 y las PD-C verificables |

## Seguimiento de complejidad

No aplica: la comprobación de la constitución no muestra violaciones.

## Punto abierto para la persona responsable

No es una ambigüedad de requisitos, y por eso no bloquea la fase 2, pero conviene decidirlo antes
de implementar la interfaz (D-C14): la página de inicio del módulo de registro (`GET /`) no enlaza
con `/citas` ni con `/agenda`. Añadir esos dos enlaces es un cambio de dos líneas en el módulo de
registro que ninguna parte de esta especificación pide, así que no se ha incluido en el plan.
Mientras no se decida, los dos flujos se alcanzan escribiendo su dirección, como documenta
[quickstart.md](quickstart.md).
