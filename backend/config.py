"""Environment-backed application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen3:4b"


@dataclass(frozen=True, slots=True)
class Settings:
    ollama_base_url: str = DEFAULT_OLLAMA_BASE_URL
    ollama_model: str = DEFAULT_OLLAMA_MODEL
    ollama_enabled: bool = True
    contact_email: str | None = None

    @classmethod
    def from_env(cls) -> "Settings":
        enabled = os.getenv("OLLAMA_ENABLED", "true").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        return cls(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL),
            ollama_model=os.getenv("OLLAMA_MODEL", DEFAULT_OLLAMA_MODEL),
            ollama_enabled=enabled,
            contact_email=os.getenv("CONTACT_EMAIL") or None,
        )
