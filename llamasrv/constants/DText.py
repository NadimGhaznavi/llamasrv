"""Stable keys for the server's English source catalogue."""

from enum import StrEnum


class DText(StrEnum):
    SERVER_DESCRIPTION = "server.description"
    SERVER_READY = "server.ready"
    SERVER_STOPPED = "server.stopped"
    SERVER_FAILED = "server.failed"
    CLI_HOST = "cli.host"
    CLI_PORT = "cli.port"
    CLI_CONFIG = "cli.config"
    CLI_LOCALE = "cli.locale"
    CONFIG_READ_FAILED = "config.read_failed"
    CONFIG_OBJECT_REQUIRED = "config.object_required"
    CONFIG_UNKNOWN_SETTING = "config.unknown_setting"
    CONFIG_INVALID_HOST = "config.invalid_host"
    CONFIG_INVALID_PORT = "config.invalid_port"
