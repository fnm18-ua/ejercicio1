"""Pruebas de reprogramación de citas (US4).

Verifican RF-C07, RN-C07, RN-C10, CA-C09, CL-C03, CL-C08, CL-C10 (una cita pasada no se
reprograma), CL-C13 (un hueco que empieza justo ahora no sirve de destino) y las precisiones
PD-C07 y PD-C08.
"""

import datetime
import unittest

from programacion_citas import servicio
from tests.utilidades_citas import (
    CENTRO,
    MOMENTO_FIJO,
    BaseCitasTestCase,
    fecha_futura,
    momento,
)


class PruebasReprogramacion(BaseCitasTestCase):
    """Traslado de una cita a otro hueco del mismo especialista (RF-C07, RN-C10)."""

    def test_cac09_reprogramar_conserva_id_y_especialista_y_libera_el_hueco(self):
        """CA-C09: mismo identificador y especialista; el hueco anterior queda libre."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        trasladada = servicio.reprogramar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", MOMENTO_FIJO
        )
        self.assertEqual(trasladada.id_cita, cita.id_cita)
        self.assertEqual(trasladada.id_especialista, cita.id_especialista)
        self.assertEqual(trasladada.hora_inicio, "11:00")
        horas = self.horas_libres(fecha=fecha)
        self.assertIn("09:00", horas)
        self.assertNotIn("11:00", horas)

    def test_cac09_reprogramar_no_crea_una_cita_nueva(self):
        """CE-C05: reprogramar es un traslado, nunca borrar e insertar."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        servicio.reprogramar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", MOMENTO_FIJO
        )
        self.assertEqual(len(servicio.consultar_citas(self.ruta_bd, self.codigo)), 1)

    def test_pdc08_la_propia_cita_no_cuenta_como_solapamiento_consigo_misma(self):
        """PD-C08: al comprobar RN-C07 se excluye la cita que se traslada."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        trasladada = servicio.reprogramar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, fecha, "09:00", MOMENTO_FIJO
        )
        self.assertEqual(trasladada.hora_inicio, "09:00")

    def test_rnc07_reprogramar_a_un_hueco_solapado_con_otra_cita_se_rechaza(self):
        """RN-C07: el traslado no puede pisar otra cita reservada del mismo paciente."""
        fecha = fecha_futura()
        primera = self.reservar(fecha=fecha, hora="09:00")
        otra = servicio.buscar_especialistas(self.ruta_bd, "Traumatología", CENTRO)[0]
        segunda = servicio.reservar_cita(
            self.ruta_bd, self.codigo, otra.id_especialista, fecha, "10:05", MOMENTO_FIJO
        )
        with self.assertRaises(servicio.CitaSolapada):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, primera.id_cita, fecha, "10:00", MOMENTO_FIJO
            )
        self.assertEqual(self.estado_de(segunda.id_cita), servicio.ESTADO_RESERVADA)

    def test_clc03_reprogramar_a_un_hueco_ocupado_se_rechaza(self):
        """CL-C03: el hueco destino debe estar libre."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        otro = self.registrar_otro_paciente()
        self.reservar(fecha=fecha, hora="11:00", codigo=otro)
        with self.assertRaises(servicio.HuecoNoDisponible):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", MOMENTO_FIJO
            )

    def test_rnc08_reprogramar_a_un_hueco_pasado_se_rechaza(self):
        """RN-C08: el hueco destino no puede estar en el pasado."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="12:40", ahora=momento(fecha, "08:00"))
        with self.assertRaises(servicio.HuecoPasado):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "09:00",
                momento(fecha, "10:00"),
            )

    def test_cac07_reprogramar_fuera_de_plazo_se_rechaza(self):
        """CA-C07: el plazo de las 24 horas también rige la reprogramación."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        with self.assertRaises(servicio.FueraDePlazo):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00",
                momento(fecha, "06:00"),
            )

    def test_clc08_reprogramar_una_cita_ya_cancelada_se_rechaza(self):
        """CL-C08: una cita cancelada no vuelve al estado reservada."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        servicio.cancelar_cita(self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO)
        with self.assertRaises(servicio.CitaYaCancelada):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", MOMENTO_FIJO
            )
        self.assertEqual(self.estado_de(cita.id_cita), servicio.ESTADO_CANCELADA_PACIENTE)

    def test_pdc07_reprogramar_actualiza_el_momento_de_reserva(self):
        """PD-C07 (aclaración Q2): tras reprogramar, la referencia de las 24 horas es el
        momento del traslado.

        Una cita reservada hace un mes para una fecha lejana, trasladada hoy a un hueco de dentro
        de 3 horas (RN-C08 no exige antelación mínima), SÍ se puede cancelar después: su reserva
        efectiva es de hace minutos. Con la lectura contraria quedaría atrapada.
        """
        fecha_lejana = fecha_futura(dias=30)
        hace_un_mes = MOMENTO_FIJO - datetime.timedelta(days=30)
        cita = self.reservar(fecha=fecha_lejana, hora="09:00", ahora=hace_un_mes)

        # Hoy (MOMENTO_FIJO, 08:00) se traslada al hueco de las 11:00 de hoy, 3 horas después.
        hoy = MOMENTO_FIJO.date().isoformat()
        trasladada = servicio.reprogramar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, hoy, "11:00", MOMENTO_FIJO
        )
        self.assertEqual(trasladada.fecha, hoy)
        self.assertEqual(
            trasladada.momento_reserva, MOMENTO_FIJO.strftime("%Y-%m-%d %H:%M:%S")
        )

        cancelada = servicio.cancelar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, MOMENTO_FIJO + datetime.timedelta(minutes=5)
        )
        self.assertEqual(cancelada.estado, servicio.ESTADO_CANCELADA_PACIENTE)

    def test_pdc07_sin_actualizar_el_momento_la_cita_quedaria_atrapada(self):
        """PD-C07: contraste explícito de la decisión Q2.

        La misma cita, si NO se reprograma, no se puede cancelar dentro de las 24 horas (CA-C07).
        Es lo que hace necesaria la actualización del momento de reserva.
        """
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00", ahora=MOMENTO_FIJO)
        with self.assertRaises(servicio.FueraDePlazo):
            servicio.cancelar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, momento(fecha, "06:00")
            )

    def test_rnc10_no_se_puede_cambiar_de_especialista(self):
        """RN-C10: reprogramar conserva el especialista; solo cambian fecha y hora."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        trasladada = servicio.reprogramar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, fecha_futura(dias=14), "09:00", MOMENTO_FIJO
        )
        self.assertEqual(trasladada.id_especialista, self.especialista.id_especialista)

    def test_rfc07_reprogramar_una_cita_de_otro_paciente_se_rechaza(self):
        """RF-C07: el paciente solo traslada sus propias citas."""
        cita = self.reservar()
        otro = self.registrar_otro_paciente()
        with self.assertRaises(servicio.CitaNoEncontrada):
            servicio.reprogramar_cita(
                self.ruta_bd, otro, cita.id_cita, fecha_futura(), "11:00", MOMENTO_FIJO
            )

    def test_clc10_reprogramar_una_cita_pasada_se_rechaza(self):
        """CL-C10, PD-C07: una cita cuya hora ya ha pasado no se traslada, aunque se reservara
        con menos de 24 horas de antelación, y conserva su fecha y su hora."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00", ahora=momento(fecha, "06:00"))
        with self.assertRaises(servicio.CitaPasada):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", momento(fecha, "09:30")
            )
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.estado, servicio.ESTADO_RESERVADA)
        self.assertEqual(listada.fecha, fecha)
        self.assertEqual(listada.hora_inicio, "09:00")

    def test_clc10_el_rechazo_por_cita_pasada_precede_al_de_plazo(self):
        """CL-C10, PD-C18: el motivo es que la cita ya ha pasado, no el plazo de 24 horas."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00", ahora=MOMENTO_FIJO)
        with self.assertRaises(servicio.CitaPasada):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha, "11:00", momento(fecha, "09:30")
            )

    def test_clc13_reprogramar_a_un_hueco_que_empieza_justo_ahora_se_rechaza(self):
        """CL-C13, PD-C05, PD-C08: el hueco destino debe empezar después del momento actual."""
        fecha_original = fecha_futura(dias=14)
        fecha_destino = fecha_futura(dias=7)
        cita = self.reservar(fecha=fecha_original, hora="09:00", ahora=MOMENTO_FIJO)
        with self.assertRaises(servicio.HuecoPasado):
            servicio.reprogramar_cita(
                self.ruta_bd, self.codigo, cita.id_cita, fecha_destino, "09:00",
                momento(fecha_destino, "09:00"),
            )
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.fecha, fecha_original)
        self.assertEqual(listada.hora_inicio, "09:00")


if __name__ == "__main__":
    unittest.main()
