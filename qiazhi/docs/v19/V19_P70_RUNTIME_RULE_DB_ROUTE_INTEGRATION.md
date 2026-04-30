# V19 P70 Runtime Rule DB Route Integration

## Goal

P70 connects the synchronized runtime Rule DB to the Rule Graph Orchestrator. After server sync, active Rule DB records can participate in chart-specific route selection, guided question ranking, and answer evidence packaging.

## Scope

- Read active runtime Rule DB records as route candidates.
- Preserve deterministic graph scoring and arbitration.
- Keep Rule DB records as route/evidence context only.
- Do not mutate answers, inference results, or rule activation state.

## Runtime Policy

Runtime Rule DB candidates may influence:

- selected route paths
- guided question ordering
- evidence pack bindings
- route-aware knowledge retrieval

Runtime Rule DB candidates may not:

- output fortune or verdict text
- change result cards
- activate disabled engine rules
- bypass synthetic gates

## Validation

- `test_p70_rule_graph_can_route_runtime_rule_db_records`
- `test_fast.sh`

## Guardrails

- `P70_RUNTIME_RULE_DB_ROUTE_INTEGRATION`
- `RULE_DB_ROUTE_CONTEXT_ONLY`
- `NO_RESULT_MUTATION`
- `NO_ANSWER_MUTATION`
- `NO_RUNTIME_RULE_ACTIVATION`
