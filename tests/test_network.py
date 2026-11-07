"""Listener configuration precedence and validation checks."""

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DText import DText
from llamasrv.interface.Localizer import Localizer
from llamasrv.interface.Network import Network


ROOT = Path(__file__).resolve().parents[1]


class NetworkTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.path = Path(self.directory.name) / "llamasrv.json"

    def configure(self, value):
        self.path.write_text(json.dumps(value), encoding="utf-8")
        return Network(self.path)

    def test_missing_configuration_uses_declared_defaults(self):
        network = Network(self.path)
        self.assertEqual(network.binding("http"), ("0.0.0.0", 51000))
        self.assertEqual(network.destination("http"), ("127.0.0.1", 51000))
        self.assertFalse(self.path.exists())
        with patch.object(DLlamaSrv, "CMDB_NETWORK", (("http", "192.0.2.1", 51002),)):
            self.assertEqual(Network(self.path).binding("http"), ("192.0.2.1", 51002))

    def test_partial_configuration_and_cli_precedence(self):
        for values in ({}, {"network": {}}, {"network": {"http": {}}}):
            with self.subTest(values=values):
                self.assertEqual(self.configure(values).binding("http"), ("0.0.0.0", 51000))
        network = self.configure({"network": {"http": {"port": 51001}}})
        self.assertEqual(network.binding("http"), ("0.0.0.0", 51001))
        self.assertEqual(network.binding("http", host="127.0.0.2", port=51002),
                         ("127.0.0.2", 51002))
        # Invocation overrides must not mutate the resolved configuration.
        self.assertEqual(network.binding("http"), ("0.0.0.0", 51001))
        network = self.configure({"network": {"http": {"interface": "192.0.2.2"}}})
        self.assertEqual(network.binding("http"), ("192.0.2.2", 51000))
        self.assertEqual(network.destination("http"), ("192.0.2.2", 51000))

    def test_default_configuration_path_comes_from_installation_root(self):
        with patch.object(DLlamaSrv, "BASE_DIR", self.directory.name):
            path = Path(self.directory.name) / "conf/llamasrv.json"
            path.parent.mkdir()
            path.write_text('{"network":{"http":{"port":51003}}}')
            network = Network()
            self.assertEqual(network.path, path)
            self.assertEqual(network.binding("http"), ("0.0.0.0", 51003))

    def test_invalid_json_types_fields_addresses_and_ports(self):
        invalid = [None, [], {"unknown": {}}, {"network": None}, {"network": []},
                   {"network": {"unknown": {}}}, {"network": {"http": []}},
                   {"network": {"http": {"host": "127.0.0.1"}}}]
        for host in (None, True, 123, "localhost", "::1", "999.1.1.1", ""):
            invalid.append({"network": {"http": {"interface": host}}})
        for port in (None, True, "51000", 1.5, -1, 0, 65536):
            invalid.append({"network": {"http": {"port": port}}})
        for values in invalid:
            with self.subTest(values=values):
                with self.assertRaises(ValueError) as raised:
                    self.configure(values)
                self.assertIn(str(self.path), str(raised.exception))
        for content in (b"{broken", b"\xff"):
            with self.subTest(content=content):
                self.path.write_bytes(content)
                with self.assertRaises(ValueError) as raised:
                    Network(self.path)
                self.assertIn(str(self.path), str(raised.exception))

    def test_unreadable_configuration_is_an_error(self):
        self.path.mkdir()
        with self.assertRaisesRegex(ValueError, "Could not read configuration"):
            Network(self.path)

    def test_locale_catalogue_covers_real_messages(self):
        directory = ROOT / "llamasrv/locales"
        english = json.loads((directory / "en.json").read_text())
        self.assertEqual(set(english), {key.value for key in DText})
        localizer = Localizer(directory)
        self.assertEqual(localizer.languages, ("en",))
        self.assertEqual(localizer.select(explicit="en-CA"), "en")
        self.assertEqual(localizer.select(accept_language="fr, en;q=0.8"), "en")
        for key in DText:
            localizer.text(key, path="example", setting="network.http", error="failure",
                           host="0.0.0.0", port=51000)


if __name__ == "__main__":
    unittest.main()
