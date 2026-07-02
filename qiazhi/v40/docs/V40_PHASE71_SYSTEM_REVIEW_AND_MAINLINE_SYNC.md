# V40 Phase 71 System Review And Mainline Sync

## Current Review

V40 is now a mostly complete isolated runtime:

- V30 and V40 directories remain separated.
- V40 has independent contracts, runtime, API, admin/control evidence, storage prefixes and tests.
- Bazi remains the primary engine.
- Ziwei remains a sidecar Domain Lens.
- LLM is required for product expression, but never verdict authority.
- DecisionEngine remains the only verdict authority.
- Training applies immediately after validated batch training, with rollback and evidence views.
- Real case acceptance is the remaining product-quality bottleneck.

## Completed Mainline Spine

```text
Phase 63: Real Case Bank / Acceptance Window
Phase 64: Bazi Fact Engine Pro
Phase 65: V30 Mingli Asset Migration Gate
Phase 66: Domain Verdict Adapters
Phase 67: Hidden Factor Probe Engine
Phase 68: Knowledge / Portrait / Ziwei Sidecar Enrichment
Phase 69: Real Case Expansion And Cutover Evidence
Phase 70: Direct Training Activation Evidence
Phase 71: Online Cutover Decision Pack
```

## System Strengths

- Evidence and decision layers are now separated.
- Probe and conversation no longer have to pollute the report flow.
- Hidden factors are trainable through `probe_voi` and reality-probe signals.
- Knowledge cards are explanation-only.
- Portrait signals are low-weight candidates.
- Ziwei is visible to practitioner lens without becoming a co-equal verdict engine.
- Training is high-iteration by design and still rollbackable.

## Remaining Gaps

The remaining work is no longer mostly architecture. It is evidence quality:

1. collect enough high-quality real cases;
2. run acceptance windows by domain;
3. inspect LLM expression quality with real reports;
4. run beta cutover smoke against real repository state;
5. let the owner approve the final online window.

## Next Mainline

```text
UI-17: online cutover decision with real case acceptance evidence
USER-18: final real case quality signoff and beta cutover window
```

The system can continue generating evidence automatically, but final product acceptance and online cutover remain human decisions.

## Boundary

This review observes V40 status and updates mainline focus. It does not write production policy, switch traffic, mutate chart facts, or import V30 runtime state.
