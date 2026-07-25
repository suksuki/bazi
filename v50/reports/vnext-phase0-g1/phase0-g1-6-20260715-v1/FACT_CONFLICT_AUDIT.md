# Retained Holistic Fact Conflict Audit

- Status: `classified`

## c2.output_to_wealth.01

- Classification: `parser_failure`
- Confidence: `0.98`
- Original detector output: `['地支关系冲突:盘中不存在子午冲所需地支', '地支关系冲突:盘中不存在午辰冲所需地支']`
- Detector output after scope fix: `[]`
- Reason: the cited relations appear only in timing, counterfactual, or interrogative clauses; they do not assert 午 as a natal branch.
- Formal impact: full nonsealed preflight must be rerun under a new run id before FormalRunLock freeze
