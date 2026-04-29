# V19 P7 Answer Quality Governance

P7 adds an answer-quality governance layer for the Guided Question Flow.

The goal is simple: if the system produces a guided answer that is empty, cut off, too mechanical, exposes internal fields, or crosses into prediction wording, the issue should be visible in an audit/report before we expand the question library further.

## Scope

P7 covers:

- guided-question audit answer text checks
- saved audit and feedback quality aggregation
- answer quality report API
- command-line P7 audit/report helper
- no runtime inference mutation

P7 does not:

- change `income_stability`
- activate new Rule DB inference
- auto-update question ranking
- auto-learn from user feedback
- generate fortune/prediction answers

## New API

```text
GET /api/lab/guided-question-answer-quality?role=admin
```

Returns:

```text
summary.by_status
summary.by_question
summary.risk_flags
items[].score
items[].status
items[].risk_flags
items[].suggested_review_action
```

Statuses:

```text
pass   answer has no detected quality issue
watch  answer is usable but should be reviewed
fail   answer has a critical issue and should not be treated as acceptable
```

Critical risks:

```text
answer_text_present
answer_not_truncated
no_internal_markers
no_prediction_terms
unsupported_has_boundary
```

Non-critical review risks:

```text
question_contract_present
intent_present
retrieved_facts_present
observed_facts_present
user_feedback_not_negative
```

## Audit integration

`POST /api/lab/guided-question-audit` now checks answer quality in addition to the existing contract/fact checks:

```text
answer_not_truncated
no_internal_answer_markers
no_prediction_terms
```

This catches the class of bug where the UI shows a half sentence, such as an unclosed quote or a sentence ending after “而 / 包括 / 例如 / ，”.

## Scripts

Run the P7 quality report against a live server:

```bash
python3 v19/scripts/p7_answer_quality_report.py --base-url http://127.0.0.1:9019
```

Run the full P7 flow:

```bash
BASE_URL=http://127.0.0.1:9019 ROLE=admin SAVE_AUDIT=1 ./v19/scripts/p7_answer_quality_audit.sh
```

The full flow:

```text
1. runs the guided-question audit matrix
2. saves audit records by default
3. reads the answer quality report
4. exits non-zero if fail items exist
```

## Feedback connection

User feedback submitted from the answer card is included in the quality report when `subject_type = guided_question`.

Feedback is treated only as a review signal:

```text
negative feedback → watch/fail review queue signal
negative feedback does not mutate rules
negative feedback does not change runtime ranking automatically
```

## Deployment checklist

1. Deploy P7 code.
2. Restart V19.
3. Run P6 seed/audit if the target environment was not seeded yet.
4. Run:

```bash
BASE_URL=http://127.0.0.1:9019 ROLE=admin SAVE_AUDIT=1 ./v19/scripts/p7_answer_quality_audit.sh
```

5. Review any `fail` items before expanding question coverage.

## Boundary

P7 is a quality governance layer.

It makes answer quality visible and auditable, but it does not alter structural inference, income stability, rule activation, or question ranking automatically.
