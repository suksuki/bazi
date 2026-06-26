# V20 Training Optimization Mainline

See also: `docs/V20_MAINLINE_TRAINING_ROADMAP.md`.

## Principle

Training must optimize system parameters through machine gates and versioned runtime pointers.
No human review flow is part of the training path.

## Pipeline

`topic -> atomic training -> artifact manifest -> synthetic gate -> optimizer writer -> active pointer -> runtime consume`

## Topics

| Topic | Roles | Atomic Training | Parameter Targets | Gate | Writer Status |
|---|---|---|---|---|---|
| Portrait | guest, user, practitioner, admin | `rule_portrait_batch`, `dynamic_decision_training`, `practitioner_calibration_training` | portrait axis weight, confidence threshold, role depth, topic projection | portrait alignment, negative boundary, role separation | ready |
| Rule | practitioner, admin | `rule_synthetic_training`, `rule_subcondition_split`, `rule_replay_eval`, `decision_registry_iteration` | rule weight, subcondition threshold, counterexample penalty, registry priority | rule precision, recall, counterexample replay | ready |
| Knowledge | practitioner, admin | `knowledge_rule_review_overlay`, `extract_rules_llm_draft`, `training_iteration_deep` | knowledge-rule mapping, answer guidance, source trust, counterexample coverage | knowledge alignment, answer boundary, traceability | ready |
| Intelligent QA | guest, user, practitioner, admin | `question_source_training`, `question_ranking_training`, `question_dag_training`, `training_iteration_fast` | source weight, rank weight, DAG transition, mainline focus | question focus, DAG coherence, role leakage | ready |
| Role Experience | guest, user, practitioner, admin | `role_interaction_training`, `question_dag_training`, `synthetic_case_suite` | role ordering, visibility, question count, seed-fit | role separation, role observation, question focus | ready |
| Feature Corpus | admin | `nightly_executor_skeleton`, `full_precompute_preview`, `training_iteration_deep` | feature threshold, coverage prior, similar-case weight, shard quality | 518K distribution, core feature, negative boundary | ready |
| Structure Dynamics | guest, user, practitioner, admin | `structure_dynamics_synthetic`, `structure_dynamics_corpus_distribution`, `synthetic_case_suite`, `rule_replay_eval` | dynamic path weight, semantic match threshold, time trigger weight, structure stability floor | path consistency, semantic coverage, counterexample boundary, time blocker | ready |

## Current Sprint

1. Build `rule_runtime_pointer`. Done.
2. Connect `rule_iteration` activation to the new writer. Done.
3. Keep blocked behavior explicit when replay/registry artifacts are missing. Done.
4. Add tests for pointer write and admin direct apply. Done.
5. Build `portrait_runtime_pointer` and connect `rule_portrait_batch` to `portrait_policy`. Done.
6. Build `knowledge_runtime_pointer` and connect `knowledge_rule_review_overlay` to `knowledge_review`. Done.
7. Build `question_runtime_pointer` and connect source/ranking/DAG training to `question_policy`. Done.
8. Build `corpus_runtime_pointer` and connect full corpus artifacts to `corpus_precompute`. Done.

## Next Sprints

1. Broaden structure dynamics 518K path distribution from the current small shard to larger scheduled shards.
2. Expand synthetic cases from smoke coverage to topic-level positive / negative / boundary / metamorphic sets.
3. Accumulate real role/question feedback signals so role_view can move from limited data to stronger runtime candidates.
4. Keep Admin UI aligned to runtime pointers, direct activation state, context binding, and machine blocker reasons.

## Current Runtime Consumption

Runtime consumption is the current completion gate for training usefulness:

```text
consumed pointer families: 8 / 8
consumption percent: 100%
remaining consumers: none
active/candidate families: rule, portrait, corpus, structure_dynamics, question, knowledge, role_view, orchestrator
next focus: larger replay gates and real interaction signal volume
```
