# V50 RA3 Path Evidence Closeout V1

Status: `CLOSED / PASS`

RA3 replaces public numeric path ranking with one discrete evidence contract.
It does not claim to identify the professionally best path.

## One Owner

```text
Graph candidate relations
→ core.graph.path_qualification
→ PathEvidenceVector
→ Reasoner context / product projection
```

The evidence vector records segment validity, direction, temporal status, root
evidence, blockers, closure and provenance. Candidate ordering is deterministic
for reproducibility and is explicitly not professional ranking.

## Removed From Authority

- top-level path scores and component scores;
- score-based candidate ordering;
- normalized node path contribution;
- score-driven graph roles and node importance;
- path `tool_score` in LLM context and product snapshots.

Legacy numeric fields remain only inside `LegacyUnvalidatedPathMetrics` for
regression compatibility. They cannot enter candidate ordering, professional
context or product projection.

## Time Boundary

Qualified official luck/year relations may produce `reinforced` or `weakened`.
Simultaneous support and restraint preserve the current state with explicit
uncertainty. RA3 does not create, promote, block or rewrite a formal path.

## Verification

```yaml
implementation_commit: e1e8b384
focused_core: 46_passed
validation_suites: 6_passed
full_regression: 570_passed
r1_locked_assets: 20_of_20_ok
architecture_gate: 17_of_17_pass
typescript: strict_pass
frontend_changes: 0
v40_changes: 0
```
