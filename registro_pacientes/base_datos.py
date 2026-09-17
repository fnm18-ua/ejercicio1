"""Acceso a la base de datos SQLite del módulo (data-model.md; D-04, D-05, D-06).

Todas las consultas usan parámetros (D-10). Las restricciones del esquema garantizan la unicidad
del código y del documento aunque haya escrituras simultáneas (RN-07, PD-04).
"""

import sqlite3
from pathlib import Path

ESQUEMA = """
CREATE TABLE IF NOT EXISTS paciente (
    codigo_historia TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    apellidos TEXT NOT NULL,
    fecha_nacimiento TEXT NOT NULL,
    tipo_documento TEXT NOT NULL CHECK (tipo_documento IN ('DNI', 'NIE', 'PASAPORTE')),
    numero_documento TEXT NOT NULL,
    tipo_cobertura TEXT NOT NULL CHECK (tipo_cobertura IN ('MUTUA', 'SIN_COBERTURA')),
    mutua TEXT,
    numero_poliza TEXT,
    telefono TEXT,
    email TEXT,
    domicilio TEXT,
    fecha_registro TEXT NOT NULL,
    UNIQUE (tipo_documento, numero_documento),
    CHECK (
        (tipo_cobertura = 'MUTUA' AND mutua IS NOT NULL AND numero_poliza IS NOT NULL)
        OR (tipo_cobertura = 'SIN_COBERTURA' AND mutua IS NULL AND numero_poliza IS NULL)
    )
)
"""

CAMPOS = (
    "codigo_historia",
    "nombre",
    "apellidos",
    "fecha_nacimiento",
    "tipo_documento",
    "numero_documento",
    "tipo_cobertura",
    "mutua",
    "numero_poliza",
    "telefono",
    "email",
    "domicilio",
    "fecha_registro",
)


def conectar(ruta_bd):
    """Abre la base de datos, creando su carpeta si no existe (PD-11).

    Las transacciones son explícitas (isolation_level=None) para poder usar BEGIN IMMEDIATE.
    """
    Path(ruta_bd).parent.mkdir(parents=True, exist_ok=True)
    conexion = sqlite3.connect(ruta_bd, isolation_level=None)
    conexion.row_factory = sqlite3.Row
    return conexion


def crear_esquema(conexion):
    """Crea la tabla paciente si no existe, sin borrar datos (PD-11; data-model.md)."""
    conexion.execute(ESQUEMA)


def obtener_mayor_codigo(conexion):
    """Devuelve el mayor código asignado o None si no hay pacientes (RN-05, CL-04, D-06)."""
    return conexion.execute("SELECT MAX(codigo_historia) FROM paciente").fetchone()[0]


def insertar_paciente(conexion, valores):
    """Inserta un paciente con los 13 campos de la tabla (RF-01, RF-02, RN-10)."""
    columnas = ", ".join(CAMPOS)
    marcadores = ", ".join("?" for _ in CAMPOS)
    conexion.execute(
        f"INSERT INTO paciente ({columnas}) VALUES ({marcadores})",
        tuple(valores[campo] for campo in CAMPOS),
    )


CAMPOS_EDITABLES = tuple(
    campo for campo in CAMPOS if campo not in ("codigo_historia", "fecha_registro")
)


def actualizar_paciente(conexion, codigo_historia, valores):
    """Actualiza los 11 campos editables de un paciente (RF-06, PD-14).

    Nunca modifica codigo_historia ni fecha_registro (RN-06, RN-10, CA-12).
    """
    asignaciones = ", ".join(f"{campo} = ?" for campo in CAMPOS_EDITABLES)
    conexion.execute(
        f"UPDATE paciente SET {asignaciones} WHERE codigo_historia = ?",
        tuple(valores[campo] for campo in CAMPOS_EDITABLES) + (codigo_historia,),
    )


def obtener_por_codigo(conexion, codigo_historia):
    """Devuelve la fila del paciente con ese código o None (RF-04)."""
    return conexion.execute(
        "SELECT * FROM paciente WHERE codigo_historia = ?", (codigo_historia,)
    ).fetchone()


def obtener_por_documento(conexion, tipo_documento, numero_documento):
    """Devuelve la fila del paciente con ese tipo y número de documento o None (RF-03, RN-07)."""
    return conexion.execute(
        "SELECT * FROM paciente WHERE tipo_documento = ? AND numero_documento = ?",
        (tipo_documento, numero_documento),
    ).fetchone()
