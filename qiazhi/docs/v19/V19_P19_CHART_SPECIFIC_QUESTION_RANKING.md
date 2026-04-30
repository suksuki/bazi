# V19 P19 Chart-Specific Question Ranking

## Issue

The guided-question area looked too similar across charts because the backend first loaded the full static question registry, then sorted by fixed scores.

That meant the first few questions were often generic, even when the chart had visible vault, branch relation, time-context, hidden-stem, or income-structure signals.

## Change

P19 changes question recommendation to use:

```text
chart facts -> structural signals -> rule-db signals -> chart-specific questions
```

The static registry is no longer treated as the full recommendation list. It is now only:

- the contract registry for known question keys;
- a low-weight fallback for baseline answerable questions.

## Ranking Policy

The top list now mixes question buckets:

- vault
- branch relation
- time context
- income stability
- metadata / anchor

Important baseline keys such as `q_income_stability`, `q_month_command_anchor`, `q_ten_god_metadata`, and `q_hidden_stem_role` are still kept in the top 10 when relevant, so existing answer routing remains stable.

## Personalization

Some labels now include the actual observed structure, for example:

- visible branch relation pairs;
- vault branches;
- day-master/month-anchor clues;
- hidden-stem clues.

This makes two charts with different structures show different question text even when they share a question category.

## Guardrails

- no fortune or prediction wording;
- no answer/result mutation;
- recommendation only;
- existing guided-answer contracts remain intact.

## Test Coverage

P19 tests verify:

- recommendation no longer equals the old static registry top five;
- synthetic charts produce multiple distinct top-five key sequences;
- synthetic charts produce multiple distinct top-five label sequences;
- `q_income_stability` remains available in the top 10 for supported charts.
