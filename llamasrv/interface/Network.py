"""Resolve listeners and client destinations from shared configuration."""

from pathlib import Path

from llamasrv.constants.DNetwork import DNetwork
from llamasrv.interface.Configuration import Configuration
from llamasrv.interface.Localizer import Localizer


class Network:
    def __init__(self, configuration: Path | Configuration | None = None, *,
                 localizer: Localizer | None = None, locale: str | None = None):
        self.configuration = (configuration if isinstance(configuration, Configuration)
                              else Configuration(configuration, localizer=localizer, locale=locale))
        self.path = self.configuration.path

    def binding(self, use: str, *, host: str | None = None,
                port: int | None = None) -> tuple[str, int]:
        default_host, default_port = self.configuration.network[use]
        return self.configuration.validate_binding(
            default_host if host is None else host,
            default_port if port is None else port,
            f"{DNetwork.NETWORK}.{use}")

    def destination(self, use: str) -> tuple[str, int]:
        host, port = self.binding(use)
        return (DNetwork.LOCALHOST if host == DNetwork.WILDCARD else host), port
