import asyncio

from backend.agents.judge_agent import judge_claim
from backend.models.schemas import AgentArgument, Claim, EvidenceItem
from backend.services.llm import LLMResult


class InvalidJudge:
    async def generate(self, *, system_prompt: str, user_prompt: str, json_schema: dict[str, object] | None = None) -> LLMResult:
        return LLMResult(
            text='{"verdict":"SUPPORTED","confidence":1,"support_score":100,"lineage_score":50,"reason":"Claimed proof",'
            '"supporting_evidence":["invented"],"contradicting_evidence":[],"limitations":[]}',
            model="fake",
        )


def test_judge_removes_invented_evidence_id() -> None:
    argument = AgentArgument(agent="evidence_agent", conclusion="Maybe", evidence_ids=["e1"])
    result = asyncio.run(judge_claim(
        Claim(id="c1", text="Claim"),
        [EvidenceItem(id="e1", source_paper_id="W1", passage="Passage")],
        argument,
        AgentArgument(agent="skeptic_agent", conclusion="Challenge", evidence_ids=["e1"]),
        InvalidJudge(),
    ))
    assert result.verdict is not None
    assert result.verdict.supporting_evidence == []
    assert result.verdict.limitations
