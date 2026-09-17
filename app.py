"""Punto de entrada: arranca el módulo en local con un único comando (principio V, PD-11).

Uso: python app.py
"""

from pathlib import Path

from registro_pacientes.servicio import inicializar_base_datos
from registro_pacientes.web import crear_servidor


def principal():
    """Prepara la base de datos persistente y arranca el servidor en http://127.0.0.1:8000."""
    ruta_bd = Path(__file__).resolve().parent / "datos" / "pacientes.db"
    inicializar_base_datos(str(ruta_bd))
    servidor = crear_servidor(str(ruta_bd))
    print("Servidor disponible en http://127.0.0.1:8000 (Ctrl+C para detener)")
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        print("Servidor detenido.")


if __name__ == "__main__":
    principal()
