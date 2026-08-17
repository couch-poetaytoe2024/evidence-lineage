"""Claim Miner MVP.

This deterministic implementation is intentionally small and testable. It gives the
project a working baseline before we connect an LLM provider. It extracts sentence-like
claims, detects simple citation markers, and assigns a coarse claim type.
"""

from __future__ import annotations

import re
import json

from pydantic import BaseModel, Field, ValidationError

from backend.models.schemas import Claim, ClaimExtractionResponse, ClaimType, ModelUsage
from backend.services.llm import LLMClient, LLMError

_CITATION_RE = re.compile(r"(?:\[(?P<bracket>\d+(?:\s*,\s*\d+)*)\]|\((?P<author>[A-Z][A-Za-z-]+(?:\s+et\s+al\.)?,?\s+\d{4})\))")
_PERCENT_RE = re.compile(r"\b\d+(?:\.\d+)?\s*%")
_NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
_CAUSAL_WORDS = ("caused", "causes", "led to", "results in", "resulted in", "because of")
_COMPARATIVE_WORDS = ("higher than", "lower than", "more than", "less than", "compared with", "compared to", "outperformed", "improved")


def _sentences(text: str) -> list[str]:
    cleaned = " ".join(text.split())
    if not cleaned:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", cleaned) if part.strip()]


def _claim_type(sentence: str) -> ClaimType:
    lowered = sentence.lower()
    if _PERCENT_RE.search(sentence) or _NUMBER_RE.search(sentence):
        return ClaimType.QUANTITATIVE
    if any(word in lowered for word in _CAUSAL_WORDS):
        return ClaimType.CAUSAL
    if any(word in lowered for word in _COMPARATIVE_WORDS):
        return ClaimType.COMPARATIVE
    return ClaimType.GENERAL


def _citation(sentence: str) -> str | None:
    match = _CITATION_RE.search(sentence)
    if not match:
        return None
    return match.group("bracket") or match.group("author")


def extract_claims(text: str) -> list[Claim]:
    """Extract a lightweight set of candidate scientific claims from text.

    This is a baseline, not the final semantic claim extractor. Future versions can
    replace/augment it with an LLM while retaining the same typed output contract.
    """
    claims: list[Claim] = []
    for index, sentence in enumerate(_sentences(text), start=1):
        # Skip extremely short fragments that are unlikely to be useful claims.
        if len(sentence.split()) < 5:
            continue
        claims.append(
            Claim(
                id=f"claim_{index:03d}",
                text=sentence,
                citation=_citation(sentence),
                claim_type=_claim_type(sentence),
            )
        )
    return claims


class _ExtractedClaim(BaseModel):
    claim: str = Field(min_length=1)
    citation: str | None = None
    claim_type: ClaimType = ClaimType.GENERAL
    importance: str = "medium"


class _ModelOutput(BaseModel):
    claims: list[_ExtractedClaim]


_SYSTEM_PROMPT = """You are the Claim Miner in EvidenceLineage.
Extract only specific, scientifically verifiable claims stated in the supplied text.
Never add facts or citations. Preserve each citation marker's content without brackets.
Prioritize the paper's central contribution, experimental result, quantitative finding, or
demonstrated capability. Do not select generic background or motivation sentences when the
text contains a claim about what the authors proposed, measured, found, or demonstrated.
Make each claim self-contained while preserving its conditions and scope.
Return at most the three most important claims, ordered from most to least important.
Return only JSON with this shape:
{"claims":[{"claim":"...","citation":"12 or Smith et al., 2020 or null","claim_type":"quantitative|causal|comparative|methodological|general|other","importance":"high|medium|low"}]}
If no verifiable claims exist, return {"claims":[]}."""


def _json_object(raw: str) -> dict[str, object]:
    """Decode a JSON object, accepting a common fenced-JSON wrapper."""
    cleaned = raw.strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if len(lines) >= 3 and lines[-1].strip() == "```":
            cleaned = "\n".join(lines[1:-1])
            if cleaned.lstrip().lower().startswith("json\n"):
                cleaned = cleaned.lstrip()[5:]
    value = json.loads(cleaned)
    if not isinstance(value, dict):
        raise ValueError("Claim Miner output must be a JSON object")
    return value


async def mine_claims(
    text: str,
    client: LLMClient | None = None,
    *,
    allow_fallback: bool = True,
) -> ClaimExtractionResponse:
    """Mine structured claims with an LLM or a deterministic safety fallback."""
    if client is None:
        return ClaimExtractionResponse(claims=extract_claims(text))

    try:
        result = await client.generate(
            system_prompt=_SYSTEM_PROMPT,
            user_prompt=text,
            json_schema=_ModelOutput.model_json_schema(),
        )
        parsed = _ModelOutput.model_validate(_json_object(result.text))
        claims = [
            Claim(
                id=f"claim_{index:03d}",
                text=item.claim,
                citation=item.citation,
                claim_type=item.claim_type,
                importance=item.importance,
            )
            for index, item in enumerate(parsed.claims[:3], start=1)
        ]
        return ClaimExtractionResponse(
            claims=claims,
            method="llm",
            usage=ModelUsage(
                model=result.model,
                input_tokens=result.input_tokens,
                output_tokens=result.output_tokens,
            ),
        )
    except (json.JSONDecodeError, ValidationError, ValueError, TypeError, LLMError) as exc:
        if not allow_fallback:
            raise
        return ClaimExtractionResponse(
            claims=extract_claims(text),
            method="heuristic_fallback",
            warning=f"Model output was invalid; deterministic fallback used ({type(exc).__name__}).",
        )
