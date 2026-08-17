import asyncio

from backend.agents.evidence_agent import build_support_argument
from backend.models.schemas import Claim, EvidenceItem
from backend.services.llm import LLMResult


class HallucinatingLLM:
    async def generate(self, *, system_prompt: str, user_prompt: str, json_schema: dict[str, object] | None = None) -> LLMResult:
        return LLMResult(
            text='{"conclusion":"Supported","evidence_ids":["made_up"],"caveats":[]}',
            model="fake",
        )


def test_evidence_agent_removes_unknown_evidence_ids() -> None:
    result = asyncio.run(
        build_support_argument(
            Claim(id="c1", text="A claim"),
            [EvidenceItem(id="evidence_001", source_paper_id="W1", passage="A passage")],
            HallucinatingLLM(),
        )
    )

    assert result.argument is not None
    assert result.argument.evidence_ids == []
    assert result.argument.caveats
