"""Pruebas de la interfaz web (contracts/interfaz-web.md)."""

import sqlite3
from contextlib import closing

from tests.utilidades import ServidorPruebaTestCase, datos_paciente

CAMPOS_ENTRADA = (
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
)


def insertar_ultimo_codigo(ruta_bd):
    """Inserta un paciente ficticio con HC-999999 para simular códigos agotados (CL-04)."""
    with closing(sqlite3.connect(ruta_bd)) as conexion, conexion:
        conexion.execute(
            "INSERT INTO paciente (codigo_historia, nombre, apellidos, fecha_nacimiento, "
            "tipo_documento, numero_documento, tipo_cobertura, fecha_registro) "
            "VALUES ('HC-999999', 'Ficticio', 'Ejemplo', '1990-01-01', 'DNI', "
            "'99999999R', 'SIN_COBERTURA', '2026-01-01')"
        )


class PruebasWebRegistro(ServidorPruebaTestCase):
    """Rutas 1, 2, 3 y 4 para el registro (Historia de usuario 1)."""

    def test_rf01_formulario_registro_tiene_todos_los_campos(self):
        """RF-01, RN-01: el formulario de registro contiene todos los campos de entrada."""
        estado, _, cuerpo = self.peticion_get("/pacientes/nuevo")
        self.assertEqual(estado, 200)
        for campo in CAMPOS_ENTRADA:
            with self.subTest(campo=campo):
                self.assertIn(f'name="{campo}"', cuerpo)

    def test_rf02_registro_redirige_a_ficha_con_codigo(self):
        """RF-02, E-01: tras registrar se muestra la ficha con el código asignado."""
        estado, cabeceras, _ = self.peticion_post("/pacientes", datos_paciente())
        self.assertEqual(estado, 303)
        self.assertEqual(cabeceras["Location"], "/buscar?codigo=HC-000001&aviso=registrado")
        estado, _, cuerpo = self.peticion_get(cabeceras["Location"])
        self.assertEqual(estado, 200)
        self.assertIn("HC-000001", cuerpo)
        self.assertIn("Paciente registrado.", cuerpo)

    def test_ca03_registro_invalido_muestra_errores_y_conserva_valores(self):
        """CA-03: un registro sin nombre responde 400 con el error y conserva lo introducido."""
        estado, _, cuerpo = self.peticion_post("/pacientes", datos_paciente(nombre=""))
        self.assertEqual(estado, 400)
        self.assertIn("Falta el dato obligatorio: nombre.", cuerpo)
        self.assertIn("Ferrández Olmo", cuerpo)

    def test_cl04_codigos_agotados_responde_409(self):
        """CL-04: con los códigos agotados el registro responde 409 con el aviso."""
        insertar_ultimo_codigo(self.ruta_bd)
        estado, _, cuerpo = self.peticion_post("/pacientes", datos_paciente())
        self.assertEqual(estado, 409)
        self.assertIn(
            "No se puede registrar: se han agotado los códigos de historia clínica.", cuerpo
        )

    def test_d10_datos_se_escapan_en_html(self):
        """D-10: los datos mostrados se escapan en el HTML."""
        self.peticion_post("/pacientes", datos_paciente(apellidos="<b>Olmo</b>"))
        _, _, cuerpo = self.peticion_get("/buscar?codigo=HC-000001")
        self.assertIn("&lt;b&gt;Olmo&lt;/b&gt;", cuerpo)
        self.assertNotIn("<b>Olmo</b>", cuerpo)

    def test_inicio_enlaza_registro(self):
        """RF-01: la página de inicio enlaza con el formulario de registro."""
        estado, _, cuerpo = self.peticion_get("/")
        self.assertEqual(estado, 200)
        self.assertIn('href="/pacientes/nuevo"', cuerpo)

    def test_ruta_desconocida_responde_404(self):
        """Contrato web: cualquier ruta fuera de las 6 definidas responde 404."""
        estado, _, cuerpo = self.peticion_get("/pacientes")
        self.assertEqual(estado, 404)
        self.assertIn("Página no encontrada", cuerpo)


class PruebasWebDuplicados(ServidorPruebaTestCase):
    """Ruta 4 ante un documento ya registrado (Historia de usuario 2)."""

    def test_ca08_registro_duplicado_responde_409_con_paciente_existente(self):
        """CA-08: el duplicado responde 409, informa del motivo y muestra el paciente existente."""
        self.peticion_post("/pacientes", datos_paciente())
        estado, _, cuerpo = self.peticion_post(
            "/pacientes", datos_paciente(nombre="Otra", apellidos="Persona Ficticia")
        )
        self.assertEqual(estado, 409)
        self.assertIn("Ya existe un paciente con el documento DNI 00000000T: HC-000001.", cuerpo)
        self.assertIn("Ferrández Olmo", cuerpo)
        self.assertNotIn("Persona Ficticia", cuerpo)


class PruebasWebBusqueda(ServidorPruebaTestCase):
    """Rutas 1 y 2: búsqueda y ficha (Historia de usuario 3)."""

    def test_ca13_inicio_solo_busca_por_codigo_o_documento(self):
        """CA-13: la búsqueda solo acepta código o documento; no hay búsqueda por nombre."""
        estado, _, cuerpo = self.peticion_get("/")
        self.assertEqual(estado, 200)
        self.assertIn('name="codigo"', cuerpo)
        self.assertIn('name="tipo_documento"', cuerpo)
        self.assertIn('name="numero_documento"', cuerpo)
        self.assertNotIn('name="nombre"', cuerpo)
        self.assertNotIn('name="apellidos"', cuerpo)

    def test_pd05_ficha_completa(self):
        """PD-05, RF-05, RN-10: la ficha muestra todos los datos y la fecha de registro."""
        self.peticion_post("/pacientes", datos_paciente())
        estado, _, cuerpo = self.peticion_get("/buscar?codigo=HC-000001")
        self.assertEqual(estado, 200)
        for texto in (
            "HC-000001",
            "Lucía",
            "Ferrández Olmo",
            "1987-03-14",
            "DNI 00000000T",
            "Mutua Ejemplo Salud",
            "POL-0000-0001",
            "—",
            "Fecha de registro",
        ):
            with self.subTest(texto=texto):
                self.assertIn(texto, cuerpo)

    def test_ca07_buscar_por_documento_en_web(self):
        """CA-07, RF-03: la búsqueda por documento normalizado muestra la ficha."""
        self.peticion_post("/pacientes", datos_paciente())
        estado, _, cuerpo = self.peticion_get(
            "/buscar?tipo_documento=DNI&numero_documento=00000000t"
        )
        self.assertEqual(estado, 200)
        self.assertIn("HC-000001", cuerpo)

    def test_cl01_sin_coincidencias_responde_200_con_mensaje(self):
        """CL-01: sin coincidencias se informa de que no existe el paciente, sin error."""
        estado, _, cuerpo = self.peticion_get("/buscar?codigo=HC-000999")
        self.assertEqual(estado, 200)
        self.assertIn("No existe ningún paciente con el código HC-000999.", cuerpo)
        estado, _, cuerpo = self.peticion_get(
            "/buscar?tipo_documento=DNI&numero_documento=99999999R"
        )
        self.assertEqual(estado, 200)
        self.assertIn("No existe ningún paciente con el documento DNI 99999999R.", cuerpo)

    def test_buscar_sin_parametros_pide_criterio(self):
        """RF-03, RF-04: una búsqueda vacía pide un código o un documento."""
        estado, _, cuerpo = self.peticion_get("/buscar")
        self.assertEqual(estado, 200)
        self.assertIn("Indica un código de historia clínica o un documento de identidad.", cuerpo)


class PruebasWebModificacion(ServidorPruebaTestCase):
    """Rutas 5 y 6: modificación de datos (Historia de usuario 4)."""

    def setUp(self):
        """Registra un paciente ficticio, HC-000001, para modificarlo."""
        super().setUp()
        self.peticion_post("/pacientes", datos_paciente())

    def test_ca12_formulario_edicion_no_permite_editar_codigo(self):
        """CA-12: el código se muestra como texto y no hay campo para editarlo."""
        estado, _, cuerpo = self.peticion_get("/pacientes/HC-000001/editar")
        self.assertEqual(estado, 200)
        self.assertIn("HC-000001", cuerpo)
        self.assertIn('value="Lucía"', cuerpo)
        self.assertIn('value="00000000T"', cuerpo)
        self.assertNotIn('name="codigo_historia"', cuerpo)

    def test_ca12_codigo_enviado_en_formulario_se_ignora(self):
        """CA-12, RN-06: un código enviado en el formulario no cambia el código del paciente."""
        estado, cabeceras, _ = self.peticion_post(
            "/pacientes/HC-000001/editar", datos_paciente(codigo_historia="HC-000500")
        )
        self.assertEqual(estado, 303)
        self.assertEqual(cabeceras["Location"], "/buscar?codigo=HC-000001&aviso=modificado")
        estado, _, cuerpo = self.peticion_get("/buscar?codigo=HC-000500")
        self.assertIn("No existe ningún paciente con el código HC-000500.", cuerpo)

    def test_ca11_modificacion_redirige_a_ficha(self):
        """CA-11: tras modificar el teléfono, la ficha muestra el teléfono nuevo."""
        estado, cabeceras, _ = self.peticion_post(
            "/pacientes/HC-000001/editar", datos_paciente(telefono="600 000 000")
        )
        self.assertEqual(estado, 303)
        self.assertEqual(cabeceras["Location"], "/buscar?codigo=HC-000001&aviso=modificado")
        _, _, cuerpo = self.peticion_get(cabeceras["Location"])
        self.assertIn("600 000 000", cuerpo)
        self.assertIn("Datos guardados.", cuerpo)

    def test_pd01_modificacion_invalida_responde_400(self):
        """PD-01: una modificación inválida responde 400 con el error."""
        estado, _, cuerpo = self.peticion_post(
            "/pacientes/HC-000001/editar", datos_paciente(apellidos="")
        )
        self.assertEqual(estado, 400)
        self.assertIn("Falta el dato obligatorio: apellidos.", cuerpo)

    def test_rf06_editar_paciente_inexistente_responde_404(self):
        """RF-06: editar un código que no existe responde 404 con el mensaje."""
        mensaje = "No existe ningún paciente con el código HC-000999."
        estado, _, cuerpo = self.peticion_get("/pacientes/HC-000999/editar")
        self.assertEqual(estado, 404)
        self.assertIn(mensaje, cuerpo)
        estado, _, cuerpo = self.peticion_post("/pacientes/HC-000999/editar", datos_paciente())
        self.assertEqual(estado, 404)
        self.assertIn(mensaje, cuerpo)

    def test_rf06_ficha_enlaza_modificacion(self):
        """RF-06: la ficha enlaza con el formulario de modificación."""
        _, _, cuerpo = self.peticion_get("/buscar?codigo=HC-000001")
        self.assertIn('href="/pacientes/HC-000001/editar"', cuerpo)


class PruebasWebCorreccionDocumento(ServidorPruebaTestCase):
    """Ruta 6 ante el documento de otro paciente (Historia de usuario 5)."""

    def test_ca10_documento_de_otro_paciente_responde_409(self):
        """CA-10: poner el documento de otro paciente responde 409 e informa del motivo."""
        self.peticion_post("/pacientes", datos_paciente())
        self.peticion_post(
            "/pacientes",
            datos_paciente(nombre="Marcos", apellidos="Ibáñez Río", numero_documento="00000001R"),
        )
        estado, _, cuerpo = self.peticion_post(
            "/pacientes/HC-000002/editar",
            datos_paciente(nombre="Marcos", apellidos="Ibáñez Río", numero_documento="00000000T"),
        )
        self.assertEqual(estado, 409)
        self.assertIn("El documento DNI 00000000T ya pertenece a otro paciente.", cuerpo)
        self.assertNotIn("Lucía", cuerpo)
