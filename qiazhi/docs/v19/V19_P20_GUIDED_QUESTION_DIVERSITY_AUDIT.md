# V19 P20 Guided Question Diversity Audit

## Goal

P20 makes the P19 chart-specific question ranking measurable. The audit answers one narrow question:

> Are guided questions changing with the synthetic chart structure, or has the old static top-five registry returned?

This is an audit-only layer. It does not approve proposals, update the guided question library, mutate runtime knowledge, or activate rules.

## Scope

- Matrix: `P11_SYNTHETIC_EXPANSION`
- Data source: synthetic cases only
- Chain checked: synthetic chart -> guided question context -> top question keys/labels
- Human review: only needed later if the audit exposes a content proposal or if a release approval is requested

## Metrics

- `top_key_sequence_count`: distinct top-five question-key sequences across P11 cases
- `top_label_sequence_count`: distinct visible Chinese label sequences across P11 cases
- `old_static_top_present`: whether the old static top five appeared again
- `income_stability_top10_count`: number of synthetic cases where `q_income_stability` remains available in top ten
- `kb_augmented_change_count`: number of cases where KB augmentation changed the top-five keys compared with no-knowledge baseline
- `failure_count`: audit failures such as no questions, static top-five recurrence, or missing income-stability fallback

## Pass Gate

The audit passes only when:

- P11 has at least 20 synthetic cases
- top key sequences have at least 3 variants
- visible label sequences have at least 8 variants
- the old static top-five sequence is absent
- `q_income_stability` appears in top ten for every case
- no audit failures are recorded

## Interfaces

- Backend: `guided_question_diversity_audit()`
- API: `GET /api/lab/guided-question-diversity-audit`
- Admin UI: `Guided Question Diversity Audit`

## Guardrails

- `AUDIT_ONLY`
- `SYNTHETIC_CASES_ONLY`
- `NO_AUTO_LEARNING`
- `NO_RUNTIME_MUTATION`
- `NO_AUTO_QUESTION_LIBRARY_CHANGE`
