# Architecture

```text
User input
   |
   v
Claim Miner
   |
   v
Source Tracer
   |
   v
Resolved source / primary evidence
   |                         |
   v                         v
Evidence Agent          Skeptic Agent
   |                         |
   +-----------+-------------+
               |
               v
           Judge Agent
               |
               v
        Evidence Report
               |
               v
      Citation Lineage Graph
```

## Design rules

- Each agent has a distinct contract and structured output.
- External source retrieval is separated from agent reasoning.
- Evidence provenance survives the full pipeline.
- Missing evidence produces explicit failure states rather than invented content.
- Agent execution should eventually be observable in the UI.
- Cache metadata, parsed documents, and safe reusable results to improve demo reliability and cost.
