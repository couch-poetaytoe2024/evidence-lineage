# Project Status

## Current milestone

Evidence retrieval and Evidence Agent MVP

## Working

- Public GitHub repository exists on `main`.
- Persistent AI/Codex instructions defined in `AGENTS.md`.
- Core project specification and hackathon constraints documented.
- FastAPI skeleton includes `/health` and `/claims` endpoints.
- Shared Pydantic claim/evidence/verdict models started.
- Deterministic Claim Miner baseline extracts sentence-level candidate claims, simple citation markers, and coarse claim types.
- Claim Miner unit tests added.
- Provider-neutral async `LLMClient` contract implemented with model/token usage metadata.
- Structured LLM Claim Miner path validates model JSON through Pydantic.
- Invalid model output and expected provider failures use an observable deterministic fallback.
- Claim extraction responses expose method, fallback warning, and model usage provenance.
- Source Tracer normalizes and validates DOI inputs.
- Crossref integration resolves DOI metadata into a typed `Paper`.
- Source resolution distinguishes `RESOLVED`, `CITATION_UNRESOLVED`, and `SOURCE_UNAVAILABLE`.
- `/sources/resolve-doi` endpoint added.
- Claim Miner and Source Tracer have deterministic tests, including malformed output, missing DOI, and network failure.
- Local Ollama provider is configured through the provider-neutral interface.
- `qwen3:4b` structured Claim Miner completed a live test with model/token provenance.
- `/health` reports the configured LLM provider, model, and availability.
- `.env.example` documents Ollama and optional research API settings.
- `/investigations/paper` accepts a DOI, OpenAlex ID, title, or supported scholarly link and starts an autonomous investigation.
- DOI, OpenAlex, PubMed, and arXiv paper URLs are normalized automatically.
- Target-claim ranking prioritizes central contributions/results over generic abstract background.
- Agent panels expose safe failure details instead of rendering blank when a model call fails.
- Unknown model-generated evidence IDs are removed and disclosed without discarding an otherwise valid argument.
- Researchers can paste their own claim/paragraph and identify the paper being cited.
- User-claim mode treats the cited paper's available abstract as direct evidence while preserving its reference lineage.
- Judge verdicts include a 0–100 claim-support score in addition to the categorical verdict and qualitative confidence.
- Judge verdicts separately score direct claim support and the cited paper's upstream reference support.
- Evidence is labeled as direct cited-paper material or upstream reference material.
- Agent analysis ranks and truncates the three most relevant passages to prevent local-model context overflow.
- User-claim analysis includes one direct cited-paper source plus two distinct upstream references when available.
- The UI maps OpenAlex work IDs to paper titles/DOIs and marks exactly which retrieved sources agents used.
- Ollama failures include their concrete exception type, and Judge workflow fallbacks are no longer labeled as successful adjudications.
- Ollama now receives agent-specific JSON Schemas and bounded response fields to prevent truncated/invalid JSON.
- Workflow errors remain in agent cards/execution trace instead of being mixed with scientific evidence limitations.
- OpenAlex integration resolves papers, reconstructs indexed abstracts, and discovers referenced works.
- Typed `ResearchCase`, `CitationEdge`, `EvidenceItem`, and `ExecutionEvent` shared state added.
- Reference abstracts become provenance-linked evidence leads without claiming they are full-text proof.
- Evidence Agent builds an argument using only retrieved evidence IDs and rejects invented IDs.
- Skeptic Agent independently inspects the same retrieved passages for drift and contradictions.
- Judge Agent validates both arguments and returns an evidence-ID-grounded verdict.
- Evidence and Skeptic calls run independently and sequentially for reliability on 16 GB shared-memory hardware.
- Minimal web interface displays the claim, debate, verdict, evidence, lineage, trace, and limitations.
- End-to-end tests cover automatic claim mining, reference traversal, evidence retrieval, and agent output.
- A live DOI test automatically resolved a real paper and two cited works with evidence abstracts.

## In progress

- Retrieve and parse open-access full text so sentence-level citation markers can be mapped to references.
- Expand lineage traversal beyond one bibliographic hop with strict depth/branch limits.

## Not started

- PDF parsing
- Cost tracking
- Citation-lineage graph
- Final demo case

## Known limitations

- Local `qwen3:4b` inference took about 37 seconds on the development machine's 16 GB RAM/Intel Iris Xe hardware; demo calls should use short inputs and caching.
- A four-agent live investigation can take several minutes on this hardware; demo-case caching remains necessary before submission.
- Model selection remains subject to final hackathon policy confirmation; the provider-neutral fallback is preserved.
- Citation extraction only handles basic numeric brackets and simple author-year forms.
- Automated retrieval currently uses OpenAlex abstracts; many papers lack abstracts or accessible full text.
- Bibliographic reference edges do not prove which cited source supports a particular claim. These remain explicitly unverified until full-text citation contexts are available.
- The current Evidence Agent analyzes the first extracted claim and one-hop reference evidence only.
- The current investigation analyzes one ranked target claim per paper and uses bibliographic reference order until full-text citation contexts are parsed.
- Hackathon model-policy wording is still ambiguous in the supplied event copy.

## Decisions

- Keep EvidenceLineage focused on evidence lineage/citation drift rather than generic research assistance.
- Favor a lightweight inspectable Python orchestrator over a large agent framework for the MVP.
- Evidence and Skeptic agents must independently inspect source evidence.
- Never hallucinate through missing sources; expose failure states instead.

## Next recommended task

Validate the complete UI workflow on the selected real demo case, then add open-access full-text retrieval and citation-context parsing where that case requires it.

## Last updated

2026-08-15
