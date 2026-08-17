import asyncio

import pytest

from backend.agents.claim_miner import extract_claims, mine_claims
from backend.models.schemas import ClaimType
from backend.services.llm import LLMError, LLMResult


def test_extracts_quantitative_claim_and_citation() -> None:
    text = "Our approach increased classification accuracy by 40% compared with the baseline [12]."
    claims = extract_claims(text)

    assert len(claims) == 1
    assert claims[0].citation == "12"
    assert claims[0].claim_type == ClaimType.QUANTITATIVE
    assert "40%" in claims[0].text


def test_empty_text_returns_no_claims() -> None:
    assert extract_claims("   ") == []


def test_short_fragment_is_ignored() -> None:
    assert extract_claims("Results were good.") == []


class FakeLLM:
    def __init__(self, text: str) -> None:
        self.text = text

    async def generate(self, *, system_prompt: str, user_prompt: str, json_schema: dict[str, object] | None = None) -> LLMResult:
        assert "Never add facts" in system_prompt
        assert user_prompt
        return LLMResult(self.text, "fake-model", 20, 10)


class FailingLLM:
    async def generate(self, *, system_prompt: str, user_prompt: str, json_schema: dict[str, object] | None = None) -> LLMResult:
        raise LLMError("provider unavailable")


def test_structured_llm_claims_include_usage() -> None:
    client = FakeLLM(
        '{"claims":[{"claim":"Accuracy increased by 40%.",'
        '"citation":"12","claim_type":"quantitative","importance":"high"}]}'
    )
    result = asyncio.run(mine_claims("Accuracy increased by 40% [12].", client))

    assert result.method == "llm"
    assert result.claims[0].id == "claim_001"
    assert result.claims[0].citation == "12"
    assert result.usage is not None
    assert result.usage.input_tokens == 20


def test_malformed_model_output_uses_deterministic_fallback() -> None:
    result = asyncio.run(
        mine_claims(
            "Accuracy increased by 40% compared with baseline [12].",
            FakeLLM("not json"),
        )
    )

    assert result.method == "heuristic_fallback"
    assert result.warning is not None
    assert len(result.claims) == 1


def test_malformed_output_can_fail_closed() -> None:
    with pytest.raises(ValueError):
        asyncio.run(mine_claims("A sufficiently long scientific claim here.", FakeLLM("[]"), allow_fallback=False))


def test_provider_failure_uses_deterministic_fallback() -> None:
    result = asyncio.run(
        mine_claims("Accuracy increased by 40% compared with baseline [12].", FailingLLM())
    )

    assert result.method == "heuristic_fallback"
    assert result.warning is not None
    assert "LLMError" in result.warning
