"""Punto de entrada: arranca la aplicación con un único comando (principio V, PD-11).

Sirve los dos módulos en un único servidor y un único puerto: el manejador de citas hereda del de
registro, de modo que las rutas de los dos conviven sin modificar el módulo de registro (D-C13).

Uso en local:       python app.py
Uso en contenedor:  docker compose up

La configuración se toma de variables de entorno, todas con valor por defecto, de modo que
ejecutar `python app.py` sin definir nada mantiene el comportamiento anterior (principio V).

- RUTA_BD: ruta del fichero SQLite. Por defecto, `datos/pacientes.db` junto a este archivo.
- PUERTO:  puerto de escucha. Por defecto, 8000.
- HOST:    interfaz de escucha. Por defecto, 127.0.0.1 (solo la máquina local). En contenedor
           debe ser 0.0.0.0 para que el puerto publicado sea accesible desde el anfitrion.
"""

import os
from pathlib import Path

from programacion_citas.servicio import inicializar_base_datos
from programacion_citas.web import crear_servidor

RUTA_BD_POR_DEFECTO = Path(__file__).resolve().parent / "datos" / "pacientes.db"
HOST_POR_DEFECTO = "127.0.0.1"
PUERTO_POR_DEFECTO = 8000


def leer_configuracion():
    """Devuelve (ruta_bd, host, puerto) a partir del entorno, con valores por defecto."""
    ruta_bd = os.environ.get("RUTA_BD") or str(RUTA_BD_POR_DEFECTO)
    host = os.environ.get("HOST") or HOST_POR_DEFECTO
    puerto_bruto = os.environ.get("PUERTO") or str(PUERTO_POR_DEFECTO)
    try:
        puerto = int(puerto_bruto)
    except ValueError:
        raise SystemExit(f"PUERTO debe ser un numero entero; se recibio: {puerto_bruto!r}")
    if not 1 <= puerto <= 65535:
        raise SystemExit(f"PUERTO debe estar entre 1 y 65535; se recibio: {puerto}")
    return ruta_bd, host, puerto


def principal():
    """Prepara la base de datos persistente y arranca el servidor web."""
    ruta_bd, host, puerto = leer_configuracion()
    inicializar_base_datos(ruta_bd)
    servidor = crear_servidor(ruta_bd, host=host, puerto=puerto)
    print(f"Base de datos en {ruta_bd}", flush=True)
    print(f"Servidor disponible en http://{host}:{puerto} (Ctrl+C para detener)", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
        print("Servidor detenido.", flush=True)


if __name__ == "__main__":
    principal()
