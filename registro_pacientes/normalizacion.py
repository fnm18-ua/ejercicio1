"""Normalización de textos para guardar y comparar (RN-08, PD-06, PD-09, PD-10, PD-12, PD-13).

Decisión D-07 de research.md.
"""

import unicodedata


def recortar(valor):
    """Quita los espacios del principio y del final; un valor vacío se trata como ausente (PD-13).

    Devuelve el texto recortado o None si el valor es None o queda vacío.
    """
    if valor is None:
        return None
    recortado = valor.strip()
    return recortado or None


def normalizar_texto(valor):
    """Normaliza un texto para guardarlo o compararlo (RN-08, PD-10, PD-12).

    1. Quita los espacios del principio y del final y reduce a uno los interiores repetidos.
    2. Elimina las tildes.
    3. Pasa a mayúsculas.
    """
    if valor is None:
        return ""
    sin_espacios_sobrantes = " ".join(valor.split())
    descompuesto = unicodedata.normalize("NFD", sin_espacios_sobrantes)
    sin_tildes = "".join(
        caracter for caracter in descompuesto if unicodedata.category(caracter) != "Mn"
    )
    return sin_tildes.upper()
