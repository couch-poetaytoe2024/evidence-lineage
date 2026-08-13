# Synthetic Citation-Drift Benchmark

This folder is a deliberately fictional mini-literature created only for testing EvidenceLineage. None of the papers, authors, identifiers, or experimental results are real.

Use this case to test:

- claim extraction
- local citation resolution
- citation-chain traversal
- numerical drift
- certainty inflation
- review-to-primary tracing
- contradictory evidence
- citation bias / ignored evidence
- dead-end citations
- Evidence Agent vs Skeptic Agent disagreement
- Judge verdicts

## Intended chain

`paper_a_primary.md` -> `paper_b_review.md` -> `paper_c_followup.md` -> `paper_d_application.md`

A separate larger replication, `paper_e_replication.md`, directly tests the original claim but is ignored by Papers C and D.

## Ground truth in one line

A small exploratory battery experiment finds a modest +6 percentage-point capacity-retention difference with high uncertainty; later papers turn that into a roughly 20-30% battery-life improvement and then an established general effect, while ignoring a larger null replication.

See `ground_truth.json` for machine-readable expected labels.
