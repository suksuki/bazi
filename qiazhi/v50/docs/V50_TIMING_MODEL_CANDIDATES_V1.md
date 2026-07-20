# V50 Timing Model Candidates v1

Status: Implemented as research policy candidates
Runtime status: not active

## Purpose

Timing Model Candidates v1 turns the timing research docs into comparable
Simulator Policy Candidates.

It does not implement runtime timing judgment.

It preserves competing models for:

```text
luck
year
month
```

## Candidate Count

```text
luck: 4
year: 4
month: 4
total: 12
```

## Current Highest-Confidence Candidates

These are not truth. They are current working hypotheses.

```text
luck  -> timing.luck.perturbation_source.v1        confidence 0.68
year  -> timing.year.activation_event.v1           confidence 0.66
month -> timing.month.event_window.v1              confidence 0.61
```

## Boundary

Every TimingModelCandidate must remain:

```text
runtime_active: false
creates_judgment: false
calls_brain: false
calls_llm: false
mutates_natal_structure: false
```

Timing candidates cannot:

- rewrite natal structure
- become user-facing verdicts
- bypass State Simulator
- bypass validation
- become Brain policy without synthetic validation

## Files

```text
packages/core/timing/schemas.py
packages/core/timing/candidates.py
scripts/v50_validate_timing_model_candidates.py
data/validation/fixtures/timing_model_candidates_v1.json
tests/test_v50_timing_model_candidates.py
```

## Next Use

The expected algorithm gaps from Synthetic Fixture Matrix v2 should feed timing
validation:

```text
path:timing_resource_reroute_candidate
path:year_activation_existing_node
```

Timing Model Candidate v1 provides the model interface for those future tests.

## Next Mainline

```text
Mechanism Discovery v1
        ↓
Timing Synthetic Validation v1
        ↓
Unified Theme Discovery v1
```
