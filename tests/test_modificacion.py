"""Pruebas de la modificación de datos (Historias de usuario 4 y 5, E-03 y E-04; RF-06, RN-11)."""

from datetime import date, timedelta

from registro_pacientes import servicio
from registro_pacientes.servicio import (
    ErrorValidacion,
    PacienteDuplicado,
    PacienteNoEncontrado,
)
from tests.utilidades import BaseDatosTemporalTestCase, datos_paciente


class PruebasModificacion(BaseDatosTemporalTestCase):
    """Actualización de datos que cambian (Historia de usuario 4)."""

    def setUp(self):
        """Registra un paciente ficticio, HC-000001, para modificarlo."""
        super().setUp()
        self.paciente = servicio.registrar_paciente(self.ruta_bd, datos_paciente())

    def test_ca11_telefono_modificado_aparece_al_buscar(self):
        """CA-11: tras modificar el teléfono, al buscar aparece el teléfono nuevo."""
        servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(telefono="600 000 000")
        )
        paciente = servicio.buscar_por_documento(self.ruta_bd, "DNI", "00000000T")
        self.assertEqual(paciente.telefono, "600 000 000")

    def test_cl05_cambiar_a_sin_cobertura_elimina_poliza(self):
        """CL-05, RN-02: al pasar a «sin cobertura» el número de póliza deja de estar presente."""
        paciente = servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(tipo_cobertura="SIN_COBERTURA")
        )
        self.assertEqual(paciente.tipo_cobertura, "SIN_COBERTURA")
        self.assertIsNone(paciente.mutua)
        self.assertIsNone(paciente.numero_poliza)

    def test_rn03_cambiar_a_mutua_exige_poliza(self):
        """RN-03, PD-01: pasar a mutua sin número de póliza no se guarda."""
        servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(tipo_cobertura="SIN_COBERTURA")
        )
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.modificar_paciente(
                self.ruta_bd, "HC-000001", datos_paciente(numero_poliza="")
            )
        self.assertIn("Falta el número de póliza de la mutua.", contexto.exception.errores)
        paciente = servicio.buscar_por_codigo(self.ruta_bd, "HC-000001")
        self.assertEqual(paciente.tipo_cobertura, "SIN_COBERTURA")

    def test_rf06_rellenar_datos_opcionales_vacios(self):
        """RF-06: se pueden rellenar los datos que quedaron vacíos en el registro."""
        servicio.modificar_paciente(
            self.ruta_bd,
            "HC-000001",
            datos_paciente(
                telefono="600 000 000",
                email="lucia.ejemplo@example.com",
                domicilio="Calle Inventada 1, 00000 Ciudad Ficticia",
            ),
        )
        paciente = servicio.buscar_por_codigo(self.ruta_bd, "HC-000001")
        self.assertEqual(paciente.telefono, "600 000 000")
        self.assertEqual(paciente.email, "lucia.ejemplo@example.com")
        self.assertEqual(paciente.domicilio, "Calle Inventada 1, 00000 Ciudad Ficticia")

    def test_pd01_modificacion_valida_igual_que_registro(self):
        """PD-01: la modificación aplica las mismas reglas que el registro."""
        manana = (date.today() + timedelta(days=1)).isoformat()
        casos = {
            "nombre vacío": (
                {"nombre": ""},
                "Falta el dato obligatorio: nombre.",
            ),
            "fecha futura": (
                {"fecha_nacimiento": manana},
                "La fecha de nacimiento no puede ser posterior a la fecha actual.",
            ),
        }
        for caso, (cambios, mensaje) in casos.items():
            with self.subTest(caso=caso):
                with self.assertRaises(ErrorValidacion) as contexto:
                    servicio.modificar_paciente(
                        self.ruta_bd, "HC-000001", datos_paciente(**cambios)
                    )
                self.assertIn(mensaje, contexto.exception.errores)
                self.assertEqual(
                    servicio.buscar_por_codigo(self.ruta_bd, "HC-000001"), self.paciente
                )

    def test_ca12_modificar_no_cambia_codigo_ni_fecha_registro(self):
        """CA-12, RN-06: la modificación nunca cambia el código ni la fecha de registro."""
        paciente = servicio.modificar_paciente(
            self.ruta_bd,
            "HC-000001",
            datos_paciente(codigo_historia="HC-000999", fecha_registro="2000-01-01"),
        )
        self.assertEqual(paciente.codigo_historia, "HC-000001")
        self.assertEqual(paciente.fecha_registro, self.paciente.fecha_registro)
        self.assertIsNone(servicio.buscar_por_codigo(self.ruta_bd, "HC-000999"))

    def test_rf06_modificar_paciente_inexistente(self):
        """RF-06: modificar un código que no existe informa de que no existe."""
        with self.assertRaises(PacienteNoEncontrado):
            servicio.modificar_paciente(self.ruta_bd, "HC-000999", datos_paciente())


class PruebasCorreccionDocumento(BaseDatosTemporalTestCase):
    """Corrección del documento de identidad (Historia de usuario 5)."""

    def setUp(self):
        """Registra dos pacientes ficticios: HC-000001 (DNI) y HC-000002 (NIE)."""
        super().setUp()
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.marcos = servicio.registrar_paciente(self.ruta_bd, self.datos_marcos())

    def datos_marcos(self, **cambios):
        """Datos ficticios de un segundo paciente, HC-000002, con NIE y sin cobertura."""
        datos = {
            "nombre": "Marcos",
            "apellidos": "Ibáñez Río",
            "fecha_nacimiento": "1990-11-02",
            "tipo_documento": "NIE",
            "numero_documento": "X0000000T",
            "tipo_cobertura": "SIN_COBERTURA",
        }
        datos.update(cambios)
        return datos

    def test_ca09_corregir_documento_mantiene_codigo(self):
        """CA-09: corregir el número de documento lo guarda y el código sigue siendo el mismo."""
        paciente = servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(numero_documento="00000001R")
        )
        self.assertEqual(paciente.numero_documento, "00000001R")
        self.assertEqual(paciente.codigo_historia, "HC-000001")
        encontrado = servicio.buscar_por_documento(self.ruta_bd, "DNI", "00000001R")
        self.assertEqual(encontrado.codigo_historia, "HC-000001")

    def test_pd12_documento_corregido_se_guarda_normalizado(self):
        """PD-12: el documento corregido se guarda normalizado."""
        paciente = servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(numero_documento=" 87654321x ")
        )
        self.assertEqual(paciente.numero_documento, "87654321X")

    def test_ca10_documento_de_otro_paciente_no_se_guarda(self):
        """CA-10, RN-11: poner el documento de otro paciente no se guarda."""
        with self.assertRaises(PacienteDuplicado) as contexto:
            servicio.modificar_paciente(
                self.ruta_bd,
                "HC-000002",
                self.datos_marcos(tipo_documento="DNI", numero_documento="00000000T"),
            )
        self.assertEqual(contexto.exception.existente.codigo_historia, "HC-000001")
        self.assertEqual(servicio.buscar_por_codigo(self.ruta_bd, "HC-000002"), self.marcos)

    def test_pd09_documento_de_otro_paciente_normalizado_se_detecta(self):
        """PD-09: la unicidad al modificar compara el documento normalizado."""
        with self.assertRaises(PacienteDuplicado):
            servicio.modificar_paciente(
                self.ruta_bd,
                "HC-000002",
                self.datos_marcos(tipo_documento="DNI", numero_documento="00000000t"),
            )

    def test_pd02_mantener_su_propio_documento_no_es_duplicado(self):
        """PD-02: el propio paciente no cuenta como duplicado de sí mismo."""
        paciente = servicio.modificar_paciente(
            self.ruta_bd, "HC-000001", datos_paciente(telefono="600 000 000")
        )
        self.assertEqual(paciente.numero_documento, "00000000T")
        self.assertEqual(paciente.telefono, "600 000 000")
