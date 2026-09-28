# Imagen del modulo de Registro e Identificacion de Pacientes (principio V: ejecucion en
# contenedores, arranque sin pasos manuales).
#
# La aplicacion usa solo la libreria estandar de Python y SQLite embebido: no se instala
# ningun paquete ni se requiere ningun servicio adicional.

# ---------------------------------------------------------------------------
# Etapa 1: constructor. Compila el codigo a bytecode para detectar aqui cualquier error de
# sintaxis y para que la imagen final no tenga que compilar en el primer arranque.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS constructor

WORKDIR /construccion

COPY app.py ./
COPY registro_pacientes/ ./registro_pacientes/
COPY programacion_citas/ ./programacion_citas/

RUN python -m compileall -q app.py registro_pacientes programacion_citas

# ---------------------------------------------------------------------------
# Etapa 2: imagen final. Solo el codigo ya verificado, sin herramientas de construccion.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS final

# PYTHONUNBUFFERED: los mensajes del servidor salen en `docker compose up` sin retardo.
# PYTHONDONTWRITEBYTECODE: no se escriben .pyc nuevos en el contenedor.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Valores por defecto de la configuracion (principio V: configuracion por variables de
# entorno). HOST es 0.0.0.0 porque, dentro del contenedor, escuchar solo en 127.0.0.1 haria
# inaccesible el puerto publicado.
ENV HOST=0.0.0.0 \
    PUERTO=8000 \
    RUTA_BD=/datos/pacientes.db

# Usuario sin privilegios.
RUN useradd --create-home --shell /usr/sbin/nologin aplicacion

WORKDIR /aplicacion

COPY --from=constructor --chown=aplicacion:aplicacion /construccion/ /aplicacion/

# El directorio del volumen se crea con la propiedad del usuario de la aplicacion: al montar
# un volumen nombrado vacio, Docker hereda esta propiedad y el contenedor puede escribir.
RUN mkdir -p /datos && chown aplicacion:aplicacion /datos

USER aplicacion

EXPOSE 8000

# Comprobacion de salud con la libreria estandar (la imagen slim no trae curl).
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen(f\"http://127.0.0.1:{os.environ['PUERTO']}/\", timeout=4)"

CMD ["python", "app.py"]
