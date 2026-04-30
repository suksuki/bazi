# V19 P17 Proposal Validation Runs

## Decision

P17 adds a batch validation layer for proposal drafts. It runs existing schema validators over rule and guided-question proposals and records the result as a validation run.

It does not approve, version, publish, or mutate runtime inference.

## Flow

```text
P16 proposal drafts
  -> P17 validation run
  -> proposal.status = validation_ready / validation_failed
  -> P18 review packet
  -> analyst/admin approval remains separate
  -> version record remains separate
  -> governance release remains separate
```

## API

```text
GET  /api/lab/proposal-validation-runs
POST /api/lab/proposal-validation-runs
```

The POST endpoint can filter by:

- `source_run_id`
- `batch_key`
- `proposal_ids`
- `statuses`

Default statuses are `draft,validation_failed`.

## Run Record

Each validation run records:

- actor role;
- source P16 run id or batch key;
- proposal ids;
- pass/fail status;
- failed checks;
- explicit flags showing no approval, no version record, and no runtime mutation.

## Guardrails

- `P17_SCHEMA_VALIDATION_ONLY`
- `NO_APPROVAL`
- `NO_VERSION_RECORD`
- `NO_RUNTIME_MUTATION`
- `ANALYST_OR_ADMIN_APPROVAL_REQUIRED_AFTER_VALIDATION`

## Test Coverage

P17 tests verify:

- P16 R1 output validates as 6 rule proposals plus 1 question proposal;
- valid proposals move to `validation_ready`;
- invalid proposals move to `validation_failed`;
- validation runs record failures without approval/version/runtime changes;
- API and Admin UI wiring is present.
