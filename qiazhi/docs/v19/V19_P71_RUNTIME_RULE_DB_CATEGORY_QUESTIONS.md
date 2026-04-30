# V19 P71 Runtime Rule DB Category Questions

## Goal

P71 makes runtime Rule DB route hints more readable in the user question layer. Instead of collapsing income-stability rules into one generic wealth question, the guided-question system can now surface category-specific prompts.

## Added Question Routes

- `kbq_income_path_route`
- `kbq_income_collision_route`
- `kbq_wealth_access_route`

These routes remain structural and non-predictive. They are used for question ordering and answer evidence only.

## Runtime Metadata

Dynamic questions now keep:

- source Rule DB category
- source topic lane
- framework state
- engine enabled flag

This lets the UI and audits distinguish active engine candidates from shadow route candidates without exposing internal IDs to normal users.

## Guardrails

- `RULE_DB_CATEGORY_QUESTION_HINT_ONLY`
- `NO_RESULT_MUTATION`
- `NO_ANSWER_MUTATION`
- `NO_RUNTIME_RULE_ACTIVATION`
- `NO_FORTUNE`
