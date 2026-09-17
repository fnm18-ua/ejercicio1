"""Interfaz web local del módulo (contracts/interfaz-web.md; D-03, D-10).

Páginas HTML en español generadas en el servidor, sin JavaScript. Todo dato mostrado se escapa.
Solo existen las 6 rutas del contrato; cualquier otra responde 404.
"""

import html
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, quote, unquote, urlsplit

from registro_pacientes import base_datos, servicio
from registro_pacientes.servicio import (
    CodigosAgotados,
    ErrorValidacion,
    PacienteDuplicado,
    PacienteNoEncontrado,
)

escapar = html.escape

RUTA_EDITAR = re.compile(r"^/pacientes/([^/]+)/editar$")

NOMBRES_TIPO_DOCUMENTO = {"DNI": "DNI", "NIE": "NIE", "PASAPORTE": "Pasaporte"}
NOMBRES_TIPO_COBERTURA = {"MUTUA": "Mutua", "SIN_COBERTURA": "Sin cobertura"}
AVISOS = {"registrado": "Paciente registrado.", "modificado": "Datos guardados."}

# Hoja de estilos mínima embebida en cada página (D-03): solo presentación, sin archivos
# externos, sin JavaScript y sin dependencias.
ESTILOS = """\
*, *::before, *::after { box-sizing: border-box; }
body {
  margin: 0;
  background: #f4f5f7;
  color: #1f2933;
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  font-size: 1rem;
  line-height: 1.5;
}
header { background: #2f4858; padding: 0.75rem 1rem; }
header a { color: #ffffff; font-weight: 600; text-decoration: none; }
header a:hover, header a:focus { text-decoration: underline; }
main {
  max-width: 42rem;
  margin: 1.5rem auto;
  padding: 1.5rem;
  background: #ffffff;
  border: 1px solid #d9dee3;
  border-radius: 6px;
}
h1 { margin: 0 0 1rem; font-size: 1.5rem; line-height: 1.25; }
h2 { margin: 1.75rem 0 0.25rem; font-size: 1.1rem; }
a { color: #1f5f8b; }
label { display: block; margin: 1rem 0 0.3rem; font-weight: 600; color: #323f4b; }
input[type="text"], input[type="date"], select {
  display: block;
  width: 100%;
  padding: 0.5rem 0.65rem;
  font: inherit;
  color: inherit;
  background: #ffffff;
  border: 1px solid #b8c1ca;
  border-radius: 4px;
}
input:focus, select:focus, button:focus, a:focus {
  outline: 2px solid #1f5f8b;
  outline-offset: 2px;
}
fieldset {
  margin: 1.25rem 0 0;
  padding: 0.25rem 1rem 1rem;
  border: 1px solid #d9dee3;
  border-radius: 4px;
}
legend { padding: 0 0.35rem; font-weight: 600; color: #323f4b; }
label:has(> input[type="radio"]) {
  display: inline-block;
  margin: 0.75rem 1.5rem 0 0;
  font-weight: normal;
}
input[type="radio"] { margin: 0 0.35rem 0 0; accent-color: #2f5d8a; }
button {
  margin-top: 0.75rem;
  padding: 0.55rem 1.5rem;
  font: inherit;
  font-weight: 600;
  color: #ffffff;
  background: #2f5d8a;
  border: 1px solid #2f5d8a;
  border-radius: 4px;
  cursor: pointer;
}
button:hover { background: #244a6f; border-color: #244a6f; }
.errores {
  margin: 0 0 1rem;
  padding: 0.75rem 1rem 0.75rem 2rem;
  color: #8a1c1c;
  background: #fdf1f1;
  border: 1px solid #f0c4c4;
  border-radius: 4px;
}
.aviso {
  margin: 0 0 1rem;
  padding: 0.6rem 1rem;
  color: #1d5e3a;
  background: #eef7f1;
  border: 1px solid #bfe0cb;
  border-radius: 4px;
}
.ficha {
  display: grid;
  grid-template-columns: max-content 1fr;
  gap: 0.45rem 1.25rem;
  margin: 0 0 1.25rem;
}
.ficha dt { font-weight: 600; color: #52606d; }
.ficha dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 36rem) {
  main { margin: 0; border-width: 0 0 1px; border-radius: 0; padding: 1rem; }
  .ficha { grid-template-columns: 1fr; gap: 0; }
  .ficha dd { margin-bottom: 0.6rem; }
}
"""


def pagina(titulo, cuerpo):
    """Genera una página HTML completa en español con el título, el cuerpo y los estilos."""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="es">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{escapar(titulo)} · Registro de pacientes</title>\n"
        f"<style>\n{ESTILOS}</style>\n"
        "</head>\n"
        "<body>\n"
        '<header><a href="/">Registro e identificación de pacientes</a></header>\n'
        "<main>\n"
        f"<h1>{escapar(titulo)}</h1>\n"
        f"{cuerpo}\n"
        "</main>\n"
        "</body>\n"
        "</html>\n"
    )


def pagina_no_encontrada():
    """Página para cualquier ruta que no figura en el contrato."""
    return pagina("Página no encontrada", "<p>La página solicitada no existe.</p>")


def html_errores(errores):
    """Lista de errores en español con el motivo concreto de cada uno (PD-07)."""
    if not errores:
        return ""
    elementos = "".join(f"<li>{escapar(error)}</li>" for error in errores)
    return f'<ul class="errores">{elementos}</ul>\n'


def html_documento(tipo_documento, numero_documento):
    """Documento de identidad legible: tipo y número."""
    tipo = NOMBRES_TIPO_DOCUMENTO.get(tipo_documento, tipo_documento)
    return f"{tipo} {numero_documento}"


def html_ficha(paciente):
    """Ficha completa del paciente para verificar su identidad (RF-05, PD-05)."""
    if paciente.tipo_cobertura == "MUTUA":
        cobertura = f"Mutua: {paciente.mutua} · Póliza: {paciente.numero_poliza}"
    else:
        cobertura = "Sin cobertura"
    filas = (
        ("Código de historia clínica", paciente.codigo_historia),
        ("Nombre", paciente.nombre),
        ("Apellidos", paciente.apellidos),
        ("Fecha de nacimiento", paciente.fecha_nacimiento),
        (
            "Documento de identidad",
            html_documento(paciente.tipo_documento, paciente.numero_documento),
        ),
        ("Cobertura sanitaria", cobertura),
        ("Teléfono", paciente.telefono or "—"),
        ("Email", paciente.email or "—"),
        ("Domicilio", paciente.domicilio or "—"),
        ("Fecha de registro", paciente.fecha_registro),
    )
    contenido = "".join(
        f"<dt>{escapar(etiqueta)}</dt><dd>{escapar(valor)}</dd>" for etiqueta, valor in filas
    )
    enlace_edicion = f"/pacientes/{quote(paciente.codigo_historia)}/editar"
    return (
        f'<dl class="ficha">{contenido}</dl>\n'
        f'<p><a href="{escapar(enlace_edicion)}">Modificar datos</a></p>\n'
    )


def html_campo_texto(nombre, etiqueta, valores, obligatorio=False, tipo="text"):
    """Campo de texto con su etiqueta y el valor introducido, escapado."""
    marca = " (obligatorio)" if obligatorio else ""
    valor = escapar(valores.get(nombre) or "")
    return (
        f'<label for="{nombre}">{escapar(etiqueta)}{marca}</label>\n'
        f'<input type="{tipo}" id="{nombre}" name="{nombre}" value="{valor}">\n'
    )


def html_selector_tipo_documento(valores):
    """Desplegable del tipo de documento: DNI, NIE o Pasaporte (RN-01)."""
    seleccionado = (valores.get("tipo_documento") or "").upper()
    opciones = "".join(
        f'<option value="{tipo}"{" selected" if tipo == seleccionado else ""}>'
        f"{escapar(nombre)}</option>"
        for tipo, nombre in NOMBRES_TIPO_DOCUMENTO.items()
    )
    return (
        '<label for="tipo_documento">Tipo de documento (obligatorio)</label>\n'
        f'<select id="tipo_documento" name="tipo_documento">{opciones}</select>\n'
    )


def formulario_paciente(accion, valores, errores, titulo, paciente=None):
    """Página con el formulario de datos del paciente para registrar o modificar (RF-01, RF-06).

    Si se indica el paciente, su código de historia clínica y su fecha de registro se muestran
    solo como texto: no son editables (RN-06, CA-12).
    """
    solo_lectura = ""
    if paciente is not None:
        solo_lectura = (
            "<p>Código de historia clínica: "
            f"<strong>{escapar(paciente.codigo_historia)}</strong></p>\n"
            f"<p>Fecha de registro: {escapar(paciente.fecha_registro)}</p>\n"
        )
    cobertura = valores.get("tipo_cobertura")
    opciones_cobertura = "".join(
        f'<label><input type="radio" name="tipo_cobertura" value="{tipo}"'
        f'{" checked" if tipo == cobertura else ""}> {escapar(nombre)}</label>\n'
        for tipo, nombre in NOMBRES_TIPO_COBERTURA.items()
    )
    cuerpo = (
        solo_lectura
        + html_errores(errores)
        + f'<form method="post" action="{escapar(accion)}">\n'
        + html_campo_texto("nombre", "Nombre", valores, obligatorio=True)
        + html_campo_texto("apellidos", "Apellidos", valores, obligatorio=True)
        + html_campo_texto(
            "fecha_nacimiento", "Fecha de nacimiento", valores, obligatorio=True, tipo="date"
        )
        + html_selector_tipo_documento(valores)
        + html_campo_texto("numero_documento", "Número de documento", valores, obligatorio=True)
        + "<fieldset>\n<legend>Cobertura sanitaria (obligatorio)</legend>\n"
        + opciones_cobertura
        + html_campo_texto("mutua", "Mutua (obligatorio con mutua)", valores)
        + html_campo_texto(
            "numero_poliza", "Número de póliza (obligatorio con mutua)", valores
        )
        + "</fieldset>\n"
        + html_campo_texto("telefono", "Teléfono", valores)
        + html_campo_texto("email", "Email", valores)
        + html_campo_texto("domicilio", "Domicilio", valores)
        + "<p><button type=\"submit\">Guardar</button></p>\n"
        + "</form>\n"
    )
    return pagina(titulo, cuerpo)


def formulario_registro(valores=None, errores=None):
    """Formulario de registro de un paciente nuevo (RF-01; ruta 3)."""
    return formulario_paciente("/pacientes", valores or {}, errores, "Registrar paciente")


def formulario_edicion(paciente, valores=None, errores=None):
    """Formulario de modificación relleno con los datos actuales (RF-06, CA-12; ruta 5)."""
    if valores is None:
        valores = {campo: getattr(paciente, campo) for campo in base_datos.CAMPOS_EDITABLES}
    accion = f"/pacientes/{quote(paciente.codigo_historia)}/editar"
    return formulario_paciente(accion, valores, errores, "Modificar datos del paciente", paciente)


def pagina_paciente_no_encontrado(codigo):
    """Página para un código de historia clínica que no existe (RF-06)."""
    mensaje = f"No existe ningún paciente con el código {codigo}."
    return pagina("Paciente no encontrado", f"<p>{escapar(mensaje)}</p>")


class ManejadorPacientes(BaseHTTPRequestHandler):
    """Atiende las rutas de contracts/interfaz-web.md."""

    def do_GET(self):
        """Enruta las peticiones GET (rutas 1, 2, 3 y 5)."""
        partes = urlsplit(self.path)
        ruta = partes.path
        parametros = self._primeros(parse_qs(partes.query, keep_blank_values=True))
        coincidencia = RUTA_EDITAR.match(ruta)
        if ruta == "/":
            self.mostrar_inicio()
        elif ruta == "/buscar":
            self.buscar(parametros)
        elif ruta == "/pacientes/nuevo":
            self.mostrar_formulario_registro()
        elif coincidencia:
            self.mostrar_formulario_edicion(unquote(coincidencia.group(1)))
        else:
            self.responder_html(404, pagina_no_encontrada())

    def do_POST(self):
        """Enruta las peticiones POST (rutas 4 y 6)."""
        ruta = urlsplit(self.path).path
        campos = self.leer_formulario()
        coincidencia = RUTA_EDITAR.match(ruta)
        if ruta == "/pacientes":
            self.registrar(campos)
        elif coincidencia:
            self.guardar_edicion(unquote(coincidencia.group(1)), campos)
        else:
            self.responder_html(404, pagina_no_encontrada())

    # Rutas del contrato.

    def mostrar_inicio(self):
        """Ruta 1 · GET /: búsqueda por código o por documento y enlace al registro.

        RF-03, RF-04, RF-01. No hay búsqueda por nombre (CA-13).
        """
        cuerpo = (
            "<h2>Buscar por código de historia clínica</h2>\n"
            '<form method="get" action="/buscar">\n'
            '<label for="codigo">Código de historia clínica</label>\n'
            '<input type="text" id="codigo" name="codigo">\n'
            '<p><button type="submit">Buscar</button></p>\n'
            "</form>\n"
            "<h2>Buscar por documento de identidad</h2>\n"
            '<form method="get" action="/buscar">\n'
            + html_selector_tipo_documento({})
            + '<label for="numero_documento">Número de documento</label>\n'
            '<input type="text" id="numero_documento" name="numero_documento">\n'
            '<p><button type="submit">Buscar</button></p>\n'
            "</form>\n"
            '<p><a href="/pacientes/nuevo">Registrar paciente</a></p>\n'
        )
        self.responder_html(200, pagina("Registro e identificación de pacientes", cuerpo))

    def buscar(self, parametros):
        """Ruta 2 · GET /buscar: muestra la ficha del paciente buscado.

        RF-03, RF-04, RF-05, PD-08; sin coincidencias informa sin error (CL-01).
        """
        codigo = (parametros.get("codigo") or "").strip()
        tipo_documento = (parametros.get("tipo_documento") or "").strip().upper()
        numero_documento = (parametros.get("numero_documento") or "").strip()
        aviso = AVISOS.get(parametros.get("aviso"))
        if codigo:
            paciente = servicio.buscar_por_codigo(self.ruta_bd, codigo)
            mensaje = f"No existe ningún paciente con el código {codigo}."
        elif numero_documento:
            paciente = servicio.buscar_por_documento(
                self.ruta_bd, tipo_documento, numero_documento
            )
            documento = html_documento(tipo_documento, numero_documento)
            mensaje = f"No existe ningún paciente con el documento {documento}."
        else:
            paciente = None
            mensaje = "Indica un código de historia clínica o un documento de identidad."
        if paciente is None:
            self.responder_html(200, pagina("Buscar paciente", f"<p>{escapar(mensaje)}</p>"))
            return
        self.mostrar_ficha(paciente, aviso)

    def mostrar_ficha(self, paciente, aviso=None, estado=200, mensaje=None):
        """Página con la ficha completa del paciente (RF-05, PD-05)."""
        cuerpo = ""
        if aviso:
            cuerpo += f'<p class="aviso">{escapar(aviso)}</p>\n'
        if mensaje:
            cuerpo += html_errores([mensaje])
        cuerpo += html_ficha(paciente)
        self.responder_html(estado, pagina("Ficha del paciente", cuerpo))

    def mostrar_formulario_registro(self):
        """Ruta 3 · GET /pacientes/nuevo: formulario de registro vacío (RF-01)."""
        self.responder_html(200, formulario_registro())

    def mostrar_formulario_edicion(self, codigo):
        """Ruta 5 · GET /pacientes/<codigo>/editar: formulario de modificación (RF-06, CA-12)."""
        paciente = servicio.buscar_por_codigo(self.ruta_bd, codigo)
        if paciente is None:
            self.responder_html(404, pagina_paciente_no_encontrado(codigo))
            return
        self.responder_html(200, formulario_edicion(paciente))

    def registrar(self, campos):
        """Ruta 4 · POST /pacientes: registra al paciente (RF-01, RF-02, CA-03, CA-08, CL-04)."""
        try:
            paciente = servicio.registrar_paciente(self.ruta_bd, campos)
        except ErrorValidacion as error:
            self.responder_html(400, formulario_registro(campos, error.errores))
            return
        except PacienteDuplicado as error:
            existente = error.existente
            documento = html_documento(existente.tipo_documento, existente.numero_documento)
            mensaje = (
                f"Ya existe un paciente con el documento {documento}: "
                f"{existente.codigo_historia}."
            )
            self.mostrar_ficha(existente, estado=409, mensaje=mensaje)
            return
        except CodigosAgotados as error:
            self.responder_html(409, formulario_registro(campos, [str(error)]))
            return
        codigo = quote(paciente.codigo_historia)
        self.redirigir(f"/buscar?codigo={codigo}&aviso=registrado")

    def guardar_edicion(self, codigo, campos):
        """Ruta 6 · POST /pacientes/<codigo>/editar: guarda la modificación (RF-06, PD-01, CA-10).

        Un campo codigo_historia en el formulario se ignora (CA-12).
        """
        try:
            paciente = servicio.modificar_paciente(self.ruta_bd, codigo, campos)
        except PacienteNoEncontrado:
            self.responder_html(404, pagina_paciente_no_encontrado(codigo))
            return
        except ErrorValidacion as error:
            actual = servicio.buscar_por_codigo(self.ruta_bd, codigo)
            self.responder_html(400, formulario_edicion(actual, campos, error.errores))
            return
        except PacienteDuplicado as error:
            existente = error.existente
            documento = html_documento(existente.tipo_documento, existente.numero_documento)
            mensaje = f"El documento {documento} ya pertenece a otro paciente."
            actual = servicio.buscar_por_codigo(self.ruta_bd, codigo)
            self.responder_html(409, formulario_edicion(actual, campos, [mensaje]))
            return
        codigo_url = quote(paciente.codigo_historia)
        self.redirigir(f"/buscar?codigo={codigo_url}&aviso=modificado")

    # Utilidades.

    @property
    def ruta_bd(self):
        """Ruta de la base de datos configurada en el servidor."""
        return self.server.ruta_bd

    @staticmethod
    def _primeros(valores):
        """Toma el primer valor de cada parámetro de un formulario o consulta."""
        return {clave: lista[0] for clave, lista in valores.items()}

    def leer_formulario(self):
        """Lee el cuerpo application/x-www-form-urlencoded de un POST en UTF-8."""
        longitud = int(self.headers.get("Content-Length") or 0)
        cuerpo = self.rfile.read(longitud).decode("utf-8")
        return self._primeros(parse_qs(cuerpo, keep_blank_values=True))

    def responder_html(self, estado, contenido):
        """Envía una página HTML con el estado indicado."""
        datos = contenido.encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def redirigir(self, url):
        """Redirige con 303 a la URL indicada."""
        self.send_response(303)
        self.send_header("Location", url)
        self.send_header("Content-Length", "0")
        self.end_headers()


def crear_servidor(ruta_bd, host="127.0.0.1", puerto=8000):
    """Crea el servidor web local sobre la base de datos indicada (D-03, D-10)."""
    servidor = ThreadingHTTPServer((host, puerto), ManejadorPacientes)
    servidor.ruta_bd = ruta_bd
    return servidor
