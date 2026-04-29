# V19 P8 Admin Answer Quality Panel

P8 exposes the P7 answer-quality governance layer in the V19 Admin UI.

## Goal

Analysts should not need SSH or command-line scripts to notice guided-answer quality issues.

P8 adds a visible Admin panel that shows:

```text
pass / watch / fail counts
risk flags
recent answer quality records
suggested review action
text preview
```

## UI Location

```text
/admin?role=admin
→ Evolution Interfaces
→ Guided Answer Quality Ledger
```

Controls:

```text
刷新回答质量
只看 fail
只看 watch
```

## Data Source

The panel reads:

```text
GET /api/lab/guided-question-answer-quality?role=admin
```

This endpoint aggregates saved guided-question audits and guided-question answer feedback.

## Boundary

The panel is review-only.

It does not:

```text
auto-learn
change question ranking
change Rule DB
change income_stability
activate inference rules
```

## Recommended Server Flow

After deploy:

```bash
cd ~/bazi/qiazhi
RUN_P6=1 RUN_P7=1 ./v19/scripts/deploy_linux.sh
```

Then open:

```text
https://dblife.com/admin?role=admin
```

Check whether Guided Answer Quality Ledger has fail/watch items.

## How to interpret statuses

```text
pass  safe enough for current supported flow
watch analyst should inspect when convenient
fail  fix before expanding question coverage
```

Typical risk flags:

```text
answer_not_truncated
no_internal_markers
no_prediction_terms
retrieved_facts_present
observed_facts_present
user_feedback_not_negative
```
