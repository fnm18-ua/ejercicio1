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

## Módulo de programación de citas

Segundo módulo del proyecto. Cubre otras tres capacidades, sobre la identidad que produce el
módulo de registro:

4. **Reservar una cita**: el paciente se identifica, busca especialista por especialidad y centro,
   ve los huecos libres de una fecha y reserva uno.
5. **Cancelar o reprogramar**: consulta sus citas con su estado y las cancela o las traslada a otro
   hueco del mismo especialista, conservando la misma cita.
6. **Gestionar la agenda de un especialista**: el personal administrativo bloquea franjas y ajusta
   la duración de las consultas; las citas futuras que dejan de ser atendibles quedan canceladas
   por el centro, con su motivo visible para el paciente.

Hay **dos flujos separados**, sin inicio de sesión:

| Flujo | Dirección |
|---|---|
| Paciente | `http://127.0.0.1:8000/citas` |
| Personal administrativo | `http://127.0.0.1:8000/agenda` |

> La página de inicio `/` todavía **no enlaza** con esos dos flujos: hay que escribir la dirección.
> Añadir los enlaces implicaría modificar el módulo de registro y ninguna especificación lo pide;
> queda como decisión pendiente (decisión D-C14 del plan del módulo).

Los centros, las especialidades y los especialistas son **datos precargados**: la aplicación no
ofrece ninguna forma de crearlos, editarlos ni eliminarlos.

### Seguridad: no introduzcas datos reales

No hay inicio de sesión ni control de acceso. Conocer el código de historia clínica de un paciente
basta para ver y operar con sus citas, y `/agenda` está abierta a cualquiera. Es una limitación
asumida del alcance académico, no un descuido.

Una cita con un especialista revela una sospecha diagnóstica, por lo que estos datos son datos
relativos a la salud, categoría especial del artículo 9 del RGPD. **La aplicación no es apta para
datos reales de pacientes.**

## Arrancar la aplicación con Docker (forma recomendada)

Solo hace falta Docker con Docker Compose v2. No se instala nada más:

```bash
docker compose up
```

El primer arranque construye la imagen; no hay ningún paso manual adicional. Abrir
`http://127.0.0.1:8000` en el navegador. Para detener el servidor, `Ctrl+C`.

```bash
docker compose up -d      # arrancar en segundo plano
docker compose logs -f    # ver los mensajes del servidor
docker compose down       # detener y eliminar el contenedor (los datos se conservan)
docker compose down -v    # detener y borrar además el volumen: se pierden los datos
```

La aplicación se ejecuta en un único contenedor: usa SQLite embebido, por lo que no hay
servicio de base de datos ni ninguna dependencia externa.

### Persistencia

El fichero SQLite vive en el volumen `datos_pacientes`, montado en `/datos` dentro del
contenedor. Los pacientes registrados **sobreviven a `docker compose down` y a los reinicios**;
solo se borran con `docker compose down -v`.

### Configuración

Todas las variables tienen valor por defecto, así que `docker compose up` funciona sin definir
ninguna:

| Variable | Por defecto (contenedor) | Descripción |
|---|---|---|
| `PUERTO` | `8000` | Puerto de escucha, publicado con el mismo número en el anfitrión |
| `RUTA_BD` | `/datos/pacientes.db` | Ruta del fichero SQLite; debe quedar bajo `/datos` para persistir |
| `HOST` | `0.0.0.0` | Interfaz de escucha; dentro del contenedor debe ser `0.0.0.0` |

Para usar otro puerto:

```bash
PUERTO=9100 docker compose up
```

## Arrancar la aplicación sin Docker

- Python 3.10 o superior. No hay que instalar ningún paquete adicional.

```bash
python app.py
```

Abrir `http://127.0.0.1:8000` en el navegador. Los datos se guardan en `datos/pacientes.db`,
que se crea automáticamente y no se sube al repositorio. Para detener el servidor, `Ctrl+C`.

Las mismas variables de entorno son válidas aquí, con valores por defecto adaptados a la
ejecución local: `RUTA_BD` apunta a `datos/pacientes.db` y `HOST` a `127.0.0.1`.

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
