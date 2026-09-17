"""Pruebas del registro de pacientes (Historia de usuario 1, E-01; RF-01, RF-02)."""

import sqlite3
import threading
from contextlib import closing
from datetime import date, timedelta

from registro_pacientes import servicio
from registro_pacientes.servicio import CodigosAgotados, ErrorValidacion
from tests.utilidades import BaseDatosTemporalTestCase, datos_paciente


class PruebasRegistro(BaseDatosTemporalTestCase):
    """Registro, asignación de código y validación de datos."""

    def contar_pacientes(self):
        """Número de pacientes guardados, para comprobar que no se crean registros."""
        with closing(sqlite3.connect(self.ruta_bd)) as conexion, conexion:
            return conexion.execute("SELECT COUNT(*) FROM paciente").fetchone()[0]

    def test_ca01_primer_codigo_es_hc000001_y_siguiente_hc000002(self):
        """CA-01, RN-04, RN-05: el primer paciente recibe HC-000001 y el siguiente HC-000002."""
        primero = servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        segundo = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(numero_documento="00000001R")
        )
        self.assertEqual(primero.codigo_historia, "HC-000001")
        self.assertEqual(segundo.codigo_historia, "HC-000002")

    def test_ca02_sin_telefono_email_ni_domicilio_se_guarda(self):
        """CA-02: un paciente sin datos opcionales se guarda y tiene código."""
        paciente = servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertEqual(paciente.codigo_historia, "HC-000001")
        self.assertIsNone(paciente.telefono)
        self.assertIsNone(paciente.email)
        self.assertIsNone(paciente.domicilio)
        self.assertEqual(self.contar_pacientes(), 1)

    def test_ca03_falta_dato_obligatorio_no_se_guarda(self):
        """CA-03, RN-01: sin un dato obligatorio no se guarda y se indica cuál falta."""
        nombres = {
            "nombre": "nombre",
            "apellidos": "apellidos",
            "fecha_nacimiento": "fecha de nacimiento",
            "tipo_documento": "tipo de documento",
            "numero_documento": "número de documento",
            "tipo_cobertura": "cobertura sanitaria",
        }
        for campo, nombre in nombres.items():
            with self.subTest(campo=campo):
                with self.assertRaises(ErrorValidacion) as contexto:
                    servicio.registrar_paciente(self.ruta_bd, datos_paciente(**{campo: ""}))
                self.assertIn(
                    f"Falta el dato obligatorio: {nombre}.", contexto.exception.errores
                )
                self.assertEqual(self.contar_pacientes(), 0)

    def test_ca04_sin_cobertura_no_tiene_poliza(self):
        """CA-04, RN-02: con «sin cobertura» se guarda sin mutua ni número de póliza."""
        paciente = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(tipo_cobertura="SIN_COBERTURA")
        )
        self.assertEqual(paciente.tipo_cobertura, "SIN_COBERTURA")
        self.assertIsNone(paciente.mutua)
        self.assertIsNone(paciente.numero_poliza)

    def test_ca05_mutua_sin_poliza_no_se_guarda(self):
        """CA-05, RN-03: con mutua y sin póliza no se guarda e indica que falta la póliza."""
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(self.ruta_bd, datos_paciente(numero_poliza=""))
        self.assertIn("Falta el número de póliza de la mutua.", contexto.exception.errores)
        self.assertEqual(self.contar_pacientes(), 0)

    def test_rn03_mutua_sin_nombre_no_se_guarda(self):
        """RN-03: con cobertura de mutua es obligatorio indicar la mutua."""
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(self.ruta_bd, datos_paciente(mutua=""))
        self.assertIn("Falta el nombre de la mutua.", contexto.exception.errores)

    def test_cl03_fecha_nacimiento_futura_se_rechaza(self):
        """CL-03, RN-09: una fecha de nacimiento futura se rechaza indicando el motivo."""
        manana = (date.today() + timedelta(days=1)).isoformat()
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(self.ruta_bd, datos_paciente(fecha_nacimiento=manana))
        self.assertIn(
            "La fecha de nacimiento no puede ser posterior a la fecha actual.",
            contexto.exception.errores,
        )
        self.assertEqual(self.contar_pacientes(), 0)

    def test_rn09_fecha_nacimiento_hoy_se_acepta(self):
        """RN-09: la fecha actual no es posterior a la fecha actual y se acepta."""
        hoy = date.today().isoformat()
        paciente = servicio.registrar_paciente(self.ruta_bd, datos_paciente(fecha_nacimiento=hoy))
        self.assertEqual(paciente.fecha_nacimiento, hoy)

    def test_d08_fecha_no_valida_se_rechaza(self):
        """D-08: una fecha que no existe se rechaza."""
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(
                self.ruta_bd, datos_paciente(fecha_nacimiento="1987-13-45")
            )
        self.assertIn("La fecha de nacimiento no es válida.", contexto.exception.errores)

    def test_ca03_varios_errores_se_indican_juntos(self):
        """CA-03, D-08: se indican todos los datos que faltan a la vez."""
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(
                self.ruta_bd, datos_paciente(nombre="", apellidos="", numero_poliza="")
            )
        errores = contexto.exception.errores
        self.assertIn("Falta el dato obligatorio: nombre.", errores)
        self.assertIn("Falta el dato obligatorio: apellidos.", errores)
        self.assertIn("Falta el número de póliza de la mutua.", errores)

    def test_pd13_dato_obligatorio_solo_espacios_es_falta(self):
        """PD-13: un dato obligatorio con solo espacios se trata como ausente."""
        with self.assertRaises(ErrorValidacion) as contexto:
            servicio.registrar_paciente(
                self.ruta_bd, datos_paciente(nombre="   ", numero_documento="   ")
            )
        self.assertIn("Falta el dato obligatorio: nombre.", contexto.exception.errores)
        self.assertIn(
            "Falta el dato obligatorio: número de documento.", contexto.exception.errores
        )

    def test_rn10_guarda_fecha_de_registro_de_hoy(self):
        """RN-10: se guarda la fecha de registro del paciente."""
        paciente = servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertEqual(paciente.fecha_registro, date.today().isoformat())

    def test_pd03_registro_rechazado_no_consume_codigo(self):
        """PD-03: los registros rechazados no consumen código."""
        with self.assertRaises(ErrorValidacion):
            servicio.registrar_paciente(self.ruta_bd, datos_paciente(nombre=""))
        paciente = servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertEqual(paciente.codigo_historia, "HC-000001")

    def test_cl04_codigos_agotados(self):
        """CL-04: agotado HC-999999 no se repite ningún código y se avisa."""
        with closing(sqlite3.connect(self.ruta_bd)) as conexion, conexion:
            conexion.execute(
                "INSERT INTO paciente (codigo_historia, nombre, apellidos, fecha_nacimiento, "
                "tipo_documento, numero_documento, tipo_cobertura, fecha_registro) "
                "VALUES ('HC-999999', 'Ficticio', 'Ejemplo', '1990-01-01', 'DNI', "
                "'99999999R', 'SIN_COBERTURA', '2026-01-01')"
            )
        with self.assertRaises(CodigosAgotados) as contexto:
            servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        self.assertEqual(
            str(contexto.exception),
            "No se puede registrar: se han agotado los códigos de historia clínica.",
        )
        self.assertEqual(self.contar_pacientes(), 1)

    def test_pd04_registros_simultaneos_reciben_codigos_distintos(self):
        """PD-04: registros simultáneos reciben códigos únicos y consecutivos."""
        codigos = []
        errores = []

        def registrar(indice):
            """Registra un paciente ficticio desde un hilo (PD-04)."""
            try:
                paciente = servicio.registrar_paciente(
                    self.ruta_bd, datos_paciente(numero_documento=f"{indice:08d}A")
                )
                codigos.append(paciente.codigo_historia)
            except Exception as error:  # noqa: BLE001 - se comprueba abajo
                errores.append(error)

        hilos = [threading.Thread(target=registrar, args=(indice,)) for indice in range(10)]
        for hilo in hilos:
            hilo.start()
        for hilo in hilos:
            hilo.join()
        self.assertEqual(errores, [])
        self.assertEqual(sorted(codigos), [f"HC-{numero:06d}" for numero in range(1, 11)])

    def test_pd11_secuencia_continua_tras_reabrir(self):
        """PD-11: tras reiniciar, los datos se conservan y la secuencia continúa."""
        servicio.registrar_paciente(self.ruta_bd, datos_paciente())
        servicio.inicializar_base_datos(self.ruta_bd)
        segundo = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(numero_documento="00000001R")
        )
        self.assertEqual(segundo.codigo_historia, "HC-000002")
        self.assertEqual(self.contar_pacientes(), 2)

    def test_ca12_codigo_en_datos_se_ignora_al_registrar(self):
        """CA-12, RN-06: el código no puede fijarse desde los datos de entrada."""
        paciente = servicio.registrar_paciente(
            self.ruta_bd, datos_paciente(codigo_historia="HC-000500")
        )
        self.assertEqual(paciente.codigo_historia, "HC-000001")
