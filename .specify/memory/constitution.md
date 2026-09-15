<!--
Informe de impacto de sincronización (Sync Impact Report)
- Cambio de versión: plantilla sin versionar → 1.0.0 (ratificación inicial)
- Principios definidos (sustituyen a los marcadores de la plantilla):
  - [PRINCIPLE_1_NAME] → I. Idioma español y vocabulario del dominio
  - [PRINCIPLE_2_NAME] → II. Simplicidad
  - [PRINCIPLE_3_NAME] → III. Trazabilidad
  - [PRINCIPLE_4_NAME] → IV. Datos ficticios
  - [PRINCIPLE_5_NAME] → V. Sin secretos en el repositorio
  - (nuevo) → VI. Ejecución local
  - (nuevo) → VII. Verificación automática de la lógica crítica
- Secciones añadidas: principios VI y VII (el usuario fijó exactamente siete principios).
- Secciones eliminadas: [SECTION_2_NAME] y [SECTION_3_NAME] de la plantilla. Se omiten
  deliberadamente porque el usuario pidió no añadir principios ni reglas adicionales.
- Plantillas dependientes: no se modifican (leen la constitución en tiempo de ejecución).
- TODO diferidos: ninguno.
-->

# Constitución del módulo de Registro e Identificación de Pacientes (HIS)

## Core Principles

### I. Idioma español y vocabulario del dominio

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

### II. Simplicidad

- NO se DEBEN añadir dependencias, capas ni abstracciones que la especificación no exija.
- Toda dependencia, capa o abstracción presente DEBE poder justificarse con un requisito
  de la especificación.

**Justificación**: la complejidad no requerida dificulta la verificación y la trazabilidad.

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
  (ejemplos, datos de prueba, tests, capturas y documentación) DEBEN ser inventados.
- NUNCA se DEBEN usar datos reales de personas.

**Justificación**: los datos de salud son categoría especial de datos personales; su exposición
en un repositorio público es inaceptable.

### V. Sin secretos en el repositorio

- Ninguna credencial ni configuración sensible DEBE versionarse.

**Justificación**: todo lo versionado en un repositorio público debe considerarse expuesto.

### VI. Ejecución local

- La aplicación DEBE poder arrancarse en local con un único comando.
- La ejecución NO DEBE requerir servicios de pago ni cuentas en plataformas externas.

**Justificación**: cualquier persona evaluadora debe poder ejecutar la práctica sin barreras.

### VII. Verificación automática de la lógica crítica

- DEBEN existir tests automáticos que cubran:
  - la generación del identificador único de paciente;
  - la validación del documento de identidad;
  - la detección de duplicados.
- El resto de la funcionalidad se verifica manualmente.

**Justificación**: estas tres piezas determinan la identificación inequívoca del paciente; un
error en ellas compromete la integridad de la historia clínica.

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

**Version**: 1.0.0 | **Ratified**: 2026-09-15 | **Last Amended**: 2026-09-15
