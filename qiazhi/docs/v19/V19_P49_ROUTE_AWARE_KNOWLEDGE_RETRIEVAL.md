# V19 P49 Route-Aware Knowledge Retrieval

P49 connects the P47 rule graph runtime context to knowledge retrieval.

## Goal

Question routing is already personalized in P48. P49 makes knowledge retrieval route-aware too:

- build the rule graph runtime route pack first
- retrieve knowledge with chart route context
- attach route match scores and route reasons to retrieved knowledge
- preserve explicit user question intent as the stronger signal

## Runtime Behavior

`retrieve_knowledge` now reads `rule_graph_runtime_context` when present.

Each retrieved knowledge item may include:

- `route_match_score`
- `route_match_reasons`

The route context includes:

- selected graph knowledge IDs
- route topic lane counts
- route domain counts
- structure-specific route terms

## Scoring Boundary

Route bias is capped for non-exact route matches. This prevents broad route terms such as branch structure from pushing out explicit query matches such as month-command knowledge.

Exact selected route IDs can receive a stronger boost, but generic lane/domain matches remain bounded.

## Integration Points

- `POST /api/agent/turn`
- `POST /api/lab/guided-question-audit`
- `v19.synthetic_validation.guided_runner._agent_data_for_case`
- `v19.knowledge_store.retrieve_knowledge`
- `v19.bazi_guided_questions.build_guided_question_answer`

## Boundaries

P49 does not:

- activate rules
- mutate inference
- mutate answers
- learn from user feedback
- output prediction text

The route-aware score only changes retrieval priority and audit context.
