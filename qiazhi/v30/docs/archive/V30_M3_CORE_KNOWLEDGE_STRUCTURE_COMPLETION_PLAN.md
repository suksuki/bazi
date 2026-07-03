# V30 M3 Core Knowledge / Rule / Portrait / Feature / Dynamic Structure Completion Plan

Updated: 2026-05-24

Status snapshot updated: 2026-06-10

## Purpose

M3 is the core support layer for Bazi calculation. It must make every non-deterministic judgment traceable, bounded, and verifiable.

M3 includes:

- Bazi knowledge library.
- Rule library.
- Portrait/projection library.
- Feature evidence compiler.
- Rule counter-evidence.
- Knowledge/rule/portrait source registry.
- Dynamic structure graph.
- Mechanism paths.
- Synthetic validation and training signals for the above.

M3 is not a UI task, not an LLM task, and not a prompt-writing task. It is the calculation support spine for M4, M5, and M6.

## Source Strategy

Network-sourced knowledge is allowed only through a source registry and extraction queue. No external text may become a runtime verdict directly.

V20 is allowed as an internal reference source, but only as asset input. V30 must not import V20 runtime modules, reuse V20 payload shapes as contracts, or inherit the old presentation/orchestrator boundaries.

Initial source families:

| Source family | M3 use | Extraction target | Boundary |
|---|---|---|---|
| Zi Ping / 格局月令 | Month-command, pattern formation, success/failure/rescue, useful-god as candidate path | Structure-pattern rules, useful-god candidate boundaries, 格局成败救应 features | Candidate review only; no fixed destiny verdict |
| San Ming Tong Hui | Five-element generation/control, 旺相休囚死, ten-god categories, branch relations, luck/flow context | Feature atoms, relation rules, time-layer evidence | Fact/relationship support only; no event prediction |
| Yuan Hai Zi Ping | Ten-god categories, month command, inner/outer pattern catalog, branch relation material | Ten-god family units, pattern catalog, branch relation feature atoms | Catalog support only; no direct outcome |
| Di Tian Sui | Flow, 通关, 制化, clearing blockage, dynamic interaction | Dynamic graph mechanism paths and path-resolution families | Mechanism candidate only |
| Qiong Tong Bao Jian | 调候, seasonal climate, ten stems by month | Regulation/climate boundary, useful-god climate candidates | Climate review only; no direct final useful-god verdict |
| Shen Feng Tong Kao | 病药, 雕枯旺弱, 损益生长 | Counter-evidence, 病药 review, useful-god weakening/supporting evidence | Diagnostic review only |
| Modern explainers / practitioner notes | Cross-check terminology and examples | Calibration hints and fixture ideas | Secondary source; never canonical by itself |

Sources found during the first network pass:

- `子平真诠`: month-command, pattern, useful-god success/failure/rescue framing.
- `三命通会`: five-element generation/control, branch relations, ten-god, luck/flow, many pattern catalogs.
- `渊海子平`: ten-god, month command, inner/outer pattern catalog, branch relation and classic pattern material.
- `滴天髓`: flow/generation/control and dynamic interaction framing.
- `穷通宝鉴`: seasonal regulation and ten-stem/month climate-use review.
- `神峰通考`: 病药 and four illness/four medicine framing.

The source registry must record URL, source tier, extraction domains, rule families, validation requirements, and boundaries. Runtime K/R/P units should bind to source family ids, not raw web text.

## V20 Reference Strategy

V20 assets are valuable because they already contain many M3-adjacent decisions, coverage checks, mechanism labels, and boundary rules. They are not directly reusable runtime code.

Initial V20 reference assets:

| V20 asset | V30 target | Reusable concept | Boundary |
|---|---|---|---|
| `../v20/knowledge/loader.py:_expanded_knowledge_units` | K/R/P library | 气势流通、寒暖燥湿、调候路径、宫位层、时间层、十神细分、五行生克制化、墓库、刑害破穿、合化合绊、做功、应用主题边界 | Convert into V30 `KnowledgeRulePortraitUnit`; no V20 runtime import |
| `../v20/knowledge/structure_mechanisms.py` | Mechanism graph | 食神制杀、伤官制杀、食伤生财、财生官、官印/杀印、印承身、比劫承身、印制食伤、比劫夺财、财破印 | Convert into V30 evidence-bound mechanism paths |
| `../v20/dynamics/graph_engine.py` | Dynamic graph | Weighted nodes/edges/paths, family chain, semantic candidates, policy weights, guardrails | Use as algorithm reference only; V30 owns graph contracts |
| `../v20/validation/structure_dynamics_knowledge_coverage.py` | M3 validation/training | Structure label coverage, mechanism support, knowledge/rule support, unsupported label gaps | Convert into synthetic/training observations |
| `../v20/validation/rule_portrait_batch.py` | Rule/portrait validation | Rule-domain generation, portrait axis coverage, runtime-blocked guard | Convert into V30 validation tier |
| `../v20/knowledge/source_catalog.py` and coverage/audit modules | Source registry governance | Source catalog, completeness audit, coverage gaps, review queue | Use only for V30 governance design |

The V20 reference registry lives in:

```text
v30/knowledge/v20_reference_registry.py
```

Completed 2026-05-24:

- Added V20 reference registry for M3.
- Registered V20 expanded knowledge units, structure mechanisms, dynamic graph v2, knowledge coverage audit, rule/portrait batch validation, and source/completeness governance as migration inputs.
- Enforced the boundary `no_v20_runtime_import` on every V20 reference asset.
- Validation passed: `python3 -m compileall -q v30`; `pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_v20_reference_registry.py tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py` -> 10 passed.

Every migrated V20 concept must pass through:

```text
V20 reference asset
-> V30 source family / synthetic-only status
-> V30 FeatureEvidence or KnowledgeRulePortraitUnit or RuleEvidenceSpec or DynamicGraphPath
-> V30 synthetic validation
-> V30 training signal
```

## Completion Definition

M3 reaches completion only when all of these are true:

1. Every M4/M5/M6 judgment path can cite evidence ids.
2. Every evidence id can be traced to a feature, rule, K/R/P unit, mechanism path, or source family.
3. Knowledge units are structured data, not prompt filler.
4. Rule units emit support, weaken, blocked, countered, and boundary states.
5. Portrait units remain projections; they never become chart facts.
6. Dynamic structure paths include competing, suppressed, blocked, countered, conflict, and resolution states.
7. Useful-god, strength, and structure decisions consume M3 evidence rather than bypass it.
8. Synthetic validation covers positive, negative, counter-evidence, boundary, and domain-calibration cases.
9. Training signals tune rule weights, K/R/P weights, dynamic path weights, and expression density only.
10. Chart facts, pillars, luck cycles, and flow timing remain immutable deterministic facts.

## One-shot Module Seal Execution Plan

M3 must be completed as one module-seal run. The work can have internal commits and targeted checks, but there is no switch to M4/M5/M6/UI/LLM/session work until M3 passes its final gate.

Execution order:

| Batch | Scope | Output | Gate |
|---|---|---|---|
| A | Knowledge library coverage | Source-family ids on K/R/P units; V20 reference concepts converted into V30 K/R/P units; expanded core domains for chart, element, ten-god, branch, time, strength, pattern, useful-god, wealth, career, relationship, health, timing | completed |
| B | Rule and feature spine | Rule specs for climate, 病药, pattern, useful-god, hidden factor, branch relation, domain outcome boundaries; feature atoms for 月令, 旺相休囚死, 调候, 病药, 通关/制化, branch arbitration | completed |
| C | Portrait and dynamic structure | Role-safe portrait projections; V20 mechanism labels rebuilt as V30 mechanism paths; dynamic graph paths for strength, pattern, useful-god, domain review, 调候, 病药, 通关, 制化 | completed |
| D | Validation and training | Dedicated `m3_core_spine` synthetic tier; M3 training signals for source coverage, K/R/P coverage, rule counter-evidence, feature-domain coverage, dynamic-path coverage, boundary leakage | completed |
| E | M3 final gate and docs | Final completion review, completion percentage update, validation results, remaining gaps, next module decision | completed targeted final gate |

Non-negotiable constraints:

- No V20 runtime import.
- No raw web text as runtime truth.
- No fixed useful-god, 格局, wealth, career, relationship, health, or timing verdict from a single rule.
- No customer projection of diagnostics, policy payloads, or raw evidence internals.
- No training mutation of chart facts, pillars, luck, or flow timing.

M3 seal target:

```text
Current: 96%
Seal target: 96%
Promotion condition: targeted final gate passed; major all/518K/full pytest gate remains reserved for the next broader module milestone.
```

## 2026-06-10 Current Module Health

M3 remains sealed for the current core runtime scope, but the seal means "usable, bounded, and verifiable for the current runtime", not "all Bazi knowledge content is exhaustively complete".

Current verified runtime inventory:

| Area | Current inventory | Judgment |
|---|---:|---|
| K/R/P units | 54 total: 14 knowledge, 35 rule, 5 portrait | Active runtime support, not prompt filler. |
| Rule evidence specs | 9 | Covers time boundary, useful-god candidate gate, hidden-factor dialogue, branch dynamic review, month-command/pattern gate, 调候, 病药, domain outcome blocking, and branch arbitration. |
| Source families | 6 | Zi Ping, San Ming Tong Hui, Yuan Hai Zi Ping, Di Tian Sui, Qiong Tong Bao Jian, Shen Feng Tong Kao are registered as source families. |
| Runtime domains | 14 | chart, element, ten-god, branch relation, time context, structure pattern, structure dynamic, useful-god, wealth, career, relationship, health, hidden factor, rule counter-evidence. |
| Macro portrait domains | 7 | foundation, wealth, career, relationship, romance, health, hidden factor. |
| Portrait dimensions/tags | 47 dimensions, 54 tags | Role-aware projection exists; customer views remain bounded and diagnostics are reserved for practitioner/admin. |

Targeted validation on 2026-06-10:

```text
pytest -q tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py tests/unit/test_portrait_projection.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_structure_mechanism_graph.py tests/unit/test_knowledge_source_registry.py
22 passed
```

Current practical judgment:

- Bazi knowledge library: current-scope complete and runtime-bound, but not exhaustive; next growth should be source-governed expansion plus real-case calibration tags.
- Bazi rule library: current-scope usable; rules are defeasible and boundary-first, but domain-specific rule depth still needs real-case replay and calibration.
- Bazi portrait system: role-aware macro portrait projection is active; next work is explanation density, not chart-fact mutation.
- Bazi feature evidence: active as M3 support spine for M4/M5/M6; the next risk is coverage depth, not pipeline absence.

Do not reopen M3 simply because content can grow. Reopen M3 only if new validation shows an unbound judgment path, source-free runtime knowledge, role leakage, chart-fact mutation, or missing rule counter-evidence.

## 2026-06-10 M3 Data Persistence And Next Gaps

M3 support data is now persisted into dedicated V30 Postgres tables instead of only living in runtime traces or JSON artifacts.

Dedicated M3 tables:

| Table | Purpose | Current rows |
|---|---|---:|
| `v30_m3_knowledge_units` | K/R/P runtime units, including knowledge/rule/portrait unit metadata and boundaries. | 54 |
| `v30_m3_rule_specs` | Defeasible rule evidence specs and rule decision states. | 9 |
| `v30_m3_portrait_assets` | Macro portrait dimensions/assets. | 7 |
| `v30_m3_validation_snapshots` | M3 inventory/runtime/synthetic snapshot plus M3 518K sample summary snapshot. | 2 |
| `v30_m3_source_backlog` | G4 source-family extraction backlog rows for review and admin/training filtering. | 6 |

Implementation:

```text
v30/storage/m3.py
v30/validation/m3_core_spine_snapshot.py
scripts/run_m3_core_spine_snapshot.py
```

Latest DB write:

```text
python3 scripts/run_m3_core_spine_snapshot.py --sample-limit 1
v30.m3.snapshot.20260610045211763673: krp=54 rules=9 portrait_assets=7 synthetic=8/8
db: postgres searchable=True rows={'knowledge_units': 54, 'rule_specs': 9, 'portrait_assets': 7, 'validation_snapshots': 1}

M3 518K summary snapshot:
v30.m3.snapshot.518k.20260610044238766995
db: postgres searchable=True rows={'knowledge_units': 0, 'rule_specs': 0, 'portrait_assets': 0, 'validation_snapshots': 1}
```

Latest focused M3 validation:

```text
pytest -q tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_storage_adapters.py tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py tests/unit/test_portrait_projection.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_structure_mechanism_graph.py tests/unit/test_knowledge_source_registry.py
30 passed

python3 scripts/run_m3_core_spine_snapshot.py --no-db --sample-limit 2
v30.m3.snapshot.20260610044222703335: krp=54 rules=9 portrait_assets=7 synthetic=8/8

python3 scripts/run_518k_validation.py --mode sample --limit 2
v30.518k.sample.20260610044238766995: eligible mode=sample cases=2 shards=0
```

Current M3 growth track:

1. `m3.real_case_calibration_tags`: G1 complete; canonical/synthetic case tags now map to K/R/P domains, rule states, dynamic paths, and portrait density.
2. `m3.domain_rule_depth_expansion`: G2 complete; weak depth candidates were expanded with source-governed K/R/P and rule specs without fixed outcome verdicts.
3. `m3.training_synthetic_distribution`: G1 complete; G3 should convert G1/G2 observations into training candidate review evidence before any pointer promotion.
4. `m3.source_extraction_queue`: G1 complete; source registry queue tags guide classic-source and V20-reference extraction without runtime V20 import.
5. `m3.518k_distribution_summary`: G1 complete; 518K sample distribution can be attached to M3 tags, while full 518K remains explicit-only.

Completed 2026-05-24:

- Batch A: K/R/P units now expose `source_family_ids` and `reference_asset_ids`; V20 concepts entered through V30 K/R/P units rather than V20 runtime imports.
- Batch B: Feature compiler now emits M3 source-backed evidence for 月令, 旺相休囚死, 调候, 病药, 通关/制化, 十神角色集, and地支仲裁; rule evidence now has gates for month-command pattern, 调候, 病药, domain outcome boundaries, and branch arbitration.
- Batch C: Dynamic structure and portrait-facing K/R/P coverage now consume the expanded source-backed units and V20 reference metadata.
- Batch D: Added `m3_core_spine`, `knowledge_rule_portrait`, and `structure_dynamic_v2` synthetic tiers plus `v30.training_signal.m3_core_spine_coverage`.
- Batch E: Targeted M3 final gate passed.

## Work Packages

### M3.1 Source Registry And Extraction Contract

Status: completed baseline

Deliverables:

- [x] `v30/knowledge/source_registry.py`.
- [x] Source family model with tier, domains, rule families, extraction targets, boundaries, validation requirements, and URLs.
- [x] Tests requiring canonical source families for Zi Ping, San Ming Tong Hui, Yuan Hai Zi Ping, Di Tian Sui, Qiong Tong Bao Jian, and Shen Feng Tong Kao.
- [x] Documentation rule: no K/R/P runtime promotion without source family or explicit synthetic-only status.

Validation:

- `python3 -m compileall -q v30`: passed.
- `pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py`: 8 passed.
- `pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_v20_reference_registry.py tests/unit/test_knowledge_library.py tests/unit/test_knowledge_rule_portrait_seed.py`: 10 passed.

Completed 2026-05-24:

- Established the first M3 knowledge source registry.
- Registered six source families across pattern/month-command, system catalog, pattern catalog, dynamic mechanism, climate review, and disease-medicine review.
- Kept source registry as extraction governance, not a runtime verdict source.
- Added V20 reference registry and made V20 assets reference-only under `no_v20_runtime_import`.

### M3.2 Knowledge Library Coverage

Status: completed baseline

Deliverables:

- [x] Expand K/R/P unit metadata with source family ids.
- [x] Use `v30/knowledge/v20_reference_registry.py` as a migration queue for V20 knowledge assets.
- [x] Cover core domains: chart, element, ten-god, branch relation, time context, strength, structure pattern, useful-god, wealth, career, relationship, health, timing.
- [x] Add explicit source-backed units for month-command, 旺相休囚死, ten-god families, 格局 candidate formation, 调候, 病药, 通关, 制化, and branch conflict/alignment.
- [x] Migrate V20 concepts only through V30 contracts; no V20 runtime imports.

Validation:

- K/R/P unit count and domain coverage tests.
- Source-family coverage tests.
- Synthetic `knowledge_rule_portrait` tier.

### M3.3 Rule Library And Counter-evidence

Status: completed baseline

Deliverables:

- [x] Rule specs for missing time, useful-god candidate-only, hidden-factor feedback-only, branch dynamic review, climate/regulation review, 病药 review, fixed 格局 blocking, and domain outcome blocking.
- [x] Rule state contract: support, requires_review, blocked, countered.
- [x] Counter-evidence must preserve original rule trace.

Validation:

- Rule evidence unit tests.
- Synthetic counter-evidence cases.
- Training signal boundary assertions.

### M3.4 Feature Evidence Compiler

Status: completed baseline

Deliverables:

- [x] Feature atoms for immutable chart facts, ten-god visible/hidden family, five-element distribution, 月令/seasonal command, 旺相休囚死, branch conflict/alignment, time layer presence/missing, climate/regulation markers, useful-god candidates, and domain path candidates.
- [x] All features must expose supports, weakens, confidence, boundary, and source.

Validation:

- Feature compiler coverage tests.
- Synthetic feature-domain observations.

### M3.5 Portrait Projection

Status: completed baseline

Deliverables:

- [x] Portrait dimensions for ten-god family, element balance, branch relation, hidden stem, wealth/career/relationship/health/timing.
- [x] Role-aware projection contract:
  - Customer: concise explanation only.
  - Practitioner/admin: evidence, rule state, source family, and boundary.
- [x] Portraits cannot override structure state or chart facts.

Validation:

- Portrait projection tests.
- Role projection leak checks.

### M3.6 Dynamic Structure Graph

Status: completed baseline

Deliverables:

- [x] Graph nodes from feature evidence and K/R/P units.
- [x] Edges for generation, control, same-family, pressure, support, branch conflict/alignment, rule blockage, counter-evidence.
- [x] Paths for strength review, 格局 candidate, 通关/制化, 病药, 调候, domain review, and useful-god candidate path.
- [x] Score reasons must expose node score, edge score, policy weight, blockage penalty, counter-evidence penalty, conflict penalty, and suppression.

Validation:

- Dynamic graph unit tests.
- Synthetic `structure_dynamic_v2` tier.
- M5 ranked decisions must consume graph path scores.

### M3.7 Synthetic Validation And Training Signals

Status: completed baseline

Deliverables:

- [x] Dedicated `m3_core_spine` synthetic tier.
- [x] Cases: positive support, negative counter, ambiguous/disputed, missing time, climate/regulation, 病药/blockage, 通关/制化, domain outcome blocked, hidden factor feedback clue.
- [x] Training signals for K/R/P source coverage, rule counter-evidence coverage, feature-domain coverage, dynamic path coverage, domain boundary leakage, and candidate-decision evidence coverage.

Validation:

- `python3 scripts/run_synthetic_validation.py --tier m3_core_spine`
- `pytest -q tests/unit/test_knowledge_library.py tests/unit/test_evidence_compiler.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_training_signals.py`

### M3.8 Background Training / Validation Queue

Status: completed admin baseline

Purpose:

- Let M3 iteration run the expensive-but-routine checks without blocking the browser request.
- Keep progress visible in Admin -> Training.
- Keep full 518K explicit-only.

Admin endpoints:

```text
POST /api/v30/admin/training/m3-background/run
GET  /api/v30/admin/training/m3-background/status?job_id=<id>
```

Default background sequence:

```text
python3 scripts/run_m3_core_spine_snapshot.py --sample-limit 8
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
python3 scripts/run_synthetic_validation.py --tier training_pipeline
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Optional long steps exposed by checkbox:

```text
python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
```

Boundary:

- No pointer promotion.
- No deterministic chart-fact mutation.
- No default full 518K run.
- Job progress and summaries are persisted under `.runtime/training/m3_background_jobs/`.
- API starts an independent background process (`scripts/run_m3_background_training_job.py`) so the Admin page can poll progress without holding the request thread.

Latest M3 training / validation run, 2026-06-10:

```text
M3 snapshot:
v30.m3.snapshot.20260610052254738537
krp=54 rules=9 portrait_assets=7 synthetic=8/8
db: postgres searchable=True rows={'knowledge_units': 54, 'rule_specs': 9, 'portrait_assets': 7, 'validation_snapshots': 1}

M3 synthetic:
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

Training synthetic:
python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

518K sample:
python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260610061011596029: eligible mode=sample cases=8 shards=0
artifact_record_id: v30.518k.artifact.v30.518k.sample.20260610061011596029
artifact_search_backend: json_fallback

518K shard:
python3 scripts/run_518k_validation.py --mode shard --shard-id 7 --limit 16
v30.518k.shard.20260610061046503507: eligible mode=shard cases=16 shards=7
artifact_record_id: v30.518k.artifact.v30.518k.shard.20260610061046503507
artifact_search_backend: json_fallback

518K readiness:
python3 scripts/run_518k_readiness_matrix.py --sample-limit 8 --shard-id 7 --shard-limit 16
v30.518k_readiness_matrix.v1: passed (7/7) bt9_518k_readiness_matrix_ready
```

Background worker fix 2026-06-10:

- Admin background task now runs through an independent `tmux` worker session and writes progress under `.runtime/training/m3_background_jobs/`.
- Validation commands run in a nonblocking artifact/json fallback environment; Postgres remains the runtime DB and M3 table status source.
- Latest verified job:

```text
m3-job-20260610071346133535-1fe685
status=completed progress=100 completed_steps=6/6
m3_snapshot: synthetic=8/8
m3_synthetic: 8/8
training_pipeline: 91/91
518k_sample: cases=8
518k_shard: shard=7 cases=16
518k_readiness_matrix: 7/7
```

### M3.9 Source-Governed Calibration Tags

Status: completed G1 2026-06-10

Purpose:

- Convert post-seal M3 growth into observable calibration tags instead of ad hoc expansion.
- Map K/R/P domains, rule states, dynamic paths, portrait density, synthetic/training distribution, source queue, and 518K sample distribution.
- Keep all tags as calibration evidence only.

Deliverables:

- [x] `v30.validation.m3_source_governed_calibration`.
- [x] `v30.m3_source_governed_calibration.v1` embedded under M3 snapshots as `source_governed_calibration`.
- [x] `scripts/run_m3_source_governed_calibration.py`.
- [x] Five tag groups:
  - `real_case_calibration_tags`
  - `domain_rule_depth_expansion`
  - `training_synthetic_distribution`
  - `source_extraction_queue`
  - `distribution_518k_summary`
- [x] Boundary contract: no chart-fact mutation, no pointer promotion, no fixed Bazi verdict, no default full 518K.

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_source_governed_calibration.py scripts/run_m3_core_spine_snapshot.py
passed

pytest -q tests/unit/test_m3_core_spine_snapshot.py
4 passed

python3 scripts/run_m3_source_governed_calibration.py --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=False

python3 scripts/run_m3_core_spine_snapshot.py --no-db --sample-limit 8
v30.m3.snapshot.20260610073045434170: krp=54 rules=9 portrait_assets=7 synthetic=8/8

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_518k_validation.py --mode sample --limit 8
v30.518k.sample.20260610073103365458: eligible mode=sample cases=8 shards=0

python3 scripts/run_m3_source_governed_calibration.py --include-518k-sample --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=True
```

Next:

```text
M3-G2 Domain Rule Depth Expansion Batch
```

Use G1 growth-candidate domain tags to add source-governed domain subfamily K/R/P and counter-evidence paths for wealth, career, relationship, health, structure dynamic, structure pattern, and useful-god. Do not add fixed outcome claims.

### M3.10 Domain Rule Depth Expansion Batch

Status: completed G2 2026-06-10

Purpose:

- Close G1 `domain_rule_depth_expansion` growth candidates by adding source-governed K/R/P and rule specs.
- Strengthen the foundation that supports wealth/career/relationship/health and M4/M5/M6 without turning domain paths into life-outcome verdicts.

Deliverables:

- [x] K/R/P inventory increased from 54 to 72.
- [x] Rule specs increased from 9 to 20.
- [x] Added chart fact boundary and calculation-basis rules.
- [x] Added element balance and seasonal counterforce rules.
- [x] Added foundation M1/M2/M3 chain and training read-only units.
- [x] Added romance/private-fact boundary units.
- [x] Added domain-rule subfamily, outcome-language, and cross-domain bridge units.
- [x] Added rule-counterevidence trace and silent-policy-override blocks.
- [x] Added structure-pattern success/failure/rescue review.
- [x] Added explicit time-layer requirement.
- [x] G1 depth tags now report `growth_count=0` for current G2 scope.

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_source_governed_calibration.py
passed

pytest -q tests/unit/test_knowledge_library.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
10 passed

python3 scripts/run_m3_source_governed_calibration.py --include-518k-sample --sample-limit 8
v30.m3_source_governed_calibration.v1: ready groups=5 real_case_tags=8 domain_tags=17 source_queue=6 518k=True

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_m3_core_spine_snapshot.py --no-db --sample-limit 8
v30.m3.snapshot.20260610095515875803: krp=72 rules=20 portrait_assets=7 synthetic=8/8
```

## M3.11 G3 Training / Synthetic Distribution Candidate Review

Status: Complete

G3 converts G1/G2 calibration tags, training-pipeline observations, and 518K sample distribution into bounded M3 training candidate review evidence. It creates review candidates only; it does not promote pointers, mutate chart facts, or create fixed Bazi verdicts.

Added:

- `v30.m3_training_candidate_review.v1`
- CLI: `python3 scripts/run_m3_training_candidate_review.py --sample-limit 8`
- Candidate types:
  - `source_coverage_weight_candidate`
  - `rule_path_priority_candidate`
  - `domain_rule_depth_candidate`
  - `counterevidence_trace_candidate`
  - `dynamic_path_priority_candidate`
  - `question_strategy_candidate`
  - `training_distribution_candidate`
  - `distribution_518k_candidate`
- Boundaries:
  - `auto_apply_allowed=false`
  - `policy_pointer_promotion_allowed=false`
  - `chart_fact_mutation_allowed=false`
  - `fixed_bazi_verdict_allowed=false`
  - `requires_operator_review=true`

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_training_candidate_review.py
passed

pytest -q tests/unit/test_m3_training_candidate_review.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_training_signals.py::test_extract_training_signals_from_synthetic_all
8 passed

python3 scripts/run_m3_training_candidate_review.py --sample-limit 8
v30.m3_training_candidate_review.v1: passed (7/7) m3_g3_training_candidate_review_ready candidates=8

python3 scripts/run_synthetic_validation.py --tier training_pipeline
v30.synthetic.training_pipeline: passed (91/91)

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

## M3.12 G4 Source Extraction Queue Operationalization

Status: Complete

G4 turns G1 source extraction queue tags into operational backlog artifacts. Rows are source-family scoped, linked to V30 K/R/P units, rule specs, portrait assets, extraction targets, validation requirements, priority, queue state, and review status. The backlog is review-only support data and cannot import V20 runtime code, promote policy pointers, mutate chart facts, or create fixed Bazi verdicts.

Added:

- `v30.m3_source_extraction_backlog.v1`
- CLI: `python3 scripts/run_m3_source_extraction_backlog.py`
- Optional Postgres write helper: `write_m3_source_backlog_to_postgres`
- Dedicated table: `v30_m3_source_backlog`

Validation 2026-06-10:

```text
python3 -m compileall -q v30 scripts/run_m3_source_extraction_backlog.py
passed

pytest -q tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_m3_core_spine_snapshot.py tests/unit/test_storage_adapters.py
12 passed

python3 scripts/run_m3_source_extraction_backlog.py
v30.m3_source_extraction_backlog.v1: passed (6/6) m3_g4_source_extraction_backlog_ready rows=6

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

## M3.13 G5 Backlog Persistence And Admin Review Surface

Status: Complete

G5 exposes G4 backlog rows through query/filter surfaces for admin/training review while keeping runtime decisions read-only. The surface uses Postgres `v30_m3_source_backlog` when available and falls back to a generated current G4 backlog artifact when DB rows are absent.

Added:

- `v30.m3_source_backlog_review_surface.v1`
- CLI: `python3 scripts/run_m3_source_backlog_review_surface.py`
- Admin endpoint: `GET /api/v30/admin/m3/source-backlog`
- Filters: `source_family_id`, `priority`, `queue_state`, `review_status`, `target_domain`, `limit`
- Storage query helper: `query_m3_source_backlog_from_postgres`

Validation 2026-06-11:

```text
python3 -m compileall -q v30 scripts/run_m3_source_backlog_review_surface.py
passed

pytest -q tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_source_extraction_backlog.py tests/unit/test_storage_adapters.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
13 passed

python3 scripts/run_m3_source_backlog_review_surface.py
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=6 backend=json_fallback_generated_backlog

python3 scripts/run_m3_source_backlog_review_surface.py --target-domain useful_god --limit 3
v30.m3_source_backlog_review_surface.v1: passed (5/5) m3_g5_backlog_review_surface_ready rows=3 backend=json_fallback_generated_backlog

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

## M3.14 G6 Source Backlog Closeout And M3 Seal Review

Status: Complete

G6 reviews G1-G5 artifacts together and closes the M3 source backlog flow. It links G3 training candidate review, G5 backlog review surface, and `m3_core_spine` synthetic validation into one read-only closeout artifact. M3 returns to steady-state calibration; future source evidence should enter through G4/G5/G3 instead of reopening runtime calculation.

Added:

- `v30.m3_source_backlog_closeout.v1`
- CLI: `python3 scripts/run_m3_source_backlog_closeout.py --sample-limit 8`
- Admin endpoint: `GET /api/v30/admin/m3/source-backlog-closeout`
- Next recommendation: `M5 Evidence Consumption Hardening`

Validation 2026-06-11:

```text
python3 -m compileall -q v30 scripts/run_m3_source_backlog_closeout.py
passed

pytest -q tests/unit/test_m3_source_backlog_closeout.py tests/unit/test_m3_source_backlog_review_surface.py tests/unit/test_m3_training_candidate_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
12 passed

python3 scripts/run_m3_source_backlog_closeout.py --sample-limit 8
v30.m3_source_backlog_closeout.v1: passed (5/5) m3_g6_source_backlog_closeout_ready candidates=8 backlog_rows=6

python3 scripts/run_synthetic_validation.py --tier m3_core_spine
v30.synthetic.m3_core_spine: passed (8/8)
```

Next:

```text
M5 Evidence Consumption Hardening
```

Use sealed M3 evidence in M5 strength, structure-pattern, and useful-god ranked decision hardening while keeping M5 candidate-bound.

## M3 Final Gate

Run only when all M3 work packages are complete:

```text
python3 -m compileall -q v30
python3 scripts/run_synthetic_validation.py --tier m3_core_spine
python3 scripts/run_synthetic_validation.py --tier knowledge_rule_portrait
python3 scripts/run_synthetic_validation.py --tier structure_dynamic_v2
pytest -q tests/unit/test_knowledge_source_registry.py tests/unit/test_knowledge_library.py tests/unit/test_evidence_compiler.py tests/unit/test_structure_mainline_spine.py tests/unit/test_structure_dynamic_graph.py tests/unit/test_training_signals.py
```

Major gate after M3 promotion:

```text
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode sample --limit 8
pytest -q
```

## Current Next Step

M3 G1-G6 is closed for the current source-backlog flow. Continue with `M5 Evidence Consumption Hardening`, using the sealed M3 evidence spine without turning M5 into fixed verdicts or chart-fact mutation.
