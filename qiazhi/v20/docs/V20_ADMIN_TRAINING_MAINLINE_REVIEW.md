# V20 Admin Training Mainline Review

## Current Focus

Admin self-training is an operational control plane, not the whole system mainline.
The page now supports script registry, background execution, progress, pause, result summary, machine optimization gates, direct runtime apply for supported optimizer writers, activation history, training cadence planning, and duplicate-run cooldown gates.

## Review Findings

1. Admin training page completion must not be reported as global system completion.
   The registry now derives `mainline_completion` from a lightweight component snapshot instead of a hard-coded 100%. Heavy full-system status remains under `/api/v20/system/status`.

2. Direct optimizer writers are intentionally explicit.
   `training_bundle` and `role_interaction_training` have runtime pointer writers and can directly apply after machine gate. `rule_iteration`, `knowledge_review`, `corpus_precompute`, and `ops_validation` now report `optimizer_writer_missing` instead of falling back to human review.

3. Training result parsing still depends on the JSON payload visible in task log tail.
   A future hardening pass should persist an explicit artifact manifest from every script.

4. Positive end-to-end test coverage is still thinner than blocked-path coverage.
   Current tests prove missing-writer and blocked paths. The next test gap is a direct optimizer task that reaches `publish_preview.ready` and writes a pointer.

## Current Completion Model

`/api/v20/admin/training/tasks/registry` exposes:

- `mainline_completion.status`
- `mainline_completion.percent`
- `mainline_completion.components`
- `mainline_completion.remaining_items`
- `parameter_impact`
- `training_plan`

Components:

- `admin_training_page`
- `knowledge_mainline`
- `rule_iteration`
- `corpus_precompute`
- `ops_validation`

## Training Plan And Dedupe

The registry now exposes `training_plan`:

- `profiles`: Fast, Nightly, Weekly, and Full learning profiles.
- `optimization_topics`: portrait, rule, knowledge, intelligent QA, role experience, and feature/corpus training topics.
- `recommended_cadence`: daily fast iteration, nightly deterministic replay expansion, and weekly rule deep training.
- `synthetic_rule_plan`: synthetic coverage gaps converted into next training targets.
- `dedupe_summary`: cooldown-blocked tasks and tracked task count.

Every visible task also exposes `dedupe_policy`. A task that succeeded recently with the same script/default arguments is blocked until its cooldown expires:

- light: 1 hour
- medium: 6 hours
- heavy: 24 hours

This prevents repeated no-input training while still allowing failed or paused tasks to rerun.

## Training Topics

Training is organized as topic -> atomic training -> parameter target -> synthetic gate:

- `portrait`: tunes portrait axis weights, confidence thresholds, role portrait depth, and topic projection weights.
- `rule`: tunes rule weights, subcondition thresholds, counterexample penalties, and DecisionRegistry priority.
- `knowledge`: tunes knowledge-rule mapping weights, answer guidance weights, counterexample coverage, and source trust.
- `intelligent_qa`: tunes question source weights, rank weights, DAG transition weights, and mainline focus weights.
- `role_experience`: tunes role question order, visibility level, question count, and seed-fit policy.
- `feature_corpus`: tunes feature thresholds, coverage priors, similar-case weights, and corpus shard quality.

Each topic declares its atomic scripts, target roles, synthetic gates, and whether a runtime optimizer writer exists. Missing writers are surfaced as `optimizer_writer_status = missing_or_partial` instead of being hidden behind a review workflow.

## Parameter Impact

Supported training families automatically optimize runtime parameters through machine gates.

The registry now reports `parameter_impact.status = partial`:

- `training_bundle`: can affect orchestrator runtime policy payload through an auto gated active pointer.
- `question_policy`: can affect role-view question ordering through automatic replay/promotion gated pointer activation.
- `rule_iteration`: optimizer writer missing; artifacts exist but cannot directly tune runtime yet.
- `knowledge_review`: optimizer writer missing; artifacts exist but cannot directly tune runtime yet.
- `corpus_precompute`: artifact/index path only.
- `ops_validation`: validation only.

Any actual runtime parameter change still requires a machine gate and a version pointer writer. Running a supported training script triggers the gate automatically; if the gate blocks, runtime is unchanged.

Admin UI no longer exposes human accept/reject/defer. It shows:

- `机器优化 gate`: whether the result can enter direct optimization.
- `直接生效`: whether a runtime optimizer writer exists.
- `重试生效`: manual retry for gated apply, only enabled when a task has a concrete runtime pointer writer (`training_bundle`, currently `role_interaction_training` inside question policy); failed gates do not write runtime.

## Next Tasks

1. Build runtime optimizer writers for `rule_iteration`, `knowledge_review`, `corpus_precompute`, and `ops_validation`.
2. Add explicit artifact manifests to training task state.
3. Replace cooldown-only dedupe with artifact/ledger cursor hashes.
4. Add one positive direct-optimizer end-to-end test.
5. Split and commit the admin training changes separately from unrelated system changes.
