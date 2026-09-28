"""Acceso a las tablas del módulo de citas (data-model.md; D-C02, D-C07, D-C08).

Las cinco tablas viven en la misma base de datos SQLite que la tabla `paciente` del módulo de
registro, de modo que una cita puede referenciar al paciente por su código de historia clínica
(RN-C05, D-C02). La conexión se reutiliza del módulo de registro: no se redefine aquí.

Todas las consultas usan parámetros. Dos restricciones del esquema hacen inviolables sendas reglas
de negocio: el CHECK de `motivo_cancelacion` (RN-C13) y el índice único parcial `hueco_ocupado`
(RN-C04, CL-C03).
"""

from registro_pacientes.base_datos import conectar  # noqa: F401  (reexportado a propósito, D-C02)

ESQUEMA = (
    """
    CREATE TABLE IF NOT EXISTS centro (
        id_centro INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS especialidad (
        id_especialidad INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL UNIQUE
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS especialista (
        id_especialista INTEGER PRIMARY KEY,
        nombre TEXT NOT NULL,
        id_centro INTEGER NOT NULL REFERENCES centro (id_centro),
        id_especialidad INTEGER NOT NULL REFERENCES especialidad (id_especialidad),
        dias_semana TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL,
        duracion_minutos INTEGER NOT NULL CHECK (duracion_minutos > 0)
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS cita (
        id_cita INTEGER PRIMARY KEY,
        codigo_historia TEXT NOT NULL REFERENCES paciente (codigo_historia),
        id_especialista INTEGER NOT NULL REFERENCES especialista (id_especialista),
        fecha TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        estado TEXT NOT NULL CHECK (
            estado IN ('RESERVADA', 'CANCELADA_PACIENTE', 'CANCELADA_CENTRO')
        ),
        motivo_cancelacion TEXT,
        momento_reserva TEXT NOT NULL,
        CHECK (
            (estado = 'RESERVADA' AND motivo_cancelacion IS NULL)
            OR (estado <> 'RESERVADA' AND motivo_cancelacion IS NOT NULL)
        )
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS franja_bloqueada (
        id_franja INTEGER PRIMARY KEY,
        id_especialista INTEGER NOT NULL REFERENCES especialista (id_especialista),
        fecha_inicio TEXT NOT NULL,
        fecha_fin TEXT NOT NULL,
        hora_inicio TEXT NOT NULL,
        hora_fin TEXT NOT NULL
    )
    """,
    # RN-C04, PD-C17 y CL-C03: un hueco no puede tener dos citas reservadas. Es parcial porque las
    # citas canceladas no ocupan hueco (RN-C06, PD-C04) y ese hueco debe poder reservarse de nuevo.
    """
    CREATE UNIQUE INDEX IF NOT EXISTS hueco_ocupado
        ON cita (id_especialista, fecha, hora_inicio)
        WHERE estado = 'RESERVADA'
    """,
)

SELECCION_ESPECIALISTA = """
SELECT especialista.id_especialista, especialista.nombre, centro.nombre AS centro,
       especialidad.nombre AS especialidad, especialista.dias_semana,
       especialista.hora_inicio, especialista.hora_fin, especialista.duracion_minutos
FROM especialista
JOIN centro ON centro.id_centro = especialista.id_centro
JOIN especialidad ON especialidad.id_especialidad = especialista.id_especialidad
"""

SELECCION_CITA = """
SELECT cita.id_cita, cita.codigo_historia, cita.id_especialista,
       especialista.nombre AS nombre_especialista, especialidad.nombre AS especialidad,
       centro.nombre AS centro, cita.fecha, cita.hora_inicio,
       especialista.duracion_minutos, cita.estado, cita.motivo_cancelacion,
       cita.momento_reserva
FROM cita
JOIN especialista ON especialista.id_especialista = cita.id_especialista
JOIN centro ON centro.id_centro = especialista.id_centro
JOIN especialidad ON especialidad.id_especialidad = especialista.id_especialidad
"""


def crear_esquema(conexion):
    """Crea las cinco tablas y el índice único parcial si no existen, sin borrar datos."""
    for sentencia in ESQUEMA:
        conexion.execute(sentencia)


def listar_centros(conexion):
    """Nombres de los centros, ordenados (RN-C01)."""
    return conexion.execute("SELECT * FROM centro ORDER BY nombre").fetchall()


def listar_especialidades(conexion):
    """Nombres de las especialidades, ordenados (RN-C01)."""
    return conexion.execute("SELECT * FROM especialidad ORDER BY nombre").fetchall()


def buscar_especialistas(conexion, especialidad, centro):
    """Especialistas que cumplen los dos filtros (RF-C02, CA-C03, PD-C15)."""
    return conexion.execute(
        SELECCION_ESPECIALISTA
        + " WHERE especialidad.nombre = ? AND centro.nombre = ? ORDER BY especialista.nombre",
        (especialidad, centro),
    ).fetchall()


def obtener_especialista(conexion, id_especialista):
    """Devuelve el especialista con ese identificador o None."""
    return conexion.execute(
        SELECCION_ESPECIALISTA + " WHERE especialista.id_especialista = ?",
        (id_especialista,),
    ).fetchone()


def listar_especialistas(conexion):
    """Todos los especialistas con su centro y su especialidad (RF-C08, RF-C09)."""
    return conexion.execute(
        SELECCION_ESPECIALISTA + " ORDER BY centro, especialidad, especialista.nombre"
    ).fetchall()


def citas_reservadas_de(conexion, id_especialista, fecha):
    """Citas reservadas de un especialista en una fecha (RN-C04)."""
    return conexion.execute(
        "SELECT * FROM cita WHERE id_especialista = ? AND fecha = ? AND estado = 'RESERVADA'",
        (id_especialista, fecha),
    ).fetchall()


def citas_reservadas_futuras_de(conexion, id_especialista, momento):
    """Citas reservadas de un especialista cuyo inicio es posterior a `momento` (PD-C11).

    `momento` llega como `YYYY-MM-DD HH:MM`; la comparación funciona porque el formato ISO hace
    coincidir el orden lexicográfico con el cronológico (D-C09).
    """
    return conexion.execute(
        "SELECT * FROM cita WHERE id_especialista = ? AND estado = 'RESERVADA'"
        " AND fecha || ' ' || hora_inicio > ? ORDER BY fecha, hora_inicio",
        (id_especialista, momento),
    ).fetchall()


def franjas_de(conexion, id_especialista):
    """Franjas bloqueadas de un especialista (RN-C04, PD-C12)."""
    return conexion.execute(
        "SELECT * FROM franja_bloqueada WHERE id_especialista = ?", (id_especialista,)
    ).fetchall()


def insertar_cita(conexion, valores):
    """Inserta una cita y devuelve su identificador (RF-C04)."""
    cursor = conexion.execute(
        "INSERT INTO cita (codigo_historia, id_especialista, fecha, hora_inicio, estado,"
        " motivo_cancelacion, momento_reserva) VALUES (?, ?, ?, ?, ?, ?, ?)",
        (
            valores["codigo_historia"],
            valores["id_especialista"],
            valores["fecha"],
            valores["hora_inicio"],
            valores["estado"],
            valores["motivo_cancelacion"],
            valores["momento_reserva"],
        ),
    )
    return cursor.lastrowid


def obtener_cita(conexion, id_cita):
    """Devuelve la cita con ese identificador o None."""
    return conexion.execute(
        SELECCION_CITA + " WHERE cita.id_cita = ?", (id_cita,)
    ).fetchone()


def citas_de_paciente(conexion, codigo_historia):
    """Todas las citas de un paciente, pasadas y futuras (RF-C05, PD-C14)."""
    return conexion.execute(
        SELECCION_CITA + " WHERE cita.codigo_historia = ? ORDER BY cita.fecha, cita.hora_inicio",
        (codigo_historia,),
    ).fetchall()


def citas_reservadas_de_paciente(conexion, codigo_historia):
    """Citas reservadas de un paciente, para comprobar el solapamiento (RN-C07)."""
    return conexion.execute(
        SELECCION_CITA + " WHERE cita.codigo_historia = ? AND cita.estado = 'RESERVADA'",
        (codigo_historia,),
    ).fetchall()


def actualizar_estado_cita(conexion, id_cita, estado, motivo):
    """Cambia el estado y el motivo de una cita (RN-C06, RN-C13)."""
    conexion.execute(
        "UPDATE cita SET estado = ?, motivo_cancelacion = ? WHERE id_cita = ?",
        (estado, motivo, id_cita),
    )


def trasladar_cita(conexion, id_cita, fecha, hora_inicio, momento_reserva):
    """Mueve una cita de fecha y hora conservando su identificador (RN-C10, PD-C07, PD-C08)."""
    conexion.execute(
        "UPDATE cita SET fecha = ?, hora_inicio = ?, momento_reserva = ? WHERE id_cita = ?",
        (fecha, hora_inicio, momento_reserva, id_cita),
    )


def insertar_franja(conexion, valores):
    """Inserta una franja bloqueada (RF-C08, PD-C12)."""
    cursor = conexion.execute(
        "INSERT INTO franja_bloqueada (id_especialista, fecha_inicio, fecha_fin, hora_inicio,"
        " hora_fin) VALUES (?, ?, ?, ?, ?)",
        (
            valores["id_especialista"],
            valores["fecha_inicio"],
            valores["fecha_fin"],
            valores["hora_inicio"],
            valores["hora_fin"],
        ),
    )
    return cursor.lastrowid


def actualizar_duracion(conexion, id_especialista, duracion_minutos):
    """Cambia la duración de consulta de un especialista (RF-C09)."""
    conexion.execute(
        "UPDATE especialista SET duracion_minutos = ? WHERE id_especialista = ?",
        (duracion_minutos, id_especialista),
    )
