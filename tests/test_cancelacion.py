"""Pruebas de cancelación de citas por el paciente (US3).

Verifican RF-C06, RN-C09, RN-C13, CA-C06, CA-C07, CA-C08 y CL-C07. Todas fijan el momento actual
y el momento de reserva de forma explícita (D-C10), porque el plazo de las 24 horas depende de
ambos.
"""

import datetime
import unittest

from programacion_citas import servicio
from tests.utilidades_citas import (
    MOMENTO_FIJO,
    BaseCitasTestCase,
    fecha_futura,
    momento,
)


class PruebasCancelacion(BaseCitasTestCase):
    """Cancelación a petición del paciente (RF-C06, RN-C09)."""

    def test_cac06_cancelacion_con_mas_de_24_horas_libera_el_hueco(self):
        """CA-C06: queda «cancelada por el paciente» y su hueco vuelve a estar libre."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        self.assertNotIn("09:00", self.horas_libres(fecha=fecha))
        cancelada = servicio.cancelar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO
        )
        self.assertEqual(cancelada.estado, servicio.ESTADO_CANCELADA_PACIENTE)
        self.assertEqual(cancelada.motivo_cancelacion, servicio.MOTIVO_PACIENTE)
        self.assertIn("09:00", self.horas_libres(fecha=fecha))

    def test_cac07_cancelacion_con_menos_de_24_horas_se_rechaza(self):
        """CA-C07: una cita reservada hace más de 24 horas ya no se puede cancelar."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        tres_horas_antes = momento(fecha, "06:00")
        with self.assertRaises(servicio.FueraDePlazo):
            servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, tres_horas_antes)
        self.assertEqual(self.estado_de(cita.id_cita), servicio.ESTADO_RESERVADA)

    def test_cac08_cita_reservada_hoy_para_dentro_de_3_horas_se_puede_cancelar(self):
        """CA-C08: si se reservó con menos de 24 horas de antelación, se puede cancelar."""
        fecha = fecha_futura()
        reserva = momento(fecha, "06:00")
        cita = self.reservar(fecha=fecha, hora="09:00", ahora=reserva)
        cancelada = servicio.cancelar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, reserva + datetime.timedelta(minutes=5)
        )
        self.assertEqual(cancelada.estado, servicio.ESTADO_CANCELADA_PACIENTE)

    def test_rnc09_justo_24_horas_antes_se_permite(self):
        """RN-C09: el límite es «hasta 24 horas antes», incluido el instante exacto."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        justo = momento(fecha, "09:00") - datetime.timedelta(hours=24)
        cancelada = servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, justo)
        self.assertEqual(cancelada.estado, servicio.ESTADO_CANCELADA_PACIENTE)

    def test_clc07_cancelar_una_cita_ya_cancelada_se_rechaza(self):
        """CL-C07: una cita cancelada no se puede volver a cancelar."""
        cita = self.reservar()
        servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO)
        with self.assertRaises(servicio.CitaYaCancelada):
            servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO)

    def test_rfc06_cancelar_una_cita_de_otro_paciente_se_rechaza(self):
        """RF-C06: el paciente solo opera con sus propias citas."""
        cita = self.reservar()
        otro = self.registrar_otro_paciente()
        with self.assertRaises(servicio.CitaNoEncontrada):
            servicio.cancelar_cita(self.ruta_bd, otro, cita.id_cita, MOMENTO_FIJO)
        self.assertEqual(self.estado_de(cita.id_cita), servicio.ESTADO_RESERVADA)

    def test_rfc06_cancelar_una_cita_inexistente_se_rechaza(self):
        """RF-C06: un identificador que no existe se rechaza con el motivo concreto."""
        with self.assertRaises(servicio.CitaNoEncontrada):
            servicio.cancelar_cita(self.ruta_bd, self.codigo, 9999, MOMENTO_FIJO)

    def test_pdc04_el_hueco_liberado_puede_reservarlo_otro_paciente(self):
        """PD-C04: las citas canceladas no ocupan hueco."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO)
        otro = self.registrar_otro_paciente()
        nueva = self.reservar(fecha=fecha, hora="09:00", codigo=otro)
        self.assertEqual(nueva.hora_inicio, "09:00")
        self.assertNotEqual(nueva.id_cita, cita.id_cita)


if __name__ == "__main__":
    unittest.main()
