# V20 P92 Rule And Portrait Batch Runner

P92 starts executable batch generation and validation for the core Bazi chain:

```text
reviewed knowledge rules
-> extracted rule atoms
-> synthetic / representative Bazi cases
-> feature spine
-> portrait projection
-> recommended questions
-> active rule collisions
-> Bazi-domain alignment validation
```

## What The Batch Does

The runner performs two passes:

1. Generate rule candidates for every allowed Bazi domain.
2. Run synthetic, golden, and representative charts through the runtime and
   validate:
   - feature domains
   - recommended question keys
   - portrait axes
   - portrait intelligence
   - rule candidate support
   - Bazi-domain alignment status

The batch is read-only. It does not write Postgres, activate rules, promote
portrait labels, or mutate runtime policy.

## CLI

```bash
python3.12 v20/scripts/run_rule_portrait_batch.py --progress
python3.12 v20/scripts/run_rule_portrait_batch.py --write --progress
python3.12 v20/scripts/run_rule_portrait_batch.py --status
```

`--write` stores a local runtime artifact under:

```text
v20/.runtime/local/training/rule_portrait_batch/latest.json
```

The artifact is intentionally local and ignored by git.

## API

```text
GET /api/v20/validation/rule-portrait-batch
GET /api/v20/learning/rule-portrait-batch
GET /api/v20/learning/rule-portrait-batch?status=true
```

## Current Scope

The first batch covers:

- all allowed Bazi domains
- P90 synthetic rule cases
- golden validation cases
- representative wealth/time and element/useful-god cases

Future batches should expand into a mechanism matrix: positive cases, negative
cases, hidden/source-layer interference, and explicit time-layer interference
for each major rule family.
