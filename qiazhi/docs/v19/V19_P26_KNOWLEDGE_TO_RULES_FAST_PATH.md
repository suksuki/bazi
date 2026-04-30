# V19 P26 Knowledge To Rules Fast Path

P26 shifts the mainline back from workflow scaffolding to content and rules.

It adds a new rule-ready knowledge pack and a fast path that converts already approved proposals into version records, then ingests current knowledge drafts into the Bazi Rule DB engine adapter.

## New Knowledge

New pack:

- `docs/bazi_knowledge/packs/p26_rule_conversion_knowledge_draft_seeds_v1.json`

It adds 12 structured drafts across:

- day/month structural anchors
- hidden-stem source layers
- branch clash/harm/break boundaries
- vault location boundaries
- time-context no-natal-mutation boundaries
- ten-god visible/hidden metadata
- wealth/income structure evidence
- month-command capacity evidence

These drafts are designed for Rule DB adapter ingestion. They remain non-predictive and do not emit fortune or life-event claims.

## Fast Path

API:

- `POST /api/lab/p26/knowledge-to-rules`

The endpoint performs:

1. Seed current knowledge drafts, including packs.
2. Convert P25-approved rule proposals into `bazi_rule_versions`.
3. Convert P25-approved guided question proposals into `guided_question_library_versions`.
4. Ingest current knowledge drafts into Rule DB.

Default knowledge can be engine-enabled. New pack drafts such as `p21.*` and `p26.*` are inserted as Rule DB records but keep `engine_enabled=false` until a separate synthetic acceptance step marks them ready. This prevents new content from hijacking the existing answer source-signal ranking.

## Guardrails

- `P26_KNOWLEDGE_TO_RULES_FAST_PATH`
- `P25_APPROVAL_REQUIRED_FOR_VERSION_RECORD`
- `RULE_DB_ENGINE_ADAPTER_ONLY`
- `NO_RESULT_MUTATION`
- `NO_FORTUNE`

Rule DB adapter signals can guide questions and answer attribution, but they must not mutate the computed chart result or generate predictive verdicts. Newly added pack rules are searchable and reviewable immediately, then promoted to engine-ready status only after regression acceptance.
