# V40 Phase 70: Direct Training Activation Evidence

## Goal

Phase 70 documents the system's high-iteration training principle in runtime evidence:

> validated training applies immediately, with visible before/after diff and rollback repair.

This phase does not add approval gating. It adds a read model that makes active policy changes understandable.

## Runtime Flow

```text
BatchTrainerV1Result
  -> Direct Training Activation Evidence
  -> Admin / release / replay / acceptance views
```

## What The Evidence Shows

`build_direct_training_activation_evidence` reports:

- base policy version;
- candidate / active policy version;
- whether active policy was applied;
- rollback registry id and readiness;
- changed weights and thresholds with before/after delta;
- affected signals, branches, verdicts, advice and probes;
- changed probe policy count;
- changed advice priority count;
- risk summary and regression failures;
- next actions.

## API

```text
POST /api/v40/project/direct-training-activation-evidence
```

The API accepts a `BatchTrainerV1Result` and returns a read-only evidence pack.

## Boundary

The evidence pack does not:

- apply training;
- roll back training;
- write V30 state;
- write V40 production policy;
- mutate chart facts.

It only explains what already happened and what must be checked next.

## Files

```text
v40/project/training_activation_evidence.py
v40/api/models.py
v40/api/app.py
tests/test_v40_phase70_direct_training_activation_evidence.py
```
