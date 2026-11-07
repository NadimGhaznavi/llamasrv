"""Default Qwen3.5-4B artifacts, matching the ax3l deployment."""

from typing import Final


class DQwen:
    GGUF: Final[str] = "Qwen3.5-4B-Q4_K_M.gguf"
    MMPROJ: Final[str] = "mmproj-Qwen3.5-4B-F16.gguf"
    CONTEXT_SIZE: Final[int] = 12288
