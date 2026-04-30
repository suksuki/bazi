# V19 P24 Item Decision Approval Preflight

P24 makes the P18/P23 review flow more operational.

It adds proposal-level decision review inside each review packet, then creates an approval preflight report that tells the analyst whether the packet is ready for a later explicit approval action.

## Scope

- Record item-level decisions by passing a `proposal_id` to the P23 decision endpoint.
- Run approval preflight with `POST /api/lab/proposal-review-packets/{packet_id}/approval-preflight`.
- Store preflight reports on the review packet as `approval_preflight_records`.

## Required Checks

- packet is `approval_review_ready`
- packet has items
- every item passed validation
- every item still maps to an existing proposal
- every proposal is still `validation_ready`
- every proposal has a proposal-scoped decision
- every latest proposal-scoped decision is `approve_candidate`
- packet and decision records have no approval/version/runtime mutation flags

## Guardrails

- `P24_APPROVAL_PREFLIGHT_ONLY`
- `NO_AUTO_APPROVAL`
- `NO_PROPOSAL_STATUS_CHANGE`
- `NO_VERSION_RECORD`
- `NO_RUNTIME_MUTATION`

`approval_preflight_ready` is only a readiness report. It does not approve proposals and does not create rule or guided question version records.

## Admin UI

The P18 Review Packet panel now renders each packet item with:

- proposal kind and id
- proposal status
- validation state
- latest item-level decision
- `记录条目 Decision`
- `运行 P24 Preflight`

This prepares the workflow for a later approval step without weakening the controlled evolution boundary.
