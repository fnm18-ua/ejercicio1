# Guía rápida de validación: Módulo de Registro e Identificación de Pacientes

**Funcionalidad**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Guía para arrancar la aplicación y comprobar que cumple los criterios de aceptación. Los detalles
de rutas, campos y mensajes están en [contracts/interfaz-web.md](contracts/interfaz-web.md) y
[contracts/servicio-pacientes.md](contracts/servicio-pacientes.md). **Todos los datos de esta
guía son ficticios** (Constitución, principio IV).

## Requisitos previos

- Python 3.10 o superior (desarrollado con Python 3.14). No hay que instalar nada más.
- Puerto 8000 libre.

## Arrancar la aplicación (un único comando)

Desde la raíz del repositorio:

```bash
python app.py
```

Resultado esperado: se crea `datos/pacientes.db` si no existía y la consola indica que el
servidor está disponible en `http://127.0.0.1:8000`. Abrir esa dirección en el navegador.
Para detenerlo, `Ctrl+C`.

Para empezar desde cero (necesario para CA-01), detener la aplicación y borrar la carpeta
`datos/` antes de arrancar.

## Ejecutar las pruebas automáticas

```bash
python -m unittest
```

Resultado esperado: todas las pruebas pasan (`OK`). Cada prueba lleva en su nombre el CA, CL o PD
que verifica. Las pruebas usan bases de datos temporales y no tocan `datos/pacientes.db`.

## Validación manual

Partir de una base de datos vacía y seguir los pasos en orden.

| Paso | Acción | Resultado esperado | Verifica |
|---|---|---|---|
| 1 | Registrar a *Lucía Ferrández Olmo*, nacida el 1987-03-14, DNI `00000000T`, mutua *Mutua Ejemplo Salud*, póliza `POL-0000-0001`, sin teléfono, email ni domicilio. | Se muestra su ficha con «Paciente registrado.» y el código `HC-000001`. | CA-01, CA-02 |
| 2 | Registrar a *Marcos Ibáñez Río*, nacido el 1990-11-02, NIE `X0000000T`, «Sin cobertura». | Código `HC-000002`; la ficha no muestra número de póliza. | CA-01, CA-04 |
| 3 | Intentar registrar un paciente sin nombre. | No se guarda; aparece «Falta el dato obligatorio: nombre.». | CA-03 |
| 4 | Intentar registrar un paciente con mutua pero sin póliza. | No se guarda; aparece «Falta el número de póliza de la mutua.». | CA-05 |
| 5 | Intentar registrar un paciente con fecha de nacimiento de mañana. | No se guarda; aparece que la fecha no puede ser posterior a la actual. | CL-03 |
| 6 | Intentar registrar otro paciente con DNI ` 00000000t `. | No se crea; aparece el aviso de duplicado y la ficha de `HC-000001`. | CA-08, PD-09 |
| 7 | Registrar un tercer paciente (datos ficticios cualesquiera) y comprobar su código. | `HC-000003`: los intentos fallidos no consumieron código. | PD-03 |
| 8 | Buscar por código `hc-000001`. | Ficha completa de Lucía, con fecha de registro. | CA-06, PD-05, PD-06 |
| 9 | Buscar por documento DNI `00000000t` con espacios delante y detrás. | Ficha de Lucía. | CA-07, CL-02 |
| 10 | Buscar por código `HC-000999`. | «No existe ningún paciente con el código HC-000999.», sin error. | CL-01 |
| 11 | Revisar la página de inicio. | Solo hay búsqueda por código o por documento; no hay búsqueda por nombre. | CA-13 |
| 12 | Modificar a Lucía: teléfono `600 000 000`. Buscarla de nuevo. | Aparece el teléfono nuevo. | CA-11 |
| 13 | En el formulario de modificación de Lucía, comprobar el código. | Se muestra como texto; no se puede editar. | CA-12 |
| 14 | Modificar a Lucía: número de documento ` 00000001r `. | Se guarda como `00000001R`; su código sigue siendo `HC-000001`. | CA-09, PD-12 |
| 15 | Modificar a Marcos poniéndole DNI `00000001R`. | No se guarda; aparece que el documento ya pertenece a otro paciente. | CA-10 |
| 16 | Modificar a Lucía: cobertura «Sin cobertura». | La ficha ya no muestra mutua ni póliza. | CL-05 |
| 17 | Detener la aplicación, volver a arrancarla y registrar un paciente más. | Los pacientes anteriores siguen existiendo; el nuevo recibe `HC-000004`. | PD-11 |

CL-04 (códigos agotados) no se valida a mano: requiere 999 999 registros y lo cubre la prueba
automática correspondiente.
