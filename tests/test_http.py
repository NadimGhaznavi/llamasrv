"""HTTP transport and real-process lifecycle acceptance checks."""

from contextlib import redirect_stdout
from datetime import datetime, timezone
from http.client import HTTPConnection
import io
import json
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
from threading import Thread
import time
import unittest
from unittest.mock import ANY, Mock, patch

from llamasrv.constants.DHTTP import DHTTP
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.server.LlamaSrvHandler import LlamaSrvHandler
from llamasrv.server.LlamaSrvServer import LlamaSrvServer, main


ROOT = Path(__file__).resolve().parents[1]


class HTTPTests(unittest.TestCase):
    def setUp(self):
        self.server = LlamaSrvServer(("127.0.0.1", 0), llama=Mock(health=Mock(return_value=True)))
        self.worker = Thread(target=self.server.serve_forever,
                             kwargs={"poll_interval": 0.01})
        self.worker.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.worker.join(timeout=2)
        self.assertFalse(self.worker.is_alive())

    def request(self, method, path, body=None, headers=None):
        connection = HTTPConnection(*self.server.server_address, timeout=2)
        try:
            connection.request(method, path, body=body, headers=headers or {})
            response = connection.getresponse()
            return response.status, dict(response.getheaders()), response.read()
        finally:
            connection.close()

    def test_get_and_head_contract(self):
        for path in ("/", "/health", "/health?lang=en", "/missing"):
            with self.subTest(path=path):
                status, headers, body = self.request("GET", path)
                self.assertEqual(status, 404 if path == "/missing" else 200)
                self.assertEqual(headers["Content-Type"], "application/json; charset=utf-8")
                self.assertEqual(int(headers["Content-Length"]), len(body))
                self.assertEqual(headers["Cache-Control"], "no-store")
                self.assertEqual(headers["X-Content-Type-Options"], "nosniff")
                json.loads(body)
                head_status, head_headers, head_body = self.request("HEAD", path)
                self.assertEqual(head_status, status)
                self.assertEqual(head_headers["Content-Length"], headers["Content-Length"])
                self.assertEqual(head_body, b"")
        self.assertEqual(json.loads(self.request("GET", "/")[2]), {
            "application": "LlamaSrv", "version": DLlamaSrv.VERSION, "health": "/health"})
        self.assertEqual(json.loads(self.request("GET", "/health")[2]), {
            "status": "ok", "components": {"http": "ok", "llm": "ok"}})

    def test_health_failure_and_recovery(self):
        failed = {"status": "error", "components": {"http": "error"}}
        with patch.object(self.server, "health", return_value=failed):
            status, _, body = self.request("GET", "/health")
            self.assertEqual(status, 503)
            self.assertEqual(json.loads(body), failed)
        self.assertEqual(self.request("GET", "/health")[0], 200)

    def test_inference_failure_is_reported_and_recovers(self):
        self.server.llama.health.return_value = False
        status, _, body = self.request("GET", "/health")
        self.assertEqual(status, 503)
        self.assertEqual(json.loads(body), {
            "status": "error", "components": {"http": "ok", "llm": "error"}})
        self.server.llama.health.return_value = True
        self.assertEqual(self.request("GET", "/health")[0], 200)

    def test_unknown_paths_cannot_read_files(self):
        for path in ("/../README.md", "/static/../../llamasrv/constants/DLlamaSrv.py"):
            with self.subTest(path=path):
                self.assertEqual(self.request("GET", path)[0], 404)

    def test_mutations_are_rejected_without_reading_unneeded_bodies(self):
        for method in ("POST", "PUT", "PATCH", "DELETE", "OPTIONS"):
            with self.subTest(method=method):
                status, headers, body = self.request(method, "/health", "{bad json", {
                    "Content-Type": "application/json", "Content-Length": "10000000"})
                self.assertEqual(status, 405)
                self.assertEqual(headers["Allow"], "GET, HEAD")
                self.assertEqual(json.loads(body), {"error": "method_not_allowed"})
        self.assertEqual(self.request("POST", "/missing")[0], 404)
        status, headers, body = self.request("BREW", "/health")
        self.assertEqual(status, 501)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(json.loads(body), {"error": "http_error", "code": 501})
        self.assertEqual(self.request("GET", "/health")[0], 200)

    def test_idle_client_is_bounded_and_does_not_block_other_requests(self):
        with patch.object(DHTTP, "REQUEST_TIMEOUT", 0.15):
            with socket.create_connection(self.server.server_address, timeout=2) as idle:
                idle.sendall(b"GET /health HTTP/1.1\r\n")
                self.assertEqual(self.request("GET", "/health")[0], 200)
                self.assertEqual(idle.recv(1), b"")

    def test_occupied_port_fails(self):
        with self.assertRaises(OSError):
            LlamaSrvServer(self.server.server_address)

    def test_bind_failure_exits_without_claiming_readiness(self):
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stdout(io.StringIO()) as output, self.assertLogs(level="ERROR") as logs:
                result = main(["--config", str(Path(directory) / "missing.json"),
                               "--host", self.server.server_address[0],
                               "--port", str(self.server.server_port)])
            self.assertEqual(result, 1)
            self.assertNotIn("listening", output.getvalue())
            self.assertIn("Could not start", logs.output[0])


class StartupTests(unittest.TestCase):
    def test_log_timestamps_use_server_local_time_across_midnight_and_dst(self):
        handler = object.__new__(LlamaSrvHandler)
        cases = (
            (datetime(2026, 1, 1, 4, 59, 59, 999999, tzinfo=timezone.utc),
             "2025-12-31 23:59:59"),
            (datetime(2026, 11, 1, 5, 59, 59, tzinfo=timezone.utc),
             "2026-11-01 01:59:59"),
            (datetime(2026, 11, 1, 6, 0, 0, tzinfo=timezone.utc),
             "2026-11-01 01:00:00"),
        )
        try:
            with patch.dict(os.environ, {"TZ": "America/Toronto"}):
                time.tzset()
                for instant, expected in cases:
                    with self.subTest(instant=instant):
                        with patch("llamasrv.server.LlamaSrvHandler.datetime") as clock:
                            clock.now.return_value = instant
                            self.assertEqual(handler.log_date_time_string(), expected)
        finally:
            time.tzset()

    def test_default_startup_binds_the_declared_wildcard_and_port(self):
        previous = signal.getsignal(signal.SIGTERM)
        with tempfile.TemporaryDirectory() as directory:
            with patch("llamasrv.server.LlamaSrvServer.LlamaSrvServer") as factory:
                server = factory.return_value.__enter__.return_value
                server.server_address = ("0.0.0.0", 51000)
                server.server_port = 51000
                server.serve_forever.side_effect = KeyboardInterrupt
                with redirect_stdout(io.StringIO()) as output:
                    self.assertEqual(main(["--config", str(Path(directory) / "missing.json")]), 0)
                factory.assert_called_once_with(("0.0.0.0", 51000), llama=ANY)
                self.assertIn("http://0.0.0.0:51000/", output.getvalue())
        self.assertEqual(signal.getsignal(signal.SIGTERM), previous)

    def test_wildcard_socket_is_bound_to_all_ipv4_interfaces(self):
        with LlamaSrvServer(("0.0.0.0", 0), llama=Mock(health=Mock(return_value=False))) as server:
            self.assertEqual(server.socket.getsockname()[0], "0.0.0.0")
            self.assertGreater(server.server_port, 0)
        self.assertEqual(server.health(), {
            "status": "error", "components": {"http": "error", "llm": "error"}})

    def test_invalid_cli_or_configuration_exits_before_binding(self):
        cases = (["--port", "0"], ["--port", "65536"], ["--port", "text"],
                 ["--host", "localhost"], ["--host", "::1"])
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "llamasrv.json"
            for options in cases:
                with self.subTest(options=options):
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "llamasrv", "--config",
                         str(configuration), *options], cwd=ROOT,
                        capture_output=True, text=True, timeout=5)
                    self.assertEqual(result.returncode, 2, result.stderr)
                    self.assertNotIn("listening", result.stdout)
            configuration.write_text('{"network":{"http":{"port":false}}}')
            result = subprocess.run(
                [sys.executable, "-B", "-m", "llamasrv", "--config", str(configuration),
                 "--host", "127.0.0.1", "--port", "51001"], cwd=ROOT,
                capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn(str(configuration), result.stderr)
            self.assertIn("network.http.port", result.stderr)

    def test_real_process_signals_release_listener_and_join_request_workers(self):
        for stop_signal in (signal.SIGTERM, signal.SIGINT):
            with self.subTest(stop_signal=stop_signal):
                with socket.socket() as reservation:
                    reservation.bind(("127.0.0.1", 0))
                    port = reservation.getsockname()[1]
                with tempfile.TemporaryDirectory() as directory:
                    # Exercise production JSON and the package entry point together.
                    configuration = Path(directory) / "llamasrv.json"
                    configuration.write_text(json.dumps({"network": {"http": {
                        "interface": "127.0.0.1", "port": port}}}))
                    with subprocess.Popen(
                        [sys.executable, "-B", "-m", "llamasrv", "--config", str(configuration)],
                        cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                    ) as process:
                        try:
                            self.assertTrue(select.select([process.stdout], [], [], 5)[0])
                            self.assertIn(f"http://127.0.0.1:{port}/", process.stdout.readline())
                            connection = HTTPConnection("127.0.0.1", port, timeout=2)
                            try:
                                connection.request("GET", "/health")
                                response = connection.getresponse()
                                self.assertEqual(response.status, 503)
                                self.assertEqual(json.loads(response.read())["components"]["llm"], "error")
                            finally:
                                connection.close()
                            with socket.create_connection(("127.0.0.1", port), timeout=2) as idle:
                                idle.sendall(b"GET /health HTTP/1.1\r\n")
                                # A subsequent response confirms the accept loop has
                                # dispatched the earlier idle connection to a worker.
                                probe = HTTPConnection("127.0.0.1", port, timeout=2)
                                try:
                                    probe.request("HEAD", "/health")
                                    probe.getresponse().read()
                                finally:
                                    probe.close()
                                process.send_signal(stop_signal)
                                output, errors = process.communicate(timeout=8)
                            self.assertEqual(process.returncode, 0, errors)
                            self.assertIn("stopped", output)
                            self.assertNotIn("Traceback", errors)
                            with socket.socket() as probe:
                                self.assertNotEqual(probe.connect_ex(("127.0.0.1", port)), 0)
                        finally:
                            if process.poll() is None:
                                process.kill()
                                process.communicate(timeout=2)


if __name__ == "__main__":
    unittest.main()
