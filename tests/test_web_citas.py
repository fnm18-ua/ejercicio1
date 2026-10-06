"""Pruebas de la interfaz web del módulo de citas (fase de cierre).

Verifican las 11 rutas del contrato, CA-C13 (no hay pantalla de gestión de centros,
especialidades ni especialistas), PD-C13 (no hay desbloqueo), D-C13 (las rutas del módulo de
registro siguen funcionando con el manejador combinado) y D-C16 (todo dato mostrado se escapa).
"""

import unittest
from urllib.parse import quote

from programacion_citas import servicio
from tests.utilidades_citas import (
    CENTRO,
    ESPECIALIDAD,
    ServidorCitasTestCase,
    fecha_futura,
    fecha_pasada,
)


class PruebasWebCitas(ServidorCitasTestCase):
    """Rutas del flujo del paciente y del flujo de la agenda."""

    def test_ruta1_identificacion(self):
        """Ruta 1 · GET /citas: formularios de identificación (RF-C01)."""
        estado, _, cuerpo = self.peticion_get("/citas")
        self.assertEqual(estado, 200)
        self.assertIn("Código de historia clínica", cuerpo)
        self.assertIn("Número de documento", cuerpo)

    def test_ruta2_busqueda_con_desplegables(self):
        """Ruta 2 · GET /citas/buscar: desplegables de especialidad y centro (RF-C02)."""
        estado, _, cuerpo = self.peticion_get(f"/citas/buscar?codigo={self.codigo}")
        self.assertEqual(estado, 200)
        self.assertIn(ESPECIALIDAD, cuerpo)
        self.assertIn(CENTRO, cuerpo)

    def test_ruta2_busqueda_sin_resultados_informa(self):
        """CL-C02: sin coincidencias se informa, sin error."""
        estado, _, cuerpo = self.peticion_get(
            f"/citas/buscar?codigo={self.codigo}"
            f"&especialidad={quote('Traumatología')}&centro={quote('Centro Sur')}"
        )
        self.assertEqual(estado, 200)
        self.assertIn("No hay especialistas de esa especialidad en ese centro.", cuerpo)

    def test_ruta2_paciente_no_identificado_responde_400(self):
        """CL-C09: un código inexistente se rechaza con el motivo concreto."""
        estado, _, cuerpo = self.peticion_get("/citas/buscar?codigo=HC-999998")
        self.assertEqual(estado, 400)
        self.assertIn("No existe ningún paciente con esos datos.", cuerpo)

    def test_ruta3_huecos_muestra_la_rejilla(self):
        """Ruta 3 · GET /citas/huecos: un botón por hueco libre (RF-C03, CA-C01)."""
        estado, _, cuerpo = self.peticion_get(
            f"/citas/huecos?codigo={self.codigo}"
            f"&id_especialista={self.especialista.id_especialista}&fecha={fecha_futura()}"
        )
        self.assertEqual(estado, 200)
        self.assertIn("Reservar 09:00", cuerpo)
        self.assertIn("Reservar 12:40", cuerpo)

    def test_ruta3_fecha_sin_consulta_informa(self):
        """CL-C06: en un sábado no se ofrece ningún hueco."""
        estado, _, cuerpo = self.peticion_get(
            f"/citas/huecos?codigo={self.codigo}"
            f"&id_especialista={self.especialista.id_especialista}&fecha=2026-10-10"
        )
        self.assertEqual(estado, 200)
        self.assertIn("No hay huecos disponibles en esa fecha.", cuerpo)

    def test_ruta3_fecha_mal_formada_responde_400(self):
        """PD-C18: una fecha inválida se rechaza indicando el motivo."""
        estado, _, cuerpo = self.peticion_get(
            f"/citas/huecos?codigo={self.codigo}"
            f"&id_especialista={self.especialista.id_especialista}&fecha=treinta-de-febrero"
        )
        self.assertEqual(estado, 400)
        self.assertIn("La fecha indicada no es válida.", cuerpo)

    def test_ruta4_reservar_redirige_al_listado(self):
        """Ruta 4 · POST /citas: reserva y redirige con 303 (RF-C04)."""
        estado, cabeceras, _ = self.peticion_post(
            "/citas",
            {
                "codigo": self.codigo,
                "id_especialista": self.especialista.id_especialista,
                "fecha": fecha_futura(),
                "hora_inicio": "09:00",
            },
        )
        self.assertEqual(estado, 303)
        self.assertIn("aviso=reservada", cabeceras["Location"])

    def test_ruta4_hueco_ocupado_responde_409(self):
        """CL-C03: la segunda reserva del mismo hueco se rechaza con 409."""
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00", codigo=self.registrar_otro_paciente())
        estado, _, cuerpo = self.peticion_post(
            "/citas",
            {
                "codigo": self.codigo,
                "id_especialista": self.especialista.id_especialista,
                "fecha": fecha,
                "hora_inicio": "09:00",
            },
        )
        self.assertEqual(estado, 409)
        self.assertIn("Ese hueco ya no está disponible.", cuerpo)

    def test_ruta5_listado_sin_citas_informa(self):
        """PD-C14: un paciente sin citas recibe un aviso, no un error."""
        estado, _, cuerpo = self.peticion_get(f"/citas/mias?codigo={self.codigo}")
        self.assertEqual(estado, 200)
        self.assertIn("No tiene ninguna cita.", cuerpo)

    def test_ruta5_listado_muestra_estado_y_motivo(self):
        """CA-C11: el listado muestra el estado y, si está cancelada, el motivo (RN-C13)."""
        cita = self.reservar()
        servicio.cancelar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, servicio.momento_actual()
        )
        estado, _, cuerpo = self.peticion_get(f"/citas/mias?codigo={self.codigo}")
        self.assertEqual(estado, 200)
        self.assertIn("Cancelada por el paciente", cuerpo)
        self.assertIn(servicio.MOTIVO_PACIENTE, cuerpo)

    def test_ruta6_cancelar_redirige_al_listado(self):
        """Ruta 6 · POST /citas/<id>/cancelar (RF-C06, CA-C06)."""
        cita = self.reservar()
        estado, cabeceras, _ = self.peticion_post(
            f"/citas/{cita.id_cita}/cancelar", {"codigo": self.codigo}
        )
        self.assertEqual(estado, 303)
        self.assertIn("aviso=cancelada", cabeceras["Location"])

    def test_ruta6_cancelar_cita_ya_cancelada_responde_409(self):
        """CL-C07: una cita ya cancelada no se puede volver a cancelar."""
        cita = self.reservar()
        self.peticion_post(f"/citas/{cita.id_cita}/cancelar", {"codigo": self.codigo})
        estado, _, cuerpo = self.peticion_post(
            f"/citas/{cita.id_cita}/cancelar", {"codigo": self.codigo}
        )
        self.assertEqual(estado, 409)
        self.assertIn("Esa cita ya está cancelada.", cuerpo)

    def test_ruta6_cancelar_cita_inexistente_responde_404(self):
        """RF-C06: una cita que no existe o no es del paciente responde 404."""
        estado, _, _ = self.peticion_post("/citas/9999/cancelar", {"codigo": self.codigo})
        self.assertEqual(estado, 404)

    def test_ruta6_cancelar_cita_pasada_responde_409(self):
        """CL-C10: una cita cuya hora ya ha pasado no se cancela, y se dice por qué (PD-C18)."""
        id_cita = self.insertar_cita_pasada()
        estado, _, cuerpo = self.peticion_post(
            f"/citas/{id_cita}/cancelar", {"codigo": self.codigo}
        )
        self.assertEqual(estado, 409)
        self.assertIn("cuya hora ya ha pasado", cuerpo)

    def test_ruta7_reprogramar_ofrece_huecos_del_mismo_especialista(self):
        """Ruta 7 · GET /citas/<id>/reprogramar: no permite cambiar de especialista (RN-C10)."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        estado, _, cuerpo = self.peticion_get(
            f"/citas/{cita.id_cita}/reprogramar?codigo={self.codigo}&fecha={fecha}"
        )
        self.assertEqual(estado, 200)
        self.assertIn("Trasladar a 11:00", cuerpo)
        self.assertIn("Se conserva el mismo especialista", cuerpo)

    def test_ruta7_reprogramar_cita_cancelada_responde_409(self):
        """CL-C08: no se ofrecen huecos para una cita ya cancelada."""
        cita = self.reservar()
        servicio.cancelar_cita(
            self.ruta_bd, self.codigo, cita.id_cita, servicio.momento_actual()
        )
        estado, _, cuerpo = self.peticion_get(
            f"/citas/{cita.id_cita}/reprogramar?codigo={self.codigo}"
        )
        self.assertEqual(estado, 409)
        self.assertIn("Esa cita ya está cancelada.", cuerpo)

    def test_ruta8_reprogramar_redirige_y_conserva_el_identificador(self):
        """Ruta 8 · POST /citas/<id>/reprogramar (RF-C07, CA-C09)."""
        fecha = fecha_futura()
        cita = self.reservar(fecha=fecha, hora="09:00")
        estado, cabeceras, _ = self.peticion_post(
            f"/citas/{cita.id_cita}/reprogramar",
            {"codigo": self.codigo, "fecha": fecha, "hora_inicio": "11:00"},
        )
        self.assertEqual(estado, 303)
        self.assertIn("aviso=reprogramada", cabeceras["Location"])
        listada = servicio.consultar_citas(self.ruta_bd, self.codigo)[0]
        self.assertEqual(listada.id_cita, cita.id_cita)
        self.assertEqual(listada.hora_inicio, "11:00")

    def test_ruta7_reprogramar_cita_pasada_responde_409(self):
        """CL-C10: para una cita ya pasada no se ofrece ningún hueco destino."""
        id_cita = self.insertar_cita_pasada()
        estado, _, cuerpo = self.peticion_get(
            f"/citas/{id_cita}/reprogramar?codigo={self.codigo}"
        )
        self.assertEqual(estado, 409)
        self.assertIn("cuya hora ya ha pasado", cuerpo)
        self.assertNotIn("Trasladar a", cuerpo)

    def test_ruta8_reprogramar_cita_pasada_responde_409(self):
        """CL-C10: el traslado de una cita ya pasada se rechaza con el motivo concreto."""
        id_cita = self.insertar_cita_pasada()
        estado, _, cuerpo = self.peticion_post(
            f"/citas/{id_cita}/reprogramar",
            {"codigo": self.codigo, "fecha": fecha_futura(), "hora_inicio": "11:00"},
        )
        self.assertEqual(estado, 409)
        self.assertIn("cuya hora ya ha pasado", cuerpo)

    def test_ruta9_agenda_lista_especialistas(self):
        """Ruta 9 · GET /agenda: especialistas con su horario y duración (RF-C08, RF-C09)."""
        estado, _, cuerpo = self.peticion_get("/agenda")
        self.assertEqual(estado, 200)
        self.assertIn(self.especialista.nombre, cuerpo)
        self.assertIn("consultas de 20 minutos", cuerpo)

    def test_ruta9_agenda_de_un_especialista_muestra_sus_dos_operaciones(self):
        """Ruta 9: bloquear franja y ajustar duración, y nada más (CA-C13)."""
        estado, _, cuerpo = self.peticion_get(
            f"/agenda?id_especialista={self.especialista.id_especialista}"
        )
        self.assertEqual(estado, 200)
        self.assertIn("Bloquear franja", cuerpo)
        self.assertIn("Ajustar la duración de las consultas", cuerpo)
        self.assertIn('name="fecha_inicio"', cuerpo)
        self.assertIn('name="fecha_fin"', cuerpo)

    def test_ruta10_bloquear_confirma_las_canceladas(self):
        """Ruta 10 · POST /agenda/bloquear (RF-C08, CA-C10)."""
        fecha = fecha_futura()
        self.reservar(fecha=fecha, hora="09:00")
        estado, _, cuerpo = self.peticion_post(
            "/agenda/bloquear",
            {
                "id_especialista": self.especialista.id_especialista,
                "fecha_inicio": fecha,
                "fecha_fin": fecha,
                "hora_inicio": "09:00",
                "hora_fin": "11:00",
            },
        )
        self.assertEqual(estado, 200)
        self.assertIn("Citas canceladas por el centro: 1", cuerpo)
        self.assertIn(servicio.MOTIVO_FRANJA, cuerpo)
        # PD-C22, CE-C10: fecha, hora y motivo de cada cita, sin ningún dato del paciente.
        self.assertIn(fecha, cuerpo)
        self.assertIn("09:00", cuerpo)
        self.assertNotIn(self.codigo, cuerpo)

    def test_ruta10_franja_pasada_responde_400(self):
        """CL-C12, PD-C23: una franja entera en el pasado se rechaza con el motivo concreto."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/bloquear",
            {
                "id_especialista": self.especialista.id_especialista,
                "fecha_inicio": fecha_pasada(),
                "fecha_fin": fecha_pasada(),
                "hora_inicio": "09:00",
                "hora_fin": "11:00",
            },
        )
        self.assertEqual(estado, 400)
        self.assertIn("cuya fecha y hora de fin ya han pasado", cuerpo)

    def test_ruta10_bloquear_sin_citas_lo_indica(self):
        """CL-C04: la franja se aplica sin cancelar nada."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/bloquear",
            {
                "id_especialista": self.especialista.id_especialista,
                "fecha_inicio": fecha_futura(),
                "fecha_fin": fecha_futura(),
                "hora_inicio": "09:00",
                "hora_fin": "11:00",
            },
        )
        self.assertEqual(estado, 200)
        self.assertIn("No se ha cancelado ninguna cita.", cuerpo)

    def test_ruta10_rango_invertido_responde_400(self):
        """PD-C18: la fecha de fin no puede ser anterior a la de inicio."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/bloquear",
            {
                "id_especialista": self.especialista.id_especialista,
                "fecha_inicio": fecha_futura(dias=8),
                "fecha_fin": fecha_futura(dias=7),
                "hora_inicio": "09:00",
                "hora_fin": "11:00",
            },
        )
        self.assertEqual(estado, 400)
        self.assertIn("La fecha de fin no puede ser anterior a la de inicio.", cuerpo)

    def test_ruta11_ajustar_duracion_confirma_y_muestra_la_rejilla(self):
        """Ruta 11 · POST /agenda/duracion (RF-C09, CA-C12)."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/duracion",
            {"id_especialista": self.especialista.id_especialista, "duracion_minutos": "30"},
        )
        self.assertEqual(estado, 200)
        self.assertIn("pasan a durar 30 minutos", cuerpo)
        self.assertIn("Nueva rejilla", cuerpo)

    def test_ruta11_duracion_no_valida_responde_400(self):
        """PD-C18: una duración no numérica se rechaza con el motivo concreto."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/duracion",
            {
                "id_especialista": self.especialista.id_especialista,
                "duracion_minutos": "media hora",
            },
        )
        self.assertEqual(estado, 400)
        self.assertIn("La duración debe ser un número entero de minutos.", cuerpo)

    def test_ruta11_duracion_sin_hueco_responde_400(self):
        """CL-C11, PD-C21: una duración con la que no cabe ningún hueco no cambia nada."""
        estado, _, cuerpo = self.peticion_post(
            "/agenda/duracion",
            {"id_especialista": self.especialista.id_especialista, "duracion_minutos": "300"},
        )
        self.assertEqual(estado, 400)
        self.assertIn("no cabe ningún hueco", cuerpo)
        especialista = servicio.obtener_especialista(
            self.ruta_bd, self.especialista.id_especialista
        )
        self.assertEqual(especialista.duracion_minutos, 20)

    def test_ruta11_la_confirmacion_no_muestra_datos_del_paciente(self):
        """PD-C22, CE-C10: fecha, hora y motivo de cada cita cancelada, sin datos del paciente."""
        self.reservar(fecha=fecha_futura(), hora="09:20")
        estado, _, cuerpo = self.peticion_post(
            "/agenda/duracion",
            {"id_especialista": self.especialista.id_especialista, "duracion_minutos": "30"},
        )
        self.assertEqual(estado, 200)
        self.assertIn("Citas canceladas por el centro: 1", cuerpo)
        self.assertIn("09:20", cuerpo)
        self.assertIn(servicio.MOTIVO_DURACION, cuerpo)
        self.assertNotIn(self.codigo, cuerpo)

    def test_cac13_no_existe_pantalla_para_gestionar_centros_ni_especialistas(self):
        """CA-C13: no hay ninguna vía para crear o editar centros, especialidades ni
        especialistas (RN-C01)."""
        for ruta in (
            "/agenda/especialistas/nuevo",
            "/agenda/especialistas",
            "/agenda/centros",
            "/agenda/especialidades",
        ):
            with self.subTest(ruta=ruta):
                estado, _, _ = self.peticion_get(ruta)
                self.assertEqual(estado, 404)

    def test_pdc13_no_existe_ruta_para_desbloquear_una_franja(self):
        """PD-C13: solo se bloquea; no hay operación de desbloqueo."""
        for ruta in ("/agenda/desbloquear", "/agenda/franjas"):
            with self.subTest(ruta=ruta):
                estado, _, _ = self.peticion_get(ruta)
                self.assertEqual(estado, 404)

    def test_dc13_las_rutas_del_modulo_de_registro_siguen_funcionando(self):
        """D-C13: el manejador combinado conserva las 6 rutas del módulo de registro."""
        for ruta in ("/", "/pacientes/nuevo", f"/buscar?codigo={self.codigo}"):
            with self.subTest(ruta=ruta):
                estado, _, _ = self.peticion_get(ruta)
                self.assertEqual(estado, 200)

    def test_dc16_los_datos_mostrados_se_escapan(self):
        """D-C16: todo dato mostrado se escapa antes de insertarlo en el HTML."""
        codigo = self.registrar_otro_paciente(apellidos="<b>Olmo</b>")
        estado, _, cuerpo = self.peticion_get(f"/citas/mias?codigo={codigo}")
        self.assertEqual(estado, 200)
        self.assertNotIn("<b>Olmo</b>", cuerpo)

    def test_pdc02_el_flujo_de_agenda_no_pide_identificacion(self):
        """PD-C02: limitación declarada; `/agenda` está abierta sin credenciales."""
        estado, _, _ = self.peticion_get("/agenda")
        self.assertEqual(estado, 200)


if __name__ == "__main__":
    unittest.main()
