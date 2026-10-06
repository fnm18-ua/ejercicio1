"""Utilidades de prueba del módulo de citas (D-C10, D-C15; principio IV).

Todos los datos son ficticios. El momento actual se fija (`MOMENTO_FIJO`) porque CA-C07, CA-C08 y
PD-C11 dependen del instante actual y no serían deterministas con el reloj real (D-C10).

No se modifica `tests/utilidades.py`: se reutiliza su `datos_paciente` para registrar el paciente
de las pruebas a través del módulo de registro (D-C04).
"""

import datetime
import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock
from urllib.parse import urlencode

from programacion_citas import servicio, web
from registro_pacientes import servicio as servicio_pacientes
from tests.utilidades import datos_paciente

# Jueves 1 de octubre de 2026 a las 08:00. Día ISO 4, dentro de los días de consulta 1,2,3,4,5.
MOMENTO_FIJO = datetime.datetime(2026, 10, 1, 8, 0, 0)

# Especialista precargado que reproduce CA-C01: 9:00-13:00 con consultas de 20 minutos.
NOMBRE_ESPECIALISTA = "Ana Ruiz Delgado"
ESPECIALIDAD = "Dermatología"
CENTRO = "Centro Norte"


def fecha_futura(dias=7):
    """Fecha de consulta posterior a `MOMENTO_FIJO`, en un día de lunes a viernes."""
    fecha = (MOMENTO_FIJO + datetime.timedelta(days=dias)).date()
    while fecha.isoweekday() > 5:
        fecha += datetime.timedelta(days=1)
    return fecha.isoformat()


def fecha_pasada(dias=7):
    """Fecha de consulta anterior a `MOMENTO_FIJO`, en un día de lunes a viernes."""
    fecha = (MOMENTO_FIJO - datetime.timedelta(days=dias)).date()
    while fecha.isoweekday() > 5:
        fecha -= datetime.timedelta(days=1)
    return fecha.isoformat()


def momento(fecha, hora):
    """Compone un `datetime` a partir de una fecha `YYYY-MM-DD` y una hora `HH:MM`."""
    return datetime.datetime.fromisoformat(f"{fecha} {hora}:00")


class BaseCitasTestCase(unittest.TestCase):
    """Base de datos temporal con la agenda precargada y un paciente ficticio registrado."""

    def setUp(self):
        self.directorio = tempfile.TemporaryDirectory()
        self.ruta_bd = str(Path(self.directorio.name) / "pruebas.db")
        servicio.inicializar_base_datos(self.ruta_bd)
        paciente = servicio_pacientes.registrar_paciente(self.ruta_bd, datos_paciente())
        self.codigo = paciente.codigo_historia
        self.especialista = self.buscar_especialista()

    def tearDown(self):
        self.directorio.cleanup()

    def buscar_especialista(self, especialidad=ESPECIALIDAD, centro=CENTRO):
        """Primer especialista precargado de esa especialidad y centro."""
        return servicio.buscar_especialistas(self.ruta_bd, especialidad, centro)[0]

    def registrar_otro_paciente(self, **cambios):
        """Registra otro paciente ficticio y devuelve su código de historia clínica.

        `cambios` puede sobrescribir cualquier dato, incluido `numero_documento`, porque cada
        paciente necesita un documento distinto (RN-C07 se comprueba por paciente).
        """
        datos = {"nombre": "Otra", "apellidos": "Persona Ficticia",
                 "numero_documento": "99999999R"}
        datos.update(cambios)
        return servicio_pacientes.registrar_paciente(
            self.ruta_bd, datos_paciente(**datos)
        ).codigo_historia

    def reservar(self, fecha=None, hora="09:00", codigo=None, ahora=MOMENTO_FIJO, especialista=None):
        """Atajo para reservar una cita en las pruebas."""
        return servicio.reservar_cita(
            self.ruta_bd,
            codigo or self.codigo,
            (especialista or self.especialista).id_especialista,
            fecha or fecha_futura(),
            hora,
            ahora,
        )

    def insertar_cita_pasada(self, hora="09:00", fecha=None, codigo=None):
        """Inserta directamente una cita reservada cuya hora ya pasó (PD-C11).

        Se hace por la base de datos porque `reservar_cita` lo impide (RN-C08), y las pruebas de
        PD-C11 necesitan exactamente ese estado de partida.
        """
        from programacion_citas import base_datos

        fecha = fecha or fecha_pasada()
        conexion = base_datos.conectar(self.ruta_bd)
        try:
            id_cita = base_datos.insertar_cita(
                conexion,
                {
                    "codigo_historia": codigo or self.codigo,
                    "id_especialista": self.especialista.id_especialista,
                    "fecha": fecha,
                    "hora_inicio": hora,
                    "estado": servicio.ESTADO_RESERVADA,
                    "motivo_cancelacion": None,
                    "momento_reserva": (MOMENTO_FIJO - datetime.timedelta(days=30)).strftime(
                        "%Y-%m-%d %H:%M:%S"
                    ),
                },
            )
        finally:
            conexion.close()
        return id_cita

    def estado_de(self, id_cita):
        """Estado actual de una cita, para comprobar las transiciones."""
        for cita in servicio.consultar_citas(self.ruta_bd, self.codigo):
            if cita.id_cita == id_cita:
                return cita.estado
        return None

    def horas_libres(self, fecha=None, ahora=MOMENTO_FIJO, especialista=None):
        """Horas de inicio de los huecos libres, para comparar con las rejillas del enunciado."""
        huecos = servicio.consultar_huecos(
            self.ruta_bd,
            (especialista or self.especialista).id_especialista,
            fecha or fecha_futura(),
            ahora,
        )
        return [hueco.hora_inicio for hueco in huecos]


class ServidorCitasTestCase(BaseCitasTestCase):
    """Servidor real en un puerto libre con el manejador combinado (D-C13).

    El momento actual se fija en `MOMENTO_FIJO` (D-C10, D-C15): la interfaz web lo pide a
    `servicio.momento_actual`, y sin fijarlo las pruebas web dependerían de la fecha real y
    dejarían de pasar cuando `fecha_futura()` quedara en el pasado.
    """

    def setUp(self):
        super().setUp()
        parche = mock.patch.object(servicio, "momento_actual", return_value=MOMENTO_FIJO)
        parche.start()
        self.addCleanup(parche.stop)
        self.servidor = web.crear_servidor(self.ruta_bd, puerto=0)
        self.puerto = self.servidor.server_address[1]
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        super().tearDown()

    def _conexion(self):
        return http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)

    def peticion_get(self, ruta):
        """GET sin seguir redirecciones; devuelve (estado, cabeceras, cuerpo)."""
        conexion = self._conexion()
        try:
            conexion.request("GET", ruta)
            respuesta = conexion.getresponse()
            return respuesta.status, dict(respuesta.getheaders()), respuesta.read().decode("utf-8")
        finally:
            conexion.close()

    def peticion_post(self, ruta, campos):
        """POST con formulario codificado; devuelve (estado, cabeceras, cuerpo)."""
        conexion = self._conexion()
        try:
            cuerpo = urlencode(campos)
            conexion.request(
                "POST",
                ruta,
                body=cuerpo,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
            respuesta = conexion.getresponse()
            return respuesta.status, dict(respuesta.getheaders()), respuesta.read().decode("utf-8")
        finally:
            conexion.close()
