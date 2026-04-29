# V19 P10 Knowledge / Rule Completion

Date: 2026-04-29

P10 extends the V19 knowledge and rule-support layer without changing deterministic `income_stability` inference.

## What P10 adds

### 1. Active knowledge domain support

`answer_expression` is now a valid knowledge domain.

This matters because several user-facing answer-quality seeds already existed, but were previously skipped by the knowledge kernel domain validator. After P10, answer style knowledge can be reviewed, compiled, retrieved, and used by the LLM rewrite boundary.

### 2. Active reviewed seed coverage

P10 adds reviewed seed units for:

- complete branch hidden-stem mapping
- branch penalty / harm / break boundary
- three-meeting boundary
- ten-god five-family plain-language explanation
- visible vs hidden ten-god evidence layers
- month-command / season context not being a standalone strength verdict
- no boilerplate tail in user answers
- concise complete answer shape

These units are evidence templates only. They do not create predictions or mutate result cards.

### 3. Knowledge retrieval improvements

Knowledge retrieval now recognizes additional user-facing terms:

- 刑 / 害 / 破
- 三会
- 墓 / 库
- 回答 / 说人话 / 废话 / 完整回答

It also boosts relevant domains when the user asks about answer quality, ten-god labels, or month-command / strength boundaries.

### 4. Rule DB draft seeds

P10 extends the current knowledge draft seed database with rule-eligible or audit-eligible drafts for:

- complete branch hidden-stem mapping
- branch penalty / harm / break boundary
- three-meeting boundary
- ten-god five-family explanation
- ten-god visible / hidden evidence boundary
- month-command season boundary
- answer no-boilerplate style
- concise complete answer shape

When deployed with `INGEST_RULE_DB=1`, eligible drafts can be ingested into the Rule DB as auditable structural support. Answer-expression drafts remain guidance/audit context and must not mutate runtime inference.

### 5. User-facing wording cleanup

Several hard-coded answer fragments were adjusted so user-facing answers no longer say things like:

- “this answer only explains...”
- “does not change income_stability”
- internal result-field names as a standalone disclaimer

The boundary remains, but it is phrased naturally and only when relevant.

## P10 Review

The review checked the full chain:

Question recommendation -> fact retrieval -> composed answer text.

Findings and fixes:

- `_chart_facts()` now exposes day stem, month branch, and hidden-stem mapping, so structural anchor and hidden-stem signals can actually drive recommendations and answers.
- Static registry questions that are not in the top 10 recommendation slice now fall back to their registry contract, so selected questions such as ten-god and hidden-stem questions keep their intended focus.
- The answer payload now records `applied_knowledge` and mirrors it under retrieved facts for audit. User text uses the knowledge semantically, without showing knowledge IDs.
- Rule DB structured branch rules now evaluate their structured facts before broad category fallback. This prevents six-clash, six-combination, harm, break, and three-meeting rules from cross-triggering on unrelated branch relations.
- Deterministic answer text now uses the P10 month-command, ten-god visible/hidden, complete hidden-stem, and penalty/harm/break boundary knowledge in the relevant answers.
- Remaining user-facing fragments were cleaned to avoid Lab/rule_id/signal_id/debug wording and generic result-mutation tails.
- The old "look at these three points" guidance panel was removed because it duplicated the question chips without adding an action or new fact.
- Repeated prediction-disclaimer badges and warning strips were removed from the Oracle/Profile UI. Boundary language remains in the relevant answer text, but the fixed UI chrome no longer spends space on "not prediction" reminders.
- The direct income-stability renderer was rewritten from an audit-log style response into a concise user-facing structure summary.

Verification:

```bash
python3 -m pytest -q v19/tests
python3 -m json.tool docs/bazi_knowledge/database/current_knowledge_draft_seeds_v1.json
```

Result: `38 passed`; the draft seed JSON is valid. A direct 23-question guided-answer matrix also passed the internal-marker and truncation checks. Frontend Oracle/Profile scripts pass `node --check`.

## Deployment note

On the Linux server, use:

```bash
cd ~/bazi/qiazhi
RUN_P9=1 INGEST_RULE_DB=1 ./v19/scripts/deploy_linux.sh
```

If runtime knowledge already exists and you need to refresh active seed units, use the Admin seed endpoint or run the deploy flow with the current seed scripts. PostgreSQL storage should keep active knowledge and Rule DB records after seed/ingest.

## Guardrails

P10 does not:

- change `income_stability` calculation
- create traditional fortune output
- allow LLM to invent facts
- activate R4 symbolic material
- auto-promote drafts without review/ingestion path
