<!--
Informe de impacto de sincronización (Sync Impact Report)
- Cambio de versión: 1.0.0 → 2.0.0 (MAYOR: se redefine un principio y se eliminan dos)
- Principios modificados:
  - I. Idioma español y vocabulario del dominio → I. Idioma (mismo contenido, título abreviado)
  - II. Simplicidad → II. Alcance mínimo (redefinido: el módulo se limita a tres capacidades
    y ante varias soluciones se elige la más simple)
  - III. Trazabilidad → III. Trazabilidad (sin cambios)
  - IV. Datos ficticios → IV. Datos ficticios (sin cambios)
  - VI. Ejecución local → V. Ejecución local (renumerado, sin cambios de contenido)
- Principios eliminados (el usuario fijó exactamente cinco principios):
  - V. Sin secretos en el repositorio
  - VII. Verificación automática de la lógica crítica
- Secciones añadidas: ninguna.
- Secciones eliminadas: ninguna respecto a 1.0.0 ([SECTION_2_NAME] y [SECTION_3_NAME] de la
  plantilla siguen omitidas deliberadamente para no añadir reglas no pedidas).
- Plantillas dependientes: no se modifican (leen la constitución en tiempo de ejecución).
- TODO diferidos: ninguno.
-->

# Constitución del módulo de Registro e Identificación de Pacientes (HIS)

## Core Principles

### I. Idioma

- La interfaz de usuario, los mensajes de error y toda la documentación DEBEN estar en español.
- El código DEBE estar en español: entidades, variables, funciones y campos. Los
  identificadores NO DEBEN contener tildes ni eñes (p. ej., `numero_historia`, no
  `número_historia`; `anio`, no `año`).
- El vocabulario del dominio DEBE ser consistente en todo el proyecto (especificación, plan,
  tareas, código, interfaz y documentación), usando siempre los términos: **paciente**,
  **historia clínica**, **mutua** y **documento de identidad**. No se admiten sinónimos
  alternativos para estos conceptos.

**Justificación**: un único idioma y un vocabulario estable eliminan ambigüedad entre
requisitos e implementación y facilitan la trazabilidad.

### II. Alcance mínimo

- El módulo DEBE cubrir exactamente tres capacidades:
  1. registro e identificación del paciente;
  2. búsqueda y verificación de identidad;
  3. modificación de datos.
- NO se DEBE añadir ninguna funcionalidad, caso de uso ni variante fuera de esas tres
  capacidades, por razonable que parezca.
- Ante varias formas de resolver algo, se DEBE elegir siempre la más simple.

**Justificación**: un alcance cerrado y la opción más simple evitan complejidad no requerida,
que dificulta la verificación y la trazabilidad.

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

### V. Ejecución local

- La aplicación DEBE poder arrancarse en local con un único comando.
- La ejecución NO DEBE requerir servicios de pago ni cuentas en plataformas externas.

**Justificación**: cualquier persona evaluadora debe poder ejecutar la práctica sin barreras.

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

**Version**: 2.0.0 | **Ratified**: 2026-09-15 | **Last Amended**: 2026-09-17
