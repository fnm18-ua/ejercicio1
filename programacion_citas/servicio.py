"""Reglas de negocio del módulo de citas (contracts/servicio-citas.md).

Toda la lógica vive aquí para que las pruebas de CA-C y CL-C no dependan del HTML (D-C15).

La identificación del paciente se delega en el módulo de registro (D-C04): así las dos vías
—código de historia clínica y documento de identidad— comparan igual y llevan al mismo paciente
(PD-C01, CA-C04). Este módulo NO crea, modifica ni borra pacientes (frontera del principio II).

Ninguna función consulta el reloj por su cuenta: el momento actual llega siempre como parámetro
`ahora` (D-C10), sin lo cual CA-C07, CA-C08 y PD-C11 no serían deterministas.
"""

import datetime
import sqlite3
from dataclasses import dataclass

from programacion_citas import agenda, base_datos, datos_iniciales
from registro_pacientes import servicio as servicio_pacientes

ESTADO_RESERVADA = "RESERVADA"
ESTADO_CANCELADA_PACIENTE = "CANCELADA_PACIENTE"
ESTADO_CANCELADA_CENTRO = "CANCELADA_CENTRO"

MOTIVO_PACIENTE = "A petición del paciente"
MOTIVO_FRANJA = "Franja bloqueada del especialista"
MOTIVO_DURACION = "Cambio de la duración de las consultas"

NOMBRES_ESTADO = {
    ESTADO_RESERVADA: "Reservada",
    ESTADO_CANCELADA_PACIENTE: "Cancelada por el paciente",
    ESTADO_CANCELADA_CENTRO: "Cancelada por el centro",
}

MINUTOS_24_HORAS = 24 * 60


@dataclass(frozen=True)
class Especialista:
    """Especialista con su centro, especialidad, horario y duración de consulta (RN-C02)."""

    id_especialista: int
    nombre: str
    centro: str
    especialidad: str
    dias_semana: str
    hora_inicio: str
    hora_fin: str
    duracion_minutos: int


@dataclass(frozen=True)
class Hueco:
    """Hueco derivado de la rejilla; nunca se almacena (RN-C03, D-C05)."""

    hora_inicio: str
    duracion_minutos: int
    libre: bool


@dataclass(frozen=True)
class Cita:
    """Cita de un paciente con un especialista (RN-C05, RN-C06).

    `duracion_minutos` es la duración vigente del especialista, no un dato de la cita (PD-C10).
    `momento_reserva` es el de la última reserva o reprogramación (PD-C07).
    """

    id_cita: int
    codigo_historia: str
    id_especialista: int
    nombre_especialista: str
    especialidad: str
    centro: str
    fecha: str
    hora_inicio: str
    duracion_minutos: int
    estado: str
    motivo_cancelacion: str
    momento_reserva: str

    @property
    def nombre_estado(self):
        """Estado en español para mostrarlo en la interfaz (principio I)."""
        return NOMBRES_ESTADO[self.estado]


class PacienteNoIdentificado(Exception):
    """El código o el documento no corresponde a ningún paciente (RF-C01, CL-C09)."""

    def __init__(self):
        super().__init__("No existe ningún paciente con esos datos.")


class HuecoNoDisponible(Exception):
    """El hueco está ocupado, bloqueado o no existe en la rejilla (RN-C04, CL-C03)."""

    def __init__(self):
        super().__init__("Ese hueco ya no está disponible.")


class HuecoPasado(Exception):
    """La hora de inicio del hueco ya ha pasado (RN-C08, PD-C05)."""

    def __init__(self):
        super().__init__("No se puede reservar un hueco cuya hora ya ha pasado.")


class CitaSolapada(Exception):
    """El paciente ya tiene otra cita reservada que se solapa (RN-C07, CA-C05)."""

    def __init__(self):
        super().__init__("Ya tiene otra cita reservada a esa hora.")


class FueraDePlazo(Exception):
    """Fuera del plazo de 24 horas de RN-C09 (CA-C07)."""

    def __init__(self):
        super().__init__(
            "Solo se puede cancelar o reprogramar hasta 24 horas antes del inicio de la cita."
        )


class CitaYaCancelada(Exception):
    """La cita no está en estado reservada (CL-C07, CL-C08)."""

    def __init__(self):
        super().__init__("Esa cita ya está cancelada.")


class CitaNoEncontrada(Exception):
    """No existe cita con ese identificador para ese paciente (RF-C06, RF-C07)."""

    def __init__(self):
        super().__init__("No existe esa cita.")


class ErrorValidacion(Exception):
    """Datos de entrada ausentes o mal formados (PD-C18)."""

    def __init__(self, mensaje):
        super().__init__(mensaje)
        self.mensaje = mensaje


def momento_actual():
    """Único punto del módulo que consulta el reloj del sistema (D-C10)."""
    return datetime.datetime.now()


def _texto_momento(momento):
    """Formatea un momento como `YYYY-MM-DD HH:MM:SS` (D-C09)."""
    return momento.strftime("%Y-%m-%d %H:%M:%S")


def _minutos_hasta(momento, fecha, hora_inicio):
    """Minutos desde `momento` hasta el inicio de una cita; negativo si ya pasó."""
    inicio = datetime.datetime.combine(
        datetime.date.fromisoformat(fecha),
        datetime.time(agenda.a_minutos(hora_inicio) // 60, agenda.a_minutos(hora_inicio) % 60),
    )
    return (inicio - momento).total_seconds() / 60


def _a_especialista(fila):
    """Convierte una fila en un `Especialista`."""
    return Especialista(
        id_especialista=fila["id_especialista"],
        nombre=fila["nombre"],
        centro=fila["centro"],
        especialidad=fila["especialidad"],
        dias_semana=fila["dias_semana"],
        hora_inicio=fila["hora_inicio"],
        hora_fin=fila["hora_fin"],
        duracion_minutos=fila["duracion_minutos"],
    )


def _a_cita(fila):
    """Convierte una fila en una `Cita`."""
    return Cita(
        id_cita=fila["id_cita"],
        codigo_historia=fila["codigo_historia"],
        id_especialista=fila["id_especialista"],
        nombre_especialista=fila["nombre_especialista"],
        especialidad=fila["especialidad"],
        centro=fila["centro"],
        fecha=fila["fecha"],
        hora_inicio=fila["hora_inicio"],
        duracion_minutos=fila["duracion_minutos"],
        estado=fila["estado"],
        motivo_cancelacion=fila["motivo_cancelacion"],
        momento_reserva=fila["momento_reserva"],
    )


def inicializar_base_datos(ruta_bd):
    """Prepara la base de datos de los dos módulos y precarga la agenda (D-C12, D-C13).

    Llama primero al módulo de registro para que la tabla `paciente` exista, porque `cita` la
    referencia (RN-C05). Es idempotente: no borra datos ni duplica la precarga.
    """
    servicio_pacientes.inicializar_base_datos(ruta_bd)
    conexion = base_datos.conectar(ruta_bd)
    try:
        base_datos.crear_esquema(conexion)
        datos_iniciales.precargar(conexion)
    finally:
        conexion.close()


def identificar_paciente(ruta_bd, codigo=None, tipo_documento=None, numero_documento=None):
    """Código de historia clínica del paciente identificado (RF-C01, PD-C01, CA-C04, CL-C09).

    Delega en el módulo de registro, de modo que la comparación es normalizada y las dos vías
    llevan al mismo paciente. NO crea pacientes.
    """
    paciente = None
    if codigo:
        paciente = servicio_pacientes.buscar_por_codigo(ruta_bd, codigo)
    elif tipo_documento and numero_documento:
        paciente = servicio_pacientes.buscar_por_documento(
            ruta_bd, tipo_documento, numero_documento
        )
    if paciente is None:
        raise PacienteNoIdentificado()
    return paciente.codigo_historia


def listar_catalogo(ruta_bd):
    """Especialidades y centros precargados, para los desplegables (RN-C01, PD-C19)."""
    conexion = base_datos.conectar(ruta_bd)
    try:
        especialidades = [fila["nombre"] for fila in base_datos.listar_especialidades(conexion)]
        centros = [fila["nombre"] for fila in base_datos.listar_centros(conexion)]
    finally:
        conexion.close()
    return especialidades, centros


def buscar_especialistas(ruta_bd, especialidad, centro):
    """Especialistas que cumplen los dos filtros (RF-C02, CA-C03, CL-C02, PD-C15)."""
    if not especialidad or not centro:
        raise ErrorValidacion("Indique la especialidad y el centro.")
    conexion = base_datos.conectar(ruta_bd)
    try:
        return [
            _a_especialista(fila)
            for fila in base_datos.buscar_especialistas(conexion, especialidad, centro)
        ]
    finally:
        conexion.close()


def obtener_especialista(ruta_bd, id_especialista):
    """Especialista con ese identificador o None."""
    conexion = base_datos.conectar(ruta_bd)
    try:
        fila = base_datos.obtener_especialista(conexion, id_especialista)
        return _a_especialista(fila) if fila else None
    finally:
        conexion.close()


def listar_especialistas(ruta_bd):
    """Todos los especialistas, para el flujo de la agenda (RF-C08, RF-C09)."""
    conexion = base_datos.conectar(ruta_bd)
    try:
        return [_a_especialista(fila) for fila in base_datos.listar_especialistas(conexion)]
    finally:
        conexion.close()


def _validar_fecha(fecha):
    """Comprueba que la fecha es `YYYY-MM-DD` y la devuelve (PD-C18)."""
    try:
        datetime.date.fromisoformat(fecha)
    except (TypeError, ValueError):
        raise ErrorValidacion("La fecha indicada no es válida.") from None
    return fecha


def _validar_hora(hora):
    """Comprueba que la hora es `HH:MM` y la devuelve (PD-C18)."""
    if not hora or len(hora) < 5:
        raise ErrorValidacion("La hora indicada no es válida.")
    try:
        datetime.time(agenda.a_minutos(hora) // 60, agenda.a_minutos(hora) % 60)
    except (TypeError, ValueError):
        raise ErrorValidacion("La hora indicada no es válida.") from None
    return hora[:5]


def _huecos_bloqueados(conexion, especialista, fecha):
    """Horas de inicio de la rejilla que caen en una franja bloqueada (RN-C04, PD-C12)."""
    rejilla = agenda.generar_rejilla(
        especialista.dias_semana,
        especialista.hora_inicio,
        especialista.hora_fin,
        especialista.duracion_minutos,
        fecha,
    )
    bloqueados = set()
    for franja in base_datos.franjas_de(conexion, especialista.id_especialista):
        if not franja["fecha_inicio"] <= fecha <= franja["fecha_fin"]:
            continue
        for hora in rejilla:
            if agenda.hueco_en_franja(
                hora,
                especialista.duracion_minutos,
                franja["hora_inicio"],
                franja["hora_fin"],
            ):
                bloqueados.add(hora)
    return rejilla, bloqueados


def consultar_huecos(ruta_bd, id_especialista, fecha, ahora):
    """Huecos libres de un especialista en una fecha (RF-C03, RN-C03, RN-C04, RN-C08).

    Excluye los ocupados por citas reservadas, los que caen en franja bloqueada (PD-C12) y los ya
    pasados (PD-C05). Lista vacía si no hay ninguno o si no es día de consulta (CL-C01, CL-C06).
    """
    _validar_fecha(fecha)
    conexion = base_datos.conectar(ruta_bd)
    try:
        fila = base_datos.obtener_especialista(conexion, id_especialista)
        if fila is None:
            raise ErrorValidacion("El especialista indicado no existe.")
        especialista = _a_especialista(fila)
        rejilla, bloqueados = _huecos_bloqueados(conexion, especialista, fecha)
        ocupados = {
            cita["hora_inicio"]
            for cita in base_datos.citas_reservadas_de(conexion, id_especialista, fecha)
        }
    finally:
        conexion.close()
    libres = []
    for hora in rejilla:
        if hora in ocupados or hora in bloqueados:
            continue
        if _minutos_hasta(ahora, fecha, hora) < 0:
            continue
        libres.append(Hueco(hora, especialista.duracion_minutos, True))
    return libres


def _comprobar_solapamiento(conexion, codigo_historia, fecha, hora_inicio, duracion, excluir=None):
    """Lanza `CitaSolapada` si el paciente ya tiene otra cita reservada solapada (RN-C07).

    `excluir` es el identificador de la cita que se está trasladando, que no debe contarse contra
    sí misma (PD-C08).
    """
    for fila in base_datos.citas_reservadas_de_paciente(conexion, codigo_historia):
        if fila["id_cita"] == excluir or fila["fecha"] != fecha:
            continue
        if agenda.se_solapan(
            hora_inicio, duracion, fila["hora_inicio"], fila["duracion_minutos"]
        ):
            raise CitaSolapada()


def _comprobar_hueco(conexion, especialista, fecha, hora_inicio, ahora, excluir=None):
    """Comprueba que el hueco existe, no ha pasado, no está bloqueado y no está ocupado."""
    rejilla, bloqueados = _huecos_bloqueados(conexion, especialista, fecha)
    if hora_inicio not in rejilla:
        raise HuecoNoDisponible()
    if _minutos_hasta(ahora, fecha, hora_inicio) < 0:
        raise HuecoPasado()
    if hora_inicio in bloqueados:
        raise HuecoNoDisponible()
    for cita in base_datos.citas_reservadas_de(conexion, especialista.id_especialista, fecha):
        if cita["hora_inicio"] == hora_inicio and cita["id_cita"] != excluir:
            raise HuecoNoDisponible()


def reservar_cita(ruta_bd, codigo_historia, id_especialista, fecha, hora_inicio, ahora):
    """Reserva un hueco libre para el paciente identificado (RF-C04).

    Comprueba el hueco (RN-C04, RN-C08) y el solapamiento del paciente (RN-C07) dentro de una
    transacción inmediata. Si el índice único parcial rechaza la inserción porque otra persona
    acaba de ocupar el hueco, se traduce a `HuecoNoDisponible` (CL-C03, PD-C17).
    """
    _validar_fecha(fecha)
    hora_inicio = _validar_hora(hora_inicio)
    conexion = base_datos.conectar(ruta_bd)
    try:
        conexion.execute("BEGIN IMMEDIATE")
        fila = base_datos.obtener_especialista(conexion, id_especialista)
        if fila is None:
            raise ErrorValidacion("El especialista indicado no existe.")
        especialista = _a_especialista(fila)
        _comprobar_hueco(conexion, especialista, fecha, hora_inicio, ahora)
        _comprobar_solapamiento(
            conexion, codigo_historia, fecha, hora_inicio, especialista.duracion_minutos
        )
        try:
            id_cita = base_datos.insertar_cita(
                conexion,
                {
                    "codigo_historia": codigo_historia,
                    "id_especialista": id_especialista,
                    "fecha": fecha,
                    "hora_inicio": hora_inicio,
                    "estado": ESTADO_RESERVADA,
                    "motivo_cancelacion": None,
                    "momento_reserva": _texto_momento(ahora),
                },
            )
        except sqlite3.IntegrityError:
            raise HuecoNoDisponible() from None
        cita = _a_cita(base_datos.obtener_cita(conexion, id_cita))
        conexion.execute("COMMIT")
        return cita
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()


def consultar_citas(ruta_bd, codigo_historia):
    """Todas las citas del paciente, pasadas y futuras, con su estado y motivo (RF-C05, PD-C14).

    No existe estado «atendida» —la asistencia está fuera de alcance—, por lo que una cita pasada
    permanece reservada.
    """
    conexion = base_datos.conectar(ruta_bd)
    try:
        return [
            _a_cita(fila) for fila in base_datos.citas_de_paciente(conexion, codigo_historia)
        ]
    finally:
        conexion.close()


def _cita_del_paciente(conexion, codigo_historia, id_cita):
    """Devuelve la cita si es de ese paciente, o lanza `CitaNoEncontrada`."""
    fila = base_datos.obtener_cita(conexion, id_cita)
    if fila is None or fila["codigo_historia"] != codigo_historia:
        raise CitaNoEncontrada()
    return _a_cita(fila)


def _comprobar_plazo(cita, ahora):
    """Comprueba el plazo de RN-C09 (CA-C06, CA-C07, CA-C08, PD-C07).

    Se permite si faltan 24 horas o más para el inicio. Si falta menos, solo se permite cuando la
    cita se reservó a menos de 24 horas de su inicio. `momento_reserva` es el de la última reserva
    o reprogramación: reprogramar lo actualiza (PD-C07, aclaración Q2 del 2026-09-28).
    """
    if _minutos_hasta(ahora, cita.fecha, cita.hora_inicio) >= MINUTOS_24_HORAS:
        return
    reserva = datetime.datetime.strptime(cita.momento_reserva, "%Y-%m-%d %H:%M:%S")
    if _minutos_hasta(reserva, cita.fecha, cita.hora_inicio) < MINUTOS_24_HORAS:
        return
    raise FueraDePlazo()


def cancelar_cita(ruta_bd, codigo_historia, id_cita, ahora):
    """Cancela una cita reservada a petición del paciente (RF-C06, RN-C09, RN-C13).

    Deja la cita en `CANCELADA_PACIENTE` con su motivo y libera su hueco (CA-C06, PD-C04).
    """
    conexion = base_datos.conectar(ruta_bd)
    try:
        conexion.execute("BEGIN IMMEDIATE")
        cita = _cita_del_paciente(conexion, codigo_historia, id_cita)
        if cita.estado != ESTADO_RESERVADA:
            raise CitaYaCancelada()
        _comprobar_plazo(cita, ahora)
        base_datos.actualizar_estado_cita(
            conexion, id_cita, ESTADO_CANCELADA_PACIENTE, MOTIVO_PACIENTE
        )
        cancelada = _a_cita(base_datos.obtener_cita(conexion, id_cita))
        conexion.execute("COMMIT")
        return cancelada
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()


def reprogramar_cita(ruta_bd, codigo_historia, id_cita, fecha, hora_inicio, ahora):
    """Traslada una cita a otro hueco libre del mismo especialista (RF-C07, RN-C10).

    Conserva el identificador, el paciente y el especialista; cambia fecha, hora y el momento de
    referencia de las 24 horas (PD-C07, PD-C08, CA-C09). Es un UPDATE, nunca borrar e insertar, y
    el hueco anterior queda libre por el propio traslado.
    """
    _validar_fecha(fecha)
    hora_inicio = _validar_hora(hora_inicio)
    conexion = base_datos.conectar(ruta_bd)
    try:
        conexion.execute("BEGIN IMMEDIATE")
        cita = _cita_del_paciente(conexion, codigo_historia, id_cita)
        if cita.estado != ESTADO_RESERVADA:
            raise CitaYaCancelada()
        _comprobar_plazo(cita, ahora)
        especialista = _a_especialista(
            base_datos.obtener_especialista(conexion, cita.id_especialista)
        )
        _comprobar_hueco(
            conexion, especialista, fecha, hora_inicio, ahora, excluir=id_cita
        )
        _comprobar_solapamiento(
            conexion,
            codigo_historia,
            fecha,
            hora_inicio,
            especialista.duracion_minutos,
            excluir=id_cita,
        )
        try:
            base_datos.trasladar_cita(
                conexion, id_cita, fecha, hora_inicio, _texto_momento(ahora)
            )
        except sqlite3.IntegrityError:
            raise HuecoNoDisponible() from None
        trasladada = _a_cita(base_datos.obtener_cita(conexion, id_cita))
        conexion.execute("COMMIT")
        return trasladada
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()


def bloquear_franja(
    ruta_bd, id_especialista, fecha_inicio, fecha_fin, hora_inicio, hora_fin, ahora
):
    """Bloquea una franja de un especialista y cancela por el centro las citas futuras (RF-C08).

    La franja abarca un rango de fechas y un tramo horario que se aplica a cada día del rango
    (PD-C12). Solo se cancelan las citas FUTURAS (PD-C11): una cita cuya hora ya pasó no cambia de
    estado, porque es historial y no agenda. No está sujeta al plazo de 24 horas (RN-C11).
    """
    _validar_fecha(fecha_inicio)
    _validar_fecha(fecha_fin)
    hora_inicio = _validar_hora(hora_inicio)
    hora_fin = _validar_hora(hora_fin)
    if fecha_fin < fecha_inicio:
        raise ErrorValidacion("La fecha de fin no puede ser anterior a la de inicio.")
    if agenda.a_minutos(hora_fin) <= agenda.a_minutos(hora_inicio):
        raise ErrorValidacion("La hora de fin debe ser posterior a la de inicio.")
    conexion = base_datos.conectar(ruta_bd)
    try:
        conexion.execute("BEGIN IMMEDIATE")
        fila = base_datos.obtener_especialista(conexion, id_especialista)
        if fila is None:
            raise ErrorValidacion("El especialista indicado no existe.")
        especialista = _a_especialista(fila)
        base_datos.insertar_franja(
            conexion,
            {
                "id_especialista": id_especialista,
                "fecha_inicio": fecha_inicio,
                "fecha_fin": fecha_fin,
                "hora_inicio": hora_inicio,
                "hora_fin": hora_fin,
            },
        )
        canceladas = []
        futuras = base_datos.citas_reservadas_futuras_de(
            conexion, id_especialista, ahora.strftime("%Y-%m-%d %H:%M")
        )
        for cita in futuras:
            if not fecha_inicio <= cita["fecha"] <= fecha_fin:
                continue
            if not agenda.hueco_en_franja(
                cita["hora_inicio"], especialista.duracion_minutos, hora_inicio, hora_fin
            ):
                continue
            base_datos.actualizar_estado_cita(
                conexion, cita["id_cita"], ESTADO_CANCELADA_CENTRO, MOTIVO_FRANJA
            )
            canceladas.append(_a_cita(base_datos.obtener_cita(conexion, cita["id_cita"])))
        conexion.execute("COMMIT")
        return canceladas
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()


def ajustar_duracion(ruta_bd, id_especialista, duracion_minutos, ahora):
    """Cambia la duración de las consultas y recalcula la rejilla (RF-C09, RN-C12).

    Cancela por el centro las citas FUTURAS reservadas que ya no encajan en la rejilla nueva
    (PD-C10, PD-C11): al pasar de 20 a 30 minutos, la de las 9:00 sobrevive y la de las 9:20 no
    (CA-C12). Las citas pasadas no se tocan (PD-C11).

    Limitación declarada (PD-C20): NO se vuelve a comprobar RN-C07. Si al alargarse las consultas
    dos citas de un mismo paciente pasan a solaparse, ambas se conservan. Es una limitación
    conocida y documentada, no un defecto silencioso.
    """
    try:
        duracion_minutos = int(duracion_minutos)
    except (TypeError, ValueError):
        raise ErrorValidacion("La duración debe ser un número entero de minutos.") from None
    if duracion_minutos <= 0:
        raise ErrorValidacion("La duración debe ser mayor que cero.")
    conexion = base_datos.conectar(ruta_bd)
    try:
        conexion.execute("BEGIN IMMEDIATE")
        fila = base_datos.obtener_especialista(conexion, id_especialista)
        if fila is None:
            raise ErrorValidacion("El especialista indicado no existe.")
        base_datos.actualizar_duracion(conexion, id_especialista, duracion_minutos)
        especialista = _a_especialista(
            base_datos.obtener_especialista(conexion, id_especialista)
        )
        canceladas = []
        futuras = base_datos.citas_reservadas_futuras_de(
            conexion, id_especialista, ahora.strftime("%Y-%m-%d %H:%M")
        )
        rejillas = {}
        for cita in futuras:
            fecha = cita["fecha"]
            if fecha not in rejillas:
                rejillas[fecha] = agenda.generar_rejilla(
                    especialista.dias_semana,
                    especialista.hora_inicio,
                    especialista.hora_fin,
                    duracion_minutos,
                    fecha,
                )
            if agenda.encaja_en_rejilla(
                cita["hora_inicio"], rejillas[fecha], especialista.hora_fin, duracion_minutos
            ):
                continue
            base_datos.actualizar_estado_cita(
                conexion, cita["id_cita"], ESTADO_CANCELADA_CENTRO, MOTIVO_DURACION
            )
            canceladas.append(_a_cita(base_datos.obtener_cita(conexion, cita["id_cita"])))
        conexion.execute("COMMIT")
        return canceladas
    except Exception:
        conexion.execute("ROLLBACK")
        raise
    finally:
        conexion.close()
