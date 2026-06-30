# V40 Phase 15: Native Batch Evaluation

Date: 2026-06-30

## Goal

Phase 15 connects V40 native runtime to the evaluation loop directly.

Before this phase, V40 could:

```text
import V30 DTO
build shadow runtime
evaluate one runtime against cases
run one native seed
generate synthetic cases
```

After this phase, V40 can:

```text
take synthetic seeds
run one native runtime per seed
evaluate each runtime against its generated EvaluationCaseSpec
create EvaluationRunResult with release gate
aggregate EvaluationBatchSummary
persist all artifacts into V40 repository when requested
```

## New Evaluation Path

New module:

```text
v40/evaluation/native_batch.py
```

Main function:

```text
evaluate_native_seeds(batch_id, seeds, candidate_version, role_key)
```

Returns:

```text
RuntimeResult[]
EvaluationCaseSpec[]
EvaluationRunResult[]
EvaluationBatchSummary
```

This is intentionally one-to-one:

```text
SyntheticCaseSeed -> Native Runtime -> EvaluationCaseSpec -> EvaluationRunResult
```

It does not reuse a single runtime for every case, because native seeds each carry their own chart facts and user question.

## API

New endpoint:

```text
POST /api/v40/evaluation/native-batch/from-seeds
```

Request:

```text
batch_id
candidate_version
seeds
role_key
persist
```

When `persist=true`, it writes:

```text
v40_runtime_records
v40_evaluation_cases
v40_evaluation_runs
v40_release_gates
v40_evaluation_batches
```

It does not:

```text
write V30 state
write V40 production weights
mutate chart facts
call LLM judge
```

## CLI

New command:

```bash
python scripts/v40_artifact_cli.py run-native-batch \
  --path data/synthetic/native_bazi_seeds.json \
  --batch-id batch.local.native.001 \
  --candidate-version v40-native
```

Use `--no-persist` to print a summary without writing artifacts.

## Why This Matters

This phase moves V40 closer to a real quality loop:

```text
native engine changes
  -> synthetic seed batch
  -> metrics
  -> release gate
  -> candidate weight
  -> readiness
  -> controlled activation
```

It also makes regressions easier to catch before UI work.

## Tests

Added:

```text
tests/test_v40_phase15_native_batch_evaluation.py
```

Coverage:

```text
one runtime per synthetic seed
one run per generated case
release gate per run
batch summary aggregation
API boundary: no V30 writes, no production writes
```

## Next Phase

Phase 16 should add:

```text
LLMExpressionTask execution adapter
AcceptanceResult scan for LLM output
Admin native batch controls
larger synthetic seed generation/import
golden case import path for native runtime
```
