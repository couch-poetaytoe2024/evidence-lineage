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


class SourceResolutionStatus(StrEnum):
    RESOLVED = "RESOLVED"
    CITATION_UNRESOLVED = "CITATION_UNRESOLVED"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


class RetrievalStatus(StrEnum):
    RETRIEVED = "RETRIEVED"
    PARTIAL = "PARTIAL"
    SOURCE_UNAVAILABLE = "SOURCE_UNAVAILABLE"


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
    authors: list[str] = Field(default_factory=list)
    abstract: str | None = None
    open_access_url: str | None = None


class SourceResolutionRequest(BaseModel):
    doi: str = Field(min_length=1)


class SourceResolution(BaseModel):
    status: SourceResolutionStatus
    paper: Paper | None = None
    provider: str = "crossref"
    reason: str | None = None


class EvidenceItem(BaseModel):
    id: str = ""
    source_paper_id: str
    passage: str
    locator: str | None = None
    supports_claim: bool | None = None
    evidence_role: str = "upstream_reference"
    used_by_agents: bool = False


class CitationEdge(BaseModel):
    citing_paper_id: str
    cited_paper_id: str
    relation: str = "cites"
    claim_id: str | None = None
    association_verified: bool = False


class ExecutionEvent(BaseModel):
    agent: str
    status: str
    detail: str
    duration_ms: int | None = None


class PaperInvestigationRequest(BaseModel):
    identifier: str = Field(min_length=1)
    claim_text: str | None = Field(default=None, min_length=1)
    max_references: int = Field(default=4, ge=1, le=25)
    use_llm: bool = True


class ResearchCase(BaseModel):
    status: RetrievalStatus
    source_paper: Paper | None = None
    claims: list[Claim] = Field(default_factory=list)
    papers: list[Paper] = Field(default_factory=list)
    citation_chain: list[CitationEdge] = Field(default_factory=list)
    evidence: list[EvidenceItem] = Field(default_factory=list)
    support_arguments: list[AgentArgument] = Field(default_factory=list)
    skeptic_arguments: list[AgentArgument] = Field(default_factory=list)
    verdicts: list[Verdict] = Field(default_factory=list)
    execution_trace: list[ExecutionEvent] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    model_usage: list[ModelUsage] = Field(default_factory=list)


class AgentArgument(BaseModel):
    agent: str
    conclusion: str
    evidence_ids: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)


class Verdict(BaseModel):
    verdict: VerdictType
    confidence: float = Field(ge=0, le=1)
    support_score: int | None = Field(default=None, ge=0, le=100)
    lineage_score: int | None = Field(default=None, ge=0, le=100)
    reason: str
    supporting_evidence: list[str] = Field(default_factory=list)
    contradicting_evidence: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ClaimExtractionRequest(BaseModel):
    text: str = Field(min_length=1)
    use_llm: bool = True


class ModelUsage(BaseModel):
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None


class ClaimExtractionResponse(BaseModel):
    claims: list[Claim]
    method: str = "heuristic"
    warning: str | None = None
    usage: ModelUsage | None = None


class HealthResponse(BaseModel):
    status: str
    llm_provider: str
    llm_model: str | None = None
    llm_available: bool
