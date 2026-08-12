from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ClaimType(StrEnum):
    QUANTITATIVE = "quantitative"
    CAUSAL = "causal"
    COMPARATIVE = "comparative"
    METHODOLOGICAL = "methodological"
    GENERAL = "general"
    OTHER = "other"


class VerdictType(StrEnum):
    SUPPORTED = "SUPPORTED"
    PARTIALLY_SUPPORTED = "PARTIALLY_SUPPORTED"
    OVERSTATED = "OVERSTATED"
    CONTRADICTED = "CONTRADICTED"
    UNSUPPORTED = "UNSUPPORTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class Claim(BaseModel):
    id: str
    text: str
    citation: str | None = None
    claim_type: ClaimType = ClaimType.GENERAL
    importance: str = "medium"


class Paper(BaseModel):
    id: str
    title: str
    doi: str | None = None
    url: str | None = None
    year: int | None = None


class EvidenceItem(BaseModel):
    source_paper_id: str
    passage: str
    locator: str | None = None
    supports_claim: bool | None = None


class AgentArgument(BaseModel):
    agent: str
    conclusion: str
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    verdict: VerdictType
    confidence: float = Field(ge=0, le=1)
    reason: str
    limitations: list[str] = Field(default_factory=list)


class ClaimExtractionRequest(BaseModel):
    text: str = Field(min_length=1)


class ClaimExtractionResponse(BaseModel):
    claims: list[Claim]
