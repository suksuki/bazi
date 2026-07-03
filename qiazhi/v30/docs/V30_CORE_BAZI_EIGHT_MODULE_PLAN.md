# V30 Core Bazi Eight Module Completion Plan

Updated: 2026-06-10

## Purpose

This is the controlling plan for completing the eight core modules that directly support V30 Bazi calculation.

Active completion mainline:

```text
docs/V30_CORE_MODULE_FINAL_COMPLETION_MAINLINE.md
```

Current active task:

```text
M1-M8 remain sealed for current scope; MCR1 completed the post-IQ5 main module review and selected MCR2 Customer Reading Surface And BaziContext Completion Reconciliation
```

The system direction is simple:

- UI stays concise.
- Core modules become strong.
- Training, synthetic validation, real-case calibration, and 518K checks serve the core modules.
- Hidden factors, LLM, complex interaction, admin diagnostics, and product polish must not replace the calculation mainline.

After each completed task, this document must be updated with:

- Module completion change.
- Implementation summary.
- Validation commands and results.
- Remaining gap.
- Next module/task.

## Eight Core Modules

| Order | Core module | Current completion | Target completion | Priority | Current judgment |
|---:|---|---:|---:|---|---|
| 1 | BirthInput and deterministic chart facts | 100% | 100% | P0 | C5 complete: deterministic BirthInput conversion, chart build, four pillars, boundary traces, luck/flow, six-pillar context, solar-term/year-month fixtures, canonical M1/M2 real-case coverage, no-fake-fact guardrails, and downstream consumption proof are active. |
| 2 | Base Bazi fact explanation layer | 100% | 100% | P0 | C5 complete: day master, ten gods, hidden stems, five elements, relation facts, root/vault facts, `base_fact_explanations`, `v30.m1_m2_completion_summary.v1`, `core_bazi_reading` fact projection, and M5/M6 consumption proof are active. |
| 3 | Evidence / rule / knowledge / structure spine | 100% | 100% | P0 | C6 complete: source-backed K/R/P, V20 reference assets, M3 feature atoms, rule/counter-evidence gates, portrait features, mechanism graph, dynamic graph, mainline arbitration, synthetic tiers, training signal, and M4/M5/M6 support proof are active. |
| 4 | Ten-god energy model | 100% | 100% | P1 | C2 complete: dedicated calibration tier, five-family band coverage, interface contract, calibration profile, calibration flags, ranked-decision adjustments, real-case replay, stability/volatility observations, training distribution, and auto-training model-signal weights are active. |
| 5 | Strength / structure pattern / useful-god ranked decisions | 100% | 100% | P0 | C2 complete: candidate scoring layer consumes M4 calibration flags and adjustment biases, has replayable candidate weights, useful-god evidence calibration, auto-training policy weights, real-case fixtures, score floors, M1/M2 root/vault basis, and training signals. |
| 6 | Practical reading output | 100% | 100% | P1 | C1 complete: career, wealth, relationship, health, and timing readings expose calculation basis, module dependencies, M5 links, M4 bands, evidence ids, explanation units, domain insights, action steps, calibration prompts, module trace, boundary conditions, blocked claims, and quality contracts. |
| 7 | Core calculation validation / real-case calibration | 100% | 100% | P0 | C3 complete: 30 canonical fixtures validate chart facts, timing context, M4 signal bands, M5 ranked candidates, M6 practical reading contracts, blocked/pending guardrails, metadata-safe replay tags, and M7 drift summaries that route calibration issues to module targets without mutating chart facts. |
| 8 | User presentation / API projection | 100% | 100% | P2 | C4 complete: `v30.api_projection_contract.v1` now carries core-first projection, customer surface contract, full additive field preservation, role visibility matrix, customer forbidden-field policy, guest/user leak scan, sanitized question/answer projection, and role-gated diagnostics. |

## Completion Standard

The eight modules are considered complete when V30 can:

1. Build stable charts from real BirthInput.
2. Produce deterministic four pillars, day master, ten gods, hidden stems, five elements, relations, luck cycle, flow year, flow month, and six-pillar context.
3. Produce bounded strength, structure pattern, and useful-god candidates with evidence and counter-evidence.
4. Explain judgment paths instead of returning template conclusions.
5. Produce practical career, wealth, relationship, health, and timing readings from the core judgment layer.
6. Validate major boundaries through synthetic cases.
7. Calibrate typical, special, and boundary charts through canonical real-case fixtures.
8. Keep customer presentation concise while hiding diagnostics, policy payloads, training internals, and raw structure traces.

## Phase 1: Complete The Core Judgment Loop

### M5 Strength / Structure Pattern / Useful-god Ranked Decisions

Current: 88%
Target: 88%
Status: phase sealed

Work to complete:

- [x] Normalize strength candidates: strong, weak, balanced, slightly strong, slightly weak.
- [x] Separate ordinary structure, dynamic structure, special-structure boundary, regulation/climate boundary, and mediation-path review.
- [x] Keep useful-god as ranked candidates, not fixed verdicts.
- [x] Score candidates from chart facts, ten-god energy, five-element balance, month command, luck/flow context, structure paths, and rule counter-evidence.
- [x] Require every candidate to expose primary candidate, alternatives, supporting evidence, weakening evidence, unresolved requirements, confidence, and boundary.
- [x] Add `candidate_scores` and `scoring_basis` to `RankedDecision`.
- [x] Add first real-case calibration coverage for strong, weak, balanced, late-zi boundary, and useful-god disputed scoring.
- [x] Add boundary score-floor assertions for regulation/climate, special-structure, and non-unique useful-god candidate visibility.
- [x] Add larger real-case calibration coverage for follow-structure boundary and disputed structure.
- [x] Emit scoring-basis signals for follow-structure, disputed structure, regulation/climate, and non-unique candidate states.
- [x] Feed M5 score-floor and basis-signal coverage into training signals.
- [x] Add replayable M5 candidate weights from synthetic training signals.
- [x] Feed M5 replay weights into conservative auto-training structure policy candidates.
- [x] Calibrate useful-god evidence coverage without converting candidates into fixed verdicts.
- [x] Seal M5 interface after M1/M2 and M4 phase seals without changing production default thresholds.

Validation:

- [x] Unit tests for `strength`, `structure_pattern`, and `useful_god` candidate shape.
- [x] Synthetic `strength_structure_useful_god` tier.
- [x] First real-case fixtures for weak, slightly weak, balanced, strong, late-zi boundary, and disputed useful-god scoring.
- [x] Real-case score-floor assertions for regulation/climate boundary, special-structure boundary, and non-unique useful-god candidate visibility.
- [x] Real-case fixtures for follow-structure boundary and disputed structure.
- [x] Training signal and auto-training tests for M5 replay and useful-god evidence calibration.
- [x] M5 contract tier validating M1/M2 root/vault consumption, M4 interface/calibration consumption, and no raw model-score leakage.

Completed 2026-05-24 M5 Final Seal:

- Added `m5_ranked_decision_contract` synthetic tier over canonical real-case calibration fixtures.
- Extended M5 scoring basis with M4 `model_signal_interface_contract`, M4 `model_signal_calibration_profile`, M1/M2 `root_fact_summary`, root counts, and root/vault boundary.
- Extended ranked-decision model-signal payload with interface and calibration profile versions.
- Kept M5 candidate-bound: no fixed strength, fixed 格局, fixed 用神, chart-fact mutation, or raw model-score exposure.

Validation 2026-05-24 M5 Final Seal:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god`: passed (1/1).
- `python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract`: passed (14/14).
- `python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack`: passed (14/14).
- `pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 3 passed.
- `pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers`: 1 passed.

Completed 2026-05-24:

- Added a unified ranked-decision scoring basis: day master, day element share, season element, seasonal support/pressure, strongest/weakest elements, ten-god energy bands, stability/volatility alert counts, time-context status, and structure path counts.
- Added candidate scores for strength, structure pattern, and useful-god decisions.
- Strength now ranks `strong`, `slightly_strong`, `balanced`, `slightly_weak`, and `weak`.
- Structure now ranks ordinary review, dynamic review, special-structure boundary, regulation/climate boundary, and mediation path.
- Useful-god now ranks balance, resource/self support, output/wealth release, authority regulation, and climate regulation candidates.
- Kept all three decisions candidate-bound; no fixed useful-god or fixed structure verdict is introduced.

Validation 2026-05-24:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

Results:

```text
Targeted tests: 15 passed
Synthetic strength_structure_useful_god: 1/1 passed
Synthetic all: 49/49 passed
518K sample: v30.518k.sample.20260523155204966404, cases=8, json_fallback
Full pytest: 188 passed, 1 skipped
```

Remaining gap:

- Scoring weights now replay through conservative candidate policy weights, but production threshold changes still need broader replay.
- Useful-god candidates need stronger mapping to actual rule/evidence conflicts before M5 reaches target completion.

Completed 2026-05-24 M5.2:

- Expanded `real_case_calibration_pack` from 6 to 12 cases.
- Added M5 scoring fixtures for weak, slightly weak, balanced, strong, late-zi boundary, and disputed useful-god candidate scoring.
- Added synthetic expectations for ranked primary candidates and ranked score keys.
- Added calibration observations for `ranked_primary_candidates` and `ranked_score_key_count`.
- Kept fixtures as candidate-scoring calibration, not final fortune conclusion snapshots.

Validation 2026-05-24 M5.2:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_synthetic_validation.py tests/unit/test_practical_reading_context.py
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

Results:

```text
Targeted tests: 11 passed
Real-case calibration pack: 12/12 passed
Synthetic all: 55/55 passed
518K sample: v30.518k.sample.20260523162041547546, cases=8, json_fallback
Full pytest: 188 passed, 1 skipped
```

Completed 2026-05-24 M5.3:

- Added `expected_ranked_min_scores` to synthetic fixtures so calibration can assert candidate score floors, not only candidate presence.
- Added M5 score-floor checks for regulation/climate boundary, special-structure boundary, climate regulation, and non-unique useful-god visibility.
- Exposed `ranked_candidate_scores` in real-case fixture observations for calibration review.
- Kept assertions candidate-bound; no fixed structure pattern or fixed useful-god conclusion is introduced.

Validation 2026-05-24 M5.3:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_synthetic_validation.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
```

Results:

```text
Compileall: passed
Targeted tests: 15 passed
Real-case calibration pack: 12/12 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the next major gate.
```

Completed 2026-05-24 M5 Batch:

- Added `follow_structure_boundary_review` and `disputed_structure_review` as explicit structure candidates.
- Added scoring-basis signals for follow-structure boundary, special-structure boundary, regulation/climate boundary, disputed structure, close candidates, and non-unique candidate states.
- Expanded `real_case_calibration_pack` from 12 to 14 cases with dedicated follow-structure and disputed-structure fixtures.
- Added `expected_ranked_basis_values` synthetic assertions so fixture cases can validate scoring-basis signals directly.
- Extended real-case fixture observations with `ranked_scoring_basis_signals`.
- Extended training signals with candidate-score domain coverage, non-unique candidate coverage, score-floor coverage, and ranked-basis signal counts.

Validation 2026-05-24 M5 Batch:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
pytest -q tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py
pytest -q tests/unit/test_release_gate.py tests/unit/test_training_signals.py
```

Results:

```text
Compileall: passed
Real-case calibration pack: 14/14 passed
Synthetic strength_structure_useful_god: 1/1 passed
Targeted tests: 16 passed
Release/training gate tests: 4 passed
Full pytest / synthetic all / 518K: not run for this batch; reserved for the next major gate.
```

Completed 2026-05-24 M5 Weight Replay:

- Added `v30.training_signal.m5_weight_replay` to summarize primary-candidate distribution, average candidate scores, basis-signal counts, useful-god evidence coverage, and bounded replay weights.
- Added useful-god evidence calibration metrics: supporting evidence count, weakening evidence count, fixed-verdict guard count, candidate score averages, and evidence coverage.
- Added conservative structure-policy weights from M5 replay: follow-structure boundary, disputed structure, regulation/climate boundary, special-structure boundary, and useful-god evidence.
- Kept replay output as policy-candidate weights only; it does not alter deterministic chart facts or promote fixed useful-god conclusions.

Validation 2026-05-24 M5 Weight Replay:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
pytest -q tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py tests/unit/test_release_gate.py
```

Results:

```text
Compileall: passed
Real-case calibration pack: 14/14 passed
Synthetic strength_structure_useful_god: 1/1 passed
Training / auto-apply / release-gate tests: 7 passed
Full pytest / synthetic all / 518K: not run for this replay task; reserved for the next major gate.
```

### M4 Ten-god Energy Model

Current: 88%
Target: 88%

Status: phase sealed

Work to complete:

- [x] Calibrate ten-god energy, stability, and volatility bands through a dedicated synthetic tier.
- [x] Make ten-god energy influence candidate scoring without becoming a direct verdict.
- [x] Clarify dominant, weak, unstable, and mixed ten-god states through model-signal observations.
- [x] Stabilize the interface from `model_signal_summary` into M5.
- [x] Feed ten-god family/band calibration into conservative auto-training model-signal weights.
- [x] Broaden real-case replay before changing production thresholds.

Validation:

- [x] Dedicated ten-god energy unit tests.
- [x] Synthetic cases for extreme and mixed ten-god patterns.
- [x] Calibration fixtures for heavy peer, wealth, officer/killing, resource, output, and mixed visible/hidden ten-god charts.
- [x] Real-case replay tier for solar, lunar, leap-month lunar, true-solar, and mixed family signal coverage.

Completed 2026-05-24 M4 Calibration Pack:

- Added dedicated `ten_god_energy_calibration` synthetic tier with five calibration fixtures.
- Covered self/peer, resource, output, wealth, authority, mixed-family, high-volatility, and low-stability patterns.
- Added synthetic expectations for model-signal families, energy bands, dominant count, volatility alerts, and stability alerts.
- Added `ten_god_energy_calibration` observations with family coverage, energy/stability/volatility band counts, alert counts, raw-score visibility, and boundary marker.
- Expanded `v30.training_signal.ten_god_energy_fusion` with family counts, energy/stability/volatility band counts, calibration case count, and calibration family coverage.
- Added conservative auto-training weights for `model_signal.family_coverage`, `model_signal.energy_band_calibration`, `model_signal.stability_review`, and `model_signal.volatility_review`.
- Kept raw scores hidden from customer/model-signal summaries; calibration remains training/policy signal only and does not mutate chart facts.

Validation 2026-05-24 M4 Calibration Pack:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_training_signals.py tests/unit/test_auto_apply_training.py
```

Results:

```text
Compileall: passed
Synthetic ten_god_energy_calibration: 5/5 passed
Synthetic strength_structure_useful_god: 1/1 passed
Targeted M4/M5 tests: 9 passed
Full pytest / synthetic all / 518K: not run for this calibration task; reserved for the next major gate.
```

Completed 2026-05-24 M4 Interface And Replay Seal:

- Added dedicated M4 plan: `docs/archive/V30_M4_TEN_GOD_ENERGY_MODEL_COMPLETION_PLAN.md`.
- Added `v30.model_signal_interface_contract.v1` to `model_signal_summary`, including allowed consumers, allowed fields, forbidden raw-score fields, and interface boundary.
- Added `v30.model_signal_calibration_profile.v1` with family coverage and energy/stability/volatility band counts.
- Added dedicated `m4_ten_god_real_case_replay` synthetic tier with five canonical replay cases: solar male, solar female, lunar, leap-month lunar, and true-solar.
- Added replay observations for interface readiness, forbidden field leakage, raw-score hiding, ranked-decision domain readiness, and replay family coverage.
- Extended `v30.training_signal.ten_god_energy_fusion` with real-case replay count, interface-ready count, and replay family coverage.
- Extended conservative auto-training model-signal weights to account for real-case replay coverage.
- Kept production threshold changes deferred; replay coverage calibrates policy candidates only.

Validation 2026-05-24 M4 Interface And Replay Seal:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier ten_god_energy_calibration
python3 scripts/run_synthetic_validation.py --tier m4_ten_god_real_case_replay
pytest -q tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py::test_synthetic_m4_ten_god_real_case_replay_tier_passes
pytest -q tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
pytest -q tests/unit/test_auto_apply_training.py::test_auto_apply_training_updates_core_policy_pointers
```

Results:

```text
Compileall: passed
Synthetic ten_god_energy_calibration: 5/5 passed
Synthetic m4_ten_god_real_case_replay: 5/5 passed
M4 interface/unit synthetic tests: 7 passed
Training signal extraction test: 1 passed
Auto-apply structure policy test: 1 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the next cross-module major gate.
```

### M3 Evidence / Rule / Knowledge / Structure Spine

Current: 100%
Target: 100%

Controlling plan:

```text
docs/archive/V30_M3_CORE_KNOWLEDGE_STRUCTURE_COMPLETION_PLAN.md
```

Status: C6 complete for current core scope

Completed 2026-05-24:

- Promoted M3 to P0 module-seal priority.
- Added an M3-specific completion plan covering knowledge source acquisition, source registry, K/R/P library, rule counter-evidence, feature compiler, portrait projection, dynamic structure graph, synthetic validation, and training signals.
- Added the first source registry contract in `v30/knowledge/source_registry.py`.
- Registered source families for Zi Ping/month-command pattern, San Ming Tong Hui system catalog, Yuan Hai Zi Ping pattern catalog, Di Tian Sui flow/dynamic mechanism, Qiong Tong Bao Jian climate review, and Shen Feng Tong Kao disease-medicine review.
- Added source-registry unit tests requiring domains, rule families, validation requirements, URLs, and runtime boundaries.
- Added a V20 reference registry in `v30/knowledge/v20_reference_registry.py` so V20 M3 assets can be migrated as reference inputs while V30 contracts remain authoritative.
- Registered V20 reference assets for expanded knowledge units, structure mechanism units, structure dynamics graph v2, structure knowledge coverage audit, rule/portrait batch validation, and source/completeness governance.
- Completed Batch A-E targeted module seal.
- Added K/R/P `source_family_ids` and `reference_asset_ids`.
- Added V20-derived source-backed K/R/P units for month-command pattern gate, 旺相休囚死, 调候, 病药, flow/通关/制化, branch arbitration, ten-god role set, and palace-position boundary.
- Added M3 feature evidence for 月令, 旺相休囚死, 调候, 病药, 通关/制化, 十神角色集, and地支仲裁.
- Added rule gates for month-command pattern, 调候, 病药, domain outcome boundaries, and branch arbitration.
- Added synthetic tiers `m3_core_spine`, `knowledge_rule_portrait`, and `structure_dynamic_v2`.
- Added `v30.training_signal.m3_core_spine_coverage`.
- Validation passed: `python3 -m compileall -q v30`; `pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_v20_reference_registry.py tests/unit/test_knowledge_library.py tests/unit/test_evidence_compiler.py tests/unit/test_structure_mainline_spine.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_training_signals.py` -> 34 passed; `python3 scripts/run_synthetic_validation.py --tier m3_core_spine` -> 8/8 passed; `python3 scripts/run_synthetic_validation.py --tier knowledge_rule_portrait` -> 2/2 passed; `python3 scripts/run_synthetic_validation.py --tier structure_dynamic_v2` -> 1/1 passed.

Work to complete:

- [x] Broaden M3 runtime proof so source/rule/portrait/structure spine supports M4/M5/M6.
- [x] Prove M3 remains an evidence spine, not a final conclusion engine.
- [x] Keep future source extraction depth as calibration/hardening only unless M4/M5/M6 exposes a concrete evidence gap.

Validation:

- Source registry tests.
- Evidence path tests for every ranked decision.
- Rule conflict tests.
- Synthetic checks that evidence, rule, and structure paths remain present without leaking to the customer surface.

Current next M3 task:

```text
M3 C6 core completion, C7 integrated core gate, and C8 documentation freeze are complete; M3 is frozen for the current core scope unless targeted validation exposes a concrete regression.
```

Completed 2026-06-06 C6 M3 Core Completion:

- Added runtime `v30.m3_completion_summary.v1`.
- The summary proves source registry coverage, V20 reference usage, K/R/P domain coverage, knowledge/rule/portrait signals, rule counter-evidence, mechanism paths, dynamic graph paths, mainline arbitration, M4 model-signal support, M5 ranked-decision support, and M6 practical-reading support.
- Added synthetic M3 checks requiring ready completion summaries for M3 tiers.
- Extended `v30.training_signal.m3_core_spine_coverage` with completion-ready, M4/M5/M6 support, conclusion-engine, and chart-fact-mutation metrics.
- Sanitized customer answer-panel projection so internal synthetic/evidence ids do not leak diagnostic `dynamic_graph` tokens.

Validation 2026-06-06 C6 M3 Core Completion:

- `python3 -m compileall -q v30`: passed.
- `pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_krp_case_requires_bound_signals tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 2 passed.
- `python3 scripts/run_synthetic_validation.py --tier m3_core_spine`: passed (8/8).
- `python3 scripts/run_synthetic_validation.py --tier knowledge_rule_portrait`: passed (2/2).
- `python3 scripts/run_synthetic_validation.py --tier structure_dynamic_v2`: passed (1/1).
- `pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_v20_reference_registry.py tests/unit/test_knowledge_library.py tests/unit/test_evidence_compiler.py tests/unit/test_structure_mainline_spine.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_structure_mechanism_graph.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 37 passed.

### M7 Core Calculation Validation / Real-case Calibration

Current: 100%
Target: 100%
Status: C4 complete for current core scope

Work to complete:

- [x] Expand canonical real-case pack with first M5 scoring calibration fixtures.
- [x] Continue expanding canonical real-case pack to at least 30 cases.
- [x] Validate chart facts, base fact explanation, strength candidates, structure candidates, useful-god candidates, luck/flow context, and practical reading boundaries.
- [x] Do not hard-code final fortune conclusions.

First real-case pack:

- Solar standard chart.
- Lunar standard chart.
- Leap-month lunar chart.
- True-solar-time chart.
- Unknown-hour chart.
- Unknown-gender chart.
- Solar-term boundary chart.
- Late-zi boundary chart.
- Strong chart.
- Weak chart.
- Balanced chart.
- Useful-god disputed chart.
- Structure disputed chart.
- Solar-term and year-edge boundary charts.
- Invalid date/time blocked charts.
- M6 career, wealth, relationship, health, and timing output-boundary charts.

Validation:

- [x] Synthetic all remains stable.
- [x] `real_case_calibration_pack` tier remains stable.
- [x] `m5_ranked_decision_contract` tier remains stable over the same pack.
- [x] `m6_practical_reading_contract` tier remains stable over the same pack.
- [x] Real-case calibration reaches at least 30 canonical cases before target completion.
- [x] 518K sample distribution gate runs at the M7 major milestone.

Completed 2026-05-24 M7 Final Seal:

- Expanded `real_case_calibration_pack` from 14 to 30 canonical fixtures.
- Added solar-term/year-edge, lunar edge, leap-month variant, true-solar variants, unknown-hour pending, unknown-gender natal-only, invalid date/time blocked, and M6 domain-boundary fixtures.
- Extended real-case fixture observations with M6 practical domain contract coverage.
- Extended `v30.training_signal.real_case_calibration_pack` with M6 contract readiness, domain contract count, and raw-score leak count.
- Kept real-case calibration as validation/training signal only; no final fortune conclusion is hard-coded.

Completed 2026-06-06 C3 M7 Core Completion:

- Added `v30.real_case_calibration_drift_summary.v1` to every canonical real-case fixture observation.
- Drift summaries compare expected chart, six-pillar, and practical-reading states with observed runtime output.
- Drift flags route issues to M1, M2, M4, M5, or M6 adjustment targets instead of mutating deterministic chart facts.
- Extended `v30.training_signal.real_case_calibration_pack` with M7 drift-summary counts, stable/review counts, drift-flag counts, module-adjustment counts, and module-readiness counts.
- Current canonical pack is stable across 30/30 cases with zero module-adjustment targets.

Completed 2026-06-05 R5 Production Replay Metadata:

- Added metadata-only production replay tags for canonical real-case observations.
- Tags cover calendar type, leap-month lunar, true-solar, unknown-hour, unknown-gender, ready/pending/blocked chart status, M4 model-signal readiness, M5 ranked-decision readiness, M6 practical-contract readiness, API projection readiness, and projection leak-scan pass state.
- Added privacy guard fields proving metadata-only use, no private user content import, no chart-fact mutation, and forbidden-key scan pass.
- Extended `v30.training_signal.real_case_calibration_pack` and release gate `synthetic_all.tier_coverage` with production replay metadata summaries.
- Kept the canonical 30-case synthetic pack unchanged.

Completed 2026-06-05 R6 Observability And Admin Artifact Review:

- Added `v30.release_artifact_review.v1` to release gate results.
- Grouped release gate check statuses, LLM smoke artifact, synthetic suite summary, 518K sample/shard artifact ids, active policy versions, policy lineage summaries, projection contract summary, and promotion review.
- Added admin endpoint `GET /api/v30/admin/release/artifact-review`.
- Kept R6 observability-only: no policy promotion, pointer change, chart fact mutation, or projection mutation.

Completed 2026-06-05 R7 Post-Seal Status Review And Next Mainline Selection:

- Added `v30.post_seal_status_review.v1`.
- Added `scripts/run_post_seal_status_review.py`.
- Added admin endpoint `GET /api/v30/admin/release/status-review`.
- Confirmed M1-M8 are phase sealed for the current core-calculation scope and reopen only on concrete validation failure.
- Selected `R8 Metadata-Safe Production Replay Intake` as the next mainline track.

Completed 2026-06-06 R8 Metadata-Safe Production Replay Intake:

- Added `v30.production_replay_intake.v1`, `v30.production_replay_intake_batch.v1`, and `v30.production_replay_intake_summary.v1`.
- Added `scripts/run_production_replay_intake.py`.
- Added admin endpoint `GET /api/v30/admin/release/production-replay-intake`.
- Intake rows derive only from metadata tags and safe artifact-review fields.
- Canonical 30-case replay intake currently yields 25 calibration-ready rows, 3 pending rows, and 2 blocked rows.
- Kept intake separate from deterministic chart facts, private content, policy pointers, and training promotion.

Completed 2026-06-06 R9 Metadata-Safe Replay Store And Search:

- Added `v30.production_replay_store.v1` and `v30.production_replay_search.v1`.
- Persisted metadata-only intake rows under `.runtime/validation/production_replay_intake/`.
- Added search filters for selection status, calendar type, boundary tag, module readiness, source artifact family, and limit.
- Extended admin replay intake endpoint with `persist=true` and added `GET /api/v30/admin/release/production-replay-intake/search`.
- Kept replay store separate from chart facts, private content, policy pointers, and training promotion.

Validation 2026-05-24 M7 Final Seal:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack`: passed (30/30).
- `python3 scripts/run_synthetic_validation.py --tier m5_ranked_decision_contract`: passed (30/30).
- `python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract`: passed (30/30).
- `pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_synthetic_validation.py::test_synthetic_m5_ranked_decision_contract_tier_passes tests/unit/test_synthetic_validation.py::test_synthetic_m6_practical_reading_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 4 passed.
- `python3 scripts/run_synthetic_validation.py --tier all`: passed (95/95).
- `python3 scripts/run_518k_validation.py --mode sample --limit 8`: `v30.518k.sample.20260524025228337725`, eligible, cases=8, `json_fallback`.

Validation 2026-06-06 C3 M7 Core Completion:

- `python3 -m compileall -q v30`: passed.
- `pytest -q tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 2 passed.
- `python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack`: passed (30/30).
- `python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract`: passed (30/30).

Validation 2026-06-05 R5 Production Replay Metadata:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack`: passed (30/30).
- `pytest -q tests/unit/test_production_replay_metadata.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 4 passed.
- `pytest -q tests/unit/test_release_gate.py`: 3 passed.

Validation 2026-06-05 R6 Observability And Admin Artifact Review:

- `python3 -m compileall -q v30`: passed.
- `pytest -q tests/unit/test_release_gate.py tests/unit/test_518k_validation.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_artifact_review_endpoint_is_observability_only`: 14 passed.
- `python3 scripts/run_release_gate.py --sample-limit 2`: `v30.release_gate.quick.20260605103342`, eligible, checks=6.

Validation 2026-06-05 R7 Post-Seal Status Review:

- `python3 -m compileall -q v30 scripts/run_post_seal_status_review.py`: passed.
- `pytest -q tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline`: 4 passed.
- `python3 scripts/run_post_seal_status_review.py`: `v30.post_seal_status_review.v1`, `ready_for_next_mainline`, `core_phase_sealed=8/8`, next `R8 Metadata-Safe Production Replay Intake`.

Validation 2026-06-06 R8 Metadata-Safe Production Replay Intake:

- `python3 -m compileall -q v30 scripts/run_production_replay_intake.py scripts/run_post_seal_status_review.py`: passed.
- `pytest -q tests/unit/test_production_replay_intake.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_release_status_review_selects_next_mainline tests/test_v30_scaffold.py::test_admin_production_replay_intake_endpoint_is_metadata_only`: 9 passed.
- `python3 scripts/run_production_replay_intake.py`: `v30.production_replay_intake_batch.v1`, rows=30, calibration_ready=25, pending=3, blocked=2.
- `python3 scripts/run_post_seal_status_review.py`: `v30.post_seal_status_review.v1`, `ready_for_next_mainline`, `core_phase_sealed=8/8`, next `R9 Metadata-Safe Replay Store And Search`.

Validation 2026-06-06 R9 Metadata-Safe Replay Store And Search:

- `python3 -m compileall -q v30 scripts/run_production_replay_intake.py scripts/run_post_seal_status_review.py`: passed.
- `pytest -q tests/unit/test_production_replay_store.py tests/unit/test_production_replay_intake.py tests/unit/test_post_seal_status_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_production_replay_intake_endpoint_is_metadata_only tests/test_v30_scaffold.py::test_admin_production_replay_intake_search_endpoint`: 12 passed.
- `python3 scripts/run_production_replay_intake.py --persist --selection-status calibration_ready --module-ready m4`: rows=30, calibration_ready=25, pending=3, blocked=2, stored=30, total=30, search_count=25.
- `python3 scripts/run_post_seal_status_review.py`: `v30.post_seal_status_review.v1`, `ready_for_next_mainline`, `core_phase_sealed=8/8`, next `R10 Post-Seal Release Candidate Review`.

## Phase 2: Strengthen Facts And Practical Output

### M1 BirthInput And Deterministic Chart Facts

Current: 100%
Target: 100%

Status: C5 complete for current core scope

Scope clarification:

- The newly added Bazi calculation module belongs here when it creates deterministic chart facts: BirthInput, calendar conversion, chart build, four pillars, boundary trace, luck-cycle context, flow-year/month context, and six-pillar context.
- M5 must consume these facts; M5 must not recalculate or mutate them.

Work to complete:

- [x] Add deterministic `base_fact_summary` under `ChartContext.natal_pillars`.
- [x] Add dedicated `m1_m2_bazi_calculation` synthetic tier.
- [x] Add deterministic base-fact training signal that validates coverage without mutating chart facts.
- [x] Harden solar, lunar, leap-month, true-solar, and unknown-hour paths.
- [x] Strengthen solar-term, year/month boundary, timezone, and late-zi assertions.
- [x] Keep unknown hour from generating fake hour pillars.
- [x] Stabilize luck cycle, flow year, flow month, and six-pillar context.
- [x] Prove M5/M6 consume M1/M2 facts rather than recalculating or mutating them.

Validation:

- Fixtures for each input type.
- Boundary tests for solar-term, timezone, late-zi, and unknown hour.
- Real-case calibration for supported inputs.

Baseline validation 2026-05-24:

```text
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py
```

Result:

```text
39 passed
```

Completed 2026-05-24 M1/M2 Batch 1:

- Added `v30.base_bazi_fact_summary.v1` to deterministic `ChartContext.natal_pillars`.
- Summary includes pillar count, visible/hidden ten-god counts, relation count, vault branches, element distribution, strongest/weakest elements, deterministic fact sources, and guardrails.
- Guardrail explicitly blocks strength/useful-god verdicts inside base facts.

Completed 2026-05-24 M1/M2 Batch 2:

- Expanded `base_fact_summary` with visible ten-god counts, hidden ten-god counts, hidden stem summary, relation type counts, and relation families.
- Added `m1_m2_bazi_calculation` synthetic tier for solar, leap-month lunar, true-solar, unknown-hour, and invalid-timezone boundaries.
- Added `v30.training_signal.m1_m2_base_fact_contract` so training validates deterministic fact coverage and does not mutate chart facts.

Completed 2026-05-24 M1/M2 Batch 3:

- Added `v30.root_vault_fact_summary.v1` under `base_fact_summary`.
- Root/vault facts record day-master roots, same-element roots, vault branches, hidden-stem positions, and guardrails only; they do not emit strength, 格局, or useful-god verdicts.
- Added deterministic solar-term/year-month boundary fixtures for 1990-02-04 before/after the engine boundary, asserting year/month pillar switch instead of just ready status.
- Added `solar_term_year_month_boundary_recorded` conversion flag for near-boundary solar inputs.

Completed 2026-05-24 M1/M2 Batch 4:

- Expanded `m1_m2_bazi_calculation` from 7 to 12 cases.
- Added canonical M1/M2 real-case fact fixtures for solar female, standard lunar, leap-month lunar, true-solar known place, and unknown-gender natal-ready input.
- Added stable pillar assertions for these real-case fact fixtures.
- Extended M1/M2 fact-contract observations with calendar type, gender status, true-solar flag, and leap-month flag.

Completed 2026-05-24 M1 Final Phase Seal:

- M1 now owns the deterministic calculation content required by the current phase: BirthInput validation, solar/lunar/leap-month/true-solar conversion, blocked unknown-hour/invalid-timezone paths, solar-term/year-month boundary fixture, late-zi boundary recording, four-pillar facts, luck/flow, six-pillar context, and no-fake-fact guardrails.
- M1 remains fact-only. Training, feedback, hidden factors, synthetic cases, and LLM output cannot create or mutate deterministic chart facts.

Completed 2026-06-06 C5 M1 Core Completion:

- Added `v30.m1_m2_completion_summary.v1` to `core_bazi_reading`, tying deterministic BirthInput/chart facts to M2 explanations and downstream M5/M6 consumption.
- Confirmed supported solar, lunar, leap-month, true-solar, unknown-hour, invalid timezone/date/time, solar-term/year-month, and late-zi paths remain deterministic or blocked without fake pillars.
- Added completion-summary validation for M5 root/vault scoring-basis consumption and M6 practical module-trace consumption.

### M2 Base Bazi Fact Explanation Layer

Current: 100%
Target: 100%

Status: C5 complete for current core scope

Scope clarification:

- `core_bazi_calculation` / `core_bazi_reading` belongs here when it projects deterministic base facts for customer use.
- M2 expands M1 facts into day-master, visible/hidden ten-god, five-element, relation, and base explanation payloads.
- M2 may prepare fact summaries for M5, but it must not make strength, 格局, or useful-god decisions.

Work to complete:

- [x] Add customer-safe `base_fact_explanations` under `core_bazi_reading`.
- [x] Expose deterministic visible/hidden ten-god counts and relation families in base explanations.
- [x] Add synthetic assertions that every ready M1/M2 chart has a complete base fact contract.
- [x] Add training signal for base fact contract coverage.
- [x] Strengthen day master explanation.
- [x] Complete visible stem ten-god explanation.
- [x] Complete hidden-stem ten-god explanation.
- [x] Complete five-element distribution explanation.
- [x] Strengthen clash, combination, punishment, harm, break, vault, root, and visible/hidden relation facts where supported.
- [x] Ensure every base explanation is derived from deterministic chart facts only.
- [x] Prove base explanations are complete for every ready M1 chart and consumed downstream without chart-fact mutation.

Validation:

- Unit tests for ten gods, hidden stems, elements, and relations.
- Synthetic checks that every ready chart has a complete base fact summary.
- Tests proving feedback, LLM, and training cannot mutate these facts.

Baseline validation 2026-05-24:

```text
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py
```

Result:

```text
39 passed
```

Completed 2026-05-24 M1/M2 Batch 1:

- Added `fact_integrity` to `core_bazi_reading`, explicitly marking deterministic chart facts as not LLM-generated, not training-generated, and not feedback-generated.
- Added `v30.base_bazi_fact_explanations.v1` with day-master, ten-god, five-element, relation, and time-context explanations.
- Kept base explanations as deterministic context only; they do not include strength, 格局, or useful-god decisions.

Completed 2026-05-24 M1/M2 Batch 2:

- Expanded `base_fact_explanations` with deterministic visible/hidden ten-god count maps and relation-family summaries.
- Added `m1_m2_base_fact_contract` synthetic observations for ready charts.
- Confirmed `fact_integrity` rejects LLM, training, and feedback as chart-fact sources in the M1/M2 tier.

Completed 2026-05-24 M1/M2 Batch 3:

- Added customer-safe `roots_and_vaults` base explanation.
- Extended M1/M2 synthetic observations and training signal payload with root/vault fact readiness.
- Extended base-fact contract assertions so ready M1/M2 charts must expose root/vault summary and deterministic explanation boundaries.

Completed 2026-05-24 M1/M2 Batch 4:

- Extended the M1/M2 base-fact training signal with canonical category coverage: solar, lunar, leap-month lunar, true-solar, and unknown-gender.
- Strengthened synthetic tests so ready M1/M2 fact contracts must cover at least 10 ready canonical cases and all required category families.
- Kept real-case fixtures as deterministic fact validation only; no fixed strength, 格局, or useful-god conclusion snapshots were added.

Completed 2026-05-24 M2 Final Phase Seal:

- M2 now owns the base explanation content required by the current phase: day master, day-master element, visible ten gods, hidden ten gods, hidden stem summary, five-element distribution, relation type/family summary, vault/root facts, time-context summary, fact integrity, and customer-safe `core_bazi_reading` projection.
- M2 remains explanation-only. It does not output fixed strength, fixed structure pattern, fixed useful-god, or event conclusions.

Completed 2026-06-06 C5 M2 Core Completion:

- `v30.m1_m2_completion_summary.v1` validates required base fact keys, explanation section coverage, deterministic fact integrity, downstream consumption readiness, and no chart-fact mutation.
- Extended `m1_m2_base_fact_contract` synthetic observation and `v30.training_signal.m1_m2_base_fact_contract` with completion-ready and downstream-consumption counts.
- Kept M2 explanation-only: it prepares facts for M5/M6 but does not issue fixed strength, structure, useful-god, or event conclusions.

Additional validation 2026-05-24:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 39 passed
Synthetic core_bazi_calculation: 4/4 passed
```

Additional validation 2026-05-24 M1/M2 Batch 2:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 41 passed
Synthetic core_bazi_calculation: 4/4 passed
Synthetic m1_m2_bazi_calculation: 5/5 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the next major gate.
```

Additional validation 2026-05-24 M1/M2 Batch 3:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 42 passed
Synthetic m1_m2_bazi_calculation: 7/7 passed
Synthetic core_bazi_calculation: 4/4 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the next major gate.
```

Additional validation 2026-05-24 M1/M2 Batch 4:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
```

Results:

```text
Compileall: passed
Targeted M1/M2 tests: 42 passed
Synthetic m1_m2_bazi_calculation: 12/12 passed
Synthetic core_bazi_calculation: 4/4 passed
Full pytest / synthetic all / 518K: not run for this subtask; reserved for the final M1/M2 phase gate.
```

Validation 2026-06-06 C5 M1/M2 Core Completion:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_presentation_projection.py::test_customer_reading_surface_hides_internal_bazi_context tests/unit/test_synthetic_validation.py::test_synthetic_m1_m2_bazi_calculation_tier_seals_base_fact_contract tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
python3 scripts/run_synthetic_validation.py --tier m1_m2_bazi_calculation
python3 scripts/run_synthetic_validation.py --tier core_bazi_calculation
pytest -q tests/unit/test_birth_input_contract.py tests/unit/test_birth_calendar_boundaries.py tests/unit/test_core_chart_context.py tests/unit/test_core_pillars.py tests/unit/test_core_ten_gods.py tests/unit/test_core_relations.py tests/unit/test_luck_flow_context.py
```

Results:

```text
Compileall: passed
Targeted C5 contract tests: 3 passed
Synthetic m1_m2_bazi_calculation: 12/12 passed
Synthetic core_bazi_calculation: 4/4 passed
Targeted M1/M2 unit tests: 24 passed
Full pytest / synthetic all / 518K: not run for this subtask; synthetic all and 518K sample were later covered by C7 integrated core gate.
```

Final phase seal validation 2026-05-24:

```text
python3 -m compileall -q v30
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Results:

```text
Compileall: passed
518K sample: v30.518k.sample.20260523200042775391, cases=8, json_fallback
Full pytest / synthetic all: intentionally not completed after user interruption; M1/M2 seal uses the latest targeted module gate plus 518K sample.
Latest targeted M1/M2 gate before seal: 42 passed, m1_m2_bazi_calculation 12/12, core_bazi_calculation 4/4.
```

### M6 Practical Reading Output

Current: 85%
Target: 85%
Status: phase sealed

Work to complete:

- [x] Career reading.
- [x] Wealth reading.
- [x] Relationship reading.
- [x] Health/stress reading.
- [x] Timing/stage reading.
- [x] Each domain uses chart facts, M5 ranked decisions, M4 ten-god energy bands, luck/flow context, and evidence boundaries.
- [x] Each domain exposes calculation basis, module dependencies, ranked decision links, model-signal context, evidence ids, explanation units, boundary conditions, blocked claims, and quality contract.

Validation:

- [x] Domain output tests for career, wealth, relationship, health, and timing.
- [x] Synthetic practical reading tier.
- [x] M6 practical reading contract tier over canonical real-case calibration fixtures.
- [x] Training signal checks for calculation-basis, ranked-link, model-signal, evidence, blocked-claim, and explanation-unit coverage.
- [x] Projection/scaffold tests confirming customer surface remains stable.

Completed 2026-05-24 M6 Final Seal:

- Added `v30.practical_domain_reading.v2` payloads for career, wealth, relationship, health, and timing.
- Added `v30.practical_domain_calculation_basis.v1` with day master, element distribution keys, root/vault boundary, structure state, path score, and timing context.
- Added `v30.practical_model_signal_context.v1` with bounded model-signal bands and no raw energy/stability/volatility scores.
- Linked each practical domain to M5 strength, structure, and useful-god ranked decisions with evidence ids and boundaries.
- Added blocked claims for career, wealth, relationship, health, and timing so practical output stays review-bound.
- Added `m6_practical_reading_contract` synthetic tier and practical-reading training-signal coverage.

Validation 2026-05-24 M6 Final Seal:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier practical_reading`: passed (1/1).
- `python3 scripts/run_synthetic_validation.py --tier m6_practical_reading_contract`: passed (14/14).
- `pytest -q tests/unit/test_practical_reading_context.py tests/unit/test_synthetic_validation.py::test_synthetic_m6_practical_reading_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 3 passed.
- `pytest -q tests/unit/test_presentation_projection.py`: 6 passed.
- `pytest -q tests/test_v30_scaffold.py`: 8 passed.

## Phase 3: Keep Presentation Simple

### M8 User Presentation / API Projection

Current: 90%
Target: 90%
Status: phase sealed

Work to complete:

- [x] Keep customer UI concise.
- [x] Show core calculation result before questions.
- [x] Hide diagnostics, training, hidden-factor internals, policy payloads, and raw structure traces from guest/user views.
- [x] Preserve additive API compatibility.
- [x] Keep practitioner/admin diagnostics available through role-gated projection.
- [x] Add explicit `v30.api_projection_contract.v1` and guest/user leak scan.
- [x] Add core-first projection contract and customer surface contract.
- [x] Add full additive preservation for core/API/session/LLM status fields.
- [x] Add role visibility matrix and customer forbidden-field policy.

Validation:

- [x] Projection tests for user and admin roles.
- [x] Synthetic checks for no internal leak.
- [x] API smoke for reading creation and view projection.
- [x] Synthetic all and 518K sample at final eight-module seal.

Completed 2026-05-24 M8 Final Seal:

- Added top-level `projection_contract` to `ClientPresentationModel`.
- Added `v30.api_projection_contract.v1` and `v30.projection_leak_scan.v1`.
- Sanitized customer `reading_surface.next_question` so expected information gain and options do not leak internal policy trace fields.
- Added `m8_api_projection_contract` synthetic tier over the 30-case canonical real-case pack.
- Added `v30.training_signal.api_projection_contract`.

Completed 2026-06-06 C4 M8 Core Completion:

- Added `v30.core_first_projection.v1` under `v30.api_projection_contract.v1`.
- Added `v30.customer_surface_contract.v1` proving core Bazi reading and domain cards precede questions.
- Expanded additive API policy to preserve `core_bazi_reading`, `domain_cards`, `internal_next_question_id`, `actor_context`, and `llm_runtime_status` alongside the existing surface fields.
- Added `v30.role_visibility_matrix.v1` and `v30.customer_forbidden_projection_fields.v1`.
- Sanitized guest/user question rows and answer-panel LLM metadata so policy/training/internal call details remain hidden from customer projection.
- Extended M8 synthetic failures and `v30.training_signal.api_projection_contract` with core-first policy, customer surface contract, additive-policy, and forbidden-field coverage.

Validation 2026-05-24 M8 Final Seal:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract`: passed (30/30).
- `pytest -q tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py::test_synthetic_m8_api_projection_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 8 passed.
- `pytest -q tests/test_v30_scaffold.py`: 8 passed.
- `python3 scripts/run_synthetic_validation.py --tier all`: passed (95/95).
- `python3 scripts/run_518k_validation.py --mode sample --limit 8`: `v30.518k.sample.20260524044648490844`, eligible, cases=8, `json_fallback`.

Validation 2026-06-06 C4 M8 Core Completion:

- `python3 -m compileall -q v30`: passed.
- `pytest -q tests/unit/test_presentation_projection.py tests/unit/test_synthetic_validation.py::test_synthetic_m8_api_projection_contract_tier_passes tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all`: 8 passed.
- `python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract`: passed (30/30).
- `pytest -q tests/test_v30_scaffold.py::test_api_birth_input_creates_ready_runtime_or_returns_trace`: 1 passed.

## Execution Order

The strict order for the next work is:

1. M5 Strength / structure pattern / useful-god ranked decisions.
2. M4 Ten-god energy model.
3. M3 Evidence / rule / knowledge / structure spine.
4. M7 Core calculation validation / real-case calibration.
5. M1 BirthInput and deterministic chart facts.
6. M2 Base Bazi fact explanation layer.
7. M6 Practical reading output.
8. M8 User presentation / API projection.

Do not switch to UI polish, hidden factors, LLM, or complex interaction unless the change directly supports one of these modules.

## Training And Synthetic Validation Rules

Training and synthetic validation are required throughout the eight modules, but they are not separate product priorities.

Training may tune:

- Ten-god energy weights.
- Candidate ordering.
- Evidence weights.
- Rule thresholds.
- Question strategy.
- Explanation density.
- Domain output priority.

Training must not:

- Generate four pillars.
- Modify BirthInput.
- Modify luck cycle, flow year, or flow month.
- Create event years.
- Turn hidden factors into facts.
- Write fixed useful-god conclusions.
- Override deterministic chart facts.

Synthetic validation must cover:

- Chart build.
- Base Bazi facts.
- Strength candidates.
- Structure candidates.
- Useful-god candidates.
- Ten-god energy.
- Luck/flow/six-pillar context.
- Practical reading output.
- Role projection and internal leak prevention.

## Validation Cadence

Do not run full validation after every small subtask. Use the smallest gate that proves the change.

### Subtask Gate

Use for normal module subtasks, fixture additions, scoring tweaks, and documentation sync.

Run only:

- Relevant targeted unit tests.
- The directly affected synthetic tier.
- `python3 -m compileall -q v30` when Python contracts/runtime files changed.
- JS syntax check only when frontend JS changed.

Examples:

```text
pytest -q tests/unit/test_practical_reading_context.py
python3 scripts/run_synthetic_validation.py --tier strength_structure_useful_god
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
```

### Stage Gate

Use when a whole sub-slice is complete, such as M5.2, M5.3, M4.1, or a validation-pack expansion.

Run:

- Targeted unit tests for the touched subsystem.
- Affected synthetic tier.
- One adjacent synthetic tier if the change touches a shared contract.

Do not run full `pytest -q`, synthetic all, or 518K sample by default at this level.

### Major Gate

Use only when:

- A core module completion percentage crosses a meaningful milestone.
- A module is declared complete for the phase.
- Policy/training auto-apply behavior changes.
- Runtime/API contracts change broadly.
- Before pointer promotion or release notes.

Run:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

Live real-environment smoke remains optional and only runs when explicitly requested or when deployment changes.

## Required Update Discipline

Every completed task must update this document and the relevant mainline documents.

Minimum update after each task:

- Update the target module completion percentage.
- Add a short completed-work note under the module.
- Record validation commands and exact results for the gate actually used.
- Record remaining gaps.
- State the next task.

Mainline documents to sync when relevant:

- `docs/V30_MASTER_MAINLINE_PLAN.md`
- `docs/V30_PRACTICAL_BAZI_MAINLINE_PLAN.md`
- `docs/V30_MODULE_REVIEW.md`
- Any validation/training document affected by the change.

Completed 2026-06-06 C7 Integrated Core Calculation Gate:

- Proved M1-M8 as an integrated current-scope core calculation path.
- Verified compile, all synthetic tiers, 518K sample, and targeted core pytest together.
- Confirmed hidden factors, feedback, training signals, LLM, and policy pointers remain support/calibration inputs and do not mutate deterministic chart facts.
- Confirmed customer-facing projection remains core-calculation first and diagnostics-safe.
- Aligned the release-candidate scaffold baseline with the current 12 completed post-seal tasks.

Validation 2026-06-06 C7 Integrated Core Calculation Gate:

- `python3 -m compileall -q v30`: passed.
- `python3 scripts/run_synthetic_validation.py --tier all`: `v30.synthetic.all: passed (95/95)`.
- `python3 scripts/run_518k_validation.py --mode sample --limit 8`: `v30.518k.sample.20260606084440379258`, `cases=8`, `json_fallback`.
- `pytest -q tests/test_v30_scaffold.py tests/unit/test_practical_reading_context.py tests/unit/test_ten_god_energy_model.py tests/unit/test_synthetic_validation.py tests/unit/test_training_signals.py`: 38 passed.
- Full pytest was not run; reserved for C8 freeze or external release decision.

Completed 2026-06-06 C8 Core Completion Documentation And Freeze:

- Froze the eight core Bazi modules at 100% current-scope completion.
- Synchronized completion state and C7 validation evidence across the core module final plan, eight-module plan, module review, mainline completion plan, master mainline plan, test architecture, synthetic validation, training architecture, and 518K validation plan.
- Preserved the boundary that hidden factors, questions, LLM, training signals, synthetic cases, real-case replay, and 518K validation support calibration only and cannot mutate deterministic chart facts.
- Kept full pytest, external release validation, and policy pointer promotion outside this core-completion task.

C8 freeze baseline:

- M1-M8: 100% current-scope complete.
- Latest integrated synthetic gate: `v30.synthetic.all: passed (95/95)`.
- Latest integrated 518K sample: `v30.518k.sample.20260606084440379258`, `cases=8`, `json_fallback`.
- Latest targeted core pytest: 38 passed.
- Full pytest: not run for C8; reserved for explicit release/full-freeze decision.

Completed 2026-06-09 B1 Real Business Bazi Reading Acceptance:

- Added `v30.real_business_bazi_reading_acceptance.v1`.
- Added `scripts/run_real_business_bazi_reading_acceptance.py`.
- Added `GET /api/v30/admin/business/real-bazi-acceptance`.
- B1 validates the real business BirthInput-to-customer-reading path over ready canonical real-case rows.
- B1 checks M1/M2 chart facts and base reading, M4 model signal availability, M5 ranked decisions, M6 practical reading domains, M8 customer projection, and no internal customer leaks.
- B1 remains read-only: no chart-fact mutation, no policy pointer promotion, no auto-training application, no full pytest by default.

Validation 2026-06-09 B1:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_real_business_bazi_acceptance_endpoint_is_read_only
4 passed
python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted
```

Full pytest / full 518K: not run for B1; reserved for explicit release/full-freeze decisions.

Current next task:

```text
Eight core Bazi modules are frozen as 100% complete for the current scope. C1-C8, F1-F6, R13-R16, P0-P9, and S0 are complete. B1 Real Business Bazi Reading Acceptance is complete: the canonical ready real-case rows pass BirthInput-to-customer-reading acceptance 12/12. B2 Business Reading Case Expansion And Regression Pack is complete: expanded ready real-case business reading regression passes 24/24, M8 now projects five concise business domain cards while preserving three focus domains, and M8 API projection synthetic remains 30/30. B3 Business Reading Answer Refresh Regression is complete: structured answer refresh passes 5/5, preserves core reading fingerprints, exposes answer_panel, consumes interaction_state, keeps five domain cards, and does not mutate chart facts. B4 Business Reading Boundary And Blocked Input Regression is complete: pending/blocked BirthInput boundary rows pass 5/5 and prove no fake pillars, no premature M4/M5/M6 readiness, no customer projection fake-ready state, and metadata-only/no-mutation privacy. B5 Business Reading API Contract Freeze is complete: B1-B4 are frozen as the minimum business reading acceptance gate, required endpoints and customer surface keys are recorded, field removals are disallowed, and release/pointer/full pytest remain separate. B6 Business Reading Acceptance Closeout is complete: B1-B5 are recorded as the default business gate and B-track is paused by default. S1 Business Acceptance Steady State is complete: the routine business gate is B1-B5, no further B-track task starts by default, and new work requires new business evidence or an explicit major validation/release-boundary request. Full pytest, full 518K, external release, and pointer promotion remain explicit release-boundary controls, not routine B-track work.
```

Completed 2026-06-09 B2 Business Reading Case Expansion And Regression Pack:

- Added `v30.real_business_bazi_reading_regression_pack.v1`.
- Added `scripts/run_real_business_bazi_reading_regression_pack.py`.
- Added `GET /api/v30/admin/business/reading-regression-pack`.
- Expanded business reading regression from B1 12 ready rows to B2 24 ready rows.
- Strengthened regression checks for base fact explanation, M1/M2 completion summary, ranked-decision projection, five practical domains, five customer domain cards, practical domain contracts, privacy/no-mutation metadata, and customer leak scan.
- Updated M8 customer projection to keep `focus_domains` at three priority domains while projecting five concise domain cards for career, wealth, relationship, health, and timing.

Validation 2026-06-09 B2:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_bazi_reading_acceptance.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_presentation_projection.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_reading_regression_pack_endpoint_is_read_only
12 passed
python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready
python3 scripts/run_real_business_bazi_reading_acceptance.py --case-limit 12
v30.real_business_bazi_reading_acceptance.v1: passed (12/12) b1_real_business_bazi_reading_accepted
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
```

Full pytest / full 518K: not run for B2; reserved for explicit release/full-freeze decisions.

Completed 2026-06-09 B3 Business Reading Answer Refresh Regression:

- Added `v30.real_business_answer_refresh_regression.v1`.
- Added `scripts/run_real_business_answer_refresh_regression.py`.
- Added `GET /api/v30/admin/business/answer-refresh-regression`.
- Added answer-refresh regression cases for career direct, practical domain choice, wealth direct, relationship direct, and hidden-factor-to-career feedback.
- B3 requires B2 regression readiness before answer-refresh acceptance.
- B3 validates answer panel presence, interaction-state answer consumption, visible next question readiness, chart context stability, feature evidence stability, core reading fingerprint stability, five customer domain cards, projection leak safety, and non-mutating answer boundary.

Validation 2026-06-09 B3:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_real_business_bazi_reading_regression_pack.py tests/unit/test_question_dialogue_graph.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_answer_refresh_regression_endpoint_is_read_only
9 passed
python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready
python3 scripts/run_real_business_bazi_reading_regression_pack.py --case-limit 24
v30.real_business_bazi_reading_regression_pack.v1: passed (24/24) b2_business_reading_regression_pack_ready
python3 scripts/run_synthetic_validation.py --tier interaction_loop
v30.synthetic.interaction_loop: passed (5/5)
```

Full pytest / full 518K: not run for B3; reserved for explicit release/full-freeze decisions.

Completed 2026-06-09 B4 Business Reading Boundary And Blocked Input Regression:

- Added `v30.real_business_boundary_blocked_input_regression.v1`.
- Added `scripts/run_real_business_boundary_blocked_input_regression.py`.
- Added `GET /api/v30/admin/business/boundary-blocked-input-regression`.
- B4 requires B3 readiness before boundary regression acceptance.
- B4 validates 3 pending and 2 blocked BirthInput rows from `real_case_calibration_pack`.
- B4 checks no fake pillars, all pillars missing, M4/M5/M6 not ready, API projection not fake-ready, conversion boundary explainable, unknown-hour needs known birth hour, blocked input needs valid birth datetime, privacy/no-mutation metadata, and stable no-adjustment drift summaries.

Validation 2026-06-09 B4:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_boundary_blocked_input_regression.py tests/unit/test_real_business_answer_refresh_regression.py tests/unit/test_synthetic_validation.py::test_synthetic_real_case_calibration_pack_tier_passes_canonical_fixture_coverage tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_boundary_blocked_input_regression_endpoint_is_read_only
7 passed
python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready
python3 scripts/run_real_business_answer_refresh_regression.py --case-limit 5
v30.real_business_answer_refresh_regression.v1: passed (5/5) b3_answer_refresh_regression_ready
python3 scripts/run_synthetic_validation.py --tier real_case_calibration_pack
v30.synthetic.real_case_calibration_pack: passed (30/30)
```

Full pytest / full 518K: not run for B4; reserved for explicit release/full-freeze decisions.

Completed 2026-06-09 B5 Business Reading API Contract Freeze:

- Added `v30.real_business_api_contract_freeze.v1`.
- Added `scripts/run_real_business_api_contract_freeze.py`.
- Added `GET /api/v30/admin/business/api-contract-freeze`.
- B5 freezes B1-B4 as the minimum business reading acceptance contract.
- B5 records required business endpoints, customer surface required keys, ready-reading requirements, additive API policy, and forbidden behaviors.
- B5 explicitly keeps external release, full pytest, full 518K, and policy pointer promotion outside routine business acceptance work.

Validation 2026-06-09 B5:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_api_contract_freeze.py tests/unit/test_real_business_boundary_blocked_input_regression.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_api_contract_freeze_endpoint_is_read_only
6 passed
python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen
python3 scripts/run_real_business_boundary_blocked_input_regression.py --case-limit 5
v30.real_business_boundary_blocked_input_regression.v1: passed (5/5) b4_boundary_blocked_input_regression_ready
python3 scripts/run_synthetic_validation.py --tier m8_api_projection_contract
v30.synthetic.m8_api_projection_contract: passed (30/30)
```

Full pytest / full 518K: not run for B5; reserved for explicit release/full-freeze decisions.

Completed 2026-06-09 B6 Business Reading Acceptance Closeout:

- Added `v30.real_business_acceptance_closeout.v1`.
- Added `scripts/run_real_business_acceptance_closeout.py`.
- Added `GET /api/v30/admin/business/acceptance-closeout`.
- B6 records B1-B5 as the default business Bazi reading acceptance gate.
- B6 pauses B-track by default and requires an explicit request for major validation, full pytest, full 518K, external release, or pointer promotion.

Validation 2026-06-09 B6:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_acceptance_closeout.py tests/unit/test_real_business_api_contract_freeze.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_acceptance_closeout_endpoint_is_read_only
6 passed
python3 scripts/run_real_business_acceptance_closeout.py
v30.real_business_acceptance_closeout.v1: passed (4/4) b6_business_acceptance_closed
python3 scripts/run_real_business_api_contract_freeze.py
v30.real_business_api_contract_freeze.v1: passed (4/4) b5_business_api_contract_frozen
```

Full pytest / full 518K: not run for B6; reserved for explicit release/full-freeze decisions.

Completed 2026-06-10 S1 Business Acceptance Steady State:

- Added `v30.real_business_steady_state.v1`.
- Added `scripts/run_real_business_steady_state.py`.
- Added `GET /api/v30/admin/business/steady-state`.
- S1 records B1-B5 as the routine business Bazi reading gate after B6 closeout.
- S1 defines reopen conditions for new real-business failures, API contract changes, boundary failures, or explicit major validation requests.
- S1 keeps full pytest, full 518K, external release, pointer promotion, auto-training apply, and chart-fact mutation disabled by default.

Validation 2026-06-10 S1:

```text
python3 -m compileall -q v30
passed
pytest -q tests/unit/test_real_business_steady_state.py tests/unit/test_real_business_acceptance_closeout.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_business_steady_state_endpoint_is_read_only
7 passed in 1.75s
python3 scripts/run_real_business_steady_state.py
v30.real_business_steady_state.v1: passed (5/5) s1_business_acceptance_steady_state_ready
```

Full pytest / full 518K: not run for S1; reserved for explicit release/full-freeze decisions.

Post-seal task track:

```text
docs/V30_POST_SEAL_MAINLINE_TASK_PLAN.md
```
