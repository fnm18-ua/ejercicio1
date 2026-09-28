"""Pruebas del ajuste de la duración de las consultas (US6).

Verifican RF-C09, RN-C12, CA-C12, CL-C05 y las precisiones PD-C10, PD-C11 y PD-C20.
"""

import unittest

from programacion_citas import servicio
from tests.utilidades_citas import (
    MOMENTO_FIJO,
    BaseCitasTestCase,
    fecha_futura,
    fecha_pasada,
)


class PruebasDuracion(BaseCitasTestCase):
    """Recálculo de la rejilla al cambiar la duración (RF-C09, RN-C12)."""

    def ajustar(self, minutos, ahora=MOMENTO_FIJO):
        """Atajo para ajustar la duración del especialista de las pruebas."""
        return servicio.ajustar_duracion(
            self.ruta_bd, self.especialista.id_especialista, minutos, ahora
        )

    def test_cac12_al_pasar_de_20_a_30_minutos_la_de_las_9_sigue_y_la_de_las_9_20_se_cancela(self):
        """CA-C12: encaja la de las 9:00 y no la de las 9:20."""
        fecha = fecha_futura()
        nueve = self.reservar(fecha=fecha, hora="09:00")
        otro = self.registrar_otro_paciente()
        nueve_veinte = self.reservar(fecha=fecha, hora="09:20", codigo=otro)
        canceladas = self.ajustar(30)
        self.assertEqual(len(canceladas), 1)
        self.assertEqual(canceladas[0].id_cita, nueve_veinte.id_cita)
        self.assertEqual(canceladas[0].motivo_cancelacion, servicio.MOTIVO_DURACION)
        self.assertEqual(self.estado_de(nueve.id_cita), servicio.ESTADO_RESERVADA)

    def test_clc05_al_pasar_a_50_minutos_la_rejilla_tiene_4_huecos(self):
        """CL-C05: 9:00-13:00 con 50 minutos genera 4 huecos, sin tramo parcial."""
        self.ajustar(50)
        self.assertEqual(
            self.horas_libres(fecha=fecha_futura()), ["09:00", "09:50", "10:40", "11:30"]
        )

    def test_cac12_la_rejilla_de_30_minutos_tiene_8_huecos(self):
        """RN-C12: los huecos se recalculan sobre la duración nueva."""
        self.ajustar(30)
        horas = self.horas_libres(fecha=fecha_futura())
        self.assertEqual(len(horas), 8)
        self.assertEqual(horas[-1], "12:30")

    def test_pdc11_el_cambio_de_duracion_no_altera_una_cita_pasada(self):
        """PD-C11 (aclaración Q3): una consulta ya celebrada no se cancela."""
        id_cita = self.insertar_cita_pasada(hora="09:20", fecha=fecha_pasada())
        canceladas = self.ajustar(30)
        self.assertEqual(canceladas, [])
        self.assertEqual(self.estado_de(id_cita), servicio.ESTADO_RESERVADA)

    def test_pdc10_la_duracion_de_una_cita_es_la_vigente_del_especialista(self):
        """PD-C10: la duración no se congela al reservar."""
        cita = self.reservar(hora="09:00")
        self.assertEqual(cita.duracion_minutos, 20)
        self.ajustar(30)
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.duracion_minutos, 30)

    def test_pdc20_el_recalculo_no_comprueba_el_solapamiento_del_paciente(self):
        """PD-C20: limitación conocida y declarada, no un defecto silencioso.

        Escenario: el paciente tiene cita con Lucía (8:00-13:00, tramos de 25) a las 9:15 y con
        Ana (9:00-13:00, tramos de 20) a las 9:40. Antes no se solapan: la primera acaba justo
        cuando empieza la segunda. Al pasar Lucía a tramos de 75 minutos, las 9:15 siguen siendo
        inicio de hueco (8:00, 9:15, 10:30, 11:45) y la cita cabe entera, así que RN-C12 NO la
        cancela; pero ahora ocupa de 9:15 a 10:30 y pisa la de Ana.

        Esta prueba fija que el sistema CONSERVA las dos citas solapadas, porque RN-C12 solo
        decide el encaje en la rejilla y no vuelve a comprobar RN-C07. Si algún día se decide
        cerrar esta limitación, será una ampliación explícita del alcance y esta prueba deberá
        cambiarse a propósito.
        """
        from programacion_citas import agenda

        fecha = fecha_futura()
        lucia = servicio.buscar_especialistas(self.ruta_bd, "Traumatología", "Centro Norte")[0]
        con_lucia = servicio.reservar_cita(
            self.ruta_bd, self.codigo, lucia.id_especialista, fecha, "09:15", MOMENTO_FIJO
        )
        con_ana = self.reservar(fecha=fecha, hora="09:40")

        canceladas = servicio.ajustar_duracion(
            self.ruta_bd, lucia.id_especialista, 75, MOMENTO_FIJO
        )

        self.assertEqual(canceladas, [], "la cita de las 9:15 sigue encajando en la rejilla nueva")
        self.assertEqual(self.estado_de(con_lucia.id_cita), servicio.ESTADO_RESERVADA)
        self.assertEqual(self.estado_de(con_ana.id_cita), servicio.ESTADO_RESERVADA)

        citas = {cita.id_cita: cita for cita in servicio.consultar_citas(self.ruta_bd, self.codigo)}
        self.assertTrue(
            agenda.se_solapan(
                citas[con_lucia.id_cita].hora_inicio,
                citas[con_lucia.id_cita].duracion_minutos,
                citas[con_ana.id_cita].hora_inicio,
                citas[con_ana.id_cita].duracion_minutos,
            ),
            "PD-C20: las dos citas quedan solapadas y el sistema las conserva",
        )

    def test_rfc09_duracion_no_positiva_se_rechaza(self):
        """PD-C18: la duración debe ser un entero positivo."""
        with self.assertRaises(servicio.ErrorValidacion):
            self.ajustar(0)
        with self.assertRaises(servicio.ErrorValidacion):
            self.ajustar(-10)

    def test_rfc09_duracion_no_numerica_se_rechaza(self):
        """PD-C18: una duración no numérica se rechaza con el motivo concreto."""
        with self.assertRaises(servicio.ErrorValidacion):
            self.ajustar("media hora")

    def test_rfc09_el_horario_no_cambia_al_ajustar_la_duracion(self):
        """PD-C19: solo la duración es ajustable; el horario es dato precargado."""
        self.ajustar(30)
        especialista = servicio.obtener_especialista(
            self.ruta_bd, self.especialista.id_especialista
        )
        self.assertEqual(especialista.hora_inicio, self.especialista.hora_inicio)
        self.assertEqual(especialista.hora_fin, self.especialista.hora_fin)
        self.assertEqual(especialista.dias_semana, self.especialista.dias_semana)
        self.assertEqual(especialista.duracion_minutos, 30)


if __name__ == "__main__":
    unittest.main()
