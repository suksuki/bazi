# V19 P9 Knowledge + Structural Rule Signal Completion

P9 fills the two gaps after P8:

```text
P9-A: knowledge explanation-chain completion
P9-B: Rule DB → Structural Rule Signals adapter
P9-C: Admin Structural Rule Signals review surface
P9-D: Knowledge → Rule DB → Structural Signal coverage report
```

The purpose is to make the knowledge/rule layer useful for guided questions and answers without changing deterministic results.

## P9-A Knowledge Completion

P9 expands runtime knowledge and current knowledge draft seeds with structure-chain concepts:

```text
structure reading chain
month command + hidden-stem source chain
ten-god relationship metadata chain
five-element relation direction chain
branch relation layer chain
vault location + hidden-stem chain
income structure signal chain
structural signal adapter boundary
```

These units help the answer layer explain:

```text
where a fact comes from
which layer it belongs to
why it is structure evidence
why it is not a prediction
```

They do not create fortune, timing, wealth, health, or marriage predictions.

## P9-B Structural Rule Signal Adapter

P9 adds:

```text
build_structural_rule_signals(chart, time_context, inference_context)
```

Location:

```text
v19/bazi_rule_db.py
```

Output contract:

```text
signal_id
source
version
rule_id
knowledge_id
domain
category
risk_level
title
layer
observed
reason
fact_refs
answer_scope
question_keys
score
mutates_result=false
runtime_scope=structural_rule_signal_only_no_result_mutation
```

The adapter consumes active Rule DB records and emits signals for:

```text
structure_anchor
hidden_stem
branch_relation
vault
time_boundary / timing_context
ten_god / wealth_boundary
wealth_feature / wealth_mechanism
strength_model
pattern_structure
```

## Guided Question Integration

`build_guided_question_context()` now consumes the Rule DB adapter report.

The guided-question context includes:

```text
rule_signal_adapter.version
rule_signal_adapter.count
rule_signal_adapter.runtime_scope
signals[] from structural_rule_signals
```

These signals can recommend questions and provide answer attribution, but they do not mutate `income_stability`.

## Review API

P9 adds:

```text
POST /api/lab/structural-rule-signals?role=admin
```

Request can use either:

```text
profile_id
```

or:

```text
birth_input
selected_year
```

The endpoint returns a structural-rule signal report for review.

P9-D also adds:

```text
POST /api/lab/knowledge-rule-signal-coverage?role=admin
```

This endpoint reviews the chain:

```text
knowledge_draft -> rule_db_record -> active_engine_rule -> sample_structural_signal -> question_keys / answer_scope
```

It is a coverage and gap report only. It does not activate rules or change runtime inference.

## Scripts

Review structural signals only:

```bash
python3 v19/scripts/p9_rule_signal_review.py --base-url http://127.0.0.1:9019
```

Review knowledge/rule/signal coverage only:

```bash
python3 v19/scripts/p9_knowledge_rule_coverage.py --base-url http://127.0.0.1:9019
```

Run full P9 knowledge/rule review:

```bash
BASE_URL=http://127.0.0.1:9019 ROLE=admin SAVE_AUDIT=1 ./v19/scripts/p9_knowledge_rule_review.sh
```

Deploy and run P9 in one command:

```bash
RUN_P9=1 ./v19/scripts/deploy_linux.sh
```

`RUN_P9=1` defaults to `INGEST_RULE_DB=1`, because P9 review requires the current knowledge drafts to be present in Rule DB.

## Boundaries

P9 does not:

```text
change income_stability
activate prediction rules
auto-learn from feedback
promote rules automatically
allow R4 symbolic material into runtime inference
```

P9 only improves:

```text
knowledge explanation coverage
Rule DB attribution
structural signal visibility
guided question relevance
answer auditability
```

## Recommended Review

After deploy:

```bash
cd ~/bazi/qiazhi
RUN_P9=1 ./v19/scripts/deploy_linux.sh
```

Then inspect:

```text
/admin?role=admin → Guided Answer Quality Ledger
POST /api/lab/structural-rule-signals?role=admin
POST /api/lab/knowledge-rule-signal-coverage?role=admin
```

Pass expectation:

```text
P9 structural rule signal count > 0
P9 coverage report shows eligible drafts mapped into Rule DB
P7 answer quality has no fail items
P6 guided question matrix passes
income_stability unchanged
```
