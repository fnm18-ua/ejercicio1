# Lista de comprobación de calidad de la especificación: Módulo de Programación de Citas

**Propósito**: validar que la especificación está completa y es de calidad antes de pasar a la
planificación.
**Creada**: 2026-09-28
**Funcionalidad**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, marcos de trabajo, API)
- [x] Centrada en el valor para el usuario y las necesidades de negocio
- [x] Redactada para partes interesadas no técnicas
- [x] Todas las secciones obligatorias completadas

## Completitud de los requisitos

- [x] No quedan marcadores [NEEDS CLARIFICATION] — las 3 preguntas se resolvieron en la sesión de
      aclaraciones del 2026-09-28: Q1 → franja con rango de fechas más tramo horario (PD-C12);
      Q2 → reprogramar actualiza la referencia de las 24 horas (PD-C07, PD-C08); Q3 → las
      cancelaciones automáticas solo alcanzan a las citas futuras (PD-C11)
- [x] Los requisitos son verificables y no ambiguos
- [x] Los criterios de éxito son medibles
- [x] Los criterios de éxito son independientes de la tecnología
- [x] Todos los escenarios de aceptación están definidos
- [x] Los casos límite están identificados
- [x] El alcance está claramente delimitado
- [x] Las dependencias y los supuestos están identificados

## Preparación de la funcionalidad

- [x] Todos los requisitos funcionales tienen criterios de aceptación claros
- [x] Los escenarios de usuario cubren los flujos principales
- [x] La funcionalidad cumple los resultados medibles de los criterios de éxito
- [x] Ningún detalle de implementación se filtra en la especificación

## Notas

- **Estado**: 16 de 16 elementos cumplidos. La especificación está lista para `/speckit-plan`.
- **Aclaraciones**: las tres ambigüedades detectadas se elevaron al usuario en vez de resolverse
  por suposición (Constitución, principio III) y quedaron cerradas el 2026-09-28. Consecuencias
  registradas: la entidad «Franja bloqueada» pasa a tener rango de fechas y tramo horario; la
  entidad «Cita» guarda el momento de la última reserva o reprogramación; y CE-C02 se acota a las
  citas futuras, porque las pasadas son historial y no agenda.
- **Trazabilidad verificada**: los 9 RF-C, las 13 RN-C, los 13 CA-C y los 7 CL-C del enunciado
  están recogidos. Las 6 historias de usuario se corresponden con E-C01 a E-C06. Los elementos
  añadidos llevan identificador propio (PD-C01 a PD-C20, CL-C08, CL-C09, CE-C01 a CE-C09) e
  indican de qué elemento del enunciado derivan.
- **Aritmética comprobada**: el algoritmo de generación de huecos de PD-C03 reproduce CA-C01
  (12 huecos de 9:00 a 12:40 con 20 minutos), CL-C05 (4 huecos con 50 minutos) y CA-C12 (en la
  rejilla de 30 minutos existe el hueco de las 9:00 y no existe el de las 9:20).
- **Cobertura de las capacidades de la constitución**: las historias P1 y P2 cubren la capacidad
  «reservar una cita»; P3 y P4, «cancelar o reprogramar»; P5 y P6, «gestionar la agenda de un
  especialista» (principio II, v3.1.0).
- **Pendiente de gobernanza**: el principio I de la constitución no incluye todavía el
  vocabulario del dominio de citas (cita, especialista, agenda). Señalado en «Supuestos».
- Los elementos marcados como incompletos requieren actualizar la especificación antes de
  `/speckit-clarify` o `/speckit-plan`.
