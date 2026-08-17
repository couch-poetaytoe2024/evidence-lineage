"""Ollama implementation of the provider-neutral LLM contract."""

from __future__ import annotations

import httpx

from backend.services.llm import LLMError, LLMResult


class OllamaClient:
    """Call a local Ollama model through its HTTP API."""

    def __init__(
        self,
        *,
        model: str = "qwen3:4b",
        base_url: str = "http://localhost:11434",
        timeout_seconds: float = 240.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._http_client = http_client

    async def generate(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        json_schema: dict[str, object] | None = None,
    ) -> LLMResult:
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=self.timeout_seconds)
        try:
            response = await client.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    "stream": False,
                    "format": json_schema or "json",
                    "think": False,
                    "options": {"temperature": 0, "num_predict": 450, "num_ctx": 4096},
                },
            )
            response.raise_for_status()
            payload = response.json()
            message = payload.get("message") if isinstance(payload, dict) else None
            content = message.get("content") if isinstance(message, dict) else None
            if not isinstance(content, str) or not content.strip():
                raise LLMError("Ollama returned no message content")
            return LLMResult(
                text=content,
                model=str(payload.get("model") or self.model),
                input_tokens=_optional_int(payload.get("prompt_eval_count")),
                output_tokens=_optional_int(payload.get("eval_count")),
            )
        except LLMError:
            raise
        except (httpx.HTTPError, ValueError, TypeError) as exc:
            detail = str(exc).strip() or type(exc).__name__
            raise LLMError(f"Ollama request failed: {detail}") from exc
        finally:
            if owns_client:
                await client.aclose()

    async def is_available(self) -> bool:
        owns_client = self._http_client is None
        client = self._http_client or httpx.AsyncClient(timeout=5.0)
        try:
            response = await client.get(f"{self.base_url}/api/tags")
            response.raise_for_status()
            payload = response.json()
            models = payload.get("models", []) if isinstance(payload, dict) else []
            return any(
                isinstance(item, dict) and item.get("name") == self.model
                for item in models
            )
        except (httpx.HTTPError, ValueError, TypeError):
            return False
        finally:
            if owns_client:
                await client.aclose()


def _optional_int(value: object) -> int | None:
    return value if isinstance(value, int) and not isinstance(value, bool) else None
