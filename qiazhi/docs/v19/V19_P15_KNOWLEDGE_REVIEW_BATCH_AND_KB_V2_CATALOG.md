# V19 P15 Knowledge Review Batch + KB v2 Catalog

## Decision

The current knowledge base has become patch-like because new drafts are appended to the old seed file. P15 does not hard-switch runtime to a new knowledge base. Instead it creates a clean catalog layer for Knowledge Base v2 and adds review batches so new content can be promoted in controlled groups.

## KB v2 Catalog

New manifest:

```text
docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json
```

The manifest maps the knowledge system into six layers:

- `L0_source_archive`
- `L1_excerpt_archive`
- `L2_knowledge_unit_drafts`
- `L3_review_batches`
- `L4_rule_and_question_proposals`
- `L5_governance_release_manifest`

It also maps domains to future clean directories:

- `core_structure`
- `ten_god`
- `strength`
- `wealth`
- `answer_expression`
- `luck_flow`

This is catalog-only. It does not change runtime inference.

## Review Batches

P15 adds Knowledge Review Batch records. A batch groups drafts for analyst/admin review but does not mutate draft status.

Seeded P14 batch plan:

- `p15.p14.r1_metadata_boundaries`
  - R1
  - ten-god family and month-command boundary drafts
  - recommended action: `review_for_proposal_ready`

- `p15.p14.r2_source_version_review`
  - R2
  - stem-combination and branch-penalty drafts
  - recommended action: `source_version_review_before_rule_proposal`

- `p15.p14.r3_archive_reference_only`
  - R3
  - twelve-growth-phase and useful-god drafts
  - recommended action: `archive_reference_only_until_architect_or_analyst_review`

## API

```text
GET  /api/lab/knowledge-review-batches
POST /api/lab/knowledge-review-batches
POST /api/lab/knowledge-review-batches/seed-p14
```

## Admin UI

Admin now includes `Knowledge Review Batches` in the Source Archive / Knowledge Draft area.

The UI can:

- seed P14 review batches;
- create a custom review batch using prefix/risk/IDs;
- list batches and show draft counts, risk counts, domains, and recommended actions.

## Architect / Analyst Review

No immediate review is required for P15 because it is catalog/batch-only. Review becomes important before:

- converting the KB v2 catalog into deployable runtime config;
- promoting R2 relation rules into Rule DB proposals;
- moving R3 content out of archive/reference status.
