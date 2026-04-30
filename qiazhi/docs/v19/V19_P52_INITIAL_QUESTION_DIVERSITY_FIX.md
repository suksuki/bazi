# V19 P52 Initial Question Diversity Fix

## Problem

The oracle first-screen recommendations were still too similar across different charts.

Two causes were found:

- Backend ranking filled broad route buckets too early, so common buckets such as vault, branch relation, time layer, metadata, and income structure repeatedly occupied the top five.
- Oracle frontend re-ranked backend `guided_question_context.questions` with an older local scorer, which diluted `personalized_score` and route-specific ordering.

## Change

- Backend question ranking now prioritizes chart-specific observed signals before generic bucket filling.
- Initial selection caps repeated signal categories in the first pass, so one hidden-stem signal does not produce multiple first-screen questions.
- Branch relation questions choose a more specific question key when the chart shows combination, three-harmony/meeting, harm/break/clash, or time-only relations.
- Vault questions remain available, but vault no longer unconditionally outranks branch/time context when other distinctive signals are present.
- Structure preview now carries deterministic `income_stability` as a question-routing signal only, so first-screen recommendations can see wealth/ten-god structure without rendering a result card.
- Oracle frontend uses backend question order for the first-screen chips instead of re-ranking it locally.

## Guardrails

- This changes question ordering only.
- No inference result, rule activation, answer content, or evidence pack is mutated.
- The UI still blocks prediction-style question labels.

## Verification

- P52 regression compares multiple synthetic charts and requires varied initial question signatures.
- Oracle static wiring verifies the frontend consumes backend personalized order.
