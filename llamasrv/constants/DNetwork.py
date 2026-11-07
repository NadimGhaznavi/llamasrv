"""Network configuration schema; listener defaults live in DLlamaSrv."""

from typing import Final


class DNetwork:
    HTTP: Final[str] = "http"
    LLM: Final[str] = "llm"
    CONFIG_FILE: Final[str] = "conf/llamasrv.json"
    NETWORK: Final[str] = "network"
    INTERFACE: Final[str] = "interface"
    PORT: Final[str] = "port"
    MIN_PORT: Final[int] = 1
    MAX_PORT: Final[int] = 65535
    WILDCARD: Final[str] = "0.0.0.0"
    LOCALHOST: Final[str] = "127.0.0.1"
