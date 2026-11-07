"""Control-panel field names, presentation assets and refresh limits."""

from typing import Final


class DControl:
    HTTP_PORT: Final[str] = "http_port"
    LLM_PORT: Final[str] = "llm_port"
    MODELS: Final[str] = "models"
    PROJECTORS: Final[str] = "projectors"
    SETTINGS: Final[str] = "settings"
    MESSAGE: Final[str] = "message"
    CHECKED_AT: Final[str] = "checked_at"
    TIMEZONE: Final[str] = "timezone"
    HTTP_RESTART_REQUIRED: Final[str] = "http_restart_required"
    REFRESH_MS: Final[int] = 5000
    REQUEST_TIMEOUT_MS: Final[int] = 70000
    MODEL_PATTERN: Final[str] = "*.gguf"
    PROJECTOR_PREFIX: Final[str] = "mmproj"
    TEMPLATE: Final[str] = "home.html"
