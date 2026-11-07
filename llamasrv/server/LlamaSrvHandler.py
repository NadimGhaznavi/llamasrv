"""Serve the small, read-only LlamaSrv HTTP API."""

from datetime import datetime
from http.server import BaseHTTPRequestHandler
import json
from urllib.parse import urlsplit

from llamasrv.constants.DHTTP import DHTTP, HealthStatus
from llamasrv.constants.DLlamaSrv import DLlamaSrv


class LlamaSrvHandler(BaseHTTPRequestHandler):
    server_version = DLlamaSrv.NAME + "/" + DLlamaSrv.VERSION
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(DHTTP.REQUEST_TIMEOUT)

    def log_date_time_string(self) -> str:
        return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S")

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
        if path == DHTTP.ROOT:
            self.respond(200, {
                DHTTP.APPLICATION: DLlamaSrv.NAME,
                DHTTP.VERSION: DLlamaSrv.VERSION,
                DHTTP.HEALTH_LINK: DHTTP.HEALTH,
            })
        elif path == DHTTP.HEALTH:
            health = self.server.health()
            self.respond(200 if health[DHTTP.STATUS] == HealthStatus.OK else 503, health)
        else:
            self.respond(404, {DHTTP.ERROR: DHTTP.NOT_FOUND})

    def reject_mutation(self) -> None:
        try:
            path = urlsplit(self.path).path
        except ValueError:
            self.send_error(400)
            return
        if path not in (DHTTP.ROOT, DHTTP.HEALTH):
            self.respond(404, {DHTTP.ERROR: DHTTP.NOT_FOUND})
        else:
            self.respond(405, {DHTTP.ERROR: DHTTP.METHOD_NOT_ALLOWED}, allow="GET, HEAD")

    do_POST = reject_mutation
    do_PUT = reject_mutation
    do_PATCH = reject_mutation
    do_DELETE = reject_mutation
    do_OPTIONS = reject_mutation

    def send_error(self, code, message=None, explain=None) -> None:
        self.log_error("http_error status=%s", code)
        self.respond(code, {DHTTP.ERROR: DHTTP.HTTP_ERROR, DHTTP.CODE: code})

    def respond(self, status: int, value: dict, *, allow: str | None = None) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if allow is not None:
            self.send_header("Allow", allow)
        self.end_headers()
        if self.command != DHTTP.HEAD:
            self.wfile.write(body)
