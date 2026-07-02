# V40 Phase 71: Online Cutover Decision Pack

## Goal

Phase 71 creates a single online cutover decision pack for UI/Admin surfaces.

It merges four evidence layers:

1. project status;
2. production cutover checklist;
3. real case expansion evidence;
4. direct training activation evidence;
5. optional release candidate audit.

The pack tells the user whether V40 is blocked, near ready, or ready for human signoff.

## API

```text
POST /api/v40/project/online-cutover-decision
```

The endpoint accepts existing read models and returns one decision object.

## Decision States

```text
blocked_by_evidence
near_ready_with_blockers
ready_for_human_signoff
```

Even when the decision is `ready_for_human_signoff`, V40 still does not switch traffic automatically.

## Boundary

The decision pack does not:

- switch traffic;
- write V30 state;
- write V40 production policy;
- mutate chart facts;
- replace final real-case quality judgment.

It only makes the final cutover decision explainable.

## Product Meaning

This phase is the product-level bridge between runtime readiness and actual online operation.

The main system can show a simple decision:

```text
自动证据是否齐？
真实命例是否过关？
训练是否可解释且可回滚？
是否可以进入人工上线窗口？
```

## Files

```text
v40/project/online_cutover_decision.py
v40/api/models.py
v40/api/app.py
tests/test_v40_phase71_online_cutover_decision_pack.py
```
