"""Resolve and validate application defaults and operator-owned JSON once."""

from ipaddress import IPv4Address
import json
from pathlib import Path

from llamasrv.constants.DLlama import DLlama
from llamasrv.constants.DLlamaSrv import DLlamaSrv
from llamasrv.constants.DNetwork import DNetwork
from llamasrv.constants.DQwen import DQwen
from llamasrv.constants.DText import DText
from llamasrv.interface.Localizer import Localizer


class Configuration:
    def __init__(self, path: Path | None = None, *,
                 localizer: Localizer | None = None, locale: str | None = None):
        self.path = Path(path) if path is not None else (
            Path(DLlamaSrv.BASE_DIR) / DNetwork.CONFIG_FILE)
        self.localizer = localizer if localizer is not None else Localizer(
            Path(__file__).resolve().parents[1] / DLlamaSrv.LOCALES_DIR)
        self.locale = self.localizer.select(explicit=locale)
        try:
            content = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            values = {}
        except (OSError, UnicodeError) as error:
            raise ValueError(self.text(DText.CONFIG_READ_FAILED, error=error)) from error
        else:
            try:
                values = json.loads(content)
            except ValueError as error:
                raise ValueError(self.text(DText.CONFIG_READ_FAILED, error=error)) from error
        self.object(values, "root", {DNetwork.NETWORK, DLlama.SECTION})
        self.network = {use: (host, port) for use, host, port in DLlamaSrv.CMDB_NETWORK}
        network = values.get(DNetwork.NETWORK, {})
        self.object(network, DNetwork.NETWORK, set(self.network))
        for use, overrides in network.items():
            setting = f"{DNetwork.NETWORK}.{use}"
            self.object(overrides, setting, {DNetwork.INTERFACE, DNetwork.PORT})
            host, port = self.network[use]
            self.network[use] = self.validate_binding(
                overrides.get(DNetwork.INTERFACE, host),
                overrides.get(DNetwork.PORT, port), setting)
        self.llama = {
            DLlama.BINARY: DLlama.DEFAULT_BINARY,
            DLlama.MODEL_DIR: DLlama.DEFAULT_MODEL_DIR,
            DLlama.MODEL: DQwen.GGUF,
            DLlama.MMPROJ: DQwen.MMPROJ,
            DLlama.CONTEXT_SIZE: DQwen.CONTEXT_SIZE,
            DLlama.METRICS: DLlama.DEFAULT_METRICS,
            DLlama.JINJA: DLlama.DEFAULT_JINJA,
        }
        overrides = values.get(DLlama.SECTION, {})
        self.object(overrides, DLlama.SECTION, set(self.llama))
        self.llama.update(overrides)
        for key in (DLlama.BINARY, DLlama.MODEL_DIR, DLlama.MODEL, DLlama.MMPROJ):
            value = self.llama[key]
            if key == DLlama.MMPROJ and value is None:
                continue
            if not isinstance(value, str) or not value.strip() or "\0" in value:
                raise ValueError(self.text(DText.CONFIG_INVALID_PATH, setting=f"llama.{key}"))
            if key in (DLlama.BINARY, DLlama.MODEL_DIR) and not Path(value).is_absolute():
                raise ValueError(self.text(DText.CONFIG_ABSOLUTE_PATH, setting=f"llama.{key}"))
        context = self.llama[DLlama.CONTEXT_SIZE]
        if type(context) is not int or context < 1:
            raise ValueError(self.text(DText.CONFIG_INVALID_CONTEXT, setting="llama.context_size"))
        for key in (DLlama.METRICS, DLlama.JINJA):
            if type(self.llama[key]) is not bool:
                raise ValueError(self.text(DText.CONFIG_INVALID_BOOL, setting=f"llama.{key}"))

    def text(self, key: DText, **values) -> str:
        return self.localizer.text(key, locale=self.locale, path=self.path, **values)

    def object(self, value, setting: str, allowed: set[str]) -> None:
        if not isinstance(value, dict):
            raise ValueError(self.text(DText.CONFIG_OBJECT_REQUIRED, setting=setting))
        for key in value:
            if key not in allowed:
                raise ValueError(self.text(DText.CONFIG_UNKNOWN_SETTING, setting=f"{setting}.{key}"))

    def validate_binding(self, host, port, setting: str) -> tuple[str, int]:
        try:
            if not isinstance(host, str):
                raise ValueError
            address = IPv4Address(host)
        except ValueError as error:
            raise ValueError(self.text(
                DText.CONFIG_INVALID_HOST, setting=f"{setting}.{DNetwork.INTERFACE}")) from error
        if type(port) is not int or not DNetwork.MIN_PORT <= port <= DNetwork.MAX_PORT:
            raise ValueError(self.text(
                DText.CONFIG_INVALID_PORT, setting=f"{setting}.{DNetwork.PORT}"))
        return str(address), port

    def as_dict(self) -> dict:
        return {
            DNetwork.NETWORK: {
                use: {DNetwork.INTERFACE: host, DNetwork.PORT: port}
                for use, (host, port) in self.network.items()},
            DLlama.SECTION: dict(self.llama),
        }
