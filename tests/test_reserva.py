"""Pruebas de reserva de citas y del listado del paciente (US1 y US2).

Verifican RF-C01 a RF-C05, CA-C01 a CA-C05, CA-C11, CL-C01, CL-C02, CL-C03, CL-C06, CL-C09, CL-C13
(un hueco que empieza justo ahora no se reserva) y las precisiones PD-C01, PD-C05, PD-C06 y
PD-C14.
"""

import unittest

from programacion_citas import servicio
from tests.utilidades_citas import (
    CENTRO,
    ESPECIALIDAD,
    MOMENTO_FIJO,
    BaseCitasTestCase,
    fecha_futura,
    momento,
)


class PruebasReserva(BaseCitasTestCase):
    """Identificación, búsqueda, huecos y reserva (RF-C01 a RF-C04)."""

    def test_cac03_busqueda_exige_especialidad_y_centro(self):
        """CA-C03: solo se devuelven los especialistas que cumplen los dos filtros."""
        encontrados = servicio.buscar_especialistas(self.ruta_bd, ESPECIALIDAD, CENTRO)
        self.assertTrue(encontrados)
        for especialista in encontrados:
            self.assertEqual(especialista.especialidad, ESPECIALIDAD)
            self.assertEqual(especialista.centro, CENTRO)

    def test_clc02_busqueda_sin_resultados_devuelve_lista_vacia(self):
        """CL-C02: una combinación sin especialistas se informa, sin error."""
        self.assertEqual(
            servicio.buscar_especialistas(self.ruta_bd, "Traumatología", "Centro Sur"), []
        )

    def test_rfc02_busqueda_sin_los_dos_filtros_se_rechaza(self):
        """PD-C15: la búsqueda exige especialidad y centro."""
        with self.assertRaises(servicio.ErrorValidacion):
            servicio.buscar_especialistas(self.ruta_bd, ESPECIALIDAD, "")

    def test_cac01_huecos_de_la_rejilla_completa(self):
        """CA-C01: el especialista de 9:00 a 13:00 con 20 minutos ofrece 12 huecos."""
        horas = self.horas_libres()
        self.assertEqual(len(horas), 12)
        self.assertEqual(horas[0], "09:00")
        self.assertEqual(horas[-1], "12:40")

    def test_cac02_hueco_reservado_desaparece_de_los_libres(self):
        """CA-C02: tras reservar las 9:00 ese hueco no se ofrece y los demás siguen."""
        self.reservar(hora="09:00")
        horas = self.horas_libres()
        self.assertNotIn("09:00", horas)
        self.assertEqual(len(horas), 11)
        self.assertIn("09:20", horas)

    def test_clc06_fecha_sin_consulta_no_ofrece_huecos(self):
        """CL-C06: en un sábado el especialista no pasa consulta."""
        self.assertEqual(self.horas_libres(fecha="2026-10-10"), [])

    def test_clc01_sin_huecos_libres_devuelve_lista_vacia(self):
        """CL-C01: con todos los huecos ocupados se informa de que no hay disponibilidad."""
        fecha = fecha_futura()
        for hora in list(self.horas_libres(fecha=fecha)):
            self.reservar(fecha=fecha, hora=hora, codigo=self.registrar_otro_paciente(
                numero_documento=f"1111111{hora[:2]}{hora[3:]}"
            ))
        self.assertEqual(self.horas_libres(fecha=fecha), [])

    def test_cac04_identificacion_por_documento_equivale_a_codigo(self):
        """CA-C04: las dos vías de identificación llevan al mismo paciente (PD-C01)."""
        por_codigo = servicio.identificar_paciente(self.ruta_bd, codigo=self.codigo)
        por_documento = servicio.identificar_paciente(
            self.ruta_bd, tipo_documento="DNI", numero_documento="00000000T"
        )
        self.assertEqual(por_codigo, por_documento)
        self.assertEqual(por_codigo, self.codigo)

    def test_pdc01_identificacion_por_documento_se_compara_normalizada(self):
        """PD-C01: la comparación reutiliza la normalización del módulo de registro."""
        self.assertEqual(
            servicio.identificar_paciente(
                self.ruta_bd, tipo_documento="DNI", numero_documento="  00000000t  "
            ),
            self.codigo,
        )

    def test_clc09_identificacion_de_paciente_inexistente_lanza_error(self):
        """CL-C09: un código inventado se rechaza sin crear ningún paciente."""
        with self.assertRaises(servicio.PacienteNoIdentificado):
            servicio.identificar_paciente(self.ruta_bd, codigo="HC-999998")
        self.assertIsNone(
            __import__("registro_pacientes.servicio", fromlist=["x"]).buscar_por_codigo(
                self.ruta_bd, "HC-999998"
            )
        )

    def test_cac05_reserva_solapada_se_rechaza(self):
        """CA-C05: el paciente no puede tener dos citas solapadas, aunque sean de
        especialistas distintos (RN-C07).

        Ana pasa consulta de 9:00 a 13:00 en tramos de 20 minutos y Lucía de 8:00 a 13:00 en
        tramos de 25; el hueco de Lucía de las 9:15 pisa la cita de las 9:00 de Ana.
        """
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        otra = servicio.buscar_especialistas(self.ruta_bd, "Traumatología", CENTRO)[0]
        self.assertNotEqual(otra.id_especialista, self.especialista.id_especialista)
        with self.assertRaises(servicio.CitaSolapada):
            servicio.reservar_cita(
                self.ruta_bd, self.codigo, otra.id_especialista, fecha, "09:15", MOMENTO_FIJO
            )

    def test_pdc06_reserva_consecutiva_se_acepta(self):
        """PD-C06: dos citas que se tocan en el extremo no se solapan."""
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        cita = self.reservar(fecha=fecha, hora="09:20")
        self.assertEqual(cita.hora_inicio, "09:20")

    def test_rnc08_hueco_pasado_se_rechaza(self):
        """RN-C08: no se puede reservar un hueco cuya hora ya ha pasado (PD-C05)."""
        fecha = fecha_futura()
        with self.assertRaises(servicio.HuecoPasado):
            self.reservar(fecha=fecha, hora="09:00", ahora=momento(fecha, "10:00"))

    def test_rnc08_se_puede_reservar_para_el_mismo_dia(self):
        """RN-C08: no hay antelación mínima; se puede reservar para hoy."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="12:40", ahora=momento(fecha, "09:05"))
        self.assertEqual(cita.estado, servicio.ESTADO_RESERVADA)

    def test_clc13_hueco_que_empieza_justo_ahora_no_se_ofrece(self):
        """CL-C13, PD-C05: un hueco solo es reservable si su inicio es estrictamente posterior
        al momento actual."""
        fecha = fecha_futura()
        horas = self.horas_libres(fecha=fecha, ahora=momento(fecha, "09:00"))
        self.assertNotIn("09:00", horas)
        self.assertEqual(horas[0], "09:20")

    def test_clc13_reservar_un_hueco_que_empieza_justo_ahora_se_rechaza(self):
        """CL-C13, PD-C05: ninguna cita nace ya pasada y sin poder cancelarse."""
        fecha = fecha_futura()
        with self.assertRaises(servicio.HuecoPasado):
            self.reservar(fecha=fecha, hora="09:00", ahora=momento(fecha, "09:00"))
        self.assertEqual(servicio.consultar_citas(self.ruta_bd, self.codigo), [])

    def test_pdc05_hueco_que_empieza_un_minuto_despues_se_reserva_y_se_puede_cancelar(self):
        """PD-C05, PD-C07: toda cita recién reservada es futura y se puede cancelar."""
        fecha = fecha_futura()
        ahora = momento(fecha, "08:59")
        cita = self.reservar(fecha=fecha, hora="09:00", ahora=ahora)
        self.assertEqual(cita.estado, servicio.ESTADO_RESERVADA)
        cancelada = servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, ahora)
        self.assertEqual(cancelada.estado, servicio.ESTADO_CANCELADA_PACIENTE)

    def test_clc03_segunda_reserva_del_mismo_hueco_se_rechaza(self):
        """CL-C03: si otra persona acaba de ocupar el hueco, la segunda reserva se rechaza."""
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        otro = self.registrar_otro_paciente()
        with self.assertRaises(servicio.HuecoNoDisponible):
            self.reservar(fecha=fecha, hora="09:00", codigo=otro)

    def test_clc03_el_indice_unico_parcial_impide_el_hueco_duplicado(self):
        """D-C08: la garantía está en la base de datos, no solo en la comprobación previa."""
        import sqlite3

        from programacion_citas import base_datos

        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        conexion = base_datos.conectar(self.ruta_bd)
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                base_datos.insertar_cita(
                    conexion,
                    {
                        "codigo_historia": self.codigo,
                        "id_especialista": self.especialista.id_especialista,
                        "fecha": fecha,
                        "hora_inicio": "09:00",
                        "estado": servicio.ESTADO_RESERVADA,
                        "motivo_cancelacion": None,
                        "momento_reserva": "2026-10-01 08:00:00",
                    },
                )
        finally:
            conexion.close()

    def test_rfc04_hueco_fuera_de_la_rejilla_se_rechaza(self):
        """RN-C03: solo se puede reservar en una hora que sea inicio de un hueco."""
        with self.assertRaises(servicio.HuecoNoDisponible):
            self.reservar(hora="09:10")


class PruebasListado(BaseCitasTestCase):
    """Listado de citas del paciente con estado y motivo (RF-C05, PD-C14)."""

    def test_rfc05_listado_muestra_estado_de_cada_cita(self):
        """RF-C05: el listado muestra cada cita con su estado."""
        fecha = fecha_futura()
        reservada = self.reservar(fecha=fecha, hora="09:00")
        cancelada = self.reservar(fecha=fecha, hora="10:00")
        servicio.cancelar_cita(self.ruta_bd, self.codigo, cancelada.id_cita, MOMENTO_FIJO)
        estados = {
            cita.id_cita: cita.estado
            for cita in servicio.consultar_citas(self.ruta_bd, self.codigo)
        }
        self.assertEqual(estados[reservada.id_cita], servicio.ESTADO_RESERVADA)
        self.assertEqual(estados[cancelada.id_cita], servicio.ESTADO_CANCELADA_PACIENTE)

    def test_pdc14_paciente_sin_citas_devuelve_lista_vacia(self):
        """PD-C14: un paciente sin citas recibe una lista vacía, no un error."""
        self.assertEqual(servicio.consultar_citas(self.ruta_bd, self.codigo), [])

    def test_pdc14_cita_pasada_sigue_reservada(self):
        """PD-C14: no existe estado «atendida»; una cita pasada permanece reservada."""
        id_cita = self.insertar_cita_pasada()
        self.assertEqual(self.estado_de(id_cita), servicio.ESTADO_RESERVADA)

    def test_rnc13_cita_cancelada_incluye_su_motivo(self):
        """RN-C13: toda cancelación registra su motivo y queda visible para el paciente."""
        cita = self.reservar()
        servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO)
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.motivo_cancelacion, servicio.MOTIVO_PACIENTE)
        self.assertEqual(listada.nombre_estado, "Cancelada por el paciente")

    def test_pdc14_el_listado_incluye_pasadas_y_futuras(self):
        """PD-C14: el listado no filtra por fecha."""
        self.insertar_cita_pasada()
        self.reservar()
        self.assertEqual(len(servicio.consultar_citas(self.ruta_bd, self.codigo)), 2)

    def test_pdc10_la_cita_se_lista_con_la_duracion_vigente(self):
        """PD-C10: la duración de una cita es la vigente de su especialista."""
        self.reservar()
        self.assertEqual(
            servicio.consultar_citas(self.ruta_bd, self.codigo)[0].duracion_minutos, 20
        )


if __name__ == "__main__":
    unittest.main()
