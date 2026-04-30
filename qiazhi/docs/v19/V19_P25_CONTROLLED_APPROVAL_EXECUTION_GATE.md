# V19 P25 Controlled Approval Execution Gate

P25 turns a P24-ready review packet into an explicit controlled approval action.

This is the first step in the P16-P25 chain that can mutate proposal status. It only moves proposal records from `validation_ready` to `approved`; it does not create rule versions, question library versions, governance releases, or runtime changes.

## Required Gate

Controlled approval requires:

- packet status is `approval_review_ready`
- latest approval preflight is `approval_preflight_ready`
- every packet item still maps to an existing proposal
- every proposal is still `validation_ready`
- every latest proposal-scoped decision is `approve_candidate`
- packet and review records have no version or runtime mutation flags

If any gate fails, P25 records a blocked execution ledger and returns `P25_APPROVAL_PREFLIGHT_NOT_READY`.

## API

- `POST /api/lab/proposal-review-packets/{packet_id}/controlled-approval`
- `GET /api/lab/proposal-review-packets`

Successful execution records are stored as `approval_execution_records` on the packet.

## Idempotency

If a packet already has a successful `controlled_approval_executed` record, repeated execution returns the existing record with `reused=true`.

This prevents duplicate approval history writes.

## Guardrails

- `P25_CONTROLLED_APPROVAL_ONLY`
- `P24_PREFLIGHT_REQUIRED`
- `NO_AUTO_APPROVAL`
- `NO_VERSION_RECORD`
- `NO_RUNTIME_MUTATION`

The next stage should decide which approved proposals are eligible for a version record. P25 itself stops at approval status.
