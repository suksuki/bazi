# V40 Phase 73: Real Case Acceptance Pack

## Goal

Phase 73 turns USER-18 from a plan into a runtime read model.

The new pack merges:

- selected real cases;
- latest Acceptance Window;
- Real Case Expansion Evidence;
- Online Cutover Decision Pack;
- failed reason counts;
- topic coverage;
- trainable attribution hints.

It tells the owner whether the current V40 candidate can enter real-case quality review.

## API

```text
POST /api/v40/project/real-case-acceptance-pack
```

## Status Values

```text
ready_for_owner_review
needs_more_cases
needs_replay
blocked_by_quality
```

## Decision Rules

- Missing owner-review cases -> `needs_more_cases`
- Missing or non-approved Acceptance Window -> `needs_replay`
- Blocked cases or overclaim -> `blocked_by_quality`
- Real case evidence not ready -> `needs_more_cases`
- Online cutover decision not ready -> `needs_replay`
- All checks ready -> `ready_for_owner_review`

## Boundary

This pack does not:

- switch traffic;
- write V30 state;
- write V40 production policy;
- mutate chart facts;
- replace final owner judgment.

It only prepares a clean owner-facing acceptance review.

## Product Meaning

Phase 73 separates two concepts:

```text
System evidence says "ready for owner review"
Owner still decides whether real cases are good enough for beta
```

That keeps V40 high-iteration while preventing automatic cutover.

## Files

```text
v40/project/real_case_acceptance.py
v40/api/models.py
v40/api/app.py
tests/test_v40_phase73_real_case_acceptance_pack.py
```
