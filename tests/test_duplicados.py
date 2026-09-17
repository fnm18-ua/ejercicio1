"""Pruebas de la detección de duplicados al registrar (Historia de usuario 2, E-05; RN-07)."""

import sqlite3
from contextlib import closing

from registro_pacientes import servicio
from registro_pacientes.servicio import PacienteDuplicado
from tests.utilidades import BaseDatosTemporalTestCase, datos_paciente


class PruebasDuplicados(BaseDatosTemporalTestCase):
    """Un documento ya registrado no puede registrarse de nuevo."""

    def contar_pacientes(self):
        """Número de pacientes guardados, para comprobar que no se crean registros."""
        with closing(sqlite3.connect(self.ruta_bd)) as conexion, conexion:
            return conexion.execute("SELECT COUNT(*) FROM paciente").fetchone()[0]

    def test_ca08_duplicado_no_crea_registro_y_devuelve_existente(self):
        """CA-08: un documento existente no crea registro y devuelve el paciente existente."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        with self.assertRaises(PacienteDuplicado) as contexto:
            servicio.registrar_paciente(
                self.ruta_bd, datos_paciente(nombre="Otra", apellidos="Persona Ficticia")
            )
        self.assertEqual(contexto.exception.existente.codigo_historia, "HC-000001")
        self.assertEqual(contexto.exception.existente.nombre, "Lucía")
        self.assertEqual(self.contar_pacientes(), 1)

    def test_pd09_duplicado_con_documento_normalizado(self):
        """PD-09: el duplicado se detecta comparando el documento normalizado."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        with self.assertRaises(PacienteDuplicado):
            servicio.registrar_paciente(
                self.ruta_bd, datos_paciente(numero_documento=" 00000000t ")
            )
        self.assertEqual(self.contar_pacientes(), 1)

    def test_rn07_mismo_numero_distinto_tipo_se_permite(self):
        """RN-07: la unicidad es por tipo y número; otro tipo con el mismo número se admite."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        paciente = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(tipo_documento="PASAPORTE")
        )
        self.assertEqual(paciente.codigo_historia, "HC-000002")

    def test_pd03_duplicado_no_consume_codigo(self):
        """PD-03: un intento de duplicado no consume código."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        with self.assertRaises(PacienteDuplicado):
            servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        paciente = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(numero_documento="00000001R")
        )
        self.assertEqual(paciente.codigo_historia, "HC-000002")
