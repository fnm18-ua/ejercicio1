"""Aritmética temporal de la agenda (RN-C03, RN-C04, RN-C07, RN-C12).

Funciones puras, sin base de datos ni HTTP, para poder probar por separado las afirmaciones
numéricas exactas del enunciado (D-C15): CA-C01, CA-C12 y CL-C05.

Todos los intervalos son semiabiertos, `[inicio, inicio + duracion)`, de modo que dos tramos que
se tocan en el extremo no se solapan (PD-C06, PD-C12).
"""

import datetime


def a_minutos(hora):
    """Convierte una hora `HH:MM` en minutos desde medianoche."""
    return int(hora[:2]) * 60 + int(hora[3:5])


def a_hora(minutos):
    """Convierte minutos desde medianoche en una hora `HH:MM` de dos dígitos."""
    return f"{minutos // 60:02d}:{minutos % 60:02d}"


def dia_de_la_semana(fecha):
    """Devuelve el número ISO del día (1 = lunes … 7 = domingo) de una fecha `YYYY-MM-DD`."""
    return datetime.date.fromisoformat(fecha).isoweekday()


def dias_de_consulta(dias_semana):
    """Convierte el texto `1,2,3,4,5` en un conjunto de números ISO (D-C11)."""
    return {int(dia) for dia in dias_semana.split(",") if dia.strip()}


def generar_rejilla(dias_semana, hora_inicio, hora_fin, duracion_minutos, fecha):
    """Horas de inicio de los huecos de esa fecha, en orden (RN-C03, PD-C03).

    Devuelve lista vacía si el especialista no pasa consulta ese día (CL-C06). El último hueco es
    el último que cabe entero: el tiempo sobrante no forma un hueco parcial (CL-C05).
    """
    if dia_de_la_semana(fecha) not in dias_de_consulta(dias_semana):
        return []
    fin = a_minutos(hora_fin)
    rejilla = []
    momento = a_minutos(hora_inicio)
    while momento + duracion_minutos <= fin:
        rejilla.append(a_hora(momento))
        momento += duracion_minutos
    return rejilla


def se_solapan(inicio_a, duracion_a, inicio_b, duracion_b):
    """Si dos citas se solapan en el tiempo (RN-C07, PD-C06).

    Las horas se reciben como `HH:MM`. Dos citas consecutivas que se tocan en el extremo (una
    acaba a las 9:20 y la otra empieza a las 9:20) NO se solapan.
    """
    minuto_a = a_minutos(inicio_a)
    minuto_b = a_minutos(inicio_b)
    return minuto_a < minuto_b + duracion_b and minuto_b < minuto_a + duracion_a


def hueco_en_franja(hueco_inicio, duracion, franja_inicio, franja_fin):
    """Si un hueco cae dentro del tramo horario de una franja bloqueada (PD-C12).

    Mismo criterio de extremos que `se_solapan`: un hueco que acaba justo a la hora de fin de la
    franja queda bloqueado, y uno que empieza justo a esa hora no.
    """
    minuto_hueco = a_minutos(hueco_inicio)
    return (
        minuto_hueco < a_minutos(franja_fin)
        and a_minutos(franja_inicio) < minuto_hueco + duracion
    )


def encaja_en_rejilla(hora_cita, rejilla, hora_fin, duracion):
    """Si una cita encaja en la rejilla indicada (RN-C12, PD-C10).

    Encaja cuando su hora de inicio coincide con el inicio de un hueco de la rejilla y cabe entera
    en el horario del especialista.
    """
    return hora_cita in rejilla and a_minutos(hora_cita) + duracion <= a_minutos(hora_fin)
