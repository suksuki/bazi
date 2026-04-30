# V19 P47 Rule Graph Runtime Context

P47 turns the P46 Rule Graph Orchestrator into a runtime route pack used by the measurement system.

## Goal

When a chart is calculated, the system should carry a chart-specific rule and knowledge route package:

- primary question route
- income structure route
- structure overview route

The package is deterministic and auditable. It does not enable production rules, mutate inference results, or change user-facing conclusions.

## Runtime Entry Point

`v19.rule_graph_runtime_context.build_rule_graph_runtime_context`

Inputs:

- `chart`
- `time_context`
- `inference_context`
- `knowledge_context`
- user message
- selected guided question key

Outputs:

- route summaries
- merged selected paths
- selected knowledge IDs
- selected candidate rule IDs
- lane/domain counts
- LLM-safe compact prompt context
- answer audit status

## Integration Points

- `POST /api/agent/turn`
- `POST /api/agent/structure`
- `POST /api/lab/guided-question-audit`
- `v19.synthetic_validation.guided_runner._agent_data_for_case`
- `v19.llm.build_agent_messages`
- `v19.bazi_guided_questions.build_guided_question_answer`

## Boundaries

P47 still keeps the following disabled:

- production rule activation
- answer mutation
- domain prediction output
- black-box model inference
- user feedback driven rule updates

The route pack can guide retrieval, audit, prompt compaction, and future UI review, but it cannot rewrite `income_stability` or any core chart signal.

## Future Slot

GNN/RL are still reserved. The runtime context provides the eventual data boundary for reranking or dialog policy, but the active route logic remains deterministic.
