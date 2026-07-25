# LAB-01 Canonical Research Foundation v1

Status: `FOUNDATION_COMPLETE`, product UI: `NOT_STARTED`.

Mingli Lab now consumes the same `Case`, `CanonicalScene`, `NodeRef`,
`RelationAssertion`, `PathAssertion`, and `ProvenanceRecord` used by the formal
product chain. It does not own chart facts, formal cognition, relations, or paths.

```text
LifeCase
  -> CanonicalSceneSource
  -> research-role CanonicalProjectionEnvelope
  -> MingliLabStudy
       |- disclosed formal assertions (read only)
       |- isolated candidate revisions
       |- competing path comparisons
       |- positive / negative / boundary evidence
       `- risk-gate proposal (never direct promotion)
```

The foundation supports relation inspection, candidate interpretation, competing
path comparison, synthetic cases, counterexample review, and algorithm-change
validation. A synthetic case still requires a fixture reference and a canonical
scene identity; it cannot bypass the product authority chain.

Hard boundaries:

- Only research disclosure can open a full Lab study.
- Hidden assertions are absent rather than visually concealed.
- Candidate revisions require candidate lifecycle and graph-candidate provenance.
- Candidate and formal assertions cannot share an assertion identity.
- Lab comparisons can reference only disclosed formal paths or local candidates.
- Evidence can produce `ready_for_risk_gate`, never `committed`.
- Lab contracts declare and enforce no Chart or LifeCase writes.

LAB-01 establishes the research workflow contract only. The final Lab UI,
relation semantics, automatic repair, and formal promotion executor remain outside
this slice.
