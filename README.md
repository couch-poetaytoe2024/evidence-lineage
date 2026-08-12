# EvidenceLineage

**EvidenceLineage** is a multi-agent scientific claim auditor that traces claims backward through citations and checks whether the original evidence actually supports what later papers say.

## Why this exists

A citation can be real while the claim attached to it has drifted. EvidenceLineage focuses on the evidence chain itself: what the primary source reported, how later papers paraphrased it, and whether a later claim became overstated, unsupported, or contradicted.

## Planned agent workflow

1. **Claim Miner** — extracts verifiable claims and attached citations.
2. **Source Tracer** — resolves papers and follows citation chains toward primary evidence.
3. **Evidence Agent** — builds the strongest evidence-based case that a claim is supported.
4. **Skeptic Agent** — independently looks for mismatches, overstatement, changed conditions, or contradictory evidence.
5. **Judge Agent** — compares both sides and produces an auditable verdict.

Target verdicts: `SUPPORTED`, `PARTIALLY_SUPPORTED`, `OVERSTATED`, `CONTRADICTED`, `UNSUPPORTED`, `INSUFFICIENT_EVIDENCE`.

## Current status

Hackathon scaffold is in place. The first implementation target is the **Claim Miner MVP**.

See:

- `AGENTS.md` for persistent Codex/AI instructions
- `docs/PROJECT_SPEC.md` for the product source of truth
- `docs/PROJECT_STATUS.md` for current progress
- `docs/HACKATHON_RULES.md` for the working competition rules

## Local setup

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn backend.main:app --reload
```

Run tests:

```bash
pytest
```

## Hackathon focus

The system is deliberately not a generic research chatbot. The submission should demonstrate genuine multi-agent collaboration, traceable evidence, failure handling, a reliable real-world demo case, and practical cost tracking.
