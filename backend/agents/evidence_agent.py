"""Evidence Agent: build a support case using only retrieved passages."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from backend.models.schemas import AgentArgument, Claim, EvidenceItem, ModelUsage
from backend.services.llm import LLMClient, LLMError


class EvidenceAgentResult(BaseModel):
    argument: AgentArgument | None = None
    usage: ModelUsage | None = None
    warning: str | None = None


class _ArgumentOutput(BaseModel):
    conclusion: str = Field(min_length=1, max_length=700)
    evidence_ids: list[str] = Field(default_factory=list, max_length=3)
    caveats: list[str] = Field(default_factory=list, max_length=3)


_PROMPT = """You are EvidenceLineage's Evidence Agent. Build the strongest legitimate case
that the target claim is supported, using ONLY the supplied evidence passages. Cite evidence
IDs. Do not invent facts. If passages are inadequate, say so plainly. Keep the conclusion
under 100 words and each caveat under 25 words. Return only JSON:
{"conclusion":"...","evidence_ids":["evidence_001"],"caveats":["..."]}."""


async def build_support_argument(
    claim: Claim, evidence: list[EvidenceItem], client: LLMClient | None
) -> EvidenceAgentResult:
    if not evidence:
        return EvidenceAgentResult(warning="No retrievable evidence passages were available.")
    if client is None:
        return EvidenceAgentResult(warning="No language model is configured for Evidence Agent analysis.")
    allowed_ids = {item.id for item in evidence}
    prompt = json.dumps(
        {
            "claim": claim.text,
            "evidence": [item.model_dump() for item in evidence],
        },
        ensure_ascii=False,
    )
    try:
        result = await client.generate(
            system_prompt=_PROMPT,
            user_prompt=prompt,
            json_schema=_ArgumentOutput.model_json_schema(),
        )
        parsed = _ArgumentOutput.model_validate_json(result.text)
        valid_ids = [item for item in parsed.evidence_ids if item in allowed_ids]
        invalid = sorted(set(parsed.evidence_ids) - allowed_ids)
        caveats = list(parsed.caveats)
        if invalid:
            caveats.append("The model referenced unknown evidence IDs; those references were removed.")
        return EvidenceAgentResult(
            argument=AgentArgument(
                agent="evidence_agent",
                conclusion=parsed.conclusion,
                evidence_ids=valid_ids,
                caveats=caveats,
            ),
            usage=ModelUsage(
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            ),
        )
    except (LLMError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        return EvidenceAgentResult(warning=_failure_message("Evidence Agent", exc))


def _failure_message(agent: str, exc: Exception) -> str:
    if isinstance(exc, ValidationError):
        message = exc.errors()[0].get("msg", "invalid structured output")
        return f"{agent} returned invalid structured output: {message}."
    return f"{agent} failed safely: {type(exc).__name__}: {exc}"
