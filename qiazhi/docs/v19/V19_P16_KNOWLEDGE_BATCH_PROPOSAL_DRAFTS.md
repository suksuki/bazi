# V19 P16 Knowledge Batch Proposal Drafts

## Decision

P16 converts reviewed knowledge batches into proposal drafts, not runtime behavior.

The first eligible path is intentionally narrow:

- `p15.p14.r1_metadata_boundaries` can generate rule proposal drafts and one guided-question proposal draft.
- `p15.p14.r2_source_version_review` is blocked until source/version review.
- `p15.p14.r3_archive_reference_only` remains archive/reference until analyst or architect review.

## Flow

```text
Knowledge Review Batch
  -> P16 proposal run ledger
  -> Bazi rule proposal drafts
  -> Guided question proposal draft
  -> existing validation / approval / version record gates
  -> P13 governance release manifest
```

P16 does not update `review_status` on knowledge drafts and does not activate any rule.

## API

```text
GET  /api/lab/knowledge-batch-proposal-runs
POST /api/lab/knowledge-review-batches/{batch_id}/proposal-drafts
```

## Run Record

Each run records:

- source batch id/key;
- actor role;
- rule proposal ids;
- guided-question proposal ids;
- blocked items for R2/R3 or missing drafts;
- guardrails and runtime mutation status.

## Admin UI

Admin now includes `P16 Batch Proposal Drafts` in the Source Archive / Knowledge Draft area.

The UI can:

- generate proposal drafts from an eligible R1 batch;
- list proposal-run records;
- show blocked R2/R3 batches without creating proposals.

## Guardrails

- `P16_BATCH_TO_PROPOSAL_DRAFT_ONLY`
- `NO_RUNTIME_MUTATION`
- `NO_AUTO_RULE_ACTIVATION`
- `VALIDATION_AND_APPROVAL_REQUIRED`
- `R2_R3_ANALYST_REVIEW_BEFORE_PROPOSAL`

## Test Coverage

P16 tests verify:

- R1 batch creates 6 rule proposal drafts and 1 guided-question proposal draft;
- generated proposals pass schema validation;
- source knowledge draft review status remains unchanged;
- R2/R3 batches are blocked and recorded as proposal-run audit items;
- API and Admin UI wiring is present.
