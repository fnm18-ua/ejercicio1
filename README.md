# Registro e Identificación de Pacientes

Módulo del Sistema de Información de Gestión Hospitalaria (HIS) construido con Spec-Driven
Development. Cubre exactamente tres capacidades:

1. **Registro e identificación del paciente**: registra sus datos personales, de contacto y de
   cobertura sanitaria y le asigna un código de historia clínica único, secuencial y permanente
   (`HC-000001`, `HC-000002`, …).
2. **Búsqueda y verificación de identidad**: localiza al paciente por su código de historia
   clínica o por su documento de identidad y muestra su ficha completa, para reconocer a quien
   ya existe en lugar de duplicarlo.
3. **Modificación de datos**: actualiza cualquier dato del paciente salvo su código de historia
   clínica.

El código de historia clínica es la identidad que el resto de módulos del HIS (citas, historia
clínica, prescripción, facturación) usarían para referirse al paciente.

## Requisitos

- Python 3.10 o superior. No hay que instalar ningún paquete adicional.

## Arrancar la aplicación

```bash
python app.py
```

Abrir `http://127.0.0.1:8000` en el navegador. Los datos se guardan en `datos/pacientes.db`,
que se crea automáticamente y no se sube al repositorio. Para detener el servidor, `Ctrl+C`.

## Ejecutar las pruebas

```bash
python -m unittest
```

Cada prueba indica en su nombre el criterio de aceptación (CA), caso límite (CL) o precisión (PD)
de la especificación que verifica.

## Documentación Spec-Driven Development

Todo el proceso está en [`specs/001-registro-identificacion-pacientes/`](specs/001-registro-identificacion-pacientes/):

| Documento | Contenido |
|---|---|
| [spec.md](specs/001-registro-identificacion-pacientes/spec.md) | Especificación funcional: objetivo, usuarios, escenarios, requisitos, reglas de negocio, criterios de aceptación, casos límite y fuera de alcance |
| [plan.md](specs/001-registro-identificacion-pacientes/plan.md) | Plan técnico: arquitectura, decisiones y trazabilidad |
| [data-model.md](specs/001-registro-identificacion-pacientes/data-model.md) | Modelo de datos e identidad reutilizable |
| [tasks.md](specs/001-registro-identificacion-pacientes/tasks.md) | Desglose de tareas |
| [quickstart.md](specs/001-registro-identificacion-pacientes/quickstart.md) | Guía de validación paso a paso |

Los principios del proyecto están en [`.specify/memory/constitution.md`](.specify/memory/constitution.md).

## Datos ficticios

El repositorio es público y el dominio es sanitario: **todos los datos que aparecen en ejemplos,
pruebas y documentación son inventados**. Nunca deben introducirse datos reales de personas.
