<!--
Informe de impacto de sincronización (Sync Impact Report)
- Cambio de versión: 3.1.0 → 3.2.0 (MENOR: se amplía el vocabulario del principio I)
- Principios modificados:
  - I. Idioma (ampliado: el vocabulario obligatorio del dominio pasa de 4 a 11 términos. Se
    añaden los 7 del módulo de programación de citas — cita, especialista, especialidad, centro,
    agenda, hueco y franja bloqueada — y la lista se agrupa por módulo. Los 4 términos previos
    y las dos primeras reglas del principio, sobre idioma e identificadores, no cambian)
  - II. Alcance mínimo (sin cambios)
  - III. Trazabilidad (sin cambios)
  - IV. Datos ficticios (sin cambios)
  - V. Ejecución local en contenedores (sin cambios)
- Principios eliminados: ninguno.
- Secciones añadidas: ninguna.
- Secciones eliminadas: ninguna ([SECTION_2_NAME] y [SECTION_3_NAME] de la plantilla siguen
  omitidas deliberadamente para no añadir reglas no pedidas).
- Justificación del salto MENOR y no MAYOR: solo se añaden términos. Los cuatro anteriores se
  conservan con el mismo significado, por lo que nada que cumpliera 3.1.0 deja de cumplir esta
  versión.
- Resuelto: queda cerrado el pendiente que el informe de la versión 3.1.0 dejaba señalado (el
  vocabulario no cubría el dominio de citas).
- Plantillas dependientes: no se modifican (leen la constitución en tiempo de ejecución).
- TODO diferidos: ninguno.
-->

# Constitución del proyecto HIS (registro de pacientes y programación de citas)

## Core Principles

### I. Idioma

- La interfaz de usuario, los mensajes de error y toda la documentación DEBEN estar en español.
- El código DEBE estar en español: entidades, variables, funciones y campos. Los
  identificadores NO DEBEN contener tildes ni eñes (p. ej., `numero_historia`, no
  `número_historia`; `anio`, no `año`).
- El vocabulario del dominio DEBE ser consistente en todo el proyecto (especificación, plan,
  tareas, código, interfaz y documentación). No se admiten sinónimos alternativos para estos
  conceptos:
  - Comunes y del módulo de registro e identificación de pacientes: **paciente**,
    **historia clínica**, **mutua** y **documento de identidad**.
  - Del módulo de programación de citas: **cita**, **especialista**, **especialidad**,
    **centro**, **agenda**, **hueco** y **franja bloqueada**.

**Justificación**: un único idioma y un vocabulario estable eliminan ambigüedad entre
requisitos e implementación y facilitan la trazabilidad. Cada módulo del principio II aporta sus
propios términos, y fijarlos evita que un mismo concepto aparezca con dos nombres distintos
(p. ej. «médico» o «doctor» en lugar de **especialista**, o «slot» en lugar de **hueco**).

### II. Alcance mínimo

- El proyecto DEBE cubrir exactamente dos módulos y, en total, exactamente seis capacidades.
- **Módulo de registro e identificación de pacientes** — tres capacidades:
  1. registro e identificación del paciente;
  2. búsqueda y verificación de identidad;
  3. modificación de datos.
- **Módulo de programación de citas** — tres capacidades:
  4. reservar una cita;
  5. cancelar o reprogramar una cita;
  6. gestionar la agenda de un especialista.
- NO se DEBE añadir ninguna funcionalidad, caso de uso ni variante fuera de esas seis
  capacidades, por razonable que parezca.
- Cada módulo DEBE mantener su alcance propio: una capacidad de un módulo NO DEBE ampliarse
  para absorber trabajo que corresponde al otro.
- Ante varias formas de resolver algo, se DEBE elegir siempre la más simple.

**Justificación**: un alcance cerrado y la opción más simple evitan complejidad no requerida,
que dificulta la verificación y la trazabilidad. Enumerar las capacidades por módulo mantiene
el límite comprobable a medida que el proyecto crece.

### III. Trazabilidad

- NO se DEBE implementar nada que no esté en la especificación.
- Todo elemento del plan, de las tareas y del código DEBE poder rastrearse hasta un requisito
  concreto de la especificación.
- Ante cualquier ambigüedad, se DEBE preguntar antes de decidir; no se permite resolverla
  mediante suposiciones.

**Justificación**: es la esencia de la Ingeniería de Requisitos: cada artefacto responde a un
requisito identificable.

### IV. Datos ficticios

- El repositorio es público y el dominio es sanitario: todos los datos que aparezcan
  (ejemplos, datos de prueba y documentación) DEBEN ser inventados.
- NUNCA se DEBEN usar datos reales de personas.

**Justificación**: los datos de salud son categoría especial de datos personales; su exposición
en un repositorio público es inaceptable.

### V. Ejecución local en contenedores

- La aplicación DEBE ejecutarse en contenedores.
- El arranque completo DEBE lograrse con un único `docker compose up`, sin pasos manuales
  previos ni posteriores: la creación del esquema de datos y cualquier inicialización
  necesaria DEBEN producirse de forma automática dentro de ese arranque.
- Los datos DEBEN persistirse en un volumen, de modo que sobrevivan a la parada y al reinicio
  de los contenedores.
- Toda la configuración (credenciales de base de datos, puertos, rutas y parámetros de
  entorno) DEBE proporcionarse mediante variables de entorno. NO se DEBEN incrustar valores de
  configuración en el código.
- La ejecución NO DEBE requerir servicios de pago ni cuentas en plataformas externas.

**Justificación**: cualquier persona evaluadora debe poder ejecutar la práctica sin barreras y
de forma reproducible en su máquina; los contenedores eliminan las diferencias de entorno, el
volumen evita la pérdida de datos entre ejecuciones y la configuración externalizada permite
cambiar el entorno sin tocar el código.

## Governance

- Esta constitución prevalece sobre cualquier otra práctica del proyecto. La especificación,
  el plan, las tareas y el código DEBEN cumplirla.
- **Enmiendas**: cualquier cambio en los principios DEBE documentarse en este archivo,
  actualizando el informe de impacto de sincronización, la versión y la fecha de última
  enmienda.
- **Versionado** (semántico):
  - MAYOR: eliminación o redefinición incompatible de un principio.
  - MENOR: incorporación de un principio o sección, o ampliación sustancial de su contenido.
  - PARCHE: aclaraciones, redacción o erratas sin cambio semántico.
- **Revisión de cumplimiento**: al elaborar el plan, las tareas y durante la implementación se
  DEBE verificar el cumplimiento de cada principio; cualquier incumplimiento DEBE señalarse y
  resolverse antes de continuar.

**Version**: 3.2.0 | **Ratified**: 2026-09-15 | **Last Amended**: 2026-09-28
