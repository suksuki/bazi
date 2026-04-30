# V19 P51 UI Framework Alignment

## Decision

P51 aligns the visible UI with the P46-P50 framework outputs without changing inference, rules, or answer content.

The system already produces:

- `rule_graph_runtime_context` for deterministic route selection.
- `guided_question_context.question_personalization_context` and `questions[].personalization` for chart-specific question ordering.
- `knowledge_context.items[].route_match_score` for route-aware retrieval.
- `guided_question_answer.evidence_pack` for unified answer facts, knowledge, and graph bindings.

## UI Surfaces

### Lab

`/lab` now displays:

- Rule Graph Route Pack: selected routes, topic lanes, audit status, and mutation guard.
- Personalized Questions: ranked question labels, route boost, bucket, and score.
- Guided Answer Evidence Pack: fact scopes, applied knowledge, runtime route knowledge, binding counts, audit status, and mutation guard.
- Knowledge Context route scores and route match reasons.

### Oracle

`/oracle` now displays:

- Personalized question chips with a lightweight structure-match indicator.
- Guided answer evidence summary after the answer, showing evidence counts and audit state.
- Feedback payload carries the evidence pack for later audit.

## Guardrails

- UI consumes framework context only.
- UI does not activate rules.
- UI does not mutate chart inference or answer semantics.
- User-facing oracle avoids exposing raw internal ids in the main answer body.
- Lab may expose internal ids because it is an analyst review surface.

## Verification

- Static UI wiring test checks lab/oracle surfaces and framework tokens.
- Existing P46-P50 tests continue to verify rule graph, personalized questions, route-aware retrieval, and evidence pack construction.
