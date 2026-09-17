"""Utilidades comunes de las pruebas: base de datos temporal, servidor y datos ficticios.

Todos los datos son inventados (Constitución, principio IV).
"""

import http.client
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.parse import urlencode

from registro_pacientes import servicio, web


def datos_paciente(**cambios):
    """Devuelve datos de entrada válidos y ficticios de un paciente, con los cambios indicados."""
    datos = {
        "nombre": "Lucía",
        "apellidos": "Ferrández Olmo",
        "fecha_nacimiento": "1987-03-14",
        "tipo_documento": "DNI",
        "numero_documento": "00000000T",
        "tipo_cobertura": "MUTUA",
        "mutua": "Mutua Ejemplo Salud",
        "numero_poliza": "POL-0000-0001",
        "telefono": "",
        "email": "",
        "domicilio": "",
    }
    datos.update(cambios)
    return datos


class BaseDatosTemporalTestCase(unittest.TestCase):
    """Caso de prueba con una base de datos vacía en un directorio temporal."""

    def setUp(self):
        self.directorio_temporal = tempfile.TemporaryDirectory()
        self.ruta_bd = str(Path(self.directorio_temporal.name) / "pacientes.db")
        servicio.inicializar_base_datos(self.ruta_bd)

    def tearDown(self):
        self.directorio_temporal.cleanup()


class ServidorPruebaTestCase(BaseDatosTemporalTestCase):
    """Caso de prueba con el servidor web arrancado sobre la base de datos temporal."""

    def setUp(self):
        super().setUp()
        self.servidor = web.crear_servidor(self.ruta_bd, puerto=0)
        self.puerto = self.servidor.server_address[1]
        self.hilo = threading.Thread(target=self.servidor.serve_forever, daemon=True)
        self.hilo.start()

    def tearDown(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.hilo.join()
        super().tearDown()

    def _peticion(self, metodo, ruta, cuerpo=None, cabeceras=None):
        """Envía una petición HTTP al servidor de prueba y devuelve (estado, cabeceras, cuerpo)."""
        conexion = http.client.HTTPConnection("127.0.0.1", self.puerto, timeout=10)
        try:
            conexion.request(metodo, ruta, body=cuerpo, headers=cabeceras or {})
            respuesta = conexion.getresponse()
            contenido = respuesta.read().decode("utf-8")
            return respuesta.status, dict(respuesta.getheaders()), contenido
        finally:
            conexion.close()

    def peticion_get(self, ruta):
        """Hace una petición GET sin seguir redirecciones; devuelve (estado, cabeceras, cuerpo)."""
        return self._peticion("GET", ruta)

    def peticion_post(self, ruta, campos):
        """Envía un formulario por POST sin seguir redirecciones; devuelve (estado, cabeceras, cuerpo)."""
        cuerpo = urlencode(campos).encode("utf-8")
        cabeceras = {"Content-Type": "application/x-www-form-urlencoded"}
        return self._peticion("POST", ruta, cuerpo, cabeceras)
