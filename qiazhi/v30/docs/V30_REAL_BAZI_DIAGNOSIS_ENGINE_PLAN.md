# V30 Real Bazi Diagnosis Engine Mainline

Updated: 2026-06-12

## Purpose

RBD-S1 is the next core mainline because the current runtime has internal evidence but the customer-facing diagnosis is still too generic.

Current audit showed:

```text
FeatureEvidence: 33
KRP units: 72
Dynamic paths: 12
Wealth paths: 7
Career paths: 12
Relationship paths: 10
Health paths: 12
Useful-god paths: 12
```

But customer output still says things like:

```text
事业线索已进入当前主线，可以先看职责压力、协作关系和阶段性机会。
```

This is not enough for Bazi measurement. The gap is not only UI or LLM wording. The missing layer is a real diagnosis engine that turns chart facts, rules, portraits, features, dynamic paths, ranked decisions, luck/flow context, and user role into traceable Bazi judgments.

## Product Principle

The system should be simple in UI and strong in modules:

```text
simple surface
strong diagnosis engine
traceable evidence
role-aware expression
trainable feedback loop
```

RBD must produce bounded diagnosis, not vague disclaimers and not absolute fortune claims.

Allowed:

```text
此局事业不宜单看财，财星容易牵动官杀压力，真正可用处在印星承接。
所以事业上更像“因资源、资质、规则、平台而成”，不是纯销售型或投机型财路。
```

Not allowed:

```text
你一定发财。
你三年内升官。
当前只作为候选路径，不作判断。
```

## Mainline Position

RBD is not a temporary presentation patch. It is a new diagnosis orchestration layer between module reasoning and expression.

```text
M1/M2 Chart Facts
-> M3 Knowledge / Rules / Portrait / Features / Dynamic Structure
-> M4 Ten-god Energy and Model Signals
-> M5 Ranked Strength / Structure / Useful-god Decisions
-> RBD Diagnosis Router and Matcher
-> RBD Diagnosis Graph
-> RBD Diagnosis Claims
-> M6 Practical Reading
-> Central Brain Route Selection
-> LLM / Expression / UI
```

RBD does not replace M3-M6. It consumes them and makes their evidence usable for actual Bazi reading.

## Architecture

### 1. Diagnosis Context

Input:

- `ChartContext`
- `FeatureEvidence[]`
- `RuleEvidence[]`
- `KnowledgeRulePortraitSignal[]`
- `StructureState`
- `TenGodEnergyModel`
- `model_signal_summary`
- `RankedDecision[]`
- `PracticalReadingContext`
- `luck_cycle_context`
- `flow_year/month_context`
- `InteractionState`
- `role_key`

Output:

```text
DiagnosisContext
```

Required fields:

- immutable chart facts
- active luck/flow layer
- strongest evidence families
- weakest/counter evidence families
- active domains
- current question focus
- role density
- blocked claim types

Boundary:

- never mutates pillars, ten gods, luck cycles, flow year/month, or deterministic facts.

### 2. Rule Matcher

Purpose:

Match actual chart evidence to Bazi rule units.

Inputs:

- M3 KRP units
- rule specs
- feature evidence supports/weakens
- branch relations
- ten-god families
- element distribution
- time activation

Output:

```text
MatchedRule[]
```

Each matched rule must include:

- `rule_id`
- `source_family_ids`
- `match_strength`
- `required_context_hit[]`
- `counter_context_hit[]`
- `missing_context[]`
- `domain_targets[]`
- `claim_templates[]`
- `blocked_claims[]`
- `evidence_ids[]`

Algorithm:

```text
match_score =
  required_context_score
  + evidence_confidence_score
  + time_activation_score
  + structure_path_support_score
  + model_signal_support_score
  - counter_evidence_penalty
  - missing_context_penalty
```

Hard blockers:

- rule requests fixed event prediction without time layer
- rule requests chart fact mutation
- rule conflicts with stronger counter evidence
- rule requires hidden factor confirmation but user has not supplied it

### 3. Portrait Matcher

Purpose:

Turn KRP portrait units and macro dimension signals into real Bazi portrait dimensions.

Output:

```text
DiagnosisPortrait[]
```

Required portrait dimensions:

- decision mode
- pressure mode
- resource mode
- wealth behavior
- career bearing
- relationship interaction
- health boundary
- timing sensitivity

Each portrait item must include:

- `portrait_id`
- `dimension`
- `statement`
- `evidence_ids[]`
- `path_ids[]`
- `confidence_band`
- `counter_notes[]`

Portrait examples:

```text
财官印路径强时，画像不是“爱钱”，而是资源、责任、规则和平台之间互相牵动。
食伤生财路径强时，画像偏向靠输出、技术、表达、方案或流量产生财源。
比劫夺财线强时，画像偏向资源竞争、合伙分账、同辈消耗或现金流被分散。
```

### 4. Feature and Pattern Extractor

Purpose:

Surface actual Bazi features before diagnosis claims.

Output:

```text
DiagnosisFeature[]
```

Feature families:

- day-master strength tendency
- season/month command
- ten-god visible/hidden distribution
- root/support condition
- element excess/thinness
- branch conflict/alignment
- structure pattern candidate
- useful-god candidate family
- time activation marker
- hidden-factor hypothesis

Each feature should become readable:

```text
月令落在丑，原局寒湿与土水气重，不能只按金日主强弱直断，需要看火木是否形成调候和流通。
```

### 5. Path Engine

Purpose:

Convert dynamic graph paths into diagnosis paths.

Input:

- `StructureState.graph_nodes`
- `StructureState.graph_edges`
- path scores
- mechanism paths
- domain path counts

Output:

```text
DiagnosisPath[]
```

Path families:

- 财官印
- 官印
- 食伤生财
- 食伤制杀转印
- 比劫争财
- 财生杀压身
- 印星通关
- 调候路径
- 病药路径
- 冲合刑害触发路径

Path output must include:

- `path_id`
- `family_chain`
- `mechanism`
- `domain_targets`
- `diagnosis_statement`
- `risk_statement`
- `timing_trigger`
- `evidence_ids[]`
- `counter_evidence_ids[]`

Example:

```text
财星不是单独成财，而是先牵动官杀压力，再由印星承接回到日主。
这类路径更像“资源转责任、责任转资质或位置”，财路往往依附平台、证照、规则、组织授权。
```

### 6. Diagnosis Claim Generator

Purpose:

Produce bounded but concrete Bazi diagnosis claims.

Output:

```text
DiagnosisClaim[]
```

Claim levels:

- `fact`: deterministic chart fact
- `feature`: structural feature
- `path`: dynamic path statement
- `portrait`: derived portrait
- `domain`: wealth/career/relationship/health diagnosis
- `timing`: luck/flow activation
- `question`: follow-up calibration need

Every claim must include:

- `claim_id`
- `claim_text`
- `claim_level`
- `domain`
- `confidence_band`
- `evidence_ids[]`
- `rule_ids[]`
- `path_ids[]`
- `blocked_overclaim[]`
- `needs_user_calibration`

Claim rules:

- Concrete claim is required when evidence is strong.
- Boundary language is allowed, but cannot replace diagnosis.
- No unsupported event certainty.
- No LLM-only claim.

### 7. Diagnosis Graph

Purpose:

The intelligent brain should route through a graph, not string templates.

Graph nodes:

- chart facts
- features
- matched rules
- portrait dimensions
- dynamic paths
- ranked decisions
- domain claims
- timing activations
- user feedback

Graph edges:

- supports
- weakens
- activates
- blocks
- requires
- explains
- asks_followup

Selection algorithm:

```text
claim_rank =
  evidence_strength
  + rule_match_strength
  + path_centrality
  + domain_relevance
  + time_activation
  + role_relevance
  - counter_evidence
  - missing_context
  - overclaim_risk
```

Centrality inputs:

- path score
- number of connected domains
- number of matched rules
- relation to selected user question
- relation to luck/flow layer

### 8. Central Brain Diagnosis Router

The central brain must own diagnosis routing, not diagnosis facts.

New brain responsibility:

```text
DiagnosisRouter
```

Responsibilities:

- choose reading mode:
  - overview
  - career
  - wealth
  - relationship
  - health
  - timing
  - hidden-factor calibration
  - practitioner diagnostic
- choose evidence depth by role
- route matched rules to path engine
- route path engine to claims
- route claims to question/LLM/expression
- decide when follow-up is needed before claim expansion

It must not:

- calculate chart facts
- invent rules
- mutate M3 knowledge
- write policy pointers
- turn hidden factors into deterministic facts

### 9. LLM Role

LLM should not do diagnosis from scratch.

LLM input should be:

```text
DiagnosisContext
DiagnosisClaim[]
DiagnosisPath[]
DiagnosisPortrait[]
RolePromptProfile
```

LLM task:

- render
- organize
- explain
- ask follow-up
- adapt tone by role/language/client

LLM forbidden:

- create new chart facts
- create new rule matches
- invent event years
- override diagnosis confidence
- ignore blocked claims

### 10. Database Layer

RBD outputs should be persisted to Postgres.

Tables or JSON artifacts:

- `v30_diagnosis_runs`
- `v30_diagnosis_rule_matches`
- `v30_diagnosis_paths`
- `v30_diagnosis_portraits`
- `v30_diagnosis_claims`
- `v30_diagnosis_feedback`

Minimum persisted fields:

- reading id
- chart context id
- policy versions
- matched rules
- path ids
- claim ids
- confidence bands
- role key
- locale
- source evidence ids
- feedback status

Redis:

- cache latest diagnosis run per session
- cache role-specific projection
- never store authoritative facts only in Redis

## Module Ownership

| Module | RBD usage | Ownership boundary |
|---|---|---|
| M1/M2 | chart facts, pillars, luck/flow | immutable facts |
| M3 | KRP, rules, portraits, features, dynamic knowledge | source of domain logic |
| M4 | ten-god energy, model-signal summary | scoring signal |
| M5 | ranked strength/structure/useful-god decisions | candidate decision input |
| M6 | practical reading projection | consumes RBD claims |
| M7 | real-case calibration | validates diagnosis quality |
| M8 | projection/API | exposes diagnosis safely |
| IQ | asks follow-up from missing/counter evidence | interaction only |
| LLM | expression only | no diagnosis generation |
| BT | training/synthetic/518K | validates and tunes policies |
| Central Brain | diagnosis routing | coordinator, not fact engine |

## RBD-S1 Implementation Plan

### RBD-S1.1 Diagnosis Contracts

Add contracts:

- `DiagnosisContext`
- `MatchedRule`
- `DiagnosisFeature`
- `DiagnosisPath`
- `DiagnosisPortrait`
- `DiagnosisClaim`
- `DiagnosisGraph`
- `DiagnosisRouteDecision`

Validation:

```text
pytest -q tests/unit/test_real_bazi_diagnosis_contracts.py
```

### RBD-S1.2 Rule Matcher

Add:

- `v30/diagnosis/rule_matcher.py`

Consumes:

- `FeatureEvidence`
- M3 KRP units
- rule policy
- structure path scores
- model signal summary

Validation:

```text
pytest -q tests/unit/test_real_bazi_rule_matcher.py
python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.rule_matcher.v1`
- `match_real_bazi_rules()`
- `summarize_rule_matches()`
- `tests/unit/test_real_bazi_rule_matcher.py`

Latest validation:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
9 passed

runtime sample:
v30.real_bazi_diagnosis.rule_matcher.v1: matches=49 claim_ready=45 calibration=5 domains={'career': 5, 'health': 6, 'hidden_factor': 1, 'overview': 7, 'relationship': 9, 'structure': 13, 'timing': 2, 'useful_god': 6, 'wealth': 6}
```

### RBD-S1.3 Path Translator

Add:

- `v30/diagnosis/path_engine.py`

Converts dynamic paths into readable Bazi mechanisms.

Validation:

```text
pytest -q tests/unit/test_real_bazi_path_engine.py
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.path_engine.v1`
- `translate_dynamic_paths()`
- `summarize_diagnosis_paths()`
- `tests/unit/test_real_bazi_path_engine.py`

Latest validation:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
13 passed

runtime sample:
v30.real_bazi_diagnosis.path_engine.v1: paths=10 high=7 domains={'career': 8, 'health': 4, 'relationship': 10, 'structure': 10, 'useful_god': 8, 'wealth': 5} mechanisms={'官印相生': 3, '财官印制化': 3, '食伤制官杀': 2, '食伤生财': 2}
top_statement=官杀 → 印星形成官印相生路径，压力、规则或职责需要通过印星转成资质、凭证、学习或平台承接。
```

### RBD-S1.4 Portrait and Feature Extractor

Add:

- `v30/diagnosis/portrait_engine.py`
- `v30/diagnosis/feature_engine.py`

Validation:

```text
pytest -q tests/unit/test_real_bazi_portrait_feature_engine.py
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.feature_engine.v1`
- `extract_diagnosis_features()`
- `summarize_diagnosis_features()`
- `v30.real_bazi_diagnosis.portrait_engine.v1`
- `extract_diagnosis_portraits()`
- `summarize_diagnosis_portraits()`
- `tests/unit/test_real_bazi_portrait_feature_engine.py`

Latest validation:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
17 passed

runtime sample:
v30.real_bazi_diagnosis.feature_engine.v1: feature_count=33 domains={'hidden_factor': 1, 'overview': 8, 'structure': 17, 'timing': 3, 'useful_god': 4}
v30.real_bazi_diagnosis.portrait_engine.v1: portrait_count=65 domains={'career': 10, 'health': 5, 'hidden_factor': 1, 'overview': 7, 'relationship': 11, 'structure': 13, 'timing': 2, 'useful_god': 8, 'wealth': 8}
top_feature=庚已经作为不可改写的排盘事实，后续断语只能引用它，不能重新生成四柱或日主。
top_portrait=此命局画像必须先锁定四柱、日主和确定性事实，后续画像只做解释投影，不改排盘来源。
```

### RBD-S1.5 Claim Generator

Add:

- `v30/diagnosis/claim_generator.py`

Rules:

- strong evidence must produce concrete claim
- missing/counter evidence must shape claim, not erase it
- every claim must be traceable

Validation:

```text
pytest -q tests/unit/test_real_bazi_claim_generator.py
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.claim_generator.v1`
- `generate_diagnosis_claims()`
- `summarize_diagnosis_claims()`
- `tests/unit/test_real_bazi_claim_generator.py`

Latest validation:

```text
python3 -m compileall -q v30/diagnosis
passed

pytest -q tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py
21 passed

runtime sample:
v30.real_bazi_diagnosis.claim_generator.v1: claim_count=71 domains={'career': 7, 'health': 3, 'hidden_factor': 4, 'overview': 1, 'relationship': 7, 'structure': 28, 'timing': 3, 'useful_god': 10, 'wealth': 8}
levels={'domain': 7, 'fact': 1, 'feature': 20, 'path': 4, 'portrait': 37, 'question': 1, 'timing': 1}
wealth=财运主线不是单点求财，而是沿财官印制化展开；财星需要被输出、官杀责任或印星资源承接，适合看资源转化、方案输出、平台授权和分配结构。
career=事业主线落在官印相生；此局更重视压力如何转成资质、规则、平台或可交付能力，不能只按职位升降下断。
timing=当前时运层为戊寅、庚子，时运只作为触发层使用：它会放大官印相生这类结构路径，但不能单独生成具体年份事件。
```

### RBD-S1.6 Diagnosis Graph and Router

Add:

- `v30/diagnosis/graph.py`
- `v30/brain/diagnosis_router.py`

Validation:

```text
pytest -q tests/unit/test_central_brain_diagnosis_router.py
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.graph.v1`
- `build_diagnosis_graph()`
- `summarize_diagnosis_graph()`
- `v30.real_bazi_diagnosis.router.v1`
- `route_real_bazi_diagnosis()`
- `summarize_diagnosis_route()`
- `tests/unit/test_central_brain_diagnosis_router.py`

Latest validation:

```text
python3 -m compileall -q v30/diagnosis v30/brain
passed

pytest -q tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py tests/unit/test_real_bazi_portrait_feature_engine.py tests/unit/test_real_bazi_path_engine.py tests/unit/test_real_bazi_rule_matcher.py tests/unit/test_real_bazi_diagnosis_contracts.py tests/unit/test_central_brain.py
29 passed

runtime sample:
v30.real_bazi_diagnosis.graph.v1: node_count=261 edge_count=1426 node_counts={'chart_fact': 1, 'claim': 71, 'feature': 65, 'matched_rule': 49, 'path': 10, 'portrait': 65}
edge_counts={'activates': 5, 'asks_followup': 23, 'blocks': 90, 'explains': 690, 'supports': 618}
v30.real_bazi_diagnosis.router.v1: mode=wealth selected_domain=wealth selected_claim_count=5 selected_path_count=6 selected_portrait_count=6 followup_required=True density=standard
```

### RBD-S1.7 Runtime Integration

Runtime adds:

```text
question_plan.policy_effect.real_bazi_diagnosis
```

M6 practical reading consumes RBD:

```text
domain_readings[].diagnosis_claims
domain_readings[].diagnosis_paths
domain_readings[].portrait_dimensions
```

UI/API consumes:

```text
reading_surface.diagnosis_overview
reading_surface.domain_cards[].diagnosis_summary
reading_surface.domain_cards[].core_claim_quality
reading_surface.structure_dynamics.top_paths[].diagnosis_statement
```

Validation:

```text
pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_presentation_projection.py
```

Status: Complete 2026-06-12

Implemented:

- Runtime attaches `question_plan.policy_effect.real_bazi_diagnosis`.
- M6 practical domain readings consume `diagnosis_summary`, `diagnosis_claims`, `diagnosis_paths`, and `portrait_dimensions`.
- Customer presentation projects `reading_surface.diagnosis_overview`, `domain_cards[].diagnosis_summary`, `domain_cards[].core_claim_quality`, and RBD path statements.
- Admin diagnostics can inspect full RBD summaries and selected routes.
- `tests/unit/test_real_bazi_runtime_integration.py`

Latest validation:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_presentation_projection.py tests/unit/test_practical_reading_context.py tests/unit/test_central_brain_diagnosis_router.py tests/unit/test_real_bazi_claim_generator.py
19 passed

runtime sample:
v30.real_bazi_diagnosis.runtime_integration.v1: claims=71 graph_nodes=261 graph_edges=1426
career=事业主线落在官印相生；此局更重视压力如何转成资质、规则、平台或可交付能力，不能只按职位升降下断。
wealth=财运主线不是单点求财，而是沿财官印制化展开；财星需要被输出、官杀责任或印星资源承接，适合看资源转化、方案输出、平台授权和分配结构。
overview=命局结构不能只按旺衰标签概括；当前核心结构路径是官印相生，需要把月令、十神、地支关系和制化承接合并判断。
```

### RBD-S1.10-CQ Core Claim Quality Projection

Status: Complete 2026-06-13

Implemented:

- Added `v30.core_bazi_claim_quality.v1` to RBD-backed practical domain readings.
- Customer projection exposes only quality flags and counts, not raw rule traces.
- UI-R1 acceptance now checks traceable claims, no generic language hits, no fixed-event prediction, and no chart-fact mutation.
- SYN-CAL1 archetype review now checks `m6_core_claim_quality_ready`.
- Customer structure dynamic paths expose concrete `diagnosis_statement` text from ten-god chain labels.

Validation:

```text
pytest -q tests/unit/test_real_bazi_product_reading_acceptance.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_ui_core_reading_product_acceptance.py tests/unit/test_synthetic_archetype_rule_claim_calibration.py
11 passed

python3 scripts/run_real_bazi_product_reading_acceptance.py
v30.real_bazi_product_reading_acceptance.v1: passed (6/6) rbd_s110_product_reading_accepted

python3 scripts/run_synthetic_archetype_rule_claim_calibration.py
v30.synthetic_archetype_rule_claim_calibration.v1: syn_cal1_archetype_rule_claim_calibration_ready

python3 scripts/run_synthetic_validation.py --tier synthetic_archetype_rule_claim
v30.synthetic.synthetic_archetype_rule_claim: passed (4/4)
```

### RBD-S1.8 DB Persistence

Add Postgres schema/adapters for diagnosis records.

Validation:

```text
pytest -q tests/unit/test_real_bazi_diagnosis_storage.py
```

Status: Complete 2026-06-12

Implemented:

- `v30.real_bazi_diagnosis.storage.v1`
- `v30/storage/diagnosis.py`
- Postgres schema tables:
  - `v30_diagnosis_runs`
  - `v30_diagnosis_rule_matches`
  - `v30_diagnosis_paths`
  - `v30_diagnosis_portraits`
  - `v30_diagnosis_claims`
  - `v30_diagnosis_feedback`
- Runtime RBD payload now includes full `matched_rules` and `features` for replay/storage.
- JSON fallback behavior for no-DB environments.
- `tests/unit/test_real_bazi_diagnosis_storage.py`

Latest validation:

```text
python3 -m compileall -q v30
passed

pytest -q tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_storage_adapters.py
14 passed

runtime sample:
v30.real_bazi_diagnosis.storage.v1: claim_count=71 path_count=10 portrait_count=65 rule_match_count=49 backend=json_fallback searchable=False
```

### RBD-S1.9 Synthetic and 518K

Status: Complete 2026-06-12

Added synthetic tier:

```text
real_bazi_diagnosis
```

Checks:

- rule match exists
- path statement exists
- portrait statement exists
- at least one concrete diagnosis claim exists
- every claim has evidence ids
- no LLM-only claim
- no chart fact mutation
- no fixed event prediction without time layer
- customer surface has diagnosis content without raw RBD internals
- admin diagnostics can inspect full RBD payload
- RBD storage record remains replay/training support, not authoritative chart facts

518K sample readiness checks:

- diagnosis run generated
- claim count > 0
- path count > 0 when dynamic paths exist
- fallback/generic language rate below threshold
- full 518K remains explicit-only

Implemented:

- `SYNTHETIC_REAL_BAZI_DIAGNOSIS_CASES`
- `SYNTHETIC_SUITES["real_bazi_diagnosis"]`
- `v30.real_bazi_diagnosis.synthetic_quality.v1`
- `v30.real_bazi_diagnosis.518k_readiness.v1`
- `TIER_CONTRACTS["real_bazi_diagnosis"]`

Validation:

```text
python3 -m compileall -q v30/validation
passed

python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
v30.synthetic.real_bazi_diagnosis: passed (4/4)

pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_real_bazi_diagnosis_storage.py tests/unit/test_synthetic_validation.py::test_synthetic_real_bazi_diagnosis_tier_passes
10 passed
```

### RBD-S1.11-CQ Distribution Replay Claim-Quality Hardening

Status: Complete 2026-06-13

Implemented:

- RBD distribution replay now reads `domain_cards[].core_claim_quality`.
- Domain readiness requires `v30.core_bazi_claim_quality.v1`, `quality_ready=True`, traceable claims, no generic language hits, no fixed-event prediction, and no chart-fact mutation.
- Replay summary records average and minimum quality-ready domain counts.
- Lightweight real-case calibration rows and generated 518K sample rows must each keep all five product domains quality-ready.

Validation:

```text
python3 -m compileall -q v30/validation/real_bazi_distribution_replay.py
passed

pytest -q tests/unit/test_real_bazi_distribution_replay.py tests/unit/test_real_bazi_product_reading_acceptance.py
4 passed

python3 scripts/run_real_bazi_distribution_replay.py
v30.real_bazi_distribution_replay.v1: passed (6/6) rbd_s111_distribution_replay_ready
- real_case=8/8 sample_518k=8/8
```

## Acceptance Criteria

RBD-S1 is complete only when a normal reading can answer:

```text
此八字命局特点是什么？
事业怎么看？
财运怎么看？
感情关系怎么看？
当前大运流年怎么触发？
此局主要路径是什么？
此人画像是什么？
哪些结论需要反馈校准？
```

Without returning only:

```text
可以先看某领域
候选路径
不作绝对断语
需要进一步确认
```

## Mainline Validation

Routine:

```text
python3 -m compileall -q v30
pytest -q tests/unit/test_real_bazi_diagnosis_contracts.py
pytest -q tests/unit/test_real_bazi_rule_matcher.py
pytest -q tests/unit/test_real_bazi_path_engine.py
pytest -q tests/unit/test_real_bazi_claim_generator.py
python3 scripts/run_synthetic_validation.py --tier real_bazi_diagnosis
```

Node closeout:

```text
pytest -q tests/unit/test_real_bazi_runtime_integration.py tests/unit/test_presentation_projection.py
python3 scripts/run_518k_validation.py --mode sample --limit 8
```

Major explicit-only:

```text
pytest -q
python3 scripts/run_synthetic_validation.py --tier all
python3 scripts/run_518k_validation.py --mode full --confirm-full
```

## Current Decision

Current completed task:

```text
RBD-S1.13 RBD Mainline Closeout And Steady State
```

Implemented:

- RBD steady-state closeout artifact over S1.12 training/calibration queue.
- Current-scope RBD module spine recorded as usable for customer reading, practitioner review, and admin diagnostics.
- S1.12 emits five read-only training signals, including `v30.training_signal.rbd_core_claim_quality`.
- Routine cadence fixed to targeted RBD replay and synthetic tier.
- Heavy gates remain explicit-only: full pytest, synthetic all, full 518K, live LLM, and pointer promotion.
- CLI entry: `scripts/run_real_bazi_diagnosis_steady_state.py`.
- Unit coverage: `tests/unit/test_real_bazi_diagnosis_steady_state.py`.

Validation:

```text
python3 -m compileall -q v30/validation/real_bazi_diagnosis_steady_state.py scripts/run_real_bazi_diagnosis_steady_state.py v30/validation/__init__.py
passed

pytest -q tests/unit/test_real_bazi_diagnosis_steady_state.py tests/unit/test_real_bazi_training_calibration_queue.py
4 passed

python3 scripts/run_real_bazi_diagnosis_steady_state.py
v30.real_bazi_diagnosis_steady_state.v1: passed (6/6) rbd_s113_steady_state_ready
signals=5 queue_items=2 next=RBD-S1-WAIT
```

Next task:

```text
RBD-S1-WAIT RBD Steady State Await New Evidence
```

Do not start with UI polish or broad M3 expansion. RBD is now current-scope steady: serve readings through the RBD spine, run targeted replay after new real-case packs or before release, and keep calibration items read-only until explicit evidence review approves tuning.
