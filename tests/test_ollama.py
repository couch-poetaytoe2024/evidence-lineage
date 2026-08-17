import asyncio

import httpx

from backend.services.ollama import OllamaClient


def test_ollama_generate_maps_content_and_usage() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        body = request.read().decode()
        assert '"format":"json"' in body
        assert '"think":false' in body
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "message": {"role": "assistant", "content": '{"claims":[]}'},
                "prompt_eval_count": 42,
                "eval_count": 9,
            },
        )

    async def scenario() -> object:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as http_client:
            client = OllamaClient(http_client=http_client)
            return await client.generate(system_prompt="system", user_prompt="text")

    result = asyncio.run(scenario())
    assert result.text == '{"claims":[]}'
    assert result.input_tokens == 42
    assert result.output_tokens == 9


def test_ollama_availability_requires_configured_model() -> None:
    transport = httpx.MockTransport(
        lambda request: httpx.Response(200, json={"models": [{"name": "qwen3:4b"}]})
    )

    async def scenario() -> bool:
        async with httpx.AsyncClient(transport=transport) as http_client:
            return await OllamaClient(http_client=http_client).is_available()

    assert asyncio.run(scenario()) is True
