"""HTTP transport limits and stable response identifiers."""

from enum import StrEnum
from typing import Final


class DHTTP:
    ROOT: Final[str] = "/"
    HEALTH: Final[str] = "/health"
    REQUEST_TIMEOUT: Final[float] = 5.0
    POLL_INTERVAL: Final[float] = 0.2
    HEAD: Final[str] = "HEAD"
    STATUS: Final[str] = "status"
    COMPONENTS: Final[str] = "components"
    APPLICATION: Final[str] = "application"
    VERSION: Final[str] = "version"
    HEALTH_LINK: Final[str] = "health"
    ERROR: Final[str] = "error"
    CODE: Final[str] = "code"
    NOT_FOUND: Final[str] = "not_found"
    METHOD_NOT_ALLOWED: Final[str] = "method_not_allowed"
    HTTP_ERROR: Final[str] = "http_error"


class HealthStatus(StrEnum):
    OK = "ok"
    ERROR = "error"
