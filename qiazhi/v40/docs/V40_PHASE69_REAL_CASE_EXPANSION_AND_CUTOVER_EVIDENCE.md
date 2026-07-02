# V40 Phase 69: Real Case Expansion And Cutover Evidence

## Goal

Phase 69 turns real-case acceptance from a one-off score into an expansion and cutover evidence pack.

The system can now answer:

- how many real cases are available;
- how many can be used for training;
- which topics are still under-covered;
- whether the latest acceptance window is clean enough;
- whether online cutover is still blocked by real-case evidence.

## Runtime Boundary

This phase is read-only.

```text
RealCaseRecord[]
AcceptanceWindowResult[]
  -> Real Case Expansion Evidence Pack
  -> Admin / release / user acceptance view
```

It does not:

- switch production traffic;
- write V30 state;
- write V40 production policy;
- mutate chart facts;
- let LLM judge acceptance.

## Evidence Gates

`build_real_case_expansion_evidence_pack` checks:

1. total case count;
2. trainable case count;
3. topic coverage for career, wealth, relationship, health, timing, useful god, hidden attribute;
4. latest acceptance window recommendation;
5. overclaim and blocked-count safety.

The pack can return `automatic_status = ready`, but cutover still remains `ready_for_human_signoff`.

## API

```text
POST /api/v40/project/real-case-expansion-evidence
```

The API accepts:

- `cases: RealCaseRecord[]`;
- `acceptance_windows: AcceptanceWindowResult[]`;
- `target_case_count`;
- `min_cases_per_topic`;
- `min_trainable_case_count`.

## Product Meaning

This closes the gap between "we can run an acceptance window" and "we know what real evidence is still missing before V40 can replace V30."

V40 can keep iterating quickly, but the final online cutover remains gated by real case quality and human confirmation.

## Files

```text
v40/project/real_case_expansion.py
v40/api/models.py
v40/api/app.py
tests/test_v40_phase69_real_case_expansion_evidence.py
```
