# V20 Orchestrator Brain Contract

`brain_state` is the public summary layer for the V20 intelligent orchestrator.
It does not create chart facts, activate rules, or override deterministic
decisions. It summarizes the already-built runtime spine so UI, answer
composition, and LLM assist prompts use the same mainline.

## Runtime Position

```text
ChartFacts
-> CoreInference
-> FeatureLayer
-> RuleDecision / PortraitProjection
-> StructureDynamics
-> OrchestratorEvidence
-> MainlineArbitration
-> QuestionMainlineFocus
-> BrainState
-> BrainMemorySignal
-> AnswerPlan / AnswerText / LLM Context
```

## Public Summary

`brain_state.public_summary` is user-safe and role-projectable. Its stable keys
are:

- `headline`
- `primary_domain`
- `primary_title`
- `primary_nodes`
- `selection_reasons`
- `selected_question_key`
- `selected_question_title`
- `selected_question_domain`
- `question_focus_status`
- `coordination_status`
- `coordination_note`
- `dynamic_chain`
- `chain_state`
- `energy_state`
- `stability_state`
- `time_layer_status`
- `supporting_evidence`
- `next_action`

Public evidence rows may include only:

- `domain`
- `label`
- `summary`
- `confidence`
- `boundary`

They must not include internal routing keys such as `source_key` or raw evidence
ids.

## Consumers

- Frontend answer panel renders `public_summary`.
- Deterministic answer composition uses `public_summary` for the visible
  `中枢判断` line.
- LLM answer rewrite context receives the compact public brain state.
- LLM practitioner answer card receives the compact public brain state.
- Analyst/admin projections may keep `review_summary`; user projection must not.
- Analyst/admin/lab projections may inspect `brain_memory_signal`; user projection
  must not expose it.

## Memory Signal

`brain_memory_signal` compiles the current brain state, mainline arbitration,
question focus, practitioner selections, and latent event answers into
appendable training material. It never changes the current runtime answer,
rules, or mainline.

It is intended for offline orchestrator memory training and future validated
rerank policies, not for user-visible verdicts.

## Guardrails

- `BRAIN_STATE_SUMMARIZES_EXISTING_RUNTIME_OUTPUTS`
- `BRAIN_STATE_DOES_NOT_CREATE_FACTS`
- `PUBLIC_SUMMARY_EXCLUDES_INTERNAL_SOURCE_KEYS`
- `LLM_CAN_EXPLAIN_BRAIN_STATE_NOT_OVERRIDE_IT`
- `NO_RUNTIME_RULE_OR_MAINLINE_MUTATION`

The contract is enforced by `tests/test_v20_orchestrator_brain_state.py`.
Current implementation progress is tracked in
`docs/V20_ORCHESTRATOR_BRAIN_PROGRESS.md`.
