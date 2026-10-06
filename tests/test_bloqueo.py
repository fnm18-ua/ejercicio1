"""Pruebas de bloqueo de franjas por el personal administrativo (US5).

Verifican RF-C08, RN-C04, RN-C11, RN-C13, CA-C10, CA-C11, CL-C04, CL-C12 y las precisiones PD-C11,
PD-C12 (franja con rango de fechas, aclaración Q1 del 2026-09-28) y PD-C23 (franjas mal formadas o
enteras en el pasado, aclaración Q4 del 2026-10-06).
"""

import unittest

from programacion_citas import base_datos, servicio
from tests.utilidades_citas import (
    MOMENTO_FIJO,
    BaseCitasTestCase,
    fecha_futura,
    fecha_pasada,
    momento,
)


class PruebasBloqueo(BaseCitasTestCase):
    """Bloqueo de una franja y cancelación por el centro (RF-C08, RN-C11)."""

    def bloquear(self, fecha_inicio, fecha_fin=None, hora_inicio="09:00", hora_fin="11:00",
                 ahora=MOMENTO_FIJO):
        """Atajo para bloquear una franja del especialista de las pruebas."""
        return servicio.bloquear_franja(
            self.ruta_bd,
            self.especialista.id_especialista,
            fecha_inicio,
            fecha_fin or fecha_inicio,
            hora_inicio,
            hora_fin,
            ahora,
        )

    def franjas_registradas(self):
        """Franjas bloqueadas guardadas para el especialista de las pruebas (PD-C23)."""
        conexion = base_datos.conectar(self.ruta_bd)
        try:
            return base_datos.franjas_de(conexion, self.especialista.id_especialista)
        finally:
            conexion.close()

    def test_cac10_bloqueo_de_9_a_11_cancela_las_de_dentro_y_conserva_las_de_las_11(self):
        """CA-C10: se cancelan 9:00, 10:00 y 10:40 (que acaba justo a las 11:00) y sobrevive 11:00."""
        fecha = fecha_futura()
        citas = {}
        for hora in ("09:00", "10:00", "10:40", "11:00"):
            codigo = self.registrar_otro_paciente(numero_documento=f"5555{hora[:2]}{hora[3:]}Z")
            citas[hora] = (self.reservar(fecha=fecha, hora=hora, codigo=codigo), codigo)
        canceladas = self.bloquear(fecha)
        self.assertEqual(len(canceladas), 3)
        for hora in ("09:00", "10:00", "10:40"):
            cita, codigo = citas[hora]
            estado = self._estado(codigo, cita.id_cita)
            self.assertEqual(estado, servicio.ESTADO_CANCELADA_CENTRO, f"hora {hora}")
        cita, codigo = citas["11:00"]
        self.assertEqual(self._estado(codigo, cita.id_cita), servicio.ESTADO_RESERVADA)

    def _estado(self, codigo, id_cita):
        """Estado de una cita de cualquier paciente."""
        for cita in servicio.consultar_citas(self.ruta_bd, codigo):
            if cita.id_cita == id_cita:
                return cita.estado
        return None

    def test_cac11_la_cita_cancelada_se_ve_con_su_motivo_en_el_listado(self):
        """CA-C11: el paciente ve su cita cancelada por el centro con el motivo (RN-C13)."""
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        self.bloquear(fecha)
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.estado, servicio.ESTADO_CANCELADA_CENTRO)
        self.assertEqual(listada.motivo_cancelacion, servicio.MOTIVO_FRANJA)
        self.assertEqual(listada.nombre_estado, "Cancelada por el centro")

    def test_rnc11_el_bloqueo_no_respeta_el_plazo_de_24_horas(self):
        """RN-C11: la cancelación por el centro no está sujeta a la regla de las 24 horas."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        canceladas = self.bloquear(fecha, ahora=momento(fecha, "06:00"))
        self.assertEqual(len(canceladas), 1)
        self.assertEqual(self.estado_de(cita.id_cita), servicio.ESTADO_CANCELADA_CENTRO)

    def test_pdc11_el_bloqueo_no_altera_una_cita_pasada(self):
        """PD-C11 (aclaración Q3): las citas pasadas son historial, no agenda.

        La franja cubre la cita pasada y su fin aún no ha llegado: una franja entera en el pasado
        se rechazaría (PD-C23) y no serviría para esta comprobación.
        """
        fecha = fecha_pasada()
        id_cita = self.insertar_cita_pasada(hora="09:00", fecha=fecha)
        canceladas = self.bloquear(fecha, fecha_fin=fecha_futura())
        self.assertEqual(canceladas, [])
        self.assertEqual(self.estado_de(id_cita), servicio.ESTADO_RESERVADA)

    def test_clc04_bloqueo_sin_citas_dentro_no_cancela_nada(self):
        """CL-C04: la franja se aplica sin cancelar ninguna cita."""
        fecha = fecha_futura()
        self.assertEqual(self.bloquear(fecha), [])
        self.assertEqual(self.horas_libres(fecha=fecha)[0], "11:00")

    def test_pdc12_bloqueo_de_varios_dias_cancela_las_citas_de_todo_el_rango(self):
        """PD-C12 (aclaración Q1): unas vacaciones se bloquean con un solo bloqueo."""
        primera = fecha_futura(dias=7)
        segunda = fecha_futura(dias=8)
        self.assertNotEqual(primera, segunda)
        otro = self.registrar_otro_paciente()
        self.reservar(fecha=primera, hora="09:00")
        self.reservar(fecha=segunda, hora="09:00", codigo=otro)
        canceladas = self.bloquear(primera, segunda)
        self.assertEqual(len(canceladas), 2)
        self.assertEqual({cita.fecha for cita in canceladas}, {primera, segunda})

    def test_pdc12_el_bloqueo_no_alcanza_fechas_fuera_del_rango(self):
        """PD-C12: el rango es cerrado; una cita del día siguiente no se cancela."""
        dentro = fecha_futura(dias=7)
        fuera = fecha_futura(dias=8)
        cita_fuera = self.reservar(fecha=fuera, hora="09:00")
        self.bloquear(dentro, dentro)
        self.assertEqual(self.estado_de(cita_fuera.id_cita), servicio.ESTADO_RESERVADA)

    def test_rnc04_los_huecos_bloqueados_dejan_de_ofrecerse(self):
        """RN-C04: un hueco dentro de una franja bloqueada no está libre."""
        fecha = fecha_futura()
        self.bloquear(fecha)
        horas = self.horas_libres(fecha=fecha)
        for hora in ("09:00", "10:00", "10:40"):
            self.assertNotIn(hora, horas)
        self.assertIn("11:00", horas)

    def test_rnc04_no_se_puede_reservar_en_una_franja_bloqueada(self):
        """RN-C04: la reserva de un hueco bloqueado se rechaza."""
        fecha = fecha_futura()
        self.bloquear(fecha)
        with self.assertRaises(servicio.HuecoNoDisponible):
            self.reservar(fecha=fecha, hora="09:00")

    def test_rfc08_rango_de_fechas_invertido_se_rechaza(self):
        """PD-C18: la fecha de fin no puede ser anterior a la de inicio (CL-C12, PD-C23 caso a)."""
        with self.assertRaises(servicio.ErrorValidacion):
            self.bloquear(fecha_futura(dias=8), fecha_futura(dias=7))

    def test_rfc08_horas_invertidas_se_rechazan(self):
        """PD-C18: la hora de fin debe ser posterior a la de inicio (CL-C12, PD-C23 caso b)."""
        with self.assertRaises(servicio.ErrorValidacion):
            self.bloquear(fecha_futura(), hora_inicio="11:00", hora_fin="09:00")

    def test_clc12_franja_con_fecha_de_fin_anterior_a_hoy_se_rechaza(self):
        """CL-C12, PD-C23 caso c: una franja entera en el pasado se rechaza y no se registra."""
        with self.assertRaises(servicio.ErrorValidacion) as contexto:
            self.bloquear(fecha_pasada())
        self.assertEqual(
            contexto.exception.mensaje,
            "No se puede bloquear una franja cuya fecha y hora de fin ya han pasado.",
        )
        self.assertEqual(self.franjas_registradas(), [])

    def test_clc12_franja_de_hoy_con_el_tramo_ya_terminado_se_rechaza(self):
        """CL-C12, PD-C23 caso c: cuenta la fecha y la hora de fin, no solo la fecha."""
        hoy = MOMENTO_FIJO.date().isoformat()
        with self.assertRaises(servicio.ErrorValidacion) as contexto:
            self.bloquear(hoy, hora_inicio="09:00", hora_fin="11:00", ahora=momento(hoy, "15:00"))
        self.assertEqual(
            contexto.exception.mensaje,
            "No se puede bloquear una franja cuya fecha y hora de fin ya han pasado.",
        )
        self.assertEqual(self.franjas_registradas(), [])

    def test_pdc23_franja_de_hoy_que_acaba_justo_ahora_se_rechaza(self):
        """PD-C23: se rechaza cuando el fin no es posterior al momento actual, también si
        coincide con él."""
        hoy = MOMENTO_FIJO.date().isoformat()
        with self.assertRaises(servicio.ErrorValidacion):
            self.bloquear(hoy, hora_inicio="09:00", hora_fin="11:00", ahora=momento(hoy, "11:00"))
        self.assertEqual(self.franjas_registradas(), [])

    def test_pdc23_franja_de_hoy_cuya_hora_de_fin_no_ha_llegado_se_acepta(self):
        """PD-C23: un bloqueo de hoy de 9:00 a 14:00 pedido a las 11:00 se acepta."""
        hoy = MOMENTO_FIJO.date().isoformat()
        canceladas = self.bloquear(
            hoy, hora_inicio="09:00", hora_fin="14:00", ahora=momento(hoy, "11:00")
        )
        self.assertEqual(canceladas, [])
        self.assertEqual(len(self.franjas_registradas()), 1)

    def test_pdc23_franja_fuera_del_horario_se_acepta(self):
        """PD-C23: una franja sin efecto no se rechaza; solo las mal formadas o ya pasadas."""
        canceladas = self.bloquear(fecha_futura(), hora_inicio="15:00", hora_fin="17:00")
        self.assertEqual(canceladas, [])
        self.assertEqual(len(self.franjas_registradas()), 1)

    def test_clc12_una_franja_rechazada_no_cancela_ninguna_cita(self):
        """CL-C12: el rechazo no registra la franja ni cancela ninguna cita."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        with self.assertRaises(servicio.ErrorValidacion):
            self.bloquear(fecha_futura(dias=8), fecha)
        self.assertEqual(self.estado_de(cita.id_cita), servicio.ESTADO_RESERVADA)
        self.assertEqual(self.franjas_registradas(), [])


if __name__ == "__main__":
    unittest.main()
