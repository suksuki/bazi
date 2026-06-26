# V30 Latent Bazi Attributes System Plan

Updated: 2026-06-13

## Concept

The hidden-factor concept is now defined as a latent Bazi attribute system.

This is not a UI feature and not a generic questionnaire. It is the model layer that explains why people with the same Bazi can diverge.

Base formula:

```text
base Bazi structure
+ luck/flow time field
+ latent personal attributes
= individualized energy state / stability state / path probability
```

The deterministic Bazi layer remains unchanged:

- four pillars
- hidden stems
- ten gods
- structure dynamics
- luck cycle
- flow year/month

Latent attributes do not mutate those facts. They modify how strongly the facts express for this person.

## Attribute Groups

### Global Attributes

Default value: `0.5`.

```text
luck_index
stability_index
execution_index
resource_index
risk_index
recovery_index
choice_quality_index
```

### Ten-God Modifiers

Default multiplier: `1.0`.

```text
day_master
wealth
authority
resource
output
peer
```

Allowed model range for HF-R2.1:

```text
0.7 - 1.3
```

### Domain Biases

Default value: `0.5`.

```text
career_bias
wealth_bias
relationship_bias
health_bias
migration_bias
learning_bias
family_drag
partnership_drag
```

### Stability Thresholds

Default value: `0.5`.

```text
pressure_tolerance
event_trigger_sensitivity
volatility_tolerance
```

## Runtime Contracts

### Evidence Binding Layer

```text
v30.latent_bazi_profile.v1
```

Purpose:

- Bind structured interaction feedback to the chart.
- Link state tags to domains, ten-god families, paths, claims, evidence ids, years, feedback ids, and question ids.

### Calculation Attribute Layer

```text
v30.latent_bazi_attributes.v1
```

Purpose:

- Start every person with neutral default values.
- Reverse-infer attribute deltas from chart-bound profile dimensions.
- Produce calculation-ready modifiers.

Runtime fields:

```text
policy_effect.latent_bazi_attributes
policy_effect.latent_bazi_attributes_summary
```

Admin diagnostics expose both fields.

Current temporary UI decision:

- The six-pillar/time page exposes all raw latent values directly.
- The section is labeled `DEBUG · 临时`.
- The projection is explicitly removable later and is not a chart fact.
- After each structured latent interaction, related latent values must be recomputed and returned in the view.

Later customer-safe UI should replace this with banded wording instead of raw numbers.

## Reverse-Inference Rule

Structured user feedback is transformed as:

```text
state_tag
+ years
+ recurrence
+ intensity
+ confidence
+ linked Bazi domains/ten-god/path/claim evidence
-> latent attribute deltas
```

Example:

```text
career_pressure
years: 2021, 2024
intensity: strong
recurrence: repeated
confidence: certain
```

Updates:

```text
resource_index up
risk_index up
authority multiplier up
resource multiplier up
career_bias up
event_trigger_sensitivity up
```

Boundary:

```text
reverse_inference_updates_latent_attributes_not_chart_facts
```

## Calculation Interface

HF-R2.1 emits:

```text
v30.latent_bazi_calculation_modifiers.v1
```

Fields:

```text
individualization_ready
family_energy_multipliers
domain_path_multipliers
global_energy_context
stability_thresholds
formula_boundary
```

This gives future M4/M5/RBD calculation code a clean input:

```text
individualized_energy =
  base_energy
  * ten_god_family_multiplier
  * domain_path_multiplier
  adjusted_by stability/risk/luck context
```

HF-R2.1 does not yet alter production energy scores. It establishes the contract and validated runtime data.

## Task Plan

### HF-R2.1 Latent Attribute Contract And Runtime Binding

Status: completed.

Implemented:

- Added `v30/hidden_factor/attributes.py`.
- Added `LatentBaziAttributes`.
- Added `LatentAttributeScore`.
- Added `LatentModifierScore`.
- Added default neutral values.
- Added reverse-inference mapping from profile state tags to attributes.
- Added calculation modifiers.
- Runtime now initializes default attributes.
- `attach_hidden_factor_state()` now rebuilds inferred attributes after structured feedback.
- Admin diagnostics expose attributes and summary.
- Added `tests/unit/test_latent_bazi_attributes.py`.

Validation:

```text
pytest -q tests/unit/test_latent_bazi_attributes.py tests/unit/test_latent_bazi_profile.py
python3 -m compileall -q v30/hidden_factor v30/runtime.py v30/presentation/client_model.py
```

Result:

```text
3 passed
```

### HF-R2.2 Calculation Fusion Gate

Status: completed.

Goal:

- Feed `latent_bazi_attributes.calculation_modifiers` into a bounded calculation layer.
- Start with diagnostic-only individualized score projections.
- Do not mutate M4 base ten-god energy.
- Do not change M5 ranked decisions until validation gates pass.

Implemented:

- Runtime exposes an individualized diagnostic projection:

```text
v30.latent_bazi_individualized_model_projection.v1
```

- Projection contains:
  - base family energy
  - latent family multiplier
  - adjusted family energy
  - neutral domain path score
  - latent domain multiplier
  - adjusted domain path score
  - ranked decision diagnostic projection
  - global latent context
  - stability thresholds
  - mutation boundaries
- Runtime writes:
  - `policy_effect.latent_bazi_individualized_projection`
  - `policy_effect.latent_bazi_individualized_projection_summary`
- Admin diagnostics expose both fields.
- Tests prove M4 base ten-god energy and M5 ranked decisions remain unchanged.

Validation:

```text
pytest -q tests/unit/test_latent_bazi_individualized_projection.py tests/unit/test_latent_bazi_attributes.py
python3 -m compileall -q v30/hidden_factor v30/runtime.py v30/presentation/client_model.py
```

Result:

```text
4 passed
```

### HF-R2.3 Synthetic Validation

Goal:

- Add synthetic cases for same-Bazi divergent latent attributes.
- Example pair:
  - Same chart + high resource/career/stability -> career pressure becomes promotion/credential path.
  - Same chart + high risk/low stability -> career pressure becomes volatility/role-loss path.

Acceptance:

- Same deterministic chart, different latent attributes, different individualized projections.
- No chart facts change.

### HF-R2.3a Latent Question Need Strategy

Status: completed.

Implemented:

- Added `v30.latent_question_need_strategy.v1`.
- Added `v30/hidden_factor/question_strategy.py`.
- Runtime emits `policy_effect.latent_question_strategy`.
- Recommender consumes latent strategy and only lightly boosts calibration questions when `ask_now=true`.
- If latent attributes are already inferred, follow-up need is reduced.
- If user recently selected uncertain/default/skip, cooldown is applied.
- Customer-visible flow remains centered on normal Bazi questions.

### HF-R2.3b Skip / Uncertain / Neutral Default Handling

Status: completed.

Implemented:

- Structured latent answers accept:
  - `hidden_factor:not_sure`
  - `hidden_factor:default`
  - `hidden_factor:skip`
- These answers are valid.
- They do not update hidden-factor state.
- They do not update latent attributes.
- They continue the reading with neutral defaults and train question strategy.

### HF-R2.3c Temporary UI Display

Status: completed.

Implemented:

- Added temporary latent attribute projection under `core_bazi_reading`.
- Chart/six-pillar page shows a temporary `DEBUG · 临时` hidden-attribute section.
- UI exposes all raw values for `global_attributes`, `ten_god_modifiers`, `domain_biases`, and `stability_thresholds`.
- The view is marked `debug_temporary_remove_later=true`.
- Admin diagnostics still expose raw model fields.

Reference:

```text
docs/V30_HIDDEN_ATTRIBUTE_CONCEPT_AND_QUESTION_DESIGN.md
```

### HF-R2.4 Training Signal

Goal:

Emit:

```text
v30.training_signal.latent_bazi_attribute_alignment
```

Allowed outputs:

- latent inference calibration
- question strategy calibration
- RBD route calibration

Blocked:

- chart-fact mutation
- pointer promotion
- final verdict auto-apply

### HF-R2.3d Same-Bazi Divergent Synthetic Validation

Status: completed.

Implemented:

- Added `v30/validation/latent_bazi_divergence.py`.
- Registered `python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence`.
- The tier creates the same deterministic BirthInput chart and applies different structured latent feedback profiles.
- It verifies:
  - chart facts remain identical
  - base M4 ten-god energy remains identical
  - base M5 ranked decisions remain identical
  - latent attributes diverge
  - individualized projections diverge
  - training routes exclude chart facts, calendar conversion, luck cycle, and flow timing
- Added `tests/unit/test_latent_bazi_divergence_synthetic.py`.

Validation:

```text
pytest -q tests/unit/test_latent_bazi_divergence_synthetic.py
2 passed

python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence
v30.synthetic.latent_bazi_divergence: passed (2/2)
```

### HF-R2.3e Latent Training Signal Extraction

Status: completed.

Implemented:

- Added `v30.training_signal.latent_bazi_attribute_alignment`.
- Signal source: `v30.synthetic.latent_bazi_divergence`.
- Signal measures:
  - same-Bazi chart-fact stability
  - base M4 model stability
  - base M5 decision stability
  - latent attribute divergence
  - individualized projection divergence
  - active state tags
  - active global attributes
  - active ten-god modifiers
  - active domain biases
- Allowed training targets:
  - latent inference calibration
  - question strategy calibration
  - individualized projection calibration
- Blocked training targets:
  - chart facts
  - calendar conversion
  - luck cycle
  - flow timing

Validation:

```text
pytest -q tests/unit/test_latent_bazi_divergence_synthetic.py
3 passed
```

### HF-R2.4 Latent Training Candidate And Policy Consumption

Status: completed.

Implemented:

- Auto-training candidate payloads can now consume `v30.training_signal.latent_bazi_attribute_alignment`.
- Added `v30.latent_bazi_attribute_policy.v1`.
- Question policy candidate includes:
  - `reverse_inference_weight`
  - `question_need_weight`
  - `individualized_projection_weight`
  - bounded domain-bias weights
  - bounded ten-god modifier weights
  - bounded global-attribute weights
- Rule policy candidate carries the same latent policy for diagnostics and future bounded rule routing.
- Runtime question recommendation consumes the policy through `latent_bazi_attribute_policy:question_need`.
- Policy explicitly keeps:
  - `can_tune_chart_facts=false`
  - blocked routes: chart facts, calendar conversion, luck cycle, flow timing
- Default pointer promotion is not expanded by this task; promotion remains a major-gate decision.

Validation:

```text
pytest -q tests/unit/test_auto_apply_training.py::test_latent_bazi_attribute_signal_builds_candidate_policy tests/unit/test_auto_apply_training.py::test_runtime_consumes_latent_bazi_attribute_question_policy tests/unit/test_latent_bazi_divergence_synthetic.py tests/unit/test_latent_question_strategy.py
8 passed

python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence
v30.synthetic.latent_bazi_divergence: passed (2/2)

python3 scripts/run_synthetic_validation.py --tier gradient
v30.synthetic.gradient: passed (19/19)
```

### HF-R2.5 Latent Policy Observability And Admin Validation Surface

Status: completed.

Implemented:

- Added Admin-only `v30.latent_policy_observability.v1`.
- Admin diagnostics expose latent policy status, active policy versions, active attribute summaries, latent question strategy status, influenced question rows, question/rule policy projections, and no-chart-fact training boundaries.
- Customer/user projection hides latent policy internals.
- Added `v30.latent_policy_observability_readiness.v1`.
- Added CLI `scripts/run_latent_policy_observability.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-policy-observability`.

Validation:

```text
pytest -q tests/unit/test_latent_policy_observability.py tests/unit/test_presentation_projection.py::test_admin_projection_exposes_diagnostics_and_training_actions tests/test_v30_scaffold.py::test_api_routes_are_v30_only
4 passed

python3 scripts/run_latent_policy_observability.py
v30.latent_policy_observability_readiness.v1: hf_r25_latent_policy_observability_ready
- passed: 6/6
- failed: none
- next: HF-R2.6
```

### HF-R2.6 Latent Attribute Admin Training Review

Status: completed.

Implemented:

- Added `v30.latent_attribute_admin_training_review.v1`.
- Review consumes:
  - HF-R2.5 latent policy observability
  - `latent_bazi_divergence` synthetic tier
  - `v30.training_signal.latent_bazi_attribute_alignment`
- Produces three Admin review-only candidates:
  - `latent_reverse_inference_review`
  - `latent_question_strategy_review`
  - `latent_individualized_projection_review`
- Allowed training scope is limited to latent inference, question strategy, and individualized projection.
- Forbidden scope includes chart facts, calendar conversion, luck cycle, flow timing, four pillars, fixed structure verdict, and fixed useful-god verdict.
- Auto-apply, pointer promotion, and chart-fact mutation remain disabled.
- Added CLI `scripts/run_latent_attribute_admin_training_review.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-attribute-review`.

Validation:

```text
pytest -q tests/unit/test_latent_attribute_admin_training_review.py tests/unit/test_latent_policy_observability.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only
5 passed

python3 scripts/run_latent_attribute_admin_training_review.py --review-id hf-r26-check
v30.latent_attribute_admin_training_review.v1: hf_r26_latent_attribute_admin_training_review_ready
- candidates: 3
- passed: 5/5
- failed: none
- next: HF-R2.7
```

### HF-R2.7 Latent Attribute Training UI Review Panel

Status: completed.

Implemented:

- Admin training tab now loads `GET /api/v30/admin/training/latent-attribute-review`.
- Added a read-only hidden-attribute training review panel.
- Panel displays candidate count, check pass count, next task, training boundaries, allowed scopes, forbidden scopes, and review-only candidate rows.
- The UI exposes no apply/promote control for hidden-attribute candidates.

Validation:

```text
node --check frontend/app.js
passed

pytest -q tests/unit/test_latent_attribute_admin_training_review.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_latent_attribute_training_review_endpoint_is_read_only
4 passed

python3 scripts/run_latent_attribute_admin_training_review.py --review-id hf-r27-ui-source-check
v30.latent_attribute_admin_training_review.v1: hf_r26_latent_attribute_admin_training_review_ready
- candidates: 3
- passed: 5/5
- failed: none
- next: HF-R2.7
```

Next task:

```text
HF-R2.8 Latent Attribute Workflow Closeout
```

### HF-R2.8 Latent Attribute Workflow Closeout

Status: completed.

Implemented:

- Added closeout artifact `v30.latent_attribute_workflow_closeout.v1`.
- Added CLI `scripts/run_latent_attribute_workflow_closeout.py`.
- Added Admin endpoint `GET /api/v30/admin/training/latent-attribute-closeout`.
- Closeout joins runtime latent-attribute update evidence, `latent_bazi_divergence` synthetic evidence, bounded training signals, Admin observability, Admin review-only candidates, and the Admin training UI panel into one gate.
- The gate keeps hidden attributes tied to the chart-bound Bazi reading workflow without turning them into deterministic chart facts.
- Training remains bounded to:
  - latent attribute inference
  - question strategy
  - individualized projection
- Training remains blocked from:
  - chart facts
  - calendar conversion
  - luck cycle
  - flow timing
  - fixed Bazi verdicts
- No auto-apply, policy pointer promotion, full pytest, synthetic-all, full 518K, or live LLM is allowed by this closeout.

Validation:

```text
python3 -m compileall -q v30/validation/latent_attribute_workflow_closeout.py v30/validation/__init__.py v30/api/app.py scripts/run_latent_attribute_workflow_closeout.py
passed

pytest -q tests/unit/test_latent_attribute_workflow_closeout.py tests/unit/test_latent_attribute_admin_training_review.py tests/unit/test_latent_policy_observability.py tests/test_v30_scaffold.py::test_api_routes_are_v30_only tests/test_v30_scaffold.py::test_admin_latent_attribute_workflow_closeout_endpoint_is_read_only
8 passed

python3 scripts/run_latent_attribute_workflow_closeout.py --closeout-id hf-r28-closeout-check
v30.latent_attribute_workflow_closeout.v1: hf_r28_latent_attribute_workflow_closeout_ready
- passed: 7/7
- failed: none
- next: HF-S1
```

Next task:

```text
HF-S1 Latent Attribute Steady-State Watch
```
