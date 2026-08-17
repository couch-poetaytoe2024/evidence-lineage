import asyncio

from backend.models.schemas import Claim, ClaimType, EvidenceItem, RetrievalStatus
from backend.orchestration.paper_investigation import investigate_paper, select_analysis_evidence, select_target_claim
from backend.services.llm import LLMResult
from backend.services.openalex import OpenAlexNotFoundError
from backend.services.openalex import normalize_paper_identifier


def _index(text: str) -> dict[str, list[int]]:
    result: dict[str, list[int]] = {}
    for position, word in enumerate(text.split()):
        result.setdefault(word, []).append(position)
    return result


def test_normalizes_supported_paper_links() -> None:
    assert normalize_paper_identifier("https://doi.org/10.1000/ABC") == "10.1000/ABC"
    assert normalize_paper_identifier("https://openalex.org/W123") == "W123"
    assert normalize_paper_identifier("https://pubmed.ncbi.nlm.nih.gov/123456/") == "pmid:123456"
    assert normalize_paper_identifier("https://arxiv.org/abs/1706.03762") == "arXiv:1706.03762"


def test_selects_central_contribution_over_background_claim() -> None:
    claims = [
        Claim(id="claim_001", text="Optical security plays an increasingly important role.", importance="high"),
        Claim(
            id="claim_002",
            text="We propose a high-security optical encryption scheme with expanded degrees of freedom.",
            claim_type=ClaimType.METHODOLOGICAL,
            importance="high",
        ),
    ]
    assert select_target_claim(claims).id == "claim_002"


class FakeOpenAlex:
    async def resolve_work(self, identifier: str) -> dict[str, object]:
        return {
            "id": "https://openalex.org/W1",
            "display_name": "Later paper",
            "publication_year": 2026,
            "ids": {"doi": "https://doi.org/10.1000/later"},
            "abstract_inverted_index": _index(
                "The intervention improved accuracy by 40% compared with baseline [12]."
            ),
            "referenced_works": ["https://openalex.org/W2"],
        }

    async def get_works(self, ids: list[str]) -> list[dict[str, object]]:
        assert ids == ["https://openalex.org/W2"]
        return [{
            "id": "https://openalex.org/W2",
            "display_name": "Primary experiment",
            "publication_year": 2020,
            "ids": {"doi": "https://doi.org/10.1000/primary"},
            "abstract_inverted_index": _index(
                "Under condition Y, the intervention improved accuracy by 12%."
            ),
        }]


class SequentialLLM:
    async def generate(self, *, system_prompt: str, user_prompt: str, json_schema: dict[str, object] | None = None) -> LLMResult:
        if "Claim Miner" in system_prompt:
            text = '{"claims":[{"claim":"The intervention improved accuracy by 40% compared with baseline.","citation":"12","claim_type":"quantitative","importance":"high"}]}'
        elif "Evidence Agent" in system_prompt:
            text = '{"conclusion":"The source reports an improvement, but only 12% under condition Y.","evidence_ids":["evidence_001"],"caveats":["Magnitude and conditions differ."]}'
        elif "Skeptic Agent" in system_prompt:
            text = '{"conclusion":"The 40% claim exceeds the retrieved 12% result and omits condition Y.","evidence_ids":["evidence_001"],"caveats":["Only an abstract was retrieved."]}'
        else:
            text = '{"verdict":"OVERSTATED","confidence":0.9,"support_score":20,"lineage_score":35,"reason":"The retrieved source reports 12% under condition Y, not a general 40%.","supporting_evidence":[],"contradicting_evidence":["evidence_001"],"limitations":["Abstract evidence only."]}'
        return LLMResult(text=text, model="fake", input_tokens=10, output_tokens=5)


def test_autonomous_paper_investigation_builds_chain_and_evidence() -> None:
    result = asyncio.run(
        investigate_paper("10.1000/later", openalex=FakeOpenAlex(), llm=SequentialLLM())
    )

    assert result.status == RetrievalStatus.RETRIEVED
    assert result.source_paper is not None
    assert result.claims[0].citation == "12"
    assert result.citation_chain[0].citing_paper_id == "W1"
    assert result.citation_chain[0].cited_paper_id == "W2"
    assert result.citation_chain[0].association_verified is False
    assert result.evidence[0].source_paper_id == "W2"
    assert result.support_arguments[0].evidence_ids == ["evidence_001"]
    assert result.skeptic_arguments[0].evidence_ids == ["evidence_001"]
    assert result.verdicts[0].verdict == "OVERSTATED"
    assert result.verdicts[0].support_score == 20
    assert result.verdicts[0].lineage_score == 35
    assert len(result.model_usage) == 4


def test_investigation_emits_real_phase_transitions() -> None:
    events = []

    async def capture(event) -> None:
        events.append((event.agent, event.status))

    result = asyncio.run(investigate_paper(
        "10.1000/later",
        openalex=FakeOpenAlex(),
        llm=SequentialLLM(),
        on_event=capture,
    ))
    assert result.verdicts
    assert ("source_tracer", "RUNNING") in events
    assert ("claim_miner", "RUNNING") in events
    assert ("evidence_agent", "RUNNING") in events
    assert ("skeptic_agent", "RUNNING") in events
    assert ("judge_agent", "RUNNING") in events
    assert events[-1] == ("judge_agent", "DONE")


def test_user_claim_is_audited_against_cited_paper() -> None:
    claim = "The intervention improves accuracy by 40% in all conditions [12]."
    result = asyncio.run(investigate_paper(
        "10.1000/later",
        openalex=FakeOpenAlex(),
        llm=SequentialLLM(),
        claim_text=claim,
    ))

    assert "40%" in result.claims[0].text
    assert result.evidence[0].id == "evidence_cited_paper"
    assert result.evidence[0].source_paper_id == "W1"
    assert result.evidence[0].used_by_agents is True
    assert "supplied by the user" in " ".join(result.limitations)


def test_analysis_evidence_prioritizes_direct_cited_paper_and_limits_size() -> None:
    claim = Claim(id="c1", text="Optical encryption increases information capacity")
    evidence = [
        EvidenceItem(id="upstream", source_paper_id="W2", passage="unrelated " * 1000),
        EvidenceItem(
            id="direct",
            source_paper_id="W1",
            passage="Optical encryption increases information capacity. " * 100,
            evidence_role="direct_cited_paper",
        ),
    ]
    selected = select_analysis_evidence(claim, evidence, limit=1)
    assert selected[0].id == "direct"
    assert len(selected[0].passage) <= 1800


def test_analysis_uses_distinct_upstream_sources() -> None:
    claim = Claim(id="c1", text="Optical encryption information security")
    evidence = [
        EvidenceItem(id="direct", source_paper_id="W1", passage="Optical encryption", evidence_role="direct_cited_paper"),
        EvidenceItem(id="up1", source_paper_id="W2", passage="Information security method one"),
        EvidenceItem(id="up2", source_paper_id="W3", passage="Information security method two"),
        EvidenceItem(id="up3", source_paper_id="W4", passage="Unrelated"),
    ]
    selected = select_analysis_evidence(claim, evidence)
    assert [item.source_paper_id for item in selected] == ["W1", "W2", "W3"]


class MissingOpenAlex:
    async def resolve_work(self, identifier: str) -> dict[str, object]:
        raise OpenAlexNotFoundError(identifier)


def test_missing_paper_fails_without_fabricating_sources() -> None:
    result = asyncio.run(
        investigate_paper("missing", openalex=MissingOpenAlex(), llm=None)
    )

    assert result.status == RetrievalStatus.SOURCE_UNAVAILABLE
    assert result.source_paper is None
    assert result.papers == []
    assert result.evidence == []
