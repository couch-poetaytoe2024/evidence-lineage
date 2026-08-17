"""Independent adversarial inspection of retrieved evidence."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field, ValidationError

from backend.models.schemas import AgentArgument, Claim, EvidenceItem, ModelUsage
from backend.services.llm import LLMClient, LLMError


class SkepticAgentResult(BaseModel):
    argument: AgentArgument | None = None
    usage: ModelUsage | None = None
    warning: str | None = None


class _Output(BaseModel):
    conclusion: str = Field(min_length=1, max_length=700)
    evidence_ids: list[str] = Field(default_factory=list, max_length=3)
    caveats: list[str] = Field(default_factory=list, max_length=3)


_PROMPT = """You are EvidenceLineage's independent Skeptic Agent. Inspect the claim and
underlying passages yourself. Find numerical mismatches, changed conditions or populations,
correlation stated as causation, overgeneralization, missing evidence, or contradictions.
Never invent evidence and cite only supplied evidence IDs. Keep the conclusion under 100
words and each caveat under 25 words. Return JSON only:
{"conclusion":"...","evidence_ids":["evidence_001"],"caveats":["..."]}."""


async def build_skeptic_argument(claim: Claim, evidence: list[EvidenceItem], client: LLMClient | None) -> SkepticAgentResult:
    if not evidence:
        return SkepticAgentResult(warning="No retrievable evidence passages were available.")
    if client is None:
        return SkepticAgentResult(warning="No language model is configured for Skeptic Agent analysis.")
    allowed_ids = {item.id for item in evidence}
    prompt = json.dumps({"claim": claim.text, "evidence": [item.model_dump() for item in evidence]}, ensure_ascii=False)
    try:
        result = await client.generate(
            system_prompt=_PROMPT,
            user_prompt=prompt,
            json_schema=_Output.model_json_schema(),
        )
        parsed = _Output.model_validate_json(result.text)
        valid_ids = [item for item in parsed.evidence_ids if item in allowed_ids]
        caveats = list(parsed.caveats)
        if set(parsed.evidence_ids) - allowed_ids:
            caveats.append("The model referenced unknown evidence IDs; those references were removed.")
        return SkepticAgentResult(
            argument=AgentArgument(
                agent="skeptic_agent",
                conclusion=parsed.conclusion,
                evidence_ids=valid_ids,
                caveats=caveats,
            ),
            usage=ModelUsage(model=result.model, input_tokens=result.input_tokens, output_tokens=result.output_tokens),
        )
    except (LLMError, ValidationError, ValueError, json.JSONDecodeError) as exc:
        if isinstance(exc, ValidationError):
            message = exc.errors()[0].get("msg", "invalid structured output")
            return SkepticAgentResult(warning=f"Skeptic Agent returned invalid structured output: {message}.")
        return SkepticAgentResult(warning=f"Skeptic Agent failed safely: {type(exc).__name__}: {exc}")
