# V19 P9-C Admin Structural Rule Signals Review

## Goal

Expose the P9 Rule DB -> Structural Rule Signals adapter in the Admin review surface.

This panel is for analysts and admins to inspect whether approved Bazi Rule DB records are producing useful structural signals for guided questions and answers.

## Admin UI

Location:

- `Admin -> Evolution Interfaces -> Structural Rule Signals`

Inputs:

- `Profile ID`: optional. If empty, the panel uses the demo birth input used by the P9 review script.
- `Selected Year`: defaults to `2026`.

Output:

- Signal count and adapter version.
- Fact summary from the current chart/time context.
- Each structural signal with:
  - `signal_id`
  - `category`
  - `layer`
  - `observed`
  - `answer_scope`
  - `question_keys`
  - `rule_id`
  - `knowledge_id`
  - `mutates_result`

## Boundary

The panel must remain review-only.

- It does not change `income_stability`.
- It does not mutate runtime inference.
- It does not approve or reject rules.
- It does not ask the LLM to create facts.
- It only calls `/api/lab/structural-rule-signals?role=admin`.

## Related backend/API

- `POST /api/lab/structural-rule-signals?role=admin`
- `v19.bazi_rule_db.build_structural_rule_signals(...)`
- `v19.bazi_guided_questions.build_guided_question_context(...)`

## Related scripts

- `v19/scripts/p9_rule_signal_review.py`
- `v19/scripts/p9_knowledge_rule_review.sh`
- `RUN_P9=1 ./v19/scripts/deploy_linux.sh`

## Review checklist

- Signals exist for chart facts that match approved Rule DB records.
- `mutates_result` is always `false`.
- Time-context signals are labeled as context/background only.
- Question keys point to guided-question contracts, not free-form prediction prompts.
- Answer scope is readable enough for an analyst to decide whether a rule should remain enabled.
