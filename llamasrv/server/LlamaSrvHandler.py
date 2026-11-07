"""Serve the control panel, bounded mutation endpoints and readiness API."""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
import logging
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from llamasrv.constants.DControl import DControl
from llamasrv.constants.DHTTP import DHTTP, HealthStatus
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DText import DText


class LlamaSrvHandler(BaseHTTPRequestHandler):
    server_version = DLlamaSrv.NAME + "/" + DLlamaSrv.VERSION
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(DHTTP.REQUEST_TIMEOUT)

    def log_date_time_string(self) -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

    def locale(self) -> str:
        query = parse_qs(urlsplit(self.path).query, keep_blank_values=True)
        return self.server.localizer.select(
            explicit=query.get(DHTTP.LANG, [None])[0],
            accept_language=self.headers.get("Accept-Language", ""))

    def text(self, key: DText, **values) -> str:
        return self.server.localizer.text(key, locale=self.locale(), **values)

    def do_GET(self) -> None:
        self.serve()

    def do_HEAD(self) -> None:
        self.serve()

    def serve(self) -> None:
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.send_error(400)
            return
        try:
            if path == DHTTP.ROOT:
                self.home()
            elif path == DHTTP.INFO:
                self.respond(200, {DHTTP.APPLICATION: DLlamaSrv.NAME,
                                   DHTTP.VERSION: DLlamaSrv.VERSION,
                                   DHTTP.HEALTH_LINK: DHTTP.HEALTH})
            elif path in (DHTTP.HEALTH, DHTTP.LIVE_STATUS):
                health = self.server.health()
                if path == DHTTP.LIVE_STATUS:
                    now = datetime.now().astimezone()
                    health.update({DControl.CHECKED_AT: now.strftime("%Y-%m-%d %H:%M:%S"),
                                   DControl.TIMEZONE: now.tzname()})
                self.respond(200 if health[DHTTP.STATUS] == HealthStatus.OK else 503, health)
            elif path in (DHTTP.CONFIGURATION, DHTTP.RESTART):
                self.respond(405, {DHTTP.ERROR: DHTTP.METHOD_NOT_ALLOWED}, allow="POST")
            elif path.startswith(DHTTP.STATIC):
                name = path.removeprefix(DHTTP.STATIC)
                if name not in DHTTP.STATIC_FILES:
                    self.respond(404, {DHTTP.ERROR: DHTTP.NOT_FOUND})
                    return
                asset = Path(__file__).resolve().parent / "static" / name
                self.respond_bytes(200, asset.read_bytes(), DHTTP.STATIC_FILES[name])
            else:
                self.respond(404, {DHTTP.ERROR: DHTTP.NOT_FOUND})
        except (ValueError, OSError):
            logging.exception("control_panel_read_failed")
            self.respond(503, {DHTTP.ERROR: self.text(DText.UI_OPERATION_FAILED)})

    def home(self) -> None:
        locale = self.locale()
        snapshot = self.server.control.snapshot(locale)
        messages = {key.value: self.server.localizer.text(key, locale=locale)
                    for key in DText if key.name.startswith("UI_")}
        page_data = {"messages": messages, "locale": locale,
                     "refresh_ms": DControl.REFRESH_MS,
                     "timeout_ms": DControl.REQUEST_TIMEOUT_MS,
                     "configuration_url": DHTTP.CONFIGURATION,
                     "restart_url": DHTTP.RESTART, "status_url": DHTTP.LIVE_STATUS,
                     "request_header": DHTTP.REQUEST_HEADER,
                     "request_marker": DHTTP.REQUEST_MARKER}
        html = self.server.templates.get_template(DControl.TEMPLATE).render(
            app=DLlamaSrv, text=DText, locale=locale, t=self.text,
            languages=self.server.localizer.languages, snapshot=snapshot, page_data=page_data,
            http_port=self.server.server_port)
        self.respond_bytes(200, html.encode("utf-8"), "text/html; charset=utf-8")

    def do_POST(self) -> None:
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.send_error(400)
            return
        if path not in (DHTTP.CONFIGURATION, DHTTP.RESTART):
            self.reject_mutation()
            return
        try:
            origin = self.headers.get("Origin")
            if (self.headers.get(DHTTP.REQUEST_HEADER) != DHTTP.REQUEST_MARKER
                    or self.headers.get("Sec-Fetch-Site") == "cross-site"
                    or origin and (urlsplit(origin).scheme not in ("http", "https")
                                   or urlsplit(origin).netloc != self.headers.get("Host"))):
                self.respond(403, {DHTTP.ERROR: self.text(DText.UI_ORIGIN_INVALID)})
                return
            if (self.headers.get_content_type() != "application/json"
                    or self.headers.get("Transfer-Encoding")):
                raise ValueError(self.text(DText.UI_BODY_INVALID))
            try:
                length = int(self.headers.get("Content-Length", "0"))
            except ValueError:
                raise ValueError(self.text(DText.UI_BODY_INVALID)) from None
            if not 0 < length <= DHTTP.MAX_BODY:
                raise ValueError(self.text(DText.UI_BODY_INVALID))
            body = self.rfile.read(length)
            if len(body) != length:
                raise ValueError(self.text(DText.UI_BODY_INVALID))
            try:
                values = json.loads(body)
            except (ValueError, UnicodeError):
                raise ValueError(self.text(DText.UI_BODY_INVALID)) from None
            if not isinstance(values, dict):
                raise ValueError(self.text(DText.UI_BODY_INVALID))
            if path == DHTTP.CONFIGURATION:
                self.server.control.update(values, self.locale())
                self.respond(200, {
                    DControl.MESSAGE: self.text(DText.UI_SAVED),
                    DControl.HTTP_RESTART_REQUIRED: values[DControl.HTTP_PORT] != self.server.server_port})
            else:
                if values:
                    raise ValueError(self.text(DText.UI_INVALID_SETTINGS))
                self.server.control.restart(self.locale())
                self.respond(202, {DControl.MESSAGE: self.text(DText.UI_RESTART_SENT)})
        except ValueError as error:
            self.respond(400, {DHTTP.ERROR: str(error)})
        except (OSError, RuntimeError):
            logging.exception("control_panel_operation_failed")
            self.respond(503, {DHTTP.ERROR: self.text(DText.UI_OPERATION_FAILED)})

    def reject_mutation(self) -> None:
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.send_error(400)
            return
        if path in (DHTTP.CONFIGURATION, DHTTP.RESTART):
            self.respond(405, {DHTTP.ERROR: DHTTP.METHOD_NOT_ALLOWED}, allow="POST")
        elif path in (DHTTP.ROOT, DHTTP.HEALTH, DHTTP.INFO, DHTTP.LIVE_STATUS) or (
                path.startswith(DHTTP.STATIC) and path.removeprefix(DHTTP.STATIC) in DHTTP.STATIC_FILES):
            self.respond(405, {DHTTP.ERROR: DHTTP.METHOD_NOT_ALLOWED}, allow="GET, HEAD")
        else:
            self.respond(404, {DHTTP.ERROR: DHTTP.NOT_FOUND})

    do_PUT = reject_mutation
    do_PATCH = reject_mutation
    do_DELETE = reject_mutation
    do_OPTIONS = reject_mutation

    def send_error(self, code, message=None, explain=None) -> None:
        self.log_error("http_error status=%s", code)
        self.respond(code, {DHTTP.ERROR: DHTTP.HTTP_ERROR, DHTTP.CODE: code})

    def respond(self, status: int, value: dict, *, allow: str | None = None) -> None:
        self.respond_bytes(status, json.dumps(value).encode("utf-8"),
                           "application/json; charset=utf-8", allow=allow)

    def respond_bytes(self, status: int, body: bytes, content_type: str, *,
                      allow: str | None = None) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; "
                         "style-src 'self'; img-src 'self'; connect-src 'self'; "
                         "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'")
        if allow is not None:
            self.send_header("Allow", allow)
        self.end_headers()
        if self.command != DHTTP.HEAD:
            self.wfile.write(body)
