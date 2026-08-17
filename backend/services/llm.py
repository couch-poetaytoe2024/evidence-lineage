"""Small provider-neutral contract for language-model calls."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class LLMError(RuntimeError):
    """Expected provider/network failure that an agent may safely recover from."""


@dataclass(frozen=True, slots=True)
class LLMResult:
    """Raw provider result plus usage data needed for later cost tracking."""

    text: str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class LLMClient(Protocol):
    """The only interface agents use to access an external model provider."""

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, object] | None = None,
    ) -> LLMResult:
        """Generate a response. Implementations should raise on provider failure."""
