# V30 518K Validation Plan

Updated: 2026-06-10

## Purpose

518K validation is V30's broad distribution validation layer. It should stress-test structure dynamics, question recommendation, answer boundaries, role projection, and training candidates across a large chart corpus.

It must be powerful but not part of default local tests.

## Modes

Current BT9 status:

- `v30.518k_readiness_matrix.v1` is implemented.
- `scripts/run_518k_readiness_matrix.py` is implemented.
- `GET /api/v30/admin/validation/518k/readiness-matrix` is implemented.
- 518K support completion is 95% for the current support-system scope.
- Full 518K remains explicit-only and is not a default local or subtask test.

Current BT10 closeout status:

- `v30.brain_training_synthetic_closeout.v1` accepts 518K readiness as one part of the unified support-system closeout.
- `scripts/run_brain_training_synthetic_closeout.py --sample-limit 8 --shard-id 7 --shard-limit 16` passed 6/6 closeout checks.
- 518K remains at 95% current-scope support completion because full-corpus execution is still an explicit heavy validation, not a default requirement.

### Sample Mode

Small representative sample.

Use for:

- Local training checks.
- Release gate.
- Quick drift detection.

### Shard Mode

One or more selected shards.

Use for:

- Policy promotion.
- Failure investigation.
- Coverage expansion.

### Full Mode

Full 518K validation.

Use for:

- Major policy changes.
- Release hardening.
- Corpus-wide drift audit.

## Flow

```text
CorpusCase
-> V30 Runtime
-> CaseSummary
-> CoverageMetrics
-> DriftMetrics
-> FailureClusters
-> PromotionSignal
```

## Required Outputs

Each run should produce:

```text
run_id
mode
corpus_version
shard_ids
policy_versions
case_count
coverage_metrics
drift_metrics
failure_clusters
promotion_signal
artifact_uri
started_at
finished_at
```

## Coverage Metrics

Initial metrics:

- Day master distribution.
- Element distribution.
- Ten god distribution.
- Structure mechanism coverage.
- Mainline domain coverage.
- Question intent coverage.
- Missing time coverage.
- Role projection coverage.
- Answer boundary coverage.
- Ten-god model-signal coverage.
- Ranked decision fusion coverage.
- Interaction-loop coverage.
- Real-case calibration coverage.

## Drift Metrics

Initial metrics:

- Structure label drift.
- Mainline selection drift.
- Question recommendation drift.
- Unsupported question rate.
- Weak anchor rate.
- Answer boundary violation rate.
- Role visibility leak rate.
- LLM unsupported claim rate.
- Model-signal raw-score leak rate.
- Visible/internal next-question mismatch rate.
- Calibration-probe visibility leak rate.

## Policy Promotion Use

Promotion can require:

- Synthetic smoke pass.
- 518K sample pass.
- Selected shard pass.
- No severe drift cluster.
- No role visibility leak.
- No unsupported question spike.

Full 518K validation is not mandatory for every small candidate, but must be available for high-impact changes.

## Storage Strategy

V30 should store:

- Case summaries.
- Aggregate metrics.
- Failure clusters.
- Artifact lineage.

Avoid storing huge raw payloads by default.

Recommended storage:

```text
v30_artifacts
v30_runtime_traces
v30_validation_cases
runtime files under .runtime/validation/518k/
```

Current indexing behavior:

- JSON artifacts and `.runtime/validation/518k/index.json` remain the canonical local/dev fallback.
- When `V30_DATABASE_URL` is available, each validation run is also upserted into `v30_artifacts`.
- No new database table is required for artifact search.
- DB indexing is additive. A local run without Postgres still completes and remains searchable through the JSON fallback.

BT9 readiness matrix behavior:

- Runs lightweight sample and selected-shard distribution gates.
- Proves full mode requires explicit `confirm_full=True`.
- Verifies generated corpus contract and external `.jsonl` / `.csv` source support.
- Verifies artifact JSON, index JSON, index-entry JSON, artifact record ids, and JSON/Postgres search fallback.
- Documents candidate-family coverage for `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy`.
- Does not authorize policy pointer promotion or chart-fact mutation.

## Test Tiering

518K validation maps to test tiers:

- Tier 6 sample.
- Tier 6 shard.
- Tier 6 full.

Default `pytest` must never run 518K validation.

## Open Questions

- Where will the canonical 518K corpus file be mounted in production?
- Which shard strategy best covers ten-god energy volatility and structure mechanisms together?
- What is the minimum sample size for model-fusion promotion?
- Which interaction-loop metrics are hard blockers versus warning signals?
- How should real-case calibration pack failures be represented in broad distribution artifacts?

Current P8/P9/P10 coverage status:

- 518K sample/shard summaries now include `model_signal_summary_coverage`, `interaction_state_coverage`, `visible_internal_next_question_split_count`, and `calibration_probe_user_visible_count`.
- Drift metrics now include missing model-signal summary rate, missing interaction-state rate, and calibration-probe user-visible rate.
- Calibration-probe visibility in user-facing next-question projection is a high-severity failure cluster.
- Real-case calibration pack is phase sealed as a dedicated 30-case synthetic tier; broad 518K real-case metadata should wait until corpus rows carry BirthInput-derived fixture tags.

## Current Implementation Slice

V30 now starts with a runner contract:

```text
sample -> bounded deterministic runtime replay
shard -> selected shard deterministic replay
full -> explicit confirm only
```

Initial inherited operating constants from V20 review:

```text
target_case_count: 518400
default_shard_count: 128
default_batch_size: 512
```

V30 does not import V20 runtime or V20 corpus modules. Until the canonical V30 corpus source is mounted, sample/shard mode uses deterministic generated corpus summaries to exercise V30 runtime and metrics.

Current status:

- `scripts/run_518k_validation.py` exists.
- `sample`, `shard`, and guarded `full` modes exist.
- `CorpusCaseSummary` and `Corpus518KValidationResult` contracts exist.
- External source input now accepts JSONL or CSV through `--source-path`.
- External rows support `case_id/source_row_id`, `day_master`, `day_master_element`, `locale`, `luck_pillar`, `flow_year_pillar`, and feedback flags used for counter-evidence replay.
- When no external source is passed, V30 keeps the deterministic generated corpus fallback.
- Each 518K run now persists a V30 artifact JSON under `.runtime/validation/518k/` by default.
- Each 518K run also updates `.runtime/validation/518k/index.json` and writes `.runtime/validation/518k/index/{run_id}.index.json`.
- `Corpus518KValidationResult` exposes `artifact_uri`, `index_uri`, `index_entry_uri`, `artifact_record_id`, `artifact_search_backend`, and `artifact_searchable`.
- When Postgres is configured, 518K run index entries are searchable from `v30_artifacts`.
- `GET /api/v30/admin/validation/518k/artifacts?mode=sample&limit=5` returns the latest matching artifact records.
- `GET /api/v30/admin/validation/518k/readiness-matrix` returns `v30.518k_readiness_matrix.v1`.
- `GET /api/v30/admin/validation/artifacts?family=518k_validation&limit=5` returns the same family through the unified validation artifact discovery surface.
- Release gate 518K checks include artifact, index, and artifact-search metadata in their summaries.
- R6 adds `v30.release_artifact_review.v1` and `GET /api/v30/admin/release/artifact-review`, grouping 518K sample/shard artifact ids with synthetic suite summaries, policy lineage, projection contract summaries, and promotion review.
- R8 adds `v30.production_replay_intake.v1` and `GET /api/v30/admin/release/production-replay-intake`, connecting metadata-only replay rows to artifact-review context and calibration-ready/pending/blocked selection.
- R9 adds `v30.production_replay_store.v1`, `v30.production_replay_search.v1`, and `GET /api/v30/admin/release/production-replay-intake/search`, allowing metadata-safe replay rows to be persisted and searched without chart fact import.
- `V30_518K_ARTIFACT_DIR` or the code-level `artifact_dir` parameter can redirect artifact storage.
- Sample mode replays current V30 runtime and reports coverage/drift metrics.
- Shard mode targets selected shard IDs.
- Full mode requires `--confirm-full`.
- 518K replay accepts candidate policy payload overrides for pre-promotion validation.
- Policy promotion now uses 518K sample as the distribution gate after synthetic `all`.
- Latest sample smoke: `eligible`, 8 cases, shard 0.
- Latest selected shard smoke: `eligible`, 16 cases, shard 7.
- Latest auto-training gate: `518k-gate-001` promoted all three core policy families.
- Release gate quick mode includes 518K sample.
- Release gate standard mode includes 518K sample and one selected shard.
- M8 final seal used 518K sample `v30.518k.sample.20260524044648490844` after synthetic all and API projection contract validation.
- Post-seal quick release gate includes `post_seal_contracts`, `production_api_smoke`, `llm_live_smoke`, synthetic all, 518K sample, and artifact review; latest quick gate `v30.release_gate.quick.20260605103342` is eligible with 6 checks.
- BT9 readiness matrix:

```text
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready
```

- Latest BT9 sample check:

```text
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260609175010408754: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260609175010408754
artifact_search_backend: json_fallback
```
- M3-focused sample check:

```text
python3 scripts/run_518k_validation.py --mode sample --limit 2
v30.518k.sample.20260610044238766995: eligible mode=sample cases=2 shards=0
```

This is M3 distribution evidence alongside `v30_m3_*` Postgres snapshots. Full 518K remains explicit-only and is not part of routine M3 iteration.

Admin background queue:

```text
POST /api/v30/admin/training/m3-background/run
GET  /api/v30/admin/training/m3-background/status
```

- Default routine step: `python3 scripts/run_518k_validation.py --mode sample --limit 8`
- Optional long step: `python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16`
- Optional matrix step: `python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16`
- Full 518K remains explicit-only through `python3 scripts/run_518k_validation.py --mode full --confirm-full`; it is not available as a one-click routine UI task.

Latest M3-focused 518K run, 2026-06-10:

```text
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260610061011596029: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260610061011596029
artifact_search_backend: json_fallback

python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16
v30.518k.shard.20260610061046503507: eligible mode=shard cases=16 shards=7
artifact_record_id: v30.518k.artifact.v30.518k.shard.20260610061046503507
artifact_search_backend: json_fallback

python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready
```

- Latest sample check for the P7/P8 baseline and next validation slice:

```text
C8 core-completion freeze baseline, 2026-06-06
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260606084440379258: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260606084440379258
artifact_search_backend: json_fallback

F3 targeted calibration validation gate, 2026-06-06
python3 scripts/run_targeted_calibration_validation_gate.py --sample-limit 8
candidate-overrides 518K sample: eligible, cases=8
policy_pointer_promotion_allowed: false

F4 targeted calibration pointer review, 2026-06-07
python3 scripts/run_targeted_calibration_pointer_review.py --sample-limit 8
candidate-overrides pointer review: ready_for_explicit_operator_pointer_decision, diffs=4
policy_pointer_promotion_allowed: false

F5 explicit operator pointer decision, 2026-06-07
python3 scripts/run_targeted_calibration_pointer_decision.py --sample-limit 8 --operator-decision defer
pointer_promotion_deferred: true
pointer_write_performed: false

F6 targeted calibration closeout, 2026-06-07
python3 scripts/run_targeted_calibration_closeout.py --sample-limit 8
targeted_calibration_closed_with_no_promotion: true
monitoring_check_count: 4
pointer_write_performed: false

M0 mainline selection, 2026-06-07
python3 scripts/run_mainline_selection.py --sample-limit 8
selected_next_task: R13 External Release Dry Run And Full Pytest Decision
full_pytest_run_now: false
full_518k_default: false

R13 external release dry run, 2026-06-07
python3 scripts/run_external_release_dry_run.py --sample-limit 8
external_release_ready: false
full_pytest_deferred: true
full_518k_required_before_external_release: false

R14 external release full pytest decision, 2026-06-07
python3 scripts/run_external_release_full_pytest_decision.py --sample-limit 8
external_release_ready: false
external_release_blocked: true
full_518k_required_before_external_release: false

R15 external release blocked status, 2026-06-07
python3 scripts/run_external_release_blocked_status.py --sample-limit 8
external_release_ready: false
external_release_blocked: true
full_518k_required_by_default: false

R16 post-release-boundary authorization, 2026-06-07
python3 scripts/run_post_release_boundary_authorization.py --sample-limit 8
release_boundary_paused: true
full_pytest_authorized: false
full_518k_required_by_default: false

M0 mainline selection after release pause, 2026-06-07
python3 scripts/run_mainline_selection_after_release_pause.py --sample-limit 8
selected_next_task: P0 Core Module Monitoring And Calibration Loop
full_518k_required_by_default: false

P0 core monitoring loop, 2026-06-07
python3 scripts/run_core_monitoring_loop.py --sample-limit 8
monitoring_checks: 4/4
full_518k_required_by_default: false

P1 lightweight core monitoring checks, 2026-06-08
python3 scripts/run_lightweight_core_monitoring_checks.py --sample-limit 8
monitoring_checks: 4/4
full_518k_required_by_default: false

P2 core calibration observation summary, 2026-06-08
python3 scripts/run_core_calibration_observation_summary.py --sample-limit 8
stable_observations: 4
needs_review_observations: 0
full_518k_required_by_default: false

P3 core calibration drift watch, 2026-06-08
python3 scripts/run_core_calibration_drift_watch.py --sample-limit 8
drift_detected: false
drift_routes: 0
full_518k_required_by_default: false

P4 focused core calibration evidence queue, 2026-06-08
python3 scripts/run_focused_core_calibration_evidence_queue.py --sample-limit 8
queued_evidence: 0
queue_items: 0
full_518k_required_by_default: false

P5 core calibration queue review, 2026-06-08
python3 scripts/run_core_calibration_queue_review.py --sample-limit 8
reviewed_modules: 0
focused_fix_candidates: 0
full_518k_required_by_default: false

P6 core calibration watch closeout, 2026-06-08
python3 scripts/run_core_calibration_watch_closeout.py --sample-limit 8
closeout_checks: 4/4
current_cycle_closed: true
full_518k_required_by_default: false

P7 core monitoring cadence baseline, 2026-06-08
python3 scripts/run_core_monitoring_cadence_baseline.py --sample-limit 8
default_cadence: on_new_calibration_evidence_only
current_cycle_closed: true
full_518k_required_by_default: false

P8 core monitoring cadence documentation sync, 2026-06-08
python3 scripts/run_core_monitoring_cadence_documentation_sync.py --sample-limit 8
required_docs_synced: 10/10
full_518k_required_by_default: false

P9 core monitoring steady state, 2026-06-09
python3 scripts/run_core_monitoring_steady_state.py --sample-limit 8
steady_state_checks: 4/4
waiting_for_new_evidence: true
full_518k_required_by_default: false

S0 core monitoring status, 2026-06-09
python3 scripts/run_core_monitoring_s0_status.py --sample-limit 8
status_checks: 4/4
new_core_monitoring_task_allowed_by_default: false
full_518k_required_by_default: false

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260522054825826322: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260522054825826322
artifact_search_backend: json_fallback
```

## Next 518K Expansion

Add coverage and drift fields for the current mainline:

```text
model_signal_summary_present_rate
ten_god_energy_dominant_distribution
ten_god_high_volatility_distribution
ranked_decision_boundary_present_rate
visible_next_question_change_rate
internal_next_question_diagnostic_rate
calibration_probe_user_visibility_leak_rate
real_case_calibration_family_coverage
```

Use in promotion:

- P7 model-fusion candidates require synthetic model-fusion pass plus 518K sample without raw-score leaks.
- P8 interaction candidates require synthetic interaction-loop pass plus 518K sample without calibration-probe user leaks.
- P9 real-case calibration remains a targeted pack first; 518K only records broad coverage and drift context.

Index contract:

```text
index_id
updated_at
run_count
latest_run_id_by_mode
entries[]
```

Entry contract:

```text
run_id
mode
corpus_version
case_count
shard_ids
promotion_signal
failure_cluster_count
artifact_uri
artifact_record_id
artifact_search_backend
artifact_searchable
index_entry_uri
coverage_metrics
drift_metrics
started_at
finished_at
```

Admin artifact search response:

```text
backend
searchable
count
artifacts[]
  artifact_record_id
  run_id
  mode
  case_count
  promotion_signal
  artifact_uri
  index_entry_uri
  coverage_metrics
  drift_metrics
  failure_cluster_count
  created_at
```

Source format examples:

```json
{"case_id":"case-001","day_master":"庚","hidden_factor_user_calibrated":true}
{"case_id":"case-002","day_master":"癸","useful_god_path_resolved":true}
```

```csv
case_id,day_master,day_master_element,hidden_factor_user_calibrated
case-001,庚,metal,true
```
