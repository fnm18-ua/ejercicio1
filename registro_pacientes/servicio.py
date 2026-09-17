"""Servicio de pacientes: reglas de negocio del módulo (contracts/servicio-pacientes.md).

Registro e identificación (RF-01, RF-02), búsqueda y verificación (RF-03 a RF-05) y
modificación de datos (RF-06). Es la interfaz que usan la web y las pruebas, y el punto por el
que otro módulo del HIS reconocería a un paciente por su código de historia clínica (D-05).
"""

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import date

from registro_pacientes import base_datos
from registro_pacientes.normalizacion import normalizar_texto, recortar

TIPOS_DOCUMENTO = ("DNI", "NIE", "PASAPORTE")
TIPOS_COBERTURA = ("MUTUA", "SIN_COBERTURA")
ULTIMO_CODIGO = "HC-999999"


@dataclass(frozen=True)
class Paciente:
    """Paciente registrado (Entidades clave de spec.md; data-model.md)."""

    codigo_historia: str
    nombre: str
    apellidos: str
    fecha_nacimiento: str
    tipo_documento: str
    numero_documento: str
    tipo_cobertura: str
    mutua: str | None
    numero_poliza: str | None
    telefono: str | None
    email: str | None
    domicilio: str | None
    fecha_registro: str


class ErrorValidacion(Exception):
    """Datos que incumplen RN-01, RN-03 o RN-09 (CA-03, CA-05, CL-03, PD-01, PD-13)."""

    def __init__(self, errores):
        super().__init__(" ".join(errores))
        self.errores = errores


class PacienteDuplicado(Exception):
    """Otro paciente ya tiene el mismo tipo y número de documento (RN-07, CA-08, CA-10)."""

    def __init__(self, existente):
        super().__init__(existente.codigo_historia)
        self.existente = existente


class CodigosAgotados(Exception):
    """Ya se asignó HC-999999 y no quedan códigos (CL-04)."""

    def __init__(self):
        super().__init__(
            "No se puede registrar: se han agotado los códigos de historia clínica."
        )


class PacienteNoEncontrado(Exception):
    """No existe ningún paciente con el código indicado (RF-06)."""

    def __init__(self, codigo):
        super().__init__(codigo)
        self.codigo = codigo


def _fila_a_paciente(fila):
    """Convierte una fila de la tabla paciente en un Paciente, o None si no hay fila."""
    if fila is None:
        return None
    return Paciente(**{campo: fila[campo] for campo in base_datos.CAMPOS})


def inicializar_base_datos(ruta_bd):
    """Crea el esquema si no existe, conservando los datos existentes (PD-11)."""
    with closing(base_datos.conectar(ruta_bd)) as conexion:
        base_datos.crear_esquema(conexion)


def validar_datos(datos):
    """Valida y limpia los datos de un paciente para registrar o modificar (PD-01, D-08).

    Aplica RN-01, RN-02, RN-03, RN-09 y PD-13. Ignora cualquier clave no prevista, incluida
    codigo_historia (RN-06, CA-12). Reúne todos los errores y, si hay alguno, lanza
    ErrorValidacion; si no, devuelve el diccionario limpio con los 11 campos editables.
    """
    errores = []

    nombre = recortar(datos.get("nombre"))
    if nombre is None:
        errores.append("Falta el dato obligatorio: nombre.")

    apellidos = recortar(datos.get("apellidos"))
    if apellidos is None:
        errores.append("Falta el dato obligatorio: apellidos.")

    fecha_nacimiento = recortar(datos.get("fecha_nacimiento"))
    if fecha_nacimiento is None:
        errores.append("Falta el dato obligatorio: fecha de nacimiento.")
    else:
        try:
            fecha = date.fromisoformat(fecha_nacimiento)
        except ValueError:
            errores.append("La fecha de nacimiento no es válida.")
        else:
            if fecha > date.today():
                errores.append("La fecha de nacimiento no puede ser posterior a la fecha actual.")
            fecha_nacimiento = fecha.isoformat()

    tipo_documento = (recortar(datos.get("tipo_documento")) or "").upper()
    if tipo_documento not in TIPOS_DOCUMENTO:
        errores.append("Falta el dato obligatorio: tipo de documento.")

    numero_documento = normalizar_texto(datos.get("numero_documento"))
    if not numero_documento:
        errores.append("Falta el dato obligatorio: número de documento.")

    tipo_cobertura = recortar(datos.get("tipo_cobertura"))
    mutua = None
    numero_poliza = None
    if tipo_cobertura not in TIPOS_COBERTURA:
        errores.append("Falta el dato obligatorio: cobertura sanitaria.")
    elif tipo_cobertura == "MUTUA":
        mutua = recortar(datos.get("mutua"))
        if mutua is None:
            errores.append("Falta el nombre de la mutua.")
        numero_poliza = recortar(datos.get("numero_poliza"))
        if numero_poliza is None:
            errores.append("Falta el número de póliza de la mutua.")

    if errores:
        raise ErrorValidacion(errores)

    return {
        "nombre": nombre,
        "apellidos": apellidos,
        "fecha_nacimiento": fecha_nacimiento,
        "tipo_documento": tipo_documento,
        "numero_documento": numero_documento,
        "tipo_cobertura": tipo_cobertura,
        "mutua": mutua,
        "numero_poliza": numero_poliza,
        "telefono": recortar(datos.get("telefono")),
        "email": recortar(datos.get("email")),
        "domicilio": recortar(datos.get("domicilio")),
    }


def _siguiente_codigo(mayor_codigo):
    """Calcula el código siguiente al mayor asignado (RN-04, RN-05, D-06)."""
    if mayor_codigo is None:
        return "HC-000001"
    numero = int(mayor_codigo.removeprefix("HC-"))
    return f"HC-{numero + 1:06d}"


def registrar_paciente(ruta_bd, datos):
    """Registra un paciente nuevo y le asigna su código de historia clínica (RF-01, RF-02).

    La transacción exclusiva impide que dos registros simultáneos reciban el mismo código o el
    mismo documento (PD-04). Si se lanza un error, no se guarda nada ni se consume código
    (PD-03). Lanza ErrorValidacion, PacienteDuplicado (RN-07, CA-08, PD-09) o
    CodigosAgotados (CL-04).
    """
    valores = validar_datos(datos)
    with closing(base_datos.conectar(ruta_bd)) as conexion:
        conexion.execute("BEGIN IMMEDIATE")
        try:
            existente = base_datos.obtener_por_documento(
                conexion, valores["tipo_documento"], valores["numero_documento"]
            )
            if existente is not None:
                raise PacienteDuplicado(_fila_a_paciente(existente))
            mayor_codigo = base_datos.obtener_mayor_codigo(conexion)
            if mayor_codigo == ULTIMO_CODIGO:
                raise CodigosAgotados()
            valores["codigo_historia"] = _siguiente_codigo(mayor_codigo)
            valores["fecha_registro"] = date.today().isoformat()
            base_datos.insertar_paciente(conexion, valores)
            conexion.execute("COMMIT")
        except sqlite3.IntegrityError:
            conexion.execute("ROLLBACK")
            existente = base_datos.obtener_por_documento(
                conexion, valores["tipo_documento"], valores["numero_documento"]
            )
            if existente is None:
                raise
            raise PacienteDuplicado(_fila_a_paciente(existente)) from None
        except BaseException:
            conexion.execute("ROLLBACK")
            raise
    return Paciente(**{campo: valores[campo] for campo in base_datos.CAMPOS})


def buscar_por_codigo(ruta_bd, codigo):
    """Devuelve el paciente con ese código de historia clínica o None (RF-04, PD-06, CL-01).

    El código introducido se normaliza, pero debe ser el código completo.
    """
    with closing(base_datos.conectar(ruta_bd)) as conexion:
        fila = base_datos.obtener_por_codigo(conexion, normalizar_texto(codigo))
    return _fila_a_paciente(fila)


def modificar_paciente(ruta_bd, codigo, datos):
    """Modifica los datos de un paciente registrado salvo su código (RF-06, RN-11).

    Aplica las mismas validaciones que el registro (PD-01) y comprueba que el documento no
    pertenece a otro paciente (PD-02, PD-09); el último guardado prevalece (PD-14).
    Lanza PacienteNoEncontrado, ErrorValidacion o PacienteDuplicado (CA-10).
    """
    codigo_historia = normalizar_texto(codigo)
    with closing(base_datos.conectar(ruta_bd)) as conexion:
        if base_datos.obtener_por_codigo(conexion, codigo_historia) is None:
            raise PacienteNoEncontrado(codigo)
        valores = validar_datos(datos)
        conexion.execute("BEGIN IMMEDIATE")
        try:
            existente = base_datos.obtener_por_documento(
                conexion, valores["tipo_documento"], valores["numero_documento"]
            )
            if existente is not None and existente["codigo_historia"] != codigo_historia:
                raise PacienteDuplicado(_fila_a_paciente(existente))
            base_datos.actualizar_paciente(conexion, codigo_historia, valores)
            conexion.execute("COMMIT")
        except sqlite3.IntegrityError:
            conexion.execute("ROLLBACK")
            existente = base_datos.obtener_por_documento(
                conexion, valores["tipo_documento"], valores["numero_documento"]
            )
            if existente is None:
                raise
            raise PacienteDuplicado(_fila_a_paciente(existente)) from None
        except BaseException:
            conexion.execute("ROLLBACK")
            raise
        fila = base_datos.obtener_por_codigo(conexion, codigo_historia)
    return _fila_a_paciente(fila)


def buscar_por_documento(ruta_bd, tipo_documento, numero_documento):
    """Devuelve el paciente con ese tipo y número de documento o None (RF-03, PD-08, CL-01).

    El número se normaliza (RN-08, CA-07, CL-02, PD-10); nunca devuelve más de un paciente.
    """
    tipo = (recortar(tipo_documento) or "").upper()
    numero = normalizar_texto(numero_documento)
    if tipo not in TIPOS_DOCUMENTO or not numero:
        return None
    with closing(base_datos.conectar(ruta_bd)) as conexion:
        fila = base_datos.obtener_por_documento(conexion, tipo, numero)
    return _fila_a_paciente(fila)
