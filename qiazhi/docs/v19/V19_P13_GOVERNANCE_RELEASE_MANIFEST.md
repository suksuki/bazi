# V19 P13 Governance Release Manifest

## Goal

P13 adds a version-governance manifest above the existing ledgers. It does not activate rules or mutate runtime behavior. It records which reviewed/versioned artifacts belong together in a controlled release.

## Release Artifacts

A governance release can include:

- Knowledge Draft IDs or Knowledge IDs
- Guided Question Library Version IDs
- Bazi Rule Knowledge Version IDs
- Active Rule Revision IDs

The release stores compact artifact summaries plus the original ID lists.

## Gate

Every release record must pass the P11 synthetic expansion matrix before it is written.

Current gate:

- matrix: `P11_SYNTHETIC_EXPANSION`
- total: 20
- failed: 0
- status: pass

If the matrix fails, release creation returns `P13_SYNTHETIC_REGRESSION_FAILED`.

## Admin UI

Admin now includes `Governance Release Manifest`.

The panel can:

- create a release manifest from reviewed/versioned artifact IDs;
- show artifact counts by type;
- show P11 gate status;
- show guardrails and runtime mutation status.

## Guardrails

- `GOVERNANCE_RELEASE_RECORD_ONLY`
- `NO_RUNTIME_MUTATION`
- `P11_SYNTHETIC_REGRESSION_REQUIRED`
- `ANALYST_OR_ADMIN_REVIEW_REQUIRED`

## Analyst / Architect Review

No new architecture decision is required for this implementation. A review becomes useful when deciding whether a future release manifest should become deployable configuration rather than an audit-only record.
