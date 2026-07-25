# V50 Runtime Module Authority Map v1

## Frozen decision

V50 has one whole-chart cognitive authority: `core.mingli_agent`, with an LLM as the cognitive reasoner. Deterministic modules provide facts, structural observations, tools, memory, and review constraints. They do not issue the final Mingli judgment.

## Production chain

```text
Birth input
→ Bazi / Ziwei fact engines
→ Graph / Path / Role / Ablation observations
→ Mingli World Instance
→ Context Compiler
→ LLM Cognitive Reasoner
→ Epistemic Review
→ Case Memory / Probe / Deliberation
→ Abu and role-aware product surfaces
```

## Authority classes

| Class | Modules | Authority |
|---|---|---|
| Fact authority | `core.contracts`, `core.engines` | Calendar, pillars, ten gods, relations, Ziwei plate facts |
| Structural tools | `core.graph`, `core.simulation` | Candidate paths, roles, salience observations, ablation deltas |
| Cognitive authority | `core.mingli_agent` | Whole-chart pattern, competing hypotheses, work path, domain reasoning |
| Interaction and memory | `core.abu_runtime`, `product` | Commands, cases, workspaces, role permissions, persistence |
| Research-only | `core.mechanism`, `core.state`, `core.timing` | Experiments and validation artifacts; no production judgment authority |
| Retired | deterministic Brain, template Product Projection, Alpha runtime | Must not return to the public reading chain |

## Non-negotiable boundaries

1. Synthetic expected contracts stay outside the model context.
2. Research modules may be promoted only through an explicit reviewed slice.
3. Product projections may omit or rephrase, but may not invent claims.
4. Probe feedback updates the current case belief state, not natal facts or global theory.
5. A module becoming importable does not make it production-authoritative.

The executable source of truth is `config/production_authority_manifest_v1.json`; `scripts/v50_audit_runtime_authority.py` enforces the current production boundary.
