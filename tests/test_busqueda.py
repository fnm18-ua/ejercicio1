"""Pruebas de la búsqueda y verificación de identidad (Historia de usuario 3, E-02; RF-03, RF-04)."""

from registro_pacientes import servicio
from tests.utilidades import BaseDatosTemporalTestCase, datos_paciente


class PruebasBusqueda(BaseDatosTemporalTestCase):
    """Búsqueda por código de historia clínica y por documento de identidad."""

    def test_ca06_buscar_codigo_hc000042_devuelve_ese_paciente(self):
        """CA-06, RF-04, RF-05: buscar HC-000042 devuelve ese paciente con todos sus datos."""
        for indice in range(1, 43):
            servicio.registrar_paciente(
                self.ruta_bd,
                datos_paciente(
                    nombre=f"Paciente{indice}",
                    numero_documento=f"{indice:08d}A",
                    telefono=f"600 000 {indice:03d}",
                ),
            )
        paciente = servicio.buscar_por_codigo(self.ruta_bd, "HC-000042")
        self.assertIsNotNone(paciente)
        self.assertEqual(paciente.codigo_historia, "HC-000042")
        self.assertEqual(paciente.nombre, "Paciente42")
        self.assertEqual(paciente.apellidos, "Ferrández Olmo")
        self.assertEqual(paciente.fecha_nacimiento, "1987-03-14")
        self.assertEqual(paciente.tipo_documento, "DNI")
        self.assertEqual(paciente.numero_documento, "00000042A")
        self.assertEqual(paciente.mutua, "Mutua Ejemplo Salud")
        self.assertEqual(paciente.numero_poliza, "POL-0000-0001")
        self.assertEqual(paciente.telefono, "600 000 042")
        self.assertIsNotNone(paciente.fecha_registro)

    def test_ca07_documento_en_minusculas_encuentra_paciente(self):
        """CA-07: buscar «12345678z» encuentra al paciente registrado con «12345678Z»."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente(numero_documento="12345678Z"))
        paciente = servicio.buscar_por_documento(self.ruta_bd, "DNI", "12345678z")
        self.assertEqual(paciente.codigo_historia, "HC-000001")

    def test_cl02_documento_con_espacios_extremos_se_localiza(self):
        """CL-02: un documento con espacios sobrantes al principio y al final se localiza."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente(numero_documento="12345678Z"))
        paciente = servicio.buscar_por_documento(self.ruta_bd, "DNI", "  12345678Z  ")
        self.assertEqual(paciente.codigo_historia, "HC-000001")

    def test_pd10_espacios_interiores_repetidos_se_reducen(self):
        """PD-10: los espacios interiores repetidos se reducen a uno al comparar."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente(numero_documento="1234 5678Z"))
        paciente = servicio.buscar_por_documento(self.ruta_bd, "DNI", "1234   5678Z")
        self.assertEqual(paciente.codigo_historia, "HC-000001")

    def test_pd10_espacio_interior_no_equivale_a_sin_espacio(self):
        """PD-10: un espacio interior simple se conserva y «1234 5678Z» no es «12345678Z»."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente(numero_documento="12345678Z"))
        self.assertIsNone(servicio.buscar_por_documento(self.ruta_bd, "DNI", "1234 5678Z"))

    def test_pd06_codigo_en_minusculas_se_localiza(self):
        """PD-06: el código se normaliza al buscar."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        paciente = servicio.buscar_por_codigo(self.ruta_bd, " hc-000001 ")
        self.assertEqual(paciente.codigo_historia, "HC-000001")

    def test_pd06_fragmento_de_codigo_no_se_localiza(self):
        """PD-06, RN-08: la comparación es del código completo, nunca de fragmentos."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertIsNone(servicio.buscar_por_codigo(self.ruta_bd, "000001"))
        self.assertIsNone(servicio.buscar_por_codigo(self.ruta_bd, "1"))

    def test_pd08_documento_con_otro_tipo_no_se_localiza(self):
        """PD-08: la búsqueda por documento exige tipo y número."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertIsNone(servicio.buscar_por_documento(self.ruta_bd, "NIE", "00000000T"))

    def test_cl01_sin_coincidencias_devuelve_none(self):
        """CL-01: una búsqueda sin coincidencias no produce error."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertIsNone(servicio.buscar_por_codigo(self.ruta_bd, "HC-000999"))
        self.assertIsNone(servicio.buscar_por_documento(self.ruta_bd, "DNI", "99999999R"))
