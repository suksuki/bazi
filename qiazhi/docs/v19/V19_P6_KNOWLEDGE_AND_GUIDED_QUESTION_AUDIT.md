# V19 P6 Knowledge + Guided Question Audit

P6 makes guided answers depend on reviewed structure knowledge instead of bare UI templates.

## Runtime seed order

Run these after deploying P6 when V19 is connected to the target storage backend.

```bash
curl -sS -X POST "http://127.0.0.1:9019/api/admin/knowledge/seed?role=admin" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'

curl -sS -X POST "http://127.0.0.1:9019/api/admin/bazi-source-archive/knowledge-drafts/seed-current?role=admin" \
  -H "Content-Type: application/json" \
  -d '{"force": true}'
```

Optional Rule DB refresh, if analyst-approved draft ingestion is desired:

```bash
curl -sS -X POST "http://127.0.0.1:9019/api/admin/bazi-rule-db/ingest-current?role=admin" \
  -H "Content-Type: application/json" \
  -d '{"force": false, "enable_engine": true}'
```

## Guided-question audit matrix

Run against a live V19 server:

```bash
python3 v19/scripts/guided_question_audit_matrix.py --base-url http://127.0.0.1:9019
```

Save audit records while running:

```bash
python3 v19/scripts/guided_question_audit_matrix.py --base-url http://127.0.0.1:9019 --save
```

Machine-readable report:

```bash
python3 v19/scripts/guided_question_audit_matrix.py --base-url http://127.0.0.1:9019 --json
```

## Pass criteria

Each core guided question should have:

- question contract
- routed intent
- retrieved facts
- observed facts
- composed answer text
- no internal debug markers in user-facing text
- existing audit checks passing when returned by the endpoint

## Failure handling

If a question fails:

- `contract_present`: add the question to `QUESTION_REGISTRY`.
- `intent_present`: update intent routing or source signal mapping.
- `retrieved_facts_present`: add fact retrieval support for that intent.
- `composed_text_present`: update Answer Composer fallback text.
- `no_internal_or_empty_text_markers`: remove UI/debug wording from composed text or LLM prompt.

## Boundary

P6 does not mutate `income_stability`. Knowledge units provide explanation and wording context only.

## One-shot P6 deploy helper

After deploying code and restarting V19, run:

```bash
BASE_URL=http://127.0.0.1:9019 ROLE=admin SAVE_AUDIT=1 ./v19/scripts/p6_seed_and_audit.sh
```

By default this seeds runtime knowledge, seeds current draft knowledge, and runs the guided-question audit matrix.

It does **not** ingest drafts into Rule DB by default. To also refresh Rule DB from current draft seeds:

```bash
INGEST_RULE_DB=1 BASE_URL=http://127.0.0.1:9019 ROLE=admin SAVE_AUDIT=1 ./v19/scripts/p6_seed_and_audit.sh
```

Keep `INGEST_RULE_DB=0` when you want knowledge wording improvements without changing active Rule DB signals.
