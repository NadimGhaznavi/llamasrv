"""llama.cpp configuration keys, defaults and command-line contract."""

from typing import Final


class DLlama:
    SECTION: Final[str] = "llama"
    BINARY: Final[str] = "binary"
    MODEL_DIR: Final[str] = "model_dir"
    MODEL: Final[str] = "model"
    MMPROJ: Final[str] = "mmproj"
    CONTEXT_SIZE: Final[str] = "context_size"
    METRICS: Final[str] = "metrics"
    JINJA: Final[str] = "jinja"
    DEFAULT_BINARY: Final[str] = "/opt/prod/llama.cpp/bin/llama-server"
    DEFAULT_MODEL_DIR: Final[str] = "/opt/prod/models"
    DEFAULT_METRICS: Final[bool] = True
    DEFAULT_JINJA: Final[bool] = True
    MODEL_OPTION: Final[str] = "--model"
    MMPROJ_OPTION: Final[str] = "--mmproj"
    CONTEXT_OPTION: Final[str] = "-c"
    HOST_OPTION: Final[str] = "--host"
    PORT_OPTION: Final[str] = "--port"
    METRICS_OPTION: Final[str] = "--metrics"
    JINJA_OPTION: Final[str] = "--jinja"
    NO_JINJA_OPTION: Final[str] = "--no-jinja"
    HEALTH_TIMEOUT: Final[float] = 2.0
    HEALTH_RESPONSE_LIMIT: Final[int] = 65536
