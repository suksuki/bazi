# V19 P23 Review Packet Decision Ledger

P23 adds a controlled analyst decision layer on top of P18/P22 review packets.

The goal is to let an analyst or admin record a review outcome without mutating proposal status, creating versions, or changing runtime behavior.

## Scope

- Input: an existing proposal review packet.
- Output: decision records attached to that packet.
- Allowed decisions: `approve_candidate`, `reject_candidate`, `needs_revision`, `hold`.
- Scope can be packet-level or proposal-level when a `proposal_id` is supplied.

## Guardrails

- `P23_DECISION_LEDGER_ONLY`
- `NO_AUTO_APPROVAL`
- `NO_PROPOSAL_STATUS_CHANGE`
- `NO_VERSION_RECORD`
- `NO_RUNTIME_MUTATION`

`approve_candidate` only means the analyst has marked the packet or proposal as a candidate for later approval. It does not call proposal approval functions and does not create rule or question library versions.

## API

- `POST /api/lab/proposal-review-packets/{packet_id}/decisions`
- `GET /api/lab/proposal-review-packets`

The list endpoint now returns `decision_summary`, `decision_records`, and `latest_decision_record` for each packet.

## Admin UI

The P18 Review Packet panel now includes:

- decision selector
- optional proposal id
- decision note
- per-packet `记录 P23 Decision` action

This gives analysts a practical review ledger while keeping approval, versioning, and runtime promotion as separate future steps.

## Verification

Regression coverage asserts that recording an `approve_candidate` decision:

- keeps packet status as `approval_review_ready`
- keeps rule and guided question proposals in `validation_ready`
- creates no rule versions
- creates no guided question library versions
- records `runtime_mutation=false`
