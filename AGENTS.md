# EvidenceLineage — Agent Instructions

EvidenceLineage is a multi-agent scientific claim auditor. Its core job is to trace scientific claims backward through citations and determine whether the original evidence actually supports what later papers say.

Before changing code, read:

1. `docs/PROJECT_SPEC.md` — stable product and architecture source of truth.
2. `docs/PROJECT_STATUS.md` — current implementation state and next task.
3. `docs/HACKATHON_RULES.md` — working competition requirements and unresolved rule ambiguities.

## Non-negotiables

- Do not turn this into a generic research chatbot, paper summarizer, or literature-review app.
- Preserve distinct agent responsibilities: Claim Miner, Source Tracer, Evidence Agent, Skeptic Agent, Judge Agent.
- Agents exchange structured state; do not simulate multi-agent collaboration with one long prompt.
- Never fabricate papers, DOIs, quotations, page numbers, results, citation relationships, or evidence.
- Prefer explicit failure states such as `SOURCE_UNAVAILABLE`, `CITATION_UNRESOLVED`, and `INSUFFICIENT_EVIDENCE` over hallucinating through missing data.
- Keep external model access behind a small provider abstraction so the project can adapt if hackathon model rules are clarified.
- Optimize for demo reliability, auditability, research utility, genuine collaboration, and cost efficiency.
- Read existing code before modifying it. Do not overwrite unrelated human work.
- Add or update tests for meaningful behavior.
- After meaningful implementation changes, update `docs/PROJECT_STATUS.md`.

## Current priority

Complete P0 in this order:

claim extraction → source resolution → evidence retrieval → Evidence/Skeptic independent analysis → Judge verdict → one reliable end-to-end real research case.
