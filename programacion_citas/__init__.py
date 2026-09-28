"""Módulo de programación de citas del HIS.

Cubre las capacidades 4, 5 y 6 del principio II de la constitución: reservar una cita, cancelar o
reprogramar, y gestionar la agenda de un especialista.

Se apoya en la identidad que produce el módulo de registro (`registro_pacientes`): cada cita
referencia al paciente por su código de historia clínica (RN-C05). La dependencia va en un solo
sentido; este módulo no crea, modifica ni borra pacientes (D-C03, D-C04).
"""
