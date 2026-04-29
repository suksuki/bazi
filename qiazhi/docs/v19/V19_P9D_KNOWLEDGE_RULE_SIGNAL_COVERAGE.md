# V19 P9-D Knowledge Rule Signal Coverage

## Goal

Create a review report for the full P9 chain:

```text
Knowledge Draft -> Bazi Rule DB -> Structural Rule Signal -> Guided Question / Answer Scope
```

This is a review and governance tool. It does not change runtime inference.

## API

```text
POST /api/lab/knowledge-rule-signal-coverage?role=admin
```

The endpoint accepts either:

```json
{
  "profile_id": "profile_xxx",
  "selected_year": 2026
}
```

or:

```json
{
  "birth_input": {
    "year": 1990,
    "month": 11,
    "day": 13,
    "hour": 12,
    "calendar_type": "solar",
    "gender": "male"
  },
  "selected_year": 2026
}
```

## Report fields

The report returns:

- `summary.draft_count`
- `summary.eligible_draft_count`
- `summary.rule_count`
- `summary.engine_ready_eligible_count`
- `summary.sample_signal_covered_count`
- `summary.gap_count`
- `items[]`
- `orphan_rules[]`
- `sample_signal_report`

Each `items[]` row contains:

- `knowledge_id`
- `draft_id`
- `domain`
- `category`
- `risk_level`
- `review_status`
- `eligible_for_rule_db`
- `rule_ids`
- `active_engine_rule_ids`
- `signal_ids`
- `answer_scopes`
- `question_keys`
- `status`
- `gaps`

## Status meanings

- `archive_only`: The knowledge row is not eligible for Rule DB, usually because it is R4/archive-only.
- `missing_rule`: The knowledge row is eligible, but no Rule DB record exists.
- `rule_present_not_engine_ready`: A Rule DB record exists, but it is inactive or engine-disabled.
- `sample_signal_covered`: The sample chart/time context produced at least one Structural Rule Signal for this knowledge row.
- `rule_ready_unmatched_in_sample`: The rule is ready, but the current sample chart/time context did not trigger it.

## Script

```bash
python3 v19/scripts/p9_knowledge_rule_coverage.py --base-url http://127.0.0.1:9019 --role admin
```

It is also included in:

```bash
v19/scripts/p9_knowledge_rule_review.sh
```

and therefore in:

```bash
RUN_P9=1 ./v19/scripts/deploy_linux.sh
```

## Guardrails

- Review only.
- No result mutation.
- No automatic rule activation.
- No LLM authority.
- A sample chart not triggering a signal is a review warning, not proof that the rule is invalid.
