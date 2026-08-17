"""Auditable Claim Miner -> Source Tracer -> Evidence Agent workflow."""

from __future__ import annotations

import time

from backend.agents.claim_miner import mine_claims
from backend.agents.evidence_agent import build_support_argument
from backend.agents.judge_agent import judge_claim
from backend.agents.skeptic_agent import build_skeptic_argument
from backend.models.schemas import (
    CitationEdge,
    EvidenceItem,
    ExecutionEvent,
    Paper,
    ResearchCase,
    RetrievalStatus,
    Claim,
    ClaimType,
)
from backend.services.llm import LLMClient
from backend.services.openalex import OpenAlexClient, OpenAlexError, OpenAlexNotFoundError, reconstruct_abstract


def paper_from_openalex(work: dict[str, object]) -> Paper | None:
    raw_id = work.get("id")
    title = work.get("display_name") or work.get("title")
    if not isinstance(raw_id, str) or not isinstance(title, str) or not title.strip():
        return None
    ids = work.get("ids") if isinstance(work.get("ids"), dict) else {}
    doi_value = ids.get("doi") if isinstance(ids, dict) else None
    doi = doi_value.removeprefix("https://doi.org/").lower() if isinstance(doi_value, str) else None
    authorships = work.get("authorships")
    authors: list[str] = []
    if isinstance(authorships, list):
        for entry in authorships:
            author = entry.get("author") if isinstance(entry, dict) else None
            name = author.get("display_name") if isinstance(author, dict) else None
            if isinstance(name, str):
                authors.append(name)
    location = work.get("best_oa_location")
    oa_url = location.get("pdf_url") or location.get("landing_page_url") if isinstance(location, dict) else None
    year = work.get("publication_year")
    return Paper(
        id=raw_id.rsplit("/", 1)[-1],
        title=title.strip(),
        doi=doi,
        url=f"https://doi.org/{doi}" if doi else raw_id,
        year=year if isinstance(year, int) else None,
        authors=authors,
        abstract=reconstruct_abstract(work.get("abstract_inverted_index")),
        open_access_url=oa_url if isinstance(oa_url, str) else None,
    )


async def investigate_paper(
    identifier: str,
    *,
    openalex: OpenAlexClient,
    llm: LLMClient | None,
    max_references: int = 8,
    claim_text: str | None = None,
) -> ResearchCase:
    events: list[ExecutionEvent] = []
    started = time.perf_counter()
    try:
        root_work = await openalex.resolve_work(identifier)
    except OpenAlexNotFoundError:
        return ResearchCase(
            status=RetrievalStatus.SOURCE_UNAVAILABLE,
            execution_trace=[ExecutionEvent(agent="source_tracer", status="FAILED", detail="Paper not found.")],
            limitations=["No paper matched the supplied DOI, OpenAlex ID, or title."],
        )
    except OpenAlexError:
        return ResearchCase(
            status=RetrievalStatus.SOURCE_UNAVAILABLE,
            execution_trace=[ExecutionEvent(agent="source_tracer", status="FAILED", detail="OpenAlex unavailable.")],
            limitations=["Paper metadata service was unavailable."],
        )

    root = paper_from_openalex(root_work)
    if root is None:
        return ResearchCase(status=RetrievalStatus.SOURCE_UNAVAILABLE, limitations=["Paper metadata was incomplete."])
    events.append(_event("source_tracer", "DONE", "Resolved input paper metadata.", started))

    claim_source = claim_text.strip() if claim_text and claim_text.strip() else root.abstract or ""
    claims_response = await mine_claims(claim_source, llm)
    source_label = "the user-provided text" if claim_text else "the available paper abstract"
    events.append(ExecutionEvent(agent="claim_miner", status="DONE", detail=f"Extracted {len(claims_response.claims)} claims from {source_label}."))

    reference_ids = root_work.get("referenced_works")
    selected = reference_ids[:max_references] if isinstance(reference_ids, list) else []
    try:
        reference_works = await openalex.get_works([item for item in selected if isinstance(item, str)])
    except OpenAlexError:
        reference_works = []
    references = [paper for item in reference_works if (paper := paper_from_openalex(item)) is not None]
    edges = [
        CitationEdge(citing_paper_id=root.id, cited_paper_id=paper.id)
        for paper in references
    ]
    evidence = [
        EvidenceItem(
            id=f"evidence_{index:03d}",
            source_paper_id=paper.id,
            passage=paper.abstract,
            locator="OpenAlex abstract",
            evidence_role="upstream_reference",
        )
        for index, paper in enumerate(references, start=1)
        if paper.abstract
    ]
    if claim_text and root.abstract:
        evidence.insert(0, EvidenceItem(
            id="evidence_cited_paper",
            source_paper_id=root.id,
            passage=root.abstract,
            locator="Cited paper abstract (OpenAlex)",
            evidence_role="direct_cited_paper",
        ))
    events.append(ExecutionEvent(agent="source_tracer", status="DONE", detail=f"Discovered {len(references)} referenced papers; {len(evidence)} had retrievable abstracts."))

    arguments = []
    skeptic_arguments = []
    verdicts = []
    usages = [claims_response.usage] if claims_response.usage else []
    limitations = [
        "Reference edges were discovered bibliographically; claim-to-reference associations are not verified without full text.",
        "Abstract passages are evidence leads, not substitutes for inspecting full methods, results, and tables.",
    ]
    if root.abstract is None and not claim_text:
        limitations.append("The input paper had no retrievable abstract, so no claims could be mined automatically.")
    if claim_text:
        limitations.append("The cited paper was supplied by the user; the system does not independently verify that it is the citation intended by the pasted paragraph.")
    target_claim = select_target_claim(claims_response.claims)
    if target_claim:
        analysis_evidence = select_analysis_evidence(target_claim, evidence)
        selected_ids = {item.id for item in analysis_evidence}
        evidence = [
            item.model_copy(update={"used_by_agents": item.id in selected_ids})
            for item in evidence
        ]
        # These are independent inspections with separate prompts and outputs. They
        # run sequentially because small local machines cannot reliably host two
        # simultaneous Ollama generations without severe memory contention.
        support = await build_support_argument(target_claim, analysis_evidence, llm)
        skeptic = await build_skeptic_argument(target_claim, analysis_evidence, llm)
        if support.argument:
            arguments.append(support.argument)
        if skeptic.argument:
            skeptic_arguments.append(skeptic.argument)
        if support.usage:
            usages.append(support.usage)
        if skeptic.usage:
            usages.append(skeptic.usage)
        events.append(ExecutionEvent(agent="evidence_agent", status="DONE" if support.argument else "FAILED", detail=support.warning or "Built a source-grounded support argument."))
        events.append(ExecutionEvent(agent="skeptic_agent", status="DONE" if skeptic.argument else "FAILED", detail=skeptic.warning or "Built an independent source-grounded challenge."))
        judged = await judge_claim(
            target_claim, analysis_evidence, support.argument, skeptic.argument, llm
        )
        if judged.verdict:
            verdicts.append(judged.verdict)
        if judged.usage:
            usages.append(judged.usage)
        judge_status = "FALLBACK" if judged.warning and judged.verdict else ("DONE" if judged.verdict else "FAILED")
        events.append(ExecutionEvent(agent="judge_agent", status=judge_status, detail=judged.warning or "Resolved the agent debate into a verdict."))
    else:
        events.append(ExecutionEvent(agent="evidence_agent", status="SKIPPED", detail="No extracted claim was available."))
        events.append(ExecutionEvent(agent="skeptic_agent", status="SKIPPED", detail="No extracted claim was available."))
        events.append(ExecutionEvent(agent="judge_agent", status="SKIPPED", detail="No agent arguments were available."))

    status = RetrievalStatus.RETRIEVED if root.abstract and evidence else RetrievalStatus.PARTIAL
    ordered_claims = (
        [target_claim, *(claim for claim in claims_response.claims if claim.id != target_claim.id)]
        if target_claim
        else []
    )
    return ResearchCase(
        status=status,
        source_paper=root,
        claims=ordered_claims,
        papers=[root, *references],
        citation_chain=edges,
        evidence=evidence,
        support_arguments=arguments,
        skeptic_arguments=skeptic_arguments,
        verdicts=verdicts,
        execution_trace=events,
        limitations=limitations,
        model_usage=usages,
    )


def _event(agent: str, status: str, detail: str, started: float) -> ExecutionEvent:
    return ExecutionEvent(agent=agent, status=status, detail=detail, duration_ms=round((time.perf_counter() - started) * 1000))


def select_target_claim(claims: list[Claim]) -> Claim | None:
    """Prefer a paper's substantive contribution over generic background prose."""
    if not claims:
        return None
    contribution_terms = (
        "we propose", "we present", "we demonstrate", "we develop", "we show",
        "our method", "our approach", "our work", "results", "improved", "increased",
        "reduced", "outperformed", "achieved", "gives rise", "provides",
    )
    background_terms = ("increasingly important", "has been investigated", "plays a role")
    type_weight = {
        ClaimType.QUANTITATIVE: 4,
        ClaimType.CAUSAL: 3,
        ClaimType.COMPARATIVE: 3,
        ClaimType.METHODOLOGICAL: 2,
        ClaimType.GENERAL: 0,
        ClaimType.OTHER: 0,
    }

    def score(item: Claim) -> int:
        lowered = item.text.lower()
        return (
            type_weight[item.claim_type]
            + (4 if item.importance.lower() == "high" else 0)
            + (2 if item.citation else 0)
            + sum(2 for term in contribution_terms if term in lowered)
            - sum(3 for term in background_terms if term in lowered)
        )

    return max(claims, key=score)


def select_analysis_evidence(claim: Claim, evidence: list[EvidenceItem], limit: int = 3) -> list[EvidenceItem]:
    """Fit the most relevant evidence into a small local model context window."""
    claim_terms = {word for word in _terms(claim.text) if len(word) > 3}

    def score(item: EvidenceItem) -> tuple[int, int]:
        overlap = len(claim_terms & set(_terms(item.passage)))
        direct_bonus = 100 if item.evidence_role == "direct_cited_paper" else 0
        return direct_bonus + overlap, -len(item.passage)

    direct = sorted(
        (item for item in evidence if item.evidence_role == "direct_cited_paper"),
        key=score,
        reverse=True,
    )
    upstream = sorted(
        (item for item in evidence if item.evidence_role != "direct_cited_paper"),
        key=score,
        reverse=True,
    )
    selected = [*direct[:1], *upstream[: max(0, limit - min(1, len(direct)))]]
    if not selected:
        selected = sorted(evidence, key=score, reverse=True)[:limit]
    return [item.model_copy(update={"passage": item.passage[:1800]}) for item in selected]


def _terms(text: str) -> list[str]:
    return ["".join(char for char in word.lower() if char.isalnum()) for word in text.split()]
