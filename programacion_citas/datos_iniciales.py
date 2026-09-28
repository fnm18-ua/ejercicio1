"""Precarga de centros, especialidades y especialistas (RN-C01, RN-C02, PD-C19, CA-C13, D-C12).

Son datos precargados: la aplicación no ofrece ninguna vía para crearlos, editarlos ni borrarlos.
La precarga es idempotente —solo inserta si la tabla está vacía—, de modo que arranques repetidos
con `docker compose up` no duplican filas ni pisan lo que haya (principio V).

Todos los nombres son INVENTADOS (principio IV): ni los centros, ni los especialistas, ni las
combinaciones corresponden a personas o entidades reales.
"""

ESPECIALIDADES = ("Dermatología", "Oftalmología", "Traumatología")

CENTROS = ("Centro Norte", "Centro Sur")

# (nombre, centro, especialidad, dias_semana, hora_inicio, hora_fin, duracion_minutos)
# El primero reproduce el caso de CA-C01: 9:00-13:00 con consultas de 20 minutos → 12 huecos.
# No existe ningún especialista de Traumatología en el Centro Sur, para poder validar CL-C02.
ESPECIALISTAS = (
    ("Ana Ruiz Delgado", "Centro Norte", "Dermatología", "1,2,3,4,5", "09:00", "13:00", 20),
    ("Marcos Herrera Pinto", "Centro Norte", "Oftalmología", "1,3,5", "10:00", "14:00", 30),
    ("Lucía Bernal Ortiz", "Centro Norte", "Traumatología", "2,4", "08:00", "13:00", 25),
    ("Daniel Sacristán Vega", "Centro Sur", "Dermatología", "1,2,3,4,5", "15:00", "19:00", 20),
    ("Nuria Calvo Esteban", "Centro Sur", "Oftalmología", "1,2,3", "09:00", "12:30", 50),
)


def _esta_vacia(conexion, tabla):
    """Si la tabla no tiene ninguna fila."""
    return conexion.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 0


def precargar(conexion):
    """Inserta los datos iniciales solo en las tablas que estén vacías (D-C12).

    Es idempotente: llamarla varias veces no duplica filas.
    """
    if _esta_vacia(conexion, "especialidad"):
        conexion.executemany(
            "INSERT INTO especialidad (nombre) VALUES (?)",
            [(nombre,) for nombre in ESPECIALIDADES],
        )
    if _esta_vacia(conexion, "centro"):
        conexion.executemany(
            "INSERT INTO centro (nombre) VALUES (?)", [(nombre,) for nombre in CENTROS]
        )
    if _esta_vacia(conexion, "especialista"):
        for nombre, centro, especialidad, dias, inicio, fin, duracion in ESPECIALISTAS:
            conexion.execute(
                "INSERT INTO especialista (nombre, id_centro, id_especialidad, dias_semana,"
                " hora_inicio, hora_fin, duracion_minutos) VALUES ("
                " ?, (SELECT id_centro FROM centro WHERE nombre = ?),"
                " (SELECT id_especialidad FROM especialidad WHERE nombre = ?), ?, ?, ?, ?)",
                (nombre, centro, especialidad, dias, inicio, fin, duracion),
            )
