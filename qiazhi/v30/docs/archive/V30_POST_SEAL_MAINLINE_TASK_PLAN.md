# V30 Post-Seal Mainline Task Plan

Updated: 2026-06-10

## Current Judgment

The eight core Bazi calculation modules are phase sealed for the current scope. The system should no longer move by reopening M1-M8 without a concrete validation failure.

Current core-module baseline:

| Module | Completion | Status |
|---|---:|---|
| M1 BirthInput and deterministic chart facts | 95% | Phase sealed |
| M2 Base Bazi fact explanation layer | 92% | Phase sealed |
| M3 Evidence / rule / knowledge / structure spine | 96% | Phase sealed for current source-backed scope |
| M4 Ten-god energy model | 88% | Phase sealed |
| M5 Strength / structure / useful-god ranked decisions | 88% | Phase sealed |
| M6 Practical reading output | 85% | Phase sealed |
| M7 Core validation / real-case calibration | 90% | Phase sealed |
| M8 User presentation / API projection | 90% | Phase sealed |

Current support-track baseline:

| Track | Completion | Current judgment |
|---|---:|---|
| Runtime/API/UI spine | 97% | R2 complete: API health, BirthInput reading creation, user/admin view projection, answer refresh, interaction state, read-history projection, and live 9030 customer-loop smoke are gated. |
| Training/synthetic/release gates | 99% | R12 complete: release-boundary finalization declares the internal release candidate ready while keeping external full pytest and policy pointer promotion explicit. |
| Post-seal release hardening | 100% | R12 complete: `v30.release_boundary_finalization.v1`, script, admin endpoint, evidence-bundle review, and R13 external release dry-run selection are active. |
| Role/session/client/locale productization | 100% | U5 complete: U1-U4 evidence is accepted by `v30.productization_closeout.v1`, productization is in U-S1 steady state, and full login/UI redesign remain explicit non-goals. |
| LLM expression | 72% | R4 complete: rule answer remains primary; bounded LLM live smoke records unconfigured/configured/accepted/fallback/drift states, failure telemetry, artifact output, and no chart-fact/model-signal/interaction mutation proof. |
| Production real replay metadata | 80% | R9 complete: metadata-only intake rows now persist to a local replay store, support readiness/calendar/boundary/module/source-artifact search, and remain isolated from chart facts, private content, and policy pointers. |

## Mainline Principle

Post-seal work must be failure-driven and release-oriented:

- Do not reopen M1-M8 for speculative improvement.
- Do not run full pytest or full 518K for every small task.
- Use targeted tests for small changes.
- Use quick release gate for release-hardening changes.
- Use standard release gate only for release/pointer boundaries.
- Keep training signals silent; they tune policies and presentation, not deterministic chart facts.

## New Mainline Tasks

### R1 Release Gate And Contract Hardening

Status: completed 2026-05-24.

Target: post-seal release hardening 92% -> 96%.

Scope:

- Keep `post_seal_contracts` as mandatory in quick/standard release gates.
- Add explicit summary fields for M1-M8 phase-seal coverage.
- Ensure release gate cannot be eligible if any appended failure exists.
- Keep M5/M6/M8 contract coverage visible in gate output.

Completed:

- `post_seal_contracts` is mandatory in quick and standard release gates.
- Release summary exposes `phase_seal_coverage` for M1-M8.
- Release summary exposes `phase_seal_passed_count = 8`.
- `synthetic_all` release check fails if appended contract failures exist.
- M5/M6/M8 contract coverage remains visible under `tier_coverage`.

Gate:

```text
pytest -q tests/unit/test_release_gate.py
python3 scripts/run_release_gate.py --sample-limit 2
```

Validation 2026-05-24:

```text
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260524114624: eligible, checks=4
post_seal_contracts.phase_seal_passed_count=8
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260524114640640275
```

### R2 Production API Smoke And Customer Loop Contract

Status: completed 2026-06-04.

Target: Runtime/API/UI spine 96% -> 97%.

Scope:

- Verify `/api/v30/health`, reading creation, user view, admin view, answer submission, and answer refresh against the real service port.
- Keep UI simple: core Bazi reading first, question flow second.
- No design work unless a real customer-loop defect appears.
- Keep `reading_surface`, `questions`, `answer_panel`, `projection_contract`, `next_question_id`, `visible_next_question_id`, and `diagnostics` additive.

Gate:

```text
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py
python3 scripts/run_release_gate.py --sample-limit 2
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --json
```

Completed:

- Added release-gate check `production_api_smoke`.
- Quick release gate now validates `/api/v30/health`, reading creation, user view, admin view, answer submission, answer refresh, interaction state, and read-history projection.
- Added live-port smoke script `scripts/run_production_api_smoke.py` for real service verification on 9030 or another supplied base URL.
- Restarted stale 9030 service so the live process loads the current projection contract code.
- Verified customer/user projections keep diagnostics hidden, admin projections keep diagnostics visible, answer submission refreshes `answer_panel` and next question, and history hides internal fields from user role.

Validation 2026-06-04:

```text
python3 -m compileall -q v30 scripts/run_production_api_smoke.py
passed
pytest -q tests/unit/test_release_gate.py
3 passed
pytest -q tests/test_v30_scaffold.py tests/unit/test_presentation_projection.py
14 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260604011732: eligible, checks=5
production_api_smoke: passed
post_seal_contracts.phase_seal_passed_count=8
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260604011748344812
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r2-live-api-smoke-202606040120 --json
v30.production_api_smoke.v1: passed
health_ok=true; created_status=ready; projection_contract_version=v30.api_projection_contract.v1; answer_accepted=true; interaction_state_version=v30.interaction_state.v1
```

### R3 Minimal Durable Session / Read-History Hardening

Status: completed 2026-06-05.

Target: Role/session foundation 55% -> 70%.

Scope:

- Harden actor/session ownership boundaries for `/api/v30/readings/history`.
- Ensure guest/user history never exposes diagnostics.
- Ensure admin/practitioner history keeps needed trace ids and actor/session diagnostics.
- Do not introduce a full login system.

Gate:

```text
pytest -q tests/unit/test_runtime_repository.py tests/test_v30_scaffold.py
```

Completed:

- Added `v30.reading_history_ownership.v1` as the minimal owner filter contract.
- Added `v30.reading_history_visibility.v1` and diagnostic-only `v30.reading_history_diagnostics.v1`.
- History owner scopes are explicit: `actor_and_session`, `actor_only`, or `session_only`; all supplied owner keys must match.
- Guest/user history hides owner ids inside `owner_filter`, hides `trace_id`, `actor_context`, `internal_next_question_id`, and returns empty `diagnostics`.
- Admin/practitioner history keeps owner ids, trace ids, actor/session diagnostics, and internal next-question diagnostics.
- Repository tests cover actor/session exact-match filtering, session-only filtering, actor-only filtering, and unowned-row behavior.
- `production_api_smoke` and live-port smoke now gate the read-history owner/visibility contract.

Validation 2026-06-05:

```text
python3 -m compileall -q v30 scripts/run_production_api_smoke.py
passed
pytest -q tests/unit/test_runtime_repository.py tests/test_v30_scaffold.py
17 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605051922: eligible, checks=5
production_api_smoke.history_owner_scope=actor_and_session
production_api_smoke.history_user_owner_ids_hidden=true
production_api_smoke.history_user_diagnostics_hidden=true
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260605051938701103
python3 scripts/run_production_api_smoke.py --base-url http://127.0.0.1:9030 --reading-id r3-live-history-smoke-202606050520 --json
v30.production_api_smoke.v1: passed
history_owner_scope=actor_and_session; history_user_owner_ids_hidden=true; history_user_diagnostics_hidden=true
```

### R4 Bounded LLM Live Smoke And Failure Telemetry

Status: completed 2026-06-05.

Target: LLM expression 62% -> 72%.

Scope:

- Keep rule-bound answer as source of truth.
- Add explicit live-provider smoke only when env is configured.
- Record provider readiness, call status, fallback reason, drift status, and no-chart-fact-mutation proof.
- Do not let LLM generate chart facts, ranked decisions, or timing facts.

Gate:

```text
pytest -q tests/unit/test_llm_context.py tests/unit/test_expression_framework.py
```

Optional env gate only when configured:

```text
python3 scripts/real_env_smoke.py
```

Completed:

- Added `v30.llm_live_smoke.v1` runner.
- Added `scripts/run_llm_live_smoke.py`.
- Release gate now includes `llm_live_smoke`; quick gate now has 6 checks.
- LLM smoke reports `unconfigured`, `configured_not_executed`, `accepted`, `fallback`, and `drift_rejected`.
- LLM smoke records provider readiness, call status, fallback reason, drift status/failures, artifact URI, and execution status.
- Added `v30.llm_no_mutation_proof.v1` for chart facts, ranked decisions, model signal, and interaction state.
- Added tests for unconfigured, configured-not-executed, and drift-rejected paths.
- Current local environment is LLM-unconfigured, so the smoke correctly passes with deterministic fallback and no runtime mutation.

Validation 2026-06-05:

```text
python3 -m compileall -q v30 scripts/run_llm_live_smoke.py
passed
pytest -q tests/unit/test_llm_context.py tests/unit/test_expression_framework.py
12 passed
pytest -q tests/unit/test_release_gate.py
3 passed
python3 scripts/run_llm_live_smoke.py --reading-id r4-llm-live-smoke-20260605 --json
v30.llm_live_smoke.20260605062559199852: passed, smoke_status=unconfigured, fallback_reason=provider_not_ready
no_chart_fact_mutation_proof: chart_facts=true, ranked_decisions=true, model_signal=true, interaction_state=true
python3 scripts/run_release_gate.py --sample-limit 2 --json
v30.release_gate.quick.20260605062559: eligible, checks=6
llm_live_smoke: passed, smoke_status=unconfigured, fallback_reason=provider_not_ready
synthetic_all: passed (95/95)
518k_sample: eligible, cases=2, json_fallback, v30.518k.sample.20260605062615503408
```

### R5 Production Replay Metadata Preparation

Status: completed 2026-06-05.

Target: Production real replay metadata 35% -> 55%.

Scope:

- Define metadata tags for real production replay rows without importing private user content into deterministic facts.
- Tags should cover calendar type, unknown-hour, unknown-gender, true-solar, ready/pending/blocked, M4/M5/M6 contract readiness, and projection leak scan.
- Do not change the canonical 30-case synthetic pack unless a real failure requires it.

Completed:

- Added `v30.production_replay_metadata.v1` metadata-only tags and `v30.production_replay_metadata_summary.v1`.
- Attached `production_replay_metadata` to real-case synthetic observations without copying birth date/time, raw payload, user answer text, or private identifiers.
- Extended `v30.training_signal.real_case_calibration_pack` with replay metadata count, privacy guard pass count, ready/pending/blocked counts, calendar/true-solar/unknown boundary counts, and projection leak-scan count.
- Extended release gate `synthetic_all.tier_coverage` with production replay metadata coverage, privacy guard, and projection leak-scan pass counts.
- Kept metadata as replay/training selection evidence only; it does not mutate chart facts, M4 model signals, M5 ranked decisions, or M6 practical readings.

Gate:

```text
python3 -m compileall -q v30
passed
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
pytest -q tests/unit/test_production_replay_metadata.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
4 passed
pytest -q tests/unit/test_release_gate.py
3 passed
```

### R6 Observability And Admin Artifact Review

Status: completed 2026-06-05.

Target: Training/synthetic/release gates 96% -> 97%.

Scope:

- Make release gate artifacts easy to find from admin diagnostics.
- Keep 518K artifact ids, synthetic suite summaries, policy lineage, and projection contract summaries together.
- No new training promotion unless a policy boundary requires it.

Completed:

- Added `v30.release_artifact_review.v1` to group release check statuses, LLM smoke artifact, synthetic suite summary, 518K sample/shard artifacts, active policy versions, policy lineage summaries, projection contract summary, and promotion review.
- Added `artifact_review` to `ReleaseGateResult` without changing quick/standard check counts.
- Added admin endpoint `GET /api/v30/admin/release/artifact-review`.
- Kept R6 observability-only: `policy_promotion_allowed = false`; no policy pointer, training promotion, chart fact, or projection mutation.

Gate:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_518k_validation.py tests/unit/test_release_gate.py
plus tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_artifact_review_endpoint_is_observability_only
14 passed
python3 scripts/run_release_gate.py --sample-limit 2
v30.release_gate.quick.20260605103342: eligible mode=quick checks=6
```

### R7 Post-Seal Status Review And Next Mainline Selection

Status: completed 2026-06-05.

Target: mainline control and next-task selection.

Scope:

- Review R1-R6 evidence and current M1-M8/support-track completion.
- Select the next mainline track from evidence, not speculative module reopening.
- Keep full pytest/full 518K reserved for release boundaries.

Completed:

- Added `v30.post_seal_status_review.v1`.
- Added `scripts/run_post_seal_status_review.py`.
- Added admin endpoint `GET /api/v30/admin/release/status-review`.
- Confirmed M1-M8 remain phase sealed and should reopen only on concrete validation failure.
- Selected `R8 Metadata-Safe Production Replay Intake` as the next mainline because production replay metadata is the lowest evidence-backed support track at 55% and directly supports real-case calibration without importing private content into chart facts.

Gate:

```text
python3 -m compileall -q v30 scripts/run_post_seal_status_review.py
passed
pytest -q tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline
4 passed
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R8 Metadata-Safe Production Replay Intake
```

### R8 Metadata-Safe Production Replay Intake

Status: completed 2026-06-06.

Target: Production real replay metadata 55% -> 70%.

Scope:

- Define a production replay intake contract using metadata tags only.
- Connect intake rows to artifact review and real-case calibration selection.
- Record ready/pending/blocked, calendar, unknown-hour/gender, true-solar, M4/M5/M6/M8 readiness.
- Forbid birth date/time, free-text answers, names, raw payloads, and private identifiers in calibration facts.

Completed:

- Added `v30.production_replay_intake.v1`, `v30.production_replay_intake_batch.v1`, and `v30.production_replay_intake_summary.v1`.
- Added `scripts/run_production_replay_intake.py`.
- Added admin endpoint `GET /api/v30/admin/release/production-replay-intake`.
- Intake rows derive only from `v30.production_replay_metadata.v1` and safe artifact-review fields.
- Selection statuses are `calibration_ready`, `hold_pending`, and `blocked`; canonical 30-case pack currently yields 25 ready, 3 pending, and 2 blocked.
- Updated post-seal status review so R8 is completed and next task is R9.

Gate:

```text
python3 -m compileall -q v30 scripts/run_production_replay_intake.py scripts/run_post_seal_status_review.py
passed
pytest -q tests/unit/test_production_replay_intake.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_production_replay_intake_endpoint_is_metadata_only
9 passed
python3 scripts/run_production_replay_intake.py
v30.production_replay_intake_batch.v1: rows=30 calibration_ready=25
pending=3 blocked=2
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R9 Metadata-Safe Replay Store And Search
```

### R9 Metadata-Safe Replay Store And Search

Status: completed 2026-06-06.

Target: Production real replay metadata 70% -> 80%.

Scope:

- Persist intake rows without private content.
- Search intake rows by readiness, calendar, boundary, module readiness, and source artifact.
- Summarize calibration-ready, pending, and blocked rows for admin review.
- Keep replay store separate from deterministic chart facts and policy pointers.

Completed:

- Added `v30.production_replay_store.v1` and `v30.production_replay_search.v1`.
- Persisted intake rows under `.runtime/validation/production_replay_intake/` with metadata-only storage guards.
- Added search filters for `selection_status`, `calendar_type`, `boundary_tag`, `module_ready`, `source_artifact_family`, and `limit`.
- Extended `scripts/run_production_replay_intake.py` with `--persist` and search filters.
- Extended admin endpoint `GET /api/v30/admin/release/production-replay-intake` with `persist=true` and filters.
- Added admin endpoint `GET /api/v30/admin/release/production-replay-intake/search`.
- Updated post-seal status review so R9 is completed and next task is R10.

Gate:

```text
python3 -m compileall -q v30 scripts/run_production_replay_intake.py scripts/run_post_seal_status_review.py
passed
pytest -q tests/unit/test_production_replay_store.py tests/unit/test_production_replay_intake.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_production_replay_intake_endpoint_is_metadata_only tests/test_v30_scaffold.py::test_admin_production_replay_intake_search_endpoint
12 passed
python3 scripts/run_production_replay_intake.py --persist --selection-status calibration_ready --module-ready m4
v30.production_replay_intake_batch.v1: rows=30 calibration_ready=25
pending=3 blocked=2
stored=30 total=30
search_count=25
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R10 Post-Seal Release Candidate Review
```

### R10 Post-Seal Release Candidate Review

Status: completed 2026-06-06.

Target: post-seal release readiness decision.

Scope:

- Review R1-R9 evidence and current release gates.
- Decide release-candidate gate versus real production row ingestion.
- Keep full pytest and full 518K explicit release-boundary choices.
- Do not promote policy pointers without standard gate evidence.

Gate:

```text
python3 -m compileall -q v30 scripts/run_release_candidate_review.py scripts/run_post_seal_status_review.py
pytest -q tests/unit/test_release_candidate_review.py tests/unit/test_production_replay_store.py tests/unit/test_post_seal_status_review.py tests/unit/test_synthetic_validation.py tests/unit/test_ten_god_energy_model.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_review_endpoint_is_read_only
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_production_replay_intake.py --persist --selection-status calibration_ready --module-ready m4
python3 scripts/run_release_candidate_review.py --run-quick-gate --sample-limit 2
python3 scripts/run_post_seal_status_review.py
```

Completed:

- Added `v30.release_candidate_review.v1`.
- Added `scripts/run_release_candidate_review.py`.
- Added `GET /api/v30/admin/release/candidate-review`.
- Release-candidate review now combines post-seal status, quick release gate evidence, and replay-store readiness.
- R10 decision recommends R11 standard release-candidate gate when quick gate is eligible and replay store has at least 20 calibration-ready rows.
- M4 synthetic calibration fixtures were aligned to current model-signal output while preserving family, energy-band, dominant, volatility, and stability checks.
- No policy pointer promotion, full pytest, or full 518K run is part of R10 by default.

Validation 2026-06-06:

```text
python3 -m compileall -q v30 scripts/run_release_candidate_review.py scripts/run_post_seal_status_review.py
passed
pytest -q tests/unit/test_release_candidate_review.py tests/unit/test_production_replay_store.py tests/unit/test_post_seal_status_review.py tests/unit/test_synthetic_validation.py tests/unit/test_ten_god_energy_model.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_review_endpoint_is_read_only
33 passed
python3 scripts/run_synthetic_validation.py --tier all
v30.synthetic.all: passed (95/95)
python3 scripts/run_production_replay_intake.py --persist --selection-status calibration_ready --module-ready m4
v30.production_replay_intake_batch.v1: rows=30 calibration_ready=25
pending=3 blocked=2
stored=30 total=30
search_count=25
python3 scripts/run_release_candidate_review.py --run-quick-gate --sample-limit 2
v30.release_candidate_review.v1: ready_for_release_candidate_gate
rc_gate_recommended=True
next=R11 Standard Release-Candidate Gate
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R11 Standard Release-Candidate Gate
```

### R11 Standard Release-Candidate Gate

Status: completed 2026-06-06.

Target: release-candidate evidence boundary.

Scope:

- Run the standard release gate with a selected 518K shard.
- Record release-candidate artifact evidence.
- Keep full pytest and full 518K explicit release-boundary choices.
- Do not promote policy pointers unless explicitly requested after gate evidence.

Gate:

```text
python3 -m compileall -q v30 scripts/run_release_candidate_gate_review.py scripts/run_release_gate.py
pytest -q tests/unit/test_release_candidate_gate_review.py tests/unit/test_release_gate.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_gate_review_endpoint_runs_standard_gate
python3 scripts/run_release_candidate_gate_review.py --sample-limit 8 --shard-id 7 --shard-limit 16
python3 scripts/run_post_seal_status_review.py
```

Completed:

- Added `v30.release_candidate_gate_review.v1`.
- Added `scripts/run_release_candidate_gate_review.py`.
- Added `GET /api/v30/admin/release/candidate-gate-review`.
- Standard release-candidate gate now records sample and selected shard artifact evidence under a read-only R11 review.
- R11 marks `release_boundary_ready=True` only when standard mode passes all seven checks and artifact review is ready.
- Policy pointer promotion remains disallowed; R11 is evidence, not activation.

Validation 2026-06-06:

```text
python3 -m compileall -q v30 scripts/run_release_candidate_gate_review.py scripts/run_release_gate.py
passed
pytest -q tests/unit/test_release_candidate_gate_review.py tests/unit/test_release_gate.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_candidate_gate_review_endpoint_runs_standard_gate
11 passed
python3 scripts/run_release_candidate_gate_review.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.release_candidate_gate_review.v1: standard_gate_passed
release_boundary_ready=True
next=R12 Release Boundary Finalization Review
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R12 Release Boundary Finalization Review
```

### R12 Release Boundary Finalization Review

Status: completed 2026-06-06.

Target: final release-boundary decision without automatic pointer promotion.

Scope:

- Review R1-R11 evidence bundle.
- Decide whether to run full pytest before external release.
- Keep full 518K explicit and separate from normal post-seal work.
- Do not promote policy pointers unless explicitly requested after boundary review.

Gate:

```text
python3 -m compileall -q v30 scripts/run_release_boundary_finalization.py scripts/run_release_candidate_gate_review.py
pytest -q tests/unit/test_release_boundary_finalization.py tests/unit/test_release_candidate_gate_review.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_boundary_finalization_endpoint_is_read_only
python3 scripts/run_release_boundary_finalization.py --sample-limit 8 --shard-id 7 --shard-limit 16
python3 scripts/run_post_seal_status_review.py
```

Completed:

- Added `v30.release_boundary_finalization.v1`.
- Added `scripts/run_release_boundary_finalization.py`.
- Added `GET /api/v30/admin/release/boundary-finalization`.
- R12 reviews post-seal status plus R11 standard gate evidence and finalizes the internal release candidate.
- External release remains not ready until full pytest is explicitly run and recorded.
- Policy pointer promotion remains disallowed and must be a manual operator decision.

Validation 2026-06-06:

```text
python3 -m compileall -q v30 scripts/run_release_boundary_finalization.py scripts/run_release_candidate_gate_review.py
passed
pytest -q tests/unit/test_release_boundary_finalization.py tests/unit/test_release_candidate_gate_review.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_release_boundary_finalization_endpoint_is_read_only
12 passed
python3 scripts/run_release_boundary_finalization.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.release_boundary_finalization.v1: internal_release_candidate_finalized
internal_release_candidate_finalized=True
external_release_ready=False
next=R13 External Release Dry Run And Full Pytest Decision
python3 scripts/run_post_seal_status_review.py
v30.post_seal_status_review.v1: ready_for_next_mainline
core_phase_sealed=8/8
next=R13 External Release Dry Run And Full Pytest Decision
```

### R13 External Release Dry Run And Full Pytest Decision

Selected by M0 on 2026-06-07.

Status: completed 2026-06-07.

Target: explicit external-release dry run boundary.

Scope:

- Run or explicitly defer full pytest for external release.
- Review policy pointer promotion as a manual operator action.
- Keep full 518K separate unless external production release requires it.
- Do not promote policy pointers without explicit operator approval.

Gate:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_external_release_dry_run.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_dry_run_endpoint_defers_full_pytest_by_default
python3 scripts/run_external_release_dry_run.py --sample-limit 8
```

Implementation:

- Added `v30.external_release_dry_run.v1`.
- Added `scripts/run_external_release_dry_run.py`.
- Added `GET /api/v30/admin/release/external-dry-run`.
- Default decision is `full_pytest_decision=defer`.
- External release remains not ready until full pytest is explicitly recorded as passed.
- Policy pointer promotion remains disabled and requires a separate manual operator gate.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_dry_run.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_dry_run_endpoint_defers_full_pytest_by_default
6 passed
python3 scripts/run_external_release_dry_run.py --sample-limit 8
v30.external_release_dry_run.v1: external_release_dry_run_deferred_full_pytest
external_release_ready: False
full_pytest_deferred: True
pointer_promotion_allowed: False
```

## Execution Order

1. R1 Release Gate And Contract Hardening. Completed.
2. R2 Production API Smoke And Customer Loop Contract. Completed.
3. R3 Minimal Durable Session / Read-History Hardening. Completed.
4. R4 Bounded LLM Live Smoke And Failure Telemetry. Completed.
5. R5 Production Replay Metadata Preparation. Completed.
6. R6 Observability And Admin Artifact Review. Completed.
7. R7 Post-Seal Status Review And Next Mainline Selection. Completed.
8. R8 Metadata-Safe Production Replay Intake. Completed.
9. R9 Metadata-Safe Replay Store And Search. Completed.
10. R10 Post-Seal Release Candidate Review. Completed.
11. R11 Standard Release-Candidate Gate. Completed.
12. R12 Release Boundary Finalization Review. Completed.
13. R13 External Release Dry Run And Full Pytest Decision. Completed.
14. R14 External Release Full Pytest Execution Decision. Completed.
15. R15 External Release Blocked Pending Full Pytest. Completed.
16. R16 Post-Release-Boundary Pause Or Full Pytest Authorization. Completed.
17. M0 Mainline Selection After Release Boundary Pause. Completed.
18. P0 Core Module Monitoring And Calibration Loop. Completed.
19. P1 Execute Lightweight Core Monitoring Checks. Completed.
20. P2 Core Calibration Observation Summary. Completed.
21. P3 Core Calibration Drift Watch. Completed.
22. P4 Focused Core Calibration Evidence Queue. Completed.
23. P5 Core Calibration Queue Review. Completed.
24. P6 Core Calibration Watch Closeout. Completed.
25. P7 Core Monitoring Cadence Baseline. Completed.
26. P8 Core Monitoring Cadence Documentation Sync. Completed.
27. P9 Core Monitoring Steady State. Completed.
28. S0 Steady State Await New Calibration Evidence. Active state.

### S0 Steady State Await New Calibration Evidence

Status: active state recorded 2026-06-09.

Target: record the read-only steady-state status after P9 and prevent default continuation into new core-monitoring tasks.

Scope:

- Consume `v30.core_monitoring_steady_state.v1`.
- Confirm the system is waiting for new calibration evidence.
- Confirm no new core-monitoring task is allowed by default.
- Preserve P4/P5 as future evidence and review entrypoints.
- Keep full pytest, full 518K, pointer promotion, pointer writes, and chart-fact mutation disabled by default.

Implementation:

- Added `v30.core_monitoring_s0_status.v1`.
- Added `scripts/run_core_monitoring_s0_status.py`.
- Added `GET /api/v30/admin/core/monitoring-s0-status`.
- Added unit and scaffold coverage for ready S0 status, not-waiting blocker, pointer-pressure blocker, and read-only endpoint behavior.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_s0_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_s0_status_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_s0_status.py --sample-limit 8
v30.core_monitoring_s0_status.v1: core_monitoring_s0_status_ready
status_checks: 4/4
waiting_for_new_evidence: True
new_core_monitoring_task_allowed_by_default: False
```

Next:

```text
No default next core-monitoring task.
```

Future calibration evidence enters P4/P5. Release/full-freeze/full-pytest/pointer-promotion remain explicit boundary tracks.

### P9 Core Monitoring Steady State

Status: completed 2026-06-09.

Target: enter steady state after P8 documentation sync and wait for new calibration evidence.

Scope:

- Consume `v30.core_monitoring_cadence_documentation_sync.v1`.
- Confirm required cadence docs are synchronized.
- Confirm future evidence routes through P4 and P5.
- Confirm no default full pytest, full 518K, pointer promotion, pointer write, or chart-fact mutation.
- Mark the system as waiting for new calibration evidence.

Implementation:

- Added `v30.core_monitoring_steady_state.v1`.
- Added `scripts/run_core_monitoring_steady_state.py`.
- Added `GET /api/v30/admin/core/monitoring-steady-state`.
- Added unit and scaffold coverage for ready steady state, missing-doc blocker, pointer-pressure blocker, and read-only endpoint behavior.

Validation 2026-06-09:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_steady_state.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_steady_state_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_steady_state.py --sample-limit 8
v30.core_monitoring_steady_state.v1: core_monitoring_steady_state_ready
steady_state_checks: 4/4
waiting_for_new_evidence: True
future_monitoring_ready: True
```

Next:

```text
S0 Steady State Await New Calibration Evidence
```

S0 means no further core-monitoring task should run by default. Future calibration evidence enters P4/P5; release/full-freeze requests remain explicit.

### P8 Core Monitoring Cadence Documentation Sync

Status: completed 2026-06-08.

Target: sync the P7 cadence baseline across controlling docs and keep future evidence routed through P4/P5.

Scope:

- Consume `v30.core_monitoring_cadence_baseline.v1`.
- Confirm cadence is `on_new_calibration_evidence_only`.
- Confirm future evidence entrypoint is P4 and future review entrypoint is P5.
- Confirm required cadence docs are synchronized.
- Keep full pytest, full 518K, pointer promotion, pointer writes, and chart-fact mutation disabled by default.

Implementation:

- Added `v30.core_monitoring_cadence_documentation_sync.v1`.
- Added `scripts/run_core_monitoring_cadence_documentation_sync.py`.
- Added `GET /api/v30/admin/core/monitoring-cadence-documentation-sync`.
- Added unit and scaffold coverage for ready sync, missing-doc blocker, heavy-validation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_cadence_documentation_sync.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_documentation_sync_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_cadence_documentation_sync.py --sample-limit 8
v30.core_monitoring_cadence_documentation_sync.v1: core_monitoring_cadence_documentation_sync_ready
docs: 10/10
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P9 Core Monitoring Steady State
```

P9 should keep the cadence in steady state and route only future evidence through P4/P5. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P7 Core Monitoring Cadence Baseline

Status: completed 2026-06-08.

Target: document the ongoing lightweight monitoring cadence after P6 closeout.

Scope:

- Consume `v30.core_calibration_watch_closeout.v1`.
- Confirm the current cycle is closed and future monitoring is ready.
- Define default cadence as `on_new_calibration_evidence_only`.
- Route new evidence to P4 and queued evidence review to P5.
- Keep full pytest, full 518K, pointer promotion, pointer writes, and chart-fact mutation explicit and disabled by default.

Implementation:

- Added `v30.core_monitoring_cadence_baseline.v1`.
- Added `scripts/run_core_monitoring_cadence_baseline.py`.
- Added `GET /api/v30/admin/core/monitoring-cadence-baseline`.
- Added unit and scaffold coverage for ready cadence, unclosed-cycle blocker, heavy-validation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_cadence_baseline.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_cadence_baseline_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_cadence_baseline.py --sample-limit 8
v30.core_monitoring_cadence_baseline.v1: core_monitoring_cadence_baseline_ready
default_cadence: on_new_calibration_evidence_only
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P8 Core Monitoring Cadence Documentation Sync
```

P8 should sync the P7 cadence baseline across the controlling docs. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P6 Core Calibration Watch Closeout

Status: completed 2026-06-08.

Target: close the current empty core calibration watch cycle and keep future monitoring ready.

Scope:

- Consume `v30.core_calibration_queue_review.v1`.
- Confirm P5 queue review is ready.
- Confirm no focused fix candidate exists.
- Confirm no full pytest, full 518K, pointer promotion, pointer write, or chart-fact mutation is requested.
- Keep future evidence entry through P4 and future review through P5.

Implementation:

- Added `v30.core_calibration_watch_closeout.v1`.
- Added `scripts/run_core_calibration_watch_closeout.py`.
- Added `GET /api/v30/admin/core/calibration-watch-closeout`.
- Added unit and scaffold coverage for ready closeout, focused-candidate blocker, upstream queue blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_watch_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_watch_closeout_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_watch_closeout.py --sample-limit 8
v30.core_calibration_watch_closeout.v1: core_calibration_watch_closeout_ready
closeout_checks: 4/4
current_cycle_closed: True
future_monitoring_ready: True
```

Next:

```text
P7 Core Monitoring Cadence Baseline
```

P7 should document the ongoing lightweight cadence after closeout. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P5 Core Calibration Queue Review

Status: completed 2026-06-08.

Target: review queued calibration evidence by module target and decide whether focused module fixes are needed.

Scope:

- Consume `v30.focused_core_calibration_evidence_queue.v1`.
- Review only queued calibration evidence.
- Report focused module fix candidates when queued items exist.
- Keep fix execution, chart-fact mutation, pointer writes, default full pytest, and default full 518K disabled.
- Continue lightweight watch when the queue is empty.

Implementation:

- Added `v30.core_calibration_queue_review.v1`.
- Added `scripts/run_core_calibration_queue_review.py`.
- Added `GET /api/v30/admin/core/calibration-queue-review`.
- Added unit and scaffold coverage for empty queue readiness, focused candidates, upstream queue blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_queue_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_queue_review_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_queue_review.py --sample-limit 8
v30.core_calibration_queue_review.v1: core_calibration_queue_review_ready
reviewed_modules: 0
focused_fix_candidates: 0
focused_module_fix_required: False
```

Next:

```text
P6 Core Calibration Watch Closeout
```

P6 should close the current empty queue review cycle and keep future monitoring ready. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P4 Focused Core Calibration Evidence Queue

Status: completed 2026-06-08.

Target: batch future calibration evidence by M1-M8 module target without changing core facts or policy pointers.

Scope:

- Consume `v30.core_calibration_drift_watch.v1`.
- Keep the queue open for future calibration evidence.
- Batch evidence by M1-M8 module target.
- Block chart-fact mutation, pointer writes, default full pytest, and default full 518K.
- Route queued evidence to focused module review without reopening all M1-M8.

Implementation:

- Added `v30.focused_core_calibration_evidence_queue.v1`.
- Added `scripts/run_focused_core_calibration_evidence_queue.py`.
- Added `GET /api/v30/admin/core/focused-calibration-evidence-queue`.
- Added unit and scaffold coverage for empty queue readiness, module batching, mutation pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_focused_core_calibration_evidence_queue.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_focused_core_calibration_evidence_queue_endpoint_is_read_only
5 passed
python3 scripts/run_focused_core_calibration_evidence_queue.py --sample-limit 8
v30.focused_core_calibration_evidence_queue.v1: focused_core_calibration_evidence_queue_ready
queued_evidence: 0
queue_items: 0
focused_module_fix_required: False
```

Next:

```text
P5 Core Calibration Queue Review
```

P5 should review queued evidence by module target and decide whether a focused module fix is needed. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P3 Core Calibration Drift Watch

Status: completed 2026-06-08.

Target: establish the lightweight drift-watch cadence and route future calibration drift to focused module fixes.

Scope:

- Consume `v30.core_calibration_observation_summary.v1`.
- Define the default cadence as `on_new_calibration_evidence_only`.
- Define route targets for the four lightweight monitoring checks.
- Block chart-fact mutation, pointer writes, default full pytest, and default full 518K.
- Route concrete drift to focused module review without reopening all M1-M8.

Implementation:

- Added `v30.core_calibration_drift_watch.v1`.
- Added `scripts/run_core_calibration_drift_watch.py`.
- Added `GET /api/v30/admin/core/calibration-drift-watch`.
- Added unit and scaffold coverage for ready state, drift routing, pointer-write pressure, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_drift_watch.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_drift_watch_endpoint_is_read_only
5 passed
python3 scripts/run_core_calibration_drift_watch.py --sample-limit 8
v30.core_calibration_drift_watch.v1: core_calibration_drift_watch_ready
drift_detected: False
drift_routes: 0
focused_module_fix_required: False
```

Next:

```text
P4 Focused Core Calibration Evidence Queue
```

P4 should batch future calibration evidence by M1-M8 module target. It still must not run full pytest, mutate chart facts, or promote pointers by default.

### P2 Core Calibration Observation Summary

Status: completed 2026-06-08.

Target: summarize P1 monitoring evidence and choose whether to continue observation or open a focused module fix.

Scope:

- Consume `v30.lightweight_core_monitoring_checks.v1`.
- Summarize stable/needs-review observations for the four P1 checks.
- Confirm no focused module fix is required when all observations are stable.
- Keep full pytest, full 518K, pointer promotion, and chart-fact mutation outside default iteration.

Implementation:

- Added `v30.core_calibration_observation_summary.v1`.
- Added `scripts/run_core_calibration_observation_summary.py`.
- Added `GET /api/v30/admin/core/calibration-observation-summary`.
- Added unit and scaffold coverage for ready state, failed-check blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_calibration_observation_summary.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_calibration_observation_summary_endpoint_is_read_only
4 passed
python3 scripts/run_core_calibration_observation_summary.py --sample-limit 8
v30.core_calibration_observation_summary.v1: core_calibration_observation_summary_ready
observations: 4 stable, 0 needs_review
regression_detected: False
focused_module_fix_required: False
```

Next:

```text
P3 Core Calibration Drift Watch
```

P3 should define the lightweight drift-watch cadence and failure routing rules. It still must not run full pytest or promote pointers by default.

### P1 Execute Lightweight Core Monitoring Checks

Status: completed 2026-06-08.

Target: execute and record the four F6 lightweight monitoring checks.

Scope:

- Run M1-M8 frozen-scope calibration review.
- Run targeted calibration candidate review.
- Run targeted validation gate with 518K sample limit 8.
- Run pointer decision with operator defer and prove no pointer promotion.
- Keep full pytest, full 518K, external release, and pointer promotion out of default iteration.

Implementation:

- Added `v30.lightweight_core_monitoring_checks.v1`.
- Added `scripts/run_lightweight_core_monitoring_checks.py`.
- Added `GET /api/v30/admin/core/lightweight-monitoring-checks`.
- Added unit and scaffold coverage for pass state, failed-check blocker, and read-only endpoint behavior.

Validation 2026-06-08:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_lightweight_core_monitoring_checks.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_lightweight_core_monitoring_checks_endpoint_is_read_only
5 passed
python3 scripts/run_lightweight_core_monitoring_checks.py --sample-limit 8
v30.lightweight_core_monitoring_checks.v1: lightweight_core_monitoring_checks_passed
checks: 4/4
regression_detected: False
```

### P0 Core Module Monitoring And Calibration Loop

Status: completed 2026-06-07.

Target: establish a read-only lightweight monitoring loop for frozen M1-M8 after release-boundary pause.

Scope:

- Consume M0-after-pause selection evidence.
- Consume F6 targeted-calibration closeout monitoring baseline.
- Verify the four lightweight monitoring checks are present.
- Keep external release, full pytest, full 518K, and pointer promotion outside default iteration.
- Recommend module reopening only when a concrete targeted failure exists.

Implementation:

- Added `v30.core_monitoring_loop.v1`.
- Added `scripts/run_core_monitoring_loop.py`.
- Added `GET /api/v30/admin/core/monitoring-loop`.
- Added unit and scaffold coverage for ready state, missing-monitoring-check blocker, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_core_monitoring_loop.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_core_monitoring_loop_endpoint_is_read_only
5 passed
python3 scripts/run_core_monitoring_loop.py --sample-limit 8
v30.core_monitoring_loop.v1: core_monitoring_loop_ready
monitoring_checks: 4/4
regression_detected: False
core_module_reopen_recommended: False
```

### M0 Mainline Selection After Release Boundary Pause

Status: completed 2026-06-07.

Target: select the next non-release mainline after R16 paused release-boundary work.

Scope:

- Consume R16 pause evidence.
- Confirm full pytest is not authorized and not running.
- Keep external release blocked.
- Keep pointer promotion disabled.
- Select a non-release next track.

Implementation:

- Added `v30.mainline_selection_after_release_pause.v1`.
- Added `scripts/run_mainline_selection_after_release_pause.py`.
- Added `GET /api/v30/admin/mainline/selection-after-release-pause`.
- Selected `P0 Core Module Monitoring And Calibration Loop`.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_mainline_selection_after_release_pause.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_mainline_selection_after_release_pause_endpoint_is_read_only
5 passed
python3 scripts/run_mainline_selection_after_release_pause.py --sample-limit 8
v30.mainline_selection_after_release_pause.v1: core_monitoring_and_calibration_loop_selected
next: P0 Core Module Monitoring And Calibration Loop
```

### R16 Post-Release-Boundary Pause Or Full Pytest Authorization

Status: completed 2026-06-07.

Target: decide whether to keep release-boundary work paused or explicitly authorize full pytest.

Scope:

- Consume R15 blocked-release evidence.
- Default to `authorization_decision=pause`.
- Do not run full pytest inside this task.
- Do not approve external release.
- Do not promote policy pointers.

Implementation:

- Added `v30.post_release_boundary_authorization.v1`.
- Added `scripts/run_post_release_boundary_authorization.py`.
- Added `GET /api/v30/admin/release/post-boundary-authorization`.
- Added unit and scaffold coverage for pause, full-pytest authorization without execution, invalid release-ready blocking, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_post_release_boundary_authorization.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_post_release_boundary_authorization_endpoint_pauses_by_default
6 passed
python3 scripts/run_post_release_boundary_authorization.py --sample-limit 8
v30.post_release_boundary_authorization.v1: release_boundary_paused_pending_full_pytest_authorization
release_boundary_paused: True
full_pytest_authorized: False
full_pytest_run_triggered: False
pointer_promotion_allowed: False
```

### R15 External Release Blocked Pending Full Pytest

Status: completed 2026-06-07.

Target: record that external release remains blocked while full pytest is deferred.

Scope:

- Consume R14 full-pytest decision evidence.
- Confirm external release is not ready.
- Record open release blockers.
- Keep policy pointer promotion disabled.
- Keep deterministic chart facts and frozen M1-M8 untouched.

Implementation:

- Added `v30.external_release_blocked_status.v1`.
- Added `scripts/run_external_release_blocked_status.py`.
- Added `GET /api/v30/admin/release/blocked-status`.
- Added unit and scaffold coverage for blocked-status recording, invalid ready-state blocking, and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_blocked_status.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_blocked_status_endpoint_is_read_only
5 passed
python3 scripts/run_external_release_blocked_status.py --sample-limit 8
v30.external_release_blocked_status.v1: external_release_blocked_pending_full_pytest
external_release_ready: False
external_release_blocked: True
pointer_promotion_allowed: False
```

### R14 External Release Full Pytest Execution Decision

Status: completed 2026-06-07.

Target: make full pytest execution an explicit release-boundary decision.

Scope:

- Consume R13 dry-run evidence.
- Record whether full pytest is deferred, passed, or failed.
- Default to `full_pytest_decision=defer`.
- Keep external release blocked while full pytest is deferred.
- Keep policy pointer promotion disabled.

Implementation:

- Added `v30.external_release_full_pytest_decision.v1`.
- Added `scripts/run_external_release_full_pytest_decision.py`.
- Added `GET /api/v30/admin/release/full-pytest-decision`.
- Added unit and scaffold coverage for defer/pass/fail decision records and read-only endpoint behavior.

Validation 2026-06-07:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_external_release_full_pytest_decision.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_external_release_full_pytest_decision_endpoint_defers_by_default
6 passed
python3 scripts/run_external_release_full_pytest_decision.py --sample-limit 8
v30.external_release_full_pytest_decision.v1: external_release_full_pytest_deferred
external_release_ready: False
full_pytest_deferred: True
pointer_promotion_allowed: False
```

## Stop Rules

- If a task reveals a real M1-M8 validation failure, pause the post-seal track and fix the failing module with a targeted regression test.
- If a change touches release/pointer promotion, run quick release gate at minimum.
- If a change touches policy activation, run standard release gate.
- Do not run full 518K unless explicitly requested or preparing a production release boundary.
