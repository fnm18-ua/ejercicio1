"""Pruebas unitarias de la aritmética temporal (D-C15).

No tocan base de datos ni HTTP: verifican directamente las afirmaciones numéricas exactas del
enunciado (CA-C01, CA-C12, CL-C05, CL-C06) y los criterios de extremos (PD-C06, PD-C10, PD-C12).
"""

import unittest

from programacion_citas import agenda

LABORABLES = "1,2,3,4,5"
JUEVES = "2026-10-08"
SABADO = "2026-10-10"


class PruebasRejilla(unittest.TestCase):
    """Generación de la rejilla de huecos (RN-C03, PD-C03)."""

    def test_cac01_rejilla_de_20_minutos_tiene_12_huecos(self):
        """CA-C01: 9:00-13:00 con 20 minutos ofrece 12 huecos, de 9:00 a 12:40."""
        rejilla = agenda.generar_rejilla(LABORABLES, "09:00", "13:00", 20, JUEVES)
        self.assertEqual(len(rejilla), 12)
        self.assertEqual(rejilla[0], "09:00")
        self.assertEqual(rejilla[-1], "12:40")

    def test_cac12_rejilla_de_30_minutos_tiene_8_huecos(self):
        """CA-C12: la rejilla nueva de 30 minutos contiene 9:00 y no contiene 9:20."""
        rejilla = agenda.generar_rejilla(LABORABLES, "09:00", "13:00", 30, JUEVES)
        self.assertEqual(len(rejilla), 8)
        self.assertIn("09:00", rejilla)
        self.assertNotIn("09:20", rejilla)
        self.assertEqual(rejilla[-1], "12:30")

    def test_clc05_rejilla_de_50_minutos_tiene_4_huecos_sin_tramo_parcial(self):
        """CL-C05: 9:00-13:00 con 50 minutos genera 4 huecos; el resto no forma hueco parcial."""
        rejilla = agenda.generar_rejilla(LABORABLES, "09:00", "13:00", 50, JUEVES)
        self.assertEqual(rejilla, ["09:00", "09:50", "10:40", "11:30"])

    def test_clc06_dia_sin_consulta_no_tiene_huecos(self):
        """CL-C06: en una fecha en la que no pasa consulta no se ofrece ningún hueco."""
        self.assertEqual(agenda.generar_rejilla(LABORABLES, "09:00", "13:00", 20, SABADO), [])

    def test_horas_siempre_con_dos_digitos(self):
        """Las horas se formatean `HH:MM` para que el orden lexicográfico sea el cronológico."""
        rejilla = agenda.generar_rejilla(LABORABLES, "08:00", "10:00", 60, JUEVES)
        self.assertEqual(rejilla, ["08:00", "09:00"])


class PruebasSolapamiento(unittest.TestCase):
    """Criterio de extremos semiabierto (RN-C07, PD-C06)."""

    def test_pdc06_citas_consecutivas_no_se_solapan(self):
        """PD-C06: una cita que acaba a las 9:20 y otra que empieza a las 9:20 no se solapan."""
        self.assertFalse(agenda.se_solapan("09:00", 20, "09:20", 20))

    def test_pdc06_citas_que_se_pisan_si_se_solapan(self):
        """PD-C06: con 30 minutos, la de las 9:00 alcanza a la de las 9:20."""
        self.assertTrue(agenda.se_solapan("09:00", 30, "09:20", 20))

    def test_pdc06_la_misma_hora_se_solapa(self):
        """CA-C05: dos citas a la misma hora se solapan aunque sean de especialistas distintos."""
        self.assertTrue(agenda.se_solapan("10:00", 20, "10:00", 30))


class PruebasFranja(unittest.TestCase):
    """Bloqueo de huecos por una franja (RN-C04, PD-C12)."""

    def test_pdc12_hueco_que_acaba_al_fin_de_la_franja_queda_bloqueado(self):
        """CA-C10: con franja 9:00-11:00 y 20 minutos se bloquean 9:00, 10:00 y 10:40."""
        for hora in ("09:00", "10:00", "10:40"):
            with self.subTest(hora=hora):
                self.assertTrue(agenda.hueco_en_franja(hora, 20, "09:00", "11:00"))

    def test_pdc12_hueco_que_empieza_al_fin_de_la_franja_queda_libre(self):
        """CA-C10: las citas de las 11:00 en adelante siguen reservadas."""
        for hora in ("11:00", "11:20"):
            with self.subTest(hora=hora):
                self.assertFalse(agenda.hueco_en_franja(hora, 20, "09:00", "11:00"))


class PruebasEncaje(unittest.TestCase):
    """Encaje en la rejilla tras cambiar la duración (RN-C12, PD-C10)."""

    def test_pdc10_encaje_en_rejilla_de_30_minutos(self):
        """CA-C12: la cita de las 9:00 encaja en la rejilla nueva y la de las 9:20 no."""
        rejilla = agenda.generar_rejilla(LABORABLES, "09:00", "13:00", 30, JUEVES)
        self.assertTrue(agenda.encaja_en_rejilla("09:00", rejilla, "13:00", 30))
        self.assertFalse(agenda.encaja_en_rejilla("09:20", rejilla, "13:00", 30))

    def test_pdc10_una_cita_que_no_cabe_entera_no_encaja(self):
        """PD-C10: «cabe entera en el horario» excluye la que rebasaría la hora de fin."""
        self.assertFalse(agenda.encaja_en_rejilla("12:40", ["12:40"], "13:00", 30))


class PruebasDiasDeConsulta(unittest.TestCase):
    """Interpretación del texto de días de la semana (RN-C02, D-C11)."""

    def test_dc11_dias_semana_se_interpreta_como_numeros_iso(self):
        """D-C11: `1,2,3,4,5` son lunes a viernes en convenio ISO."""
        self.assertEqual(agenda.dias_de_consulta(LABORABLES), {1, 2, 3, 4, 5})
        self.assertEqual(agenda.dia_de_la_semana(JUEVES), 4)
        self.assertEqual(agenda.dia_de_la_semana(SABADO), 6)


if __name__ == "__main__":
    unittest.main()
