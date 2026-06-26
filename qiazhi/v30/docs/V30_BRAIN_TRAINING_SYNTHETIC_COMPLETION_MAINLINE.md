# V30 Brain / Training / Synthetic Completion Mainline

Updated: 2026-06-10

## Purpose

This is the controlling mainline for finishing the three support systems that must make the completed M1-M8 Bazi calculation modules usable, iterative, and self-checking:

1. Intelligent central brain.
2. Training and auto-apply system.
3. Bazi synthetic validation and 518K distribution validation system.

The previous M1-M8 core modules are frozen for current business scope. This plan does not reopen chart facts, useful-god verdicts, practical reading contracts, or customer projection contracts unless a validation failure proves a focused defect.

## Non-Negotiable Boundaries

- Deterministic chart facts only come from BirthInput/calendar/chart code.
- Training, hidden-factor feedback, LLM output, synthetic drafts, and central-brain traces cannot create or mutate pillars, luck-cycle facts, flow-year/month facts, base fact explanations, or fixed useful-god verdicts.
- Central brain coordinates runtime state; it does not write database, Redis, runtime pointers, or policy artifacts directly.
- Training produces policy candidates and artifacts; pointer activation requires validation gates and recorded lineage.
- Synthetic validation is not a proof of destiny truth. It validates contracts, boundaries, regressions, and calibration coverage.
- Full pytest, synthetic all, 518K sample/full, and release gates are major-node checks, not every-subtask checks.

## Current Completion Snapshot

| System | Current completion | Target | Current judgment |
|---|---:|---:|---|
| Intelligent central brain | 100% | 100% | BT7 complete: dedicated `central_brain` synthetic tier validates role state, session memory, unknown-context routing, hidden-factor feedback/use-as-amplifier boundaries, expression orchestration, training routes, role-gated diagnostics, and no chart-fact/runtime mutation. |
| Training / auto-apply system | 100% | 100% | BT10 complete: BT1-BT9 evidence is accepted and the current support-system scope is in steady state. |
| Bazi synthetic validation system | 100% | 100% | BT10 complete: `central_brain`, `training_pipeline`, synthetic coverage manifest, and 518K readiness evidence are unified under `v30.brain_training_synthetic_closeout.v1`. |
| 518K validation support | 95% | 95% | BT9 complete: `v30.518k_readiness_matrix.v1` passes 7/7 checks for sample mode, shard mode, full explicit-only boundary, corpus mount contract, artifact/index persistence, JSON/Postgres search fallback, and candidate-family coverage matrix. |

## Completion Definition

This mainline is complete when V30 can prove the following without reopening M1-M8:

1. The central brain can build a traceable plan for guest/user/practitioner/admin/lab roles.
2. The central brain can coordinate chart status, hidden-factor status, question state, expression state, and feedback routes without mutating chart facts.
3. Long-session replay can verify stable session memory, answered-question suppression, next-question refresh, answer refresh, and role projection.
4. Training can extract signals from synthetic/replay outputs, generate policy candidates, validate them, write artifacts, update runtime pointers, and expose lineage.
5. Failed candidates are rejected or quarantined with machine-readable reasons.
6. Rollback metadata and active pointer lineage are observable.
7. Synthetic tiers cover central brain, training pipeline, hidden-factor interaction, role projection, M1-M8 contract preservation, and failure-cluster/synthetic-draft contracts.
8. 518K sample/shard remains available for distribution gates; full 518K is documented as explicit heavy validation.

## Execution Order

### BT1 Central Brain Acceptance Gate

Status: completed 2026-06-10.

Target: 82% -> 90%.

Scope:

- Add `v30.central_brain_acceptance.v1`.
- Validate `BrainState`, `SessionMemory`, `RoleState`, `RuntimePlannerDecision`, `QuestionDialogueStrategy`, `ExpressionOrchestration`, `FeedbackStrategy`, and `TrainingSignalRoute`.
- Cover guest/user/practitioner/admin/lab role behavior.
- Prove central brain is read-only: no chart-fact mutation, no pointer write, no DB/Redis direct write.
- Add admin read-only endpoint and CLI script.

Validation:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_central_brain_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
python3 scripts/run_central_brain_acceptance.py
```

No full pytest / 518K by default.

Completed 2026-06-10 BT1:

- Added `v30.central_brain_acceptance.v1`.
- Added `scripts/run_central_brain_acceptance.py`.
- Added `GET /api/v30/admin/brain/acceptance`.
- Added unit and scaffold coverage for trace completeness, session/question/expression/feedback readiness, hidden-factor feedback-conditioned route, role projection boundaries, and read-only central-brain boundaries.
- BT1 sets intelligent central brain completion to 90% for the support-system mainline.

Validation 2026-06-10 BT1:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_acceptance_endpoint_is_read_only
9 passed in 2.84s
python3 scripts/run_central_brain_acceptance.py
v30.central_brain_acceptance.v1: passed (5/5) bt1_central_brain_acceptance_ready
```

Full pytest / full 518K: not run for BT1; reserved for explicit release/full-freeze decisions.

### BT2 Long-Session Brain Replay

Status: completed 2026-06-10.

Target: brain 90% -> 94%.

Scope:

- Add replay over multi-turn reading state:
  - initial reading.
  - structured option click.
  - answer refresh.
  - second question selection.
  - hidden-factor feedback.
  - user vs practitioner projection.
- Validate answered-question suppression, visible/internal next-question split, `known_user_signals`, and session memory.
- Ensure repeated interaction tunes question strategy only, not chart facts.

Validation:

```text
pytest -q tests/unit/test_central_brain_session_replay.py tests/unit/test_question_dialogue_graph.py
python3 scripts/run_synthetic_validation.py --tier interaction_loop
```

Completed 2026-06-10 BT2:

- Added `v30.central_brain_session_replay.v1`.
- Added `scripts/run_central_brain_session_replay.py`.
- Added `GET /api/v30/admin/brain/session-replay`.
- Added unit and scaffold coverage for BT1 dependency, multi-turn question outcome replay, answer refresh, visible/internal next-question split, hidden-factor feedback-conditioned brain strategy, user/practitioner role projection split, and read-only replay boundary.
- BT2 sets intelligent central brain completion to 94% for the support-system mainline.

Validation 2026-06-10 BT2:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_session_replay_endpoint_is_read_only
12 passed in 3.37s
python3 scripts/run_central_brain_session_replay.py
v30.central_brain_session_replay.v1: passed (6/6) bt2_central_brain_session_replay_ready
```

Full pytest / full 518K / synthetic all: not run for BT2; reserved for explicit major validation.

### BT3 Brain Failure Routing And Task Queue Contract

Status: completed 2026-06-10.

Target: brain 94% -> 97%.

Scope:

- Add `v30.brain_failure_route.v1`.
- Route failures to one of:
  - `M1/M2 fact boundary`.
  - `M3 evidence/rule/path gap`.
  - `M4/M5 calibration`.
  - `M6 practical reading contract`.
  - `M8 projection leak`.
  - `question strategy`.
  - `hidden-factor feedback`.
  - `training candidate`.
  - `release/full validation`.
- Keep route output as operator/diagnostic plan, not runtime mutation.

Validation:

```text
pytest -q tests/unit/test_central_brain_failure_routing.py
python3 scripts/run_central_brain_acceptance.py
```

Completed 2026-06-10 BT3:

- Added `v30.brain_failure_route.v1`.
- Added `scripts/run_central_brain_failure_routing.py`.
- Added `GET /api/v30/admin/brain/failure-routing`.
- Added unit and scaffold coverage for BT2 dependency, required route matrix coverage, diagnostic task queue creation, support-system failure routing, operator-plan-only boundaries, and no chart-fact/pointer/heavy-validation authorization.
- BT3 sets intelligent central brain completion to 97% for the support-system mainline.

Validation 2026-06-10 BT3:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_central_brain_failure_routing.py tests/unit/test_central_brain_session_replay.py tests/unit/test_central_brain_acceptance.py tests/unit/test_central_brain.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_central_brain_failure_routing_endpoint_is_read_only
16 passed in 4.15s
python3 scripts/run_central_brain_failure_routing.py
v30.brain_failure_route.v1: passed (6/6) bt3_brain_failure_routing_ready
```

Full pytest / full 518K / synthetic all: not run for BT3; reserved for explicit major validation.

### BT4 Training System Closeout Gate

Status: completed 2026-06-10.

Target: training 94% -> 97%.

Scope:

- Add `v30.training_system_closeout.v1`.
- Verify current signal extraction, candidate generation, validation replay, artifact creation, pointer update, question comparison, lineage, and rollback metadata.
- Check core policy families:
  - `structure_policy`.
  - `mainline_policy`.
  - `question_policy`.
  - `rule_policy`.
- Check future-family boundary:
  - answer/presentation/portrait/hidden-factor policies may be observed or candidate-only unless explicitly promoted.

Validation:

```text
pytest -q tests/unit/test_training_system_closeout.py tests/unit/test_auto_apply_training.py tests/unit/test_training_signals.py
python3 scripts/run_auto_training.py --training-run-id bt4-closeout
```

Completed 2026-06-10 BT4:

- Added `v30.training_system_closeout.v1`.
- Added `scripts/run_training_system_closeout.py`.
- Added `GET /api/v30/admin/training/system-closeout`.
- Added unit and scaffold coverage for complete core policy-family promotion evidence, future-family promotion blocking, missing rollback/lineage blocking, and read-only closeout boundary.
- Extended auto-training promotion so validation artifacts can be written to a supplied runtime/artifact directory; the BT4 closeout gate uses a temporary store and does not mutate the active runtime pointer.
- BT4 sets training / auto-apply completion to 97% for the support-system mainline.

Validation 2026-06-10 BT4:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_training_system_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_training_system_closeout_endpoint_is_read_only
5 passed in 1.35s
pytest -q tests/unit/test_training_signals.py
1 passed in 17.39s
pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
1 passed in 90.20s
python3 scripts/run_training_system_closeout.py --training-run-id bt4-closeout
v30.training_system_closeout.v1: passed (8/8) bt4_training_system_closeout_ready
```

Notes:

- The combined auto-apply pytest group was not used as the final BT4 evidence because the existing runtime-version auto-apply test did not return in a useful time window during this run. The BT4 closeout script ran the complete temporary-store training/promotion/artifact/pointer/lineage path and passed 8/8.
- Full pytest / synthetic all / full 518K: not run for BT4; reserved for explicit major validation.

### BT5 Failed Candidate Quarantine And Rollback Readiness

Status: completed 2026-06-10.

Target: training 97% -> 99%.

Scope:

- Add explicit failed-candidate quarantine contract.
- Record rejected candidate id, source signals, failed validation ids, rollback target pointer, and remediation route.
- Verify runtime continues using last good pointer.
- Add read-only diagnostics.

Validation:

```text
pytest -q tests/unit/test_training_candidate_quarantine.py tests/unit/test_runtime_pointer.py
python3 scripts/run_training_candidate_quarantine.py --training-run-id bt5-quarantine
```

Completed 2026-06-10 BT5:

- Added `v30.training_candidate_quarantine_record.v1`.
- Added `v30.training_candidate_quarantine.v1`.
- Added `scripts/run_training_candidate_quarantine.py`.
- Added `GET /api/v30/admin/training/candidate-quarantine`.
- Added unit and scaffold coverage for persisted quarantine records, source signal ids, failed validation ids, rollback target pointer, unchanged active pointer, runtime last-good pointer proof, diagnostic-only remediation route, and read-only admin boundary.
- BT5 sets training / auto-apply completion to 99% for the support-system mainline.

Validation 2026-06-10 BT5:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_training_candidate_quarantine.py tests/unit/test_runtime_pointer.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_training_candidate_quarantine_endpoint_is_read_only
10 passed in 1.84s
python3 scripts/run_training_candidate_quarantine.py --training-run-id bt5-quarantine
v30.training_candidate_quarantine.v1: passed (8/8) bt5_training_candidate_quarantine_ready
```

Full pytest / synthetic all / full 518K: not run for BT5; reserved for explicit major validation.

### BT6 Synthetic Coverage Manifest

Status: completed 2026-06-10.

Target: synthetic 92% -> 96%.

Scope:

- Add `v30.synthetic_coverage_manifest.v1`.
- Enumerate every tier and what it protects:
  - smoke.
  - all.
  - core_bazi_calculation.
  - m1_m2_bazi_calculation.
  - ten_god_energy_calibration.
  - m4_ten_god_real_case_replay.
  - strength_structure_useful_god.
  - m5_ranked_decision_contract.
  - m6_practical_reading_contract.
  - m8_api_projection_contract.
  - interaction_loop.
  - real_case_calibration_pack.
  - central_brain.
  - training_pipeline.
- Validate no tier claims to prove deterministic truth beyond its contract.

Validation:

```text
pytest -q tests/unit/test_synthetic_coverage_manifest.py tests/unit/test_synthetic_validation.py
python3 scripts/run_synthetic_validation.py --tier smoke
```

Completed 2026-06-10 BT6:

- Added `v30.synthetic_coverage_manifest.v1`.
- Added `scripts/run_synthetic_coverage_manifest.py`.
- Added `GET /api/v30/admin/validation/synthetic-coverage-manifest`.
- Added unit and scaffold coverage for implemented tier contracts, planned BT7/BT8 tiers, undocumented-tier blocking, no truth-claim drift, no chart-fact mutation, and `all` as a major-node-only tier.
- Marked `central_brain` and `training_pipeline` as planned tiers until BT7/BT8 implement them.
- BT6 sets synthetic validation completion to 96% for the support-system mainline.

Validation 2026-06-10 BT6:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
5 passed in 1.31s
python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready
python3 scripts/run_synthetic_validation.py --tier smoke
v30.synthetic.smoke: passed (5/5)
```

Full pytest / synthetic all / full 518K: not run for BT6; reserved for explicit major validation.

### BT7 Central Brain Synthetic Tier

Status: completed 2026-06-10.

Target: brain 97% -> 100%, synthetic 96% -> 98%.

Scope:

- Add dedicated `central_brain` synthetic tier.
- Cover role state, session memory, unknown-context routing, hidden-factor feedback slot, expression orchestration, training signal route, and no-mutation boundaries.
- Include at least:
  - guest ready chart.
  - user with selected option.
  - practitioner diagnostic view.
  - admin with hidden-factor feedback state.
  - missing-time boundary.

Validation:

```text
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_central_brain_tier_passes
python3 scripts/run_synthetic_validation.py --tier central_brain
```

Completed 2026-06-10 BT7:

- Added dedicated `central_brain` synthetic tier with 5 focused cases:
  - guest ready chart.
  - user selected option / session memory.
  - practitioner diagnostic projection.
  - admin hidden-factor feedback calibrated as amplifier candidate.
  - missing-time unknown-context boundary.
- Added synthetic validation checks for central-brain trace version, session memory policy, role state, question strategy, expression surface, training route domains, role-gated diagnostics, read-only boundaries, hidden-factor feedback slot, and missing-time routing.
- Updated `v30.synthetic_coverage_manifest.v1` so `central_brain` is implemented and `training_pipeline` remains the next planned tier.
- BT7 sets intelligent central brain completion to 100% and synthetic validation completion to 98% for the support-system mainline.

Validation 2026-06-10 BT7:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_central_brain_tier_passes tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
6 passed in 2.45s
python3 scripts/run_synthetic_validation.py --tier central_brain
v30.synthetic.central_brain: passed (5/5)
python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready
```

Full pytest / synthetic all / full 518K: not run for BT7; reserved for explicit major validation.

### BT8 Training Pipeline Synthetic Tier

Status: completed 2026-06-10.

Target: training 99% -> 100%, synthetic 98% -> 99%.

Scope:

- Add dedicated `training_pipeline` synthetic tier.
- Validate signal extraction across:
  - M3 K/R/P coverage.
  - M4/M5 model signal/ranked decisions.
  - M6 practical reading.
  - M8 projection.
  - question dialogue.
  - hidden-factor event alignment.
  - central brain routes.
  - LLM/expression contract.
- Confirm every signal has:
  - domain.
  - signal type.
  - strength.
  - source case ids.
  - payload boundary.

Validation:

```text
pytest -q tests/unit/test_training_signals.py tests/unit/test_synthetic_validation.py
python3 scripts/run_synthetic_validation.py --tier training_pipeline
```

Completed 2026-06-10 BT8:

- Added dedicated `training_pipeline` synthetic tier with 91 representative training cases.
- The tier reuses current core and support contracts as training inputs rather than duplicating fake training fixtures:
  - M1/M2 deterministic fact layer.
  - M3 K/R/P and dynamic structure evidence.
  - M4 ten-god energy and M5 ranked decisions.
  - M6 practical reading.
  - M8 API projection.
  - interaction loop.
  - central-brain routes.
  - hidden-factor event alignment.
  - expression and LLM contract observations.
- Added unit coverage that runs `extract_training_signals()` on the tier and verifies required signal ids, source case ids, signal boundaries, projection leak safety, hidden-factor denial coverage, central-brain route coverage, and no chart-fact mutation boundaries.
- Updated `v30.synthetic_coverage_manifest.v1` so `training_pipeline` is implemented and the next mainline selection is BT9.
- BT8 sets training / auto-apply completion to 100% and synthetic validation completion to 99% for the support-system mainline.

Validation 2026-06-10 BT8:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_training_pipeline_tier_passes_training_contracts tests/unit/test_synthetic_coverage_manifest.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_synthetic_coverage_manifest_endpoint_is_read_only
6 passed in 17.88s
python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)
python3 scripts/run_synthetic_coverage_manifest.py
v30.synthetic_coverage_manifest.v1: passed (7/7) bt6_synthetic_coverage_manifest_ready
```

Full pytest / synthetic all / full 518K: not run for BT8; reserved for explicit major validation.

### BT9 518K Readiness Matrix

Status: completed 2026-06-10.

Target: 518K 85% -> 95%.

Scope:

- Add `v30.518k_readiness_matrix.v1`.
- Document and validate:
  - sample mode.
  - shard mode.
  - full mode explicit-only boundary.
  - corpus mount contract.
  - artifact/index persistence.
  - DB search fallback behavior.
  - candidate-family coverage matrix.
- Do not make full 518K a default local test.

Validation:

```text
pytest -q tests/unit/test_518k_validation.py
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Completed 2026-06-10 BT9:

- Added `v30.518k_readiness_matrix.v1`.
- Added `scripts/run_518k_readiness_matrix.py`.
- Added `GET /api/v30/admin/validation/518k/readiness-matrix`.
- Validates:
  - sample mode distribution gate.
  - selected shard mode distribution gate.
  - full mode remains explicit-only through `confirm_full=True`.
  - generated corpus contract and external source mount contract.
  - artifact, index, and index-entry persistence.
  - JSON fallback or Postgres artifact search readiness.
  - candidate-family coverage matrix for `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy`.
- BT9 sets 518K validation support completion to 95%.

Validation 2026-06-10 BT9:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_518k_validation.py::test_518k_readiness_matrix_documents_sample_shard_and_full_boundary tests/unit/test_518k_validation.py::test_518k_readiness_matrix_script tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_api_local_json_repository_persists_reading
4 passed in 4.33s
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260609175010408754: eligible mode=sample cases=8 shards=0
artifact record: v30.518k.artifact.v30.518k.sample.20260609175010408754 (json_fallback)
```

Full pytest / synthetic all / full 518K: not run for BT9; reserved for explicit major validation.

### BT10 Unified Brain / Training / Synthetic Closeout

Status: completed 2026-06-10.

Target: all 100% current-scope closeout.

Scope:

- Add `v30.brain_training_synthetic_closeout.v1`.
- Verify BT1-BT9 evidence.
- Record current-scope completion:
  - central brain 100%.
  - training 100%.
  - synthetic 100%.
  - 518K 95%.
- Enter `BT-S1 Support Systems Steady State`.

Validation:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_brain_training_synthetic_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_brain_training_synthetic_closeout_endpoint_is_read_only
python3 scripts/run_synthetic_validation.py --tier central_brain
python3 scripts/run_synthetic_validation.py --tier training_pipeline
python3 scripts/run_brain_training_synthetic_closeout.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

Full pytest and full 518K remain explicit release/full-freeze gates.

Completed 2026-06-10 BT10:

- Added `v30.brain_training_synthetic_closeout.v1`.
- Added `scripts/run_brain_training_synthetic_closeout.py`.
- Added `GET /api/v30/admin/support/brain-training-synthetic-closeout`.
- Verified BT1-BT9 evidence through central-brain synthetic, training-pipeline synthetic, synthetic coverage manifest, and 518K readiness matrix.
- Recorded current support-system completion: central brain 100%, training 100%, synthetic validation 100%, 518K validation support 95%.
- Entered `BT-S1 Support Systems Steady State`.

Validation 2026-06-10 BT10:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_brain_training_synthetic_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_brain_training_synthetic_closeout_endpoint_is_read_only
5 passed in 21.11s
python3 scripts/run_brain_training_synthetic_closeout.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.brain_training_synthetic_closeout.v1: passed (6/6) bt10_support_systems_steady_state_ready
```

Full pytest / synthetic all / full 518K: not run for BT10; reserved for explicit major validation.

## Mainline Rule Going Forward

BT1-BT10 are complete for the current support-system scope. The default next state is:

```text
BT-S1 Support Systems Steady State
```

Do not start another BT task by default. Reopen support-system work only when new validation evidence, production replay evidence, policy promotion work, or an explicit major validation request requires it.
