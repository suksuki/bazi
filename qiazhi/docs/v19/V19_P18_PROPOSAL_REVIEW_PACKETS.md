# V19 P18 Proposal Review Packets

## Decision

P18 creates analyst/admin review packets from validated proposal drafts.

It is the handoff layer between machine validation and human approval. It does not approve proposals, create version records, publish releases, or mutate runtime inference.

## Flow

```text
P17 validation run
  -> P18 review packet
  -> analyst/admin approve or reject each proposal
  -> version record
  -> governance release
```

## API

```text
GET  /api/lab/proposal-review-packets
POST /api/lab/proposal-review-packets
```

The POST endpoint can select a validation run by:

- `validation_run_id`
- `source_run_id`
- `batch_key`

If no id is supplied, it uses the latest matching validation run.

## Packet Status

- `approval_review_ready`: every proposal in the validation run passed.
- `blocked_by_validation`: at least one proposal failed validation or the validation run itself is not ready.

## Packet Contents

Each packet records:

- source validation run;
- source P16 run or batch key;
- proposal ids;
- rule ids / question keys;
- source knowledge id when available;
- failed validation checks when blocked;
- explicit no-approval, no-version, and no-runtime flags.

## Guardrails

- `P18_REVIEW_PACKET_ONLY`
- `NO_AUTO_APPROVAL`
- `NO_VERSION_RECORD`
- `NO_RUNTIME_MUTATION`
- `ANALYST_OR_ADMIN_DECISION_REQUIRED`

## Test Coverage

P18 tests verify:

- validation-ready proposals become an approval review packet;
- failed validation creates a blocked packet;
- packet creation does not change proposal status beyond P17 validation;
- no approval/version/runtime flags remain false;
- API and Admin UI wiring is present.
