"""Resolve and validate listener defaults, production JSON and CLI overrides."""

from ipaddress import IPv4Address
import json
from pathlib import Path

from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DText import DText
from llamasrv.interface.Localizer import Localizer


class Network:
    def __init__(self, configuration: Path | None = None, *,
                 localizer: Localizer | None = None, locale: str | None = None):
        self.path = (Path(configuration) if configuration is not None
                     else Path(DLlamaSrv.BASE_DIR) / DNetwork.CONFIG_FILE)
        self.localizer = localizer if localizer is not None else Localizer(
            Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)
        self.locale = self.localizer.select(explicit=locale)
        self._bindings = {use: (host, port) for use, host, port in DLlamaSrv.CMDB_NETWORK}
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            values = {}
        except (OSError, UnicodeError) as error:
            raise ValueError(self.localizer.text(
                DText.CONFIG_READ_FAILED, locale=self.locale,
                path=self.path, error=error)) from error
        else:
            try:
                values = json.loads(content)
            except ValueError as error:
                raise ValueError(self.localizer.text(
                    DText.CONFIG_READ_FAILED, locale=self.locale,
                    path=self.path, error=error)) from error
        self._object(values, "root", {DNetwork.NETWORK})
        network = values.get(DNetwork.NETWORK, {})
        self._object(network, DNetwork.NETWORK, set(self._bindings))
        for use, overrides in network.items():
            setting = f"{DNetwork.NETWORK}.{use}"
            self._object(overrides, setting, {DNetwork.INTERFACE, DNetwork.PORT})
            host, port = self._bindings[use]
            self._bindings[use] = self._validate(
                overrides.get(DNetwork.INTERFACE, host),
                overrides.get(DNetwork.PORT, port), setting)

    def _error(self, key: DText, setting: str) -> ValueError:
        return ValueError(self.localizer.text(
            key, locale=self.locale, path=self.path, setting=setting))

    def _object(self, value, setting: str, allowed: set[str]) -> None:
        if not isinstance(value, dict):
            raise self._error(DText.CONFIG_OBJECT_REQUIRED, setting)
        for key in value:
            if key not in allowed:
                raise self._error(DText.CONFIG_UNKNOWN_SETTING, f"{setting}.{key}")

    def _validate(self, host, port, setting: str) -> tuple[str, int]:
        try:
            if not isinstance(host, str):
                raise ValueError
            address = IPv4Address(host)
        except ValueError as error:
            raise self._error(
                DText.CONFIG_INVALID_HOST, f"{setting}.{DNetwork.INTERFACE}") from error
        if type(port) is not int or not DNetwork.MIN_PORT <= port <= DNetwork.MAX_PORT:
            raise self._error(DText.CONFIG_INVALID_PORT, f"{setting}.{DNetwork.PORT}")
        return str(address), port

    def binding(self, use: str, *, host: str | None = None,
                port: int | None = None) -> tuple[str, int]:
        default_host, default_port = self._bindings[use]
        return self._validate(default_host if host is None else host,
                              default_port if port is None else port,
                              f"{DNetwork.NETWORK}.{use}")

    def destination(self, use: str) -> tuple[str, int]:
        host, port = self.binding(use)
        return (DNetwork.LOCALHOST if host == DNetwork.WILDCARD else host), port
