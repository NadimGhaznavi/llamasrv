"""Application-owned systemd resources and bounded installation checks."""

from typing import Final


class DService:
    ACCOUNT: Final[str] = "llamasrv"
    HTTP: Final[str] = "llamasrv-http.service"
    LLM: Final[str] = "llamasrv-llm.service"
    START_ORDER: Final[tuple[str, ...]] = (LLM, HTTP)
    UNIT_DIR: Final[str] = "/etc/systemd/system"
    USERADD: Final[str] = "/usr/sbin/useradd"
    RUNUSER: Final[str] = "/usr/sbin/runuser"
    COMMAND_TIMEOUT: Final[int] = 30
    STARTUP_TIMEOUT: Final[float] = 120.0
    POLL_INTERVAL: Final[float] = 0.5
