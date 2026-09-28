"""Interfaz web del módulo de citas (contracts/interfaz-web-citas.md; D-C13, D-C16).

`ManejadorCitas` HEREDA del manejador del módulo de registro y atiende primero las 11 rutas de
citas; cualquier otra se delega a la clase base, de modo que las 6 rutas del módulo de registro
siguen funcionando sin tocar ese módulo (D-C13). Así hay un solo servidor y un solo puerto, como
exige el principio V.

Dos flujos separados por prefijo y sin inicio de sesión (PD-C02, D-C14): `/citas` para el paciente
y `/agenda` para el personal administrativo.

Páginas HTML en español, sin JavaScript. Todo dato mostrado se escapa (D-C16).
"""

import datetime
import re
from http.server import ThreadingHTTPServer
from urllib.parse import parse_qs, quote, urlsplit

from programacion_citas import servicio
from programacion_citas.servicio import (
    CitaNoEncontrada,
    CitaSolapada,
    CitaYaCancelada,
    ErrorValidacion,
    FueraDePlazo,
    HuecoNoDisponible,
    HuecoPasado,
    PacienteNoIdentificado,
)
from registro_pacientes.web import ManejadorPacientes, escapar, pagina

RUTA_CANCELAR = re.compile(r"^/citas/([0-9]+)/cancelar$")
RUTA_REPROGRAMAR = re.compile(r"^/citas/([0-9]+)/reprogramar$")

AVISOS = {
    "reservada": "Cita reservada.",
    "cancelada": "Cita cancelada.",
    "reprogramada": "Cita reprogramada.",
}

NOMBRES_TIPO_DOCUMENTO = {"DNI": "DNI", "NIE": "NIE", "PASAPORTE": "Pasaporte"}


def _valor(parametros, nombre):
    """Valor del parámetro, sin espacios extremos, o cadena vacía.

    Los parámetros llegan ya normalizados a un valor por clave, con el mismo convenio que usa el
    módulo de registro (`_primeros`), tanto en GET como en POST.
    """
    return parametros.get(nombre, "").strip()


def _cabecera_flujos():
    """Enlaces entre las páginas del módulo de citas."""
    return (
        '<p><a href="/citas">Reservar cita</a> · '
        '<a href="/agenda">Agenda del especialista</a></p>\n'
    )


def pagina_error(titulo, mensaje):
    """Página de rechazo con el motivo concreto (PD-C18)."""
    return pagina(
        titulo,
        f"<p>{escapar(mensaje)}</p>\n" + _cabecera_flujos(),
    )


class ManejadorCitas(ManejadorPacientes):
    """Manejador HTTP del módulo de citas; delega en el de registro lo que no es suyo (D-C13)."""

    # Enrutado.

    def do_GET(self):
        """Enruta las peticiones GET de citas y delega el resto (rutas 1, 2, 3, 5, 7, 9)."""
        partes = urlsplit(self.path)
        ruta = partes.path
        parametros = self._primeros(parse_qs(partes.query, keep_blank_values=True))
        coincidencia = RUTA_REPROGRAMAR.match(ruta)
        if ruta == "/citas":
            self.mostrar_identificacion()
        elif ruta == "/citas/buscar":
            self.mostrar_busqueda(parametros)
        elif ruta == "/citas/huecos":
            self.mostrar_huecos(parametros)
        elif ruta == "/citas/mias":
            self.mostrar_citas(parametros)
        elif coincidencia:
            self.mostrar_reprogramacion(int(coincidencia.group(1)), parametros)
        elif ruta == "/agenda":
            self.mostrar_agenda(parametros)
        else:
            super().do_GET()

    def do_POST(self):
        """Enruta las peticiones POST de citas y delega el resto (rutas 4, 6, 8, 10, 11)."""
        ruta = urlsplit(self.path).path
        if ruta not in ("/citas", "/agenda/bloquear", "/agenda/duracion") and not (
            RUTA_CANCELAR.match(ruta) or RUTA_REPROGRAMAR.match(ruta)
        ):
            super().do_POST()
            return
        campos = self.leer_formulario()
        cancelar = RUTA_CANCELAR.match(ruta)
        reprogramar = RUTA_REPROGRAMAR.match(ruta)
        if ruta == "/citas":
            self.reservar(campos)
        elif cancelar:
            self.cancelar(int(cancelar.group(1)), campos)
        elif reprogramar:
            self.reprogramar(int(reprogramar.group(1)), campos)
        elif ruta == "/agenda/bloquear":
            self.bloquear(campos)
        elif ruta == "/agenda/duracion":
            self.ajustar_duracion(campos)

    # Utilidades comunes.

    def identificar(self, parametros):
        """Código de historia clínica del paciente, o None tras responder 400 (RF-C01, CL-C09)."""
        try:
            return servicio.identificar_paciente(
                self.server.ruta_bd,
                codigo=_valor(parametros, "codigo"),
                tipo_documento=_valor(parametros, "tipo_documento"),
                numero_documento=_valor(parametros, "numero_documento"),
            )
        except PacienteNoIdentificado as error:
            self.responder_html(
                400,
                pagina(
                    "Paciente no identificado",
                    f"<p>{escapar(str(error))}</p>\n"
                    '<p><a href="/citas">Volver a identificarse</a></p>\n',
                ),
            )
            return None

    # Ruta 1 · GET /citas

    def mostrar_identificacion(self):
        """Ruta 1: identificación por código de historia clínica o por documento (RF-C01)."""
        opciones = "\n".join(
            f'<option value="{clave}">{escapar(nombre)}</option>'
            for clave, nombre in NOMBRES_TIPO_DOCUMENTO.items()
        )
        cuerpo = (
            "<h2>Identificarse por código de historia clínica</h2>\n"
            '<form method="get" action="/citas/buscar">\n'
            '<label for="codigo">Código de historia clínica</label>\n'
            '<input type="text" id="codigo" name="codigo">\n'
            '<button type="submit">Continuar</button>\n'
            "</form>\n"
            "<h2>Identificarse por documento de identidad</h2>\n"
            '<form method="get" action="/citas/buscar">\n'
            '<label for="tipo_documento">Tipo de documento</label>\n'
            f'<select id="tipo_documento" name="tipo_documento">\n{opciones}\n</select>\n'
            '<label for="numero_documento">Número de documento</label>\n'
            '<input type="text" id="numero_documento" name="numero_documento">\n'
            '<button type="submit">Continuar</button>\n'
            "</form>\n"
        )
        self.responder_html(200, pagina("Reservar cita", cuerpo))

    # Ruta 2 · GET /citas/buscar

    def mostrar_busqueda(self, parametros):
        """Ruta 2: elegir especialidad y centro, y listar especialistas (RF-C02, CL-C02)."""
        codigo = self.identificar(parametros)
        if codigo is None:
            return
        especialidades, centros = servicio.listar_catalogo(self.server.ruta_bd)
        especialidad = _valor(parametros, "especialidad")
        centro = _valor(parametros, "centro")
        cuerpo = [f"<p>Paciente: {escapar(codigo)}</p>\n"]
        cuerpo.append(f'<p><a href="/citas/mias?codigo={quote(codigo)}">Ver mis citas</a></p>\n')
        cuerpo.append("<h2>Buscar especialista</h2>\n")
        cuerpo.append('<form method="get" action="/citas/buscar">\n')
        cuerpo.append(f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n')
        cuerpo.append('<label for="especialidad">Especialidad</label>\n')
        cuerpo.append('<select id="especialidad" name="especialidad">\n')
        for nombre in especialidades:
            marca = " selected" if nombre == especialidad else ""
            cuerpo.append(
                f'<option value="{escapar(nombre)}"{marca}>{escapar(nombre)}</option>\n'
            )
        cuerpo.append("</select>\n")
        cuerpo.append('<label for="centro">Centro</label>\n')
        cuerpo.append('<select id="centro" name="centro">\n')
        for nombre in centros:
            marca = " selected" if nombre == centro else ""
            cuerpo.append(
                f'<option value="{escapar(nombre)}"{marca}>{escapar(nombre)}</option>\n'
            )
        cuerpo.append("</select>\n")
        cuerpo.append('<button type="submit">Buscar</button>\n</form>\n')
        if especialidad and centro:
            especialistas = servicio.buscar_especialistas(
                self.server.ruta_bd, especialidad, centro
            )
            if not especialistas:
                cuerpo.append(
                    "<p>No hay especialistas de esa especialidad en ese centro.</p>\n"
                )
            else:
                cuerpo.append("<h2>Especialistas</h2>\n<ul>\n")
                for especialista in especialistas:
                    enlace = (
                        f"/citas/huecos?codigo={quote(codigo)}"
                        f"&id_especialista={especialista.id_especialista}"
                    )
                    cuerpo.append(
                        f"<li>{escapar(especialista.nombre)} · "
                        f"{escapar(especialista.especialidad)} · "
                        f"{escapar(especialista.centro)} · consultas de "
                        f"{especialista.duracion_minutos} minutos · "
                        f'<a href="{enlace}">Ver huecos</a></li>\n'
                    )
                cuerpo.append("</ul>\n")
        self.responder_html(200, pagina("Buscar especialista", "".join(cuerpo)))

    # Ruta 3 · GET /citas/huecos

    def mostrar_huecos(self, parametros):
        """Ruta 3: huecos libres de un especialista en una fecha (RF-C03, CL-C01, CL-C06)."""
        codigo = self.identificar(parametros)
        if codigo is None:
            return
        id_especialista = _valor(parametros, "id_especialista")
        fecha = _valor(parametros, "fecha")
        especialista = servicio.obtener_especialista(self.server.ruta_bd, id_especialista)
        if especialista is None:
            self.responder_html(
                400, pagina_error("Dato no válido", "El especialista indicado no existe.")
            )
            return
        cuerpo = [
            f"<p>Paciente: {escapar(codigo)}</p>\n",
            f"<p>{escapar(especialista.nombre)} · {escapar(especialista.especialidad)} · "
            f"{escapar(especialista.centro)}</p>\n",
            f"<p>Horario de {escapar(especialista.hora_inicio)} a "
            f"{escapar(especialista.hora_fin)}, consultas de "
            f"{especialista.duracion_minutos} minutos.</p>\n",
            '<form method="get" action="/citas/huecos">\n',
            f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n',
            f'<input type="hidden" name="id_especialista" value="{especialista.id_especialista}">\n',
            '<label for="fecha">Fecha</label>\n',
            f'<input type="date" id="fecha" name="fecha" value="{escapar(fecha)}">\n',
            '<button type="submit">Ver huecos</button>\n</form>\n',
        ]
        if fecha:
            try:
                huecos = servicio.consultar_huecos(
                    self.server.ruta_bd,
                    especialista.id_especialista,
                    fecha,
                    servicio.momento_actual(),
                )
            except ErrorValidacion as error:
                self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
                return
            if not huecos:
                cuerpo.append("<p>No hay huecos disponibles en esa fecha.</p>\n")
            else:
                cuerpo.append("<h2>Huecos libres</h2>\n")
                for hueco in huecos:
                    cuerpo.append(
                        '<form method="post" action="/citas">\n'
                        f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n'
                        '<input type="hidden" name="id_especialista" '
                        f'value="{especialista.id_especialista}">\n'
                        f'<input type="hidden" name="fecha" value="{escapar(fecha)}">\n'
                        '<input type="hidden" name="hora_inicio" '
                        f'value="{escapar(hueco.hora_inicio)}">\n'
                        f"<button type=\"submit\">Reservar {escapar(hueco.hora_inicio)}</button>\n"
                        "</form>\n"
                    )
        self.responder_html(200, pagina("Huecos del especialista", "".join(cuerpo)))

    # Ruta 4 · POST /citas

    def reservar(self, campos):
        """Ruta 4: reservar el hueco elegido (RF-C04, CA-C05, CL-C03)."""
        codigo = self.identificar(campos)
        if codigo is None:
            return
        try:
            servicio.reservar_cita(
                self.server.ruta_bd,
                codigo,
                _valor(campos, "id_especialista"),
                _valor(campos, "fecha"),
                _valor(campos, "hora_inicio"),
                servicio.momento_actual(),
            )
        except ErrorValidacion as error:
            self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
            return
        except (HuecoNoDisponible, HuecoPasado, CitaSolapada) as error:
            self.responder_html(409, pagina_error("No se puede reservar", str(error)))
            return
        self.redirigir(f"/citas/mias?codigo={quote(codigo)}&aviso=reservada")

    # Ruta 5 · GET /citas/mias

    def mostrar_citas(self, parametros):
        """Ruta 5: listado de citas del paciente con estado y motivo (RF-C05, CA-C11, PD-C14)."""
        codigo = self.identificar(parametros)
        if codigo is None:
            return
        citas = servicio.consultar_citas(self.server.ruta_bd, codigo)
        cuerpo = [f"<p>Paciente: {escapar(codigo)}</p>\n"]
        aviso = AVISOS.get(_valor(parametros, "aviso"))
        if aviso:
            cuerpo.append(f"<p>{escapar(aviso)}</p>\n")
        cuerpo.append(
            f'<p><a href="/citas/buscar?codigo={quote(codigo)}">Reservar otra cita</a></p>\n'
        )
        if not citas:
            cuerpo.append("<p>No tiene ninguna cita.</p>\n")
        else:
            cuerpo.append("<h2>Mis citas</h2>\n")
            for cita in citas:
                cuerpo.append("<h3>")
                cuerpo.append(f"{escapar(cita.fecha)} a las {escapar(cita.hora_inicio)}")
                cuerpo.append("</h3>\n<p>")
                cuerpo.append(
                    f"{escapar(cita.nombre_especialista)} · {escapar(cita.especialidad)} · "
                    f"{escapar(cita.centro)}<br>\n"
                    f"Estado: {escapar(cita.nombre_estado)}"
                )
                if cita.motivo_cancelacion:
                    cuerpo.append(f"<br>\nMotivo: {escapar(cita.motivo_cancelacion)}")
                cuerpo.append("</p>\n")
                if cita.estado == servicio.ESTADO_RESERVADA:
                    cuerpo.append(
                        f'<form method="post" action="/citas/{cita.id_cita}/cancelar">\n'
                        f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n'
                        '<button type="submit">Cancelar</button>\n</form>\n'
                        f'<p><a href="/citas/{cita.id_cita}/reprogramar?codigo={quote(codigo)}">'
                        "Reprogramar</a></p>\n"
                    )
        self.responder_html(200, pagina("Mis citas", "".join(cuerpo)))

    # Ruta 6 · POST /citas/<id_cita>/cancelar

    def cancelar(self, id_cita, campos):
        """Ruta 6: cancelar una cita reservada (RF-C06, CA-C06, CA-C07, CL-C07)."""
        codigo = self.identificar(campos)
        if codigo is None:
            return
        try:
            servicio.cancelar_cita(
                self.server.ruta_bd, codigo, id_cita, servicio.momento_actual()
            )
        except CitaNoEncontrada as error:
            self.responder_html(404, pagina_error("Cita no encontrada", str(error)))
            return
        except (FueraDePlazo, CitaYaCancelada) as error:
            self.responder_html(409, pagina_error("No se puede cancelar", str(error)))
            return
        self.redirigir(f"/citas/mias?codigo={quote(codigo)}&aviso=cancelada")

    # Ruta 7 · GET /citas/<id_cita>/reprogramar

    def mostrar_reprogramacion(self, id_cita, parametros):
        """Ruta 7: elegir el hueco destino del mismo especialista (RF-C07, RN-C10, CL-C08)."""
        codigo = self.identificar(parametros)
        if codigo is None:
            return
        citas = {cita.id_cita: cita for cita in servicio.consultar_citas(self.server.ruta_bd, codigo)}
        cita = citas.get(id_cita)
        if cita is None:
            self.responder_html(404, pagina_error("Cita no encontrada", "No existe esa cita."))
            return
        if cita.estado != servicio.ESTADO_RESERVADA:
            self.responder_html(
                409, pagina_error("No se puede reprogramar", "Esa cita ya está cancelada.")
            )
            return
        try:
            servicio._comprobar_plazo(cita, servicio.momento_actual())
        except FueraDePlazo as error:
            self.responder_html(409, pagina_error("No se puede reprogramar", str(error)))
            return
        fecha = _valor(parametros, "fecha")
        cuerpo = [
            f"<p>Paciente: {escapar(codigo)}</p>\n",
            f"<p>Cita actual: {escapar(cita.fecha)} a las {escapar(cita.hora_inicio)} con "
            f"{escapar(cita.nombre_especialista)}.</p>\n",
            "<p>Se conserva el mismo especialista; solo cambian la fecha y la hora.</p>\n",
            f'<form method="get" action="/citas/{id_cita}/reprogramar">\n',
            f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n',
            '<label for="fecha">Nueva fecha</label>\n',
            f'<input type="date" id="fecha" name="fecha" value="{escapar(fecha)}">\n',
            '<button type="submit">Ver huecos</button>\n</form>\n',
        ]
        if fecha:
            try:
                huecos = servicio.consultar_huecos(
                    self.server.ruta_bd,
                    cita.id_especialista,
                    fecha,
                    servicio.momento_actual(),
                )
            except ErrorValidacion as error:
                self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
                return
            if not huecos:
                cuerpo.append("<p>No hay huecos disponibles en esa fecha.</p>\n")
            else:
                for hueco in huecos:
                    cuerpo.append(
                        f'<form method="post" action="/citas/{id_cita}/reprogramar">\n'
                        f'<input type="hidden" name="codigo" value="{escapar(codigo)}">\n'
                        f'<input type="hidden" name="fecha" value="{escapar(fecha)}">\n'
                        '<input type="hidden" name="hora_inicio" '
                        f'value="{escapar(hueco.hora_inicio)}">\n'
                        f'<button type="submit">Trasladar a {escapar(hueco.hora_inicio)}'
                        "</button>\n</form>\n"
                    )
        self.responder_html(200, pagina("Reprogramar cita", "".join(cuerpo)))

    # Ruta 8 · POST /citas/<id_cita>/reprogramar

    def reprogramar(self, id_cita, campos):
        """Ruta 8: guardar el traslado (RF-C07, CA-C09, CL-C08)."""
        codigo = self.identificar(campos)
        if codigo is None:
            return
        try:
            servicio.reprogramar_cita(
                self.server.ruta_bd,
                codigo,
                id_cita,
                _valor(campos, "fecha"),
                _valor(campos, "hora_inicio"),
                servicio.momento_actual(),
            )
        except CitaNoEncontrada as error:
            self.responder_html(404, pagina_error("Cita no encontrada", str(error)))
            return
        except ErrorValidacion as error:
            self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
            return
        except (
            HuecoNoDisponible,
            HuecoPasado,
            CitaSolapada,
            FueraDePlazo,
            CitaYaCancelada,
        ) as error:
            self.responder_html(409, pagina_error("No se puede reprogramar", str(error)))
            return
        self.redirigir(f"/citas/mias?codigo={quote(codigo)}&aviso=reprogramada")

    # Ruta 9 · GET /agenda

    def mostrar_agenda(self, parametros):
        """Ruta 9: elegir especialista y ver sus dos operaciones (RF-C08, RF-C09, CA-C13).

        Sin identificación de ningún tipo (PD-C02). No hay ningún formulario de alta o edición de
        centros, especialidades ni especialistas (CA-C13, RN-C01).
        """
        especialistas = servicio.listar_especialistas(self.server.ruta_bd)
        elegido = _valor(parametros, "id_especialista")
        cuerpo = [
            "<p>Mantenimiento de la agenda. Los centros, las especialidades y los especialistas "
            "son datos precargados y no se pueden crear, editar ni eliminar.</p>\n",
            "<h2>Especialistas</h2>\n<ul>\n",
        ]
        for especialista in especialistas:
            cuerpo.append(
                f"<li>{escapar(especialista.nombre)} · "
                f"{escapar(especialista.especialidad)} · {escapar(especialista.centro)} · "
                f"{escapar(especialista.hora_inicio)}–{escapar(especialista.hora_fin)} · "
                f"consultas de {especialista.duracion_minutos} minutos · "
                f'<a href="/agenda?id_especialista={especialista.id_especialista}">'
                "Gestionar</a></li>\n"
            )
        cuerpo.append("</ul>\n")
        especialista = servicio.obtener_especialista(self.server.ruta_bd, elegido) if elegido else None
        if especialista is not None:
            cuerpo.append(f"<h2>Agenda de {escapar(especialista.nombre)}</h2>\n")
            cuerpo.append("<h3>Bloquear franja</h3>\n")
            cuerpo.append('<form method="post" action="/agenda/bloquear">\n')
            cuerpo.append(
                f'<input type="hidden" name="id_especialista" '
                f'value="{especialista.id_especialista}">\n'
            )
            cuerpo.append('<label for="fecha_inicio">Fecha de inicio</label>\n')
            cuerpo.append('<input type="date" id="fecha_inicio" name="fecha_inicio">\n')
            cuerpo.append('<label for="fecha_fin">Fecha de fin</label>\n')
            cuerpo.append('<input type="date" id="fecha_fin" name="fecha_fin">\n')
            cuerpo.append('<label for="hora_inicio">Hora de inicio</label>\n')
            cuerpo.append('<input type="time" id="hora_inicio" name="hora_inicio">\n')
            cuerpo.append('<label for="hora_fin">Hora de fin</label>\n')
            cuerpo.append('<input type="time" id="hora_fin" name="hora_fin">\n')
            cuerpo.append('<button type="submit">Bloquear</button>\n</form>\n')
            cuerpo.append("<h3>Ajustar la duración de las consultas</h3>\n")
            cuerpo.append('<form method="post" action="/agenda/duracion">\n')
            cuerpo.append(
                f'<input type="hidden" name="id_especialista" '
                f'value="{especialista.id_especialista}">\n'
            )
            cuerpo.append('<label for="duracion_minutos">Duración en minutos</label>\n')
            cuerpo.append(
                '<input type="text" id="duracion_minutos" name="duracion_minutos" '
                f'value="{especialista.duracion_minutos}">\n'
            )
            cuerpo.append('<button type="submit">Guardar</button>\n</form>\n')
        self.responder_html(200, pagina("Agenda del especialista", "".join(cuerpo)))

    # Rutas 10 y 11 · POST /agenda/bloquear y POST /agenda/duracion

    def _confirmar_canceladas(self, titulo, encabezado, canceladas, extra=""):
        """Página de confirmación con las citas canceladas por el centro (PD-C11)."""
        cuerpo = [f"<p>{escapar(encabezado)}</p>\n"]
        if extra:
            cuerpo.append(f"<p>{escapar(extra)}</p>\n")
        if not canceladas:
            cuerpo.append("<p>No se ha cancelado ninguna cita.</p>\n")
        else:
            cuerpo.append(
                f"<p>Citas canceladas por el centro: {len(canceladas)}.</p>\n<ul>\n"
            )
            for cita in canceladas:
                cuerpo.append(
                    f"<li>{escapar(cita.fecha)} a las {escapar(cita.hora_inicio)} · "
                    f"paciente {escapar(cita.codigo_historia)} · "
                    f"motivo: {escapar(cita.motivo_cancelacion)}</li>\n"
                )
            cuerpo.append("</ul>\n")
        cuerpo.append(
            "<p>Las citas cuya hora ya había pasado no se han cancelado: son historial, no "
            "agenda.</p>\n"
        )
        cuerpo.append('<p><a href="/agenda">Volver a la agenda</a></p>\n')
        self.responder_html(200, pagina(titulo, "".join(cuerpo)))

    def bloquear(self, campos):
        """Ruta 10: bloquear una franja (RF-C08, CA-C10, CL-C04, PD-C11, PD-C12)."""
        try:
            canceladas = servicio.bloquear_franja(
                self.server.ruta_bd,
                _valor(campos, "id_especialista"),
                _valor(campos, "fecha_inicio"),
                _valor(campos, "fecha_fin"),
                _valor(campos, "hora_inicio"),
                _valor(campos, "hora_fin"),
                servicio.momento_actual(),
            )
        except ErrorValidacion as error:
            self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
            return
        self._confirmar_canceladas(
            "Franja bloqueada",
            "Franja bloqueada correctamente.",
            canceladas,
        )

    def ajustar_duracion(self, campos):
        """Ruta 11: ajustar la duración de las consultas (RF-C09, CA-C12, PD-C11)."""
        id_especialista = _valor(campos, "id_especialista")
        try:
            canceladas = servicio.ajustar_duracion(
                self.server.ruta_bd,
                id_especialista,
                _valor(campos, "duracion_minutos"),
                servicio.momento_actual(),
            )
        except ErrorValidacion as error:
            self.responder_html(400, pagina_error("Dato no válido", error.mensaje))
            return
        especialista = servicio.obtener_especialista(self.server.ruta_bd, id_especialista)
        self._confirmar_canceladas(
            "Duración ajustada",
            f"Las consultas pasan a durar {especialista.duracion_minutos} minutos.",
            canceladas,
            extra=(
                "Nueva rejilla: "
                + ", ".join(
                    servicio.agenda.generar_rejilla(
                        especialista.dias_semana,
                        especialista.hora_inicio,
                        especialista.hora_fin,
                        especialista.duracion_minutos,
                        _proxima_fecha_de_consulta(especialista),
                    )
                )
            ),
        )


def _proxima_fecha_de_consulta(especialista):
    """Primera fecha, a partir de hoy, en que el especialista pasa consulta (para la rejilla)."""
    dias = servicio.agenda.dias_de_consulta(especialista.dias_semana)
    fecha = datetime.date.today()
    for _ in range(7):
        if fecha.isoweekday() in dias:
            return fecha.isoformat()
        fecha += datetime.timedelta(days=1)
    return datetime.date.today().isoformat()


def crear_servidor(ruta_bd, host="127.0.0.1", puerto=8000):
    """Servidor único que sirve los dos módulos con el manejador combinado (D-C13)."""
    servidor = ThreadingHTTPServer((host, puerto), ManejadorCitas)
    servidor.ruta_bd = ruta_bd
    return servidor
