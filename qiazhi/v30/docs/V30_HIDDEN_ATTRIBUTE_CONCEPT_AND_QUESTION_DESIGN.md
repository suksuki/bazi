# V30 Hidden Attribute Concept And Question Design

Updated: 2026-06-13

## Core Concept

V30 defines hidden attributes as latent personal Bazi variables.

Reason:

- The complete Bazi space is finite.
- A large number of people can share the same four pillars.
- People with the same Bazi can still diverge strongly in real life.
- Therefore the system needs a layer that explains individual differences without changing deterministic Bazi facts.

Base model:

```text
base Bazi structure
+ luck/flow time field
+ latent personal attributes
= individualized energy state / stability state / path probability
```

Hidden attributes are not mystical labels and not a questionnaire product.

They are internal model variables that should be inferred from observable user feedback and then used by calculation and diagnosis modules.

## Boundary

Hidden attributes may modify:

- family energy projection
- domain path projection
- stability threshold
- question strategy
- diagnosis route priority
- training signals

Hidden attributes may not modify:

- four pillars
- hidden stems
- ten-god deterministic facts
- luck cycles
- flow year/month
- chart context
- fixed event conclusions

## Attribute Taxonomy

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

HF-R2 range:

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

## Reverse-Inference Principle

The system must not ask the user for model variables.

Bad questions:

```text
你的 luck_index 高不高？
你的 authority_amplifier 是多少？
```

Good questions:

```text
过去遇到责任加重时，更常见的是压力转成资质/平台，还是转成消耗和不稳定？
```

Reason:

```text
observable experience
-> structured answer
-> state_tag / years / recurrence / intensity / confidence
-> chart-bound profile
-> latent attribute deltas
```

## Question Types

### Year Anchor Question

Purpose:

- Validate whether a specific luck/flow period activated a path.

Example:

```text
在 2021 或 2024 前后，事业压力更像哪一种？
A. 责任变大，但最后能力/资质提升
B. 压力变大，反而出现不稳定或损耗
C. 没有明显变化
D. 不确定
```

Inference:

```text
A -> authority/resource up, stability/resource up
B -> authority up, risk up, stability down
C -> weaken current trigger
D -> no update, low confidence
```

### Repeated-State Question

Purpose:

- Detect stable personal response patterns.

Example:

```text
过去更常见哪种状态？
A. 压力越大，越能逼出学习/证书/平台能力
B. 压力越大，越容易情绪/身体/关系被拖住
C. 机会来了能抓住，但后续稳定性一般
D. 机会不算少，但容易错过或拖延
```

Inference:

```text
A -> resource_index, stability_index, authority/resource modifier up
B -> risk_index up, pressure_tolerance down
C -> luck_index up, stability_index down
D -> luck_index maybe up, execution/choice_quality down
```

### Domain Divergence Question

Purpose:

- Decide where a chart path expresses in real life.

Example:

```text
同样遇到压力，你更容易被哪一块牵动？
A. 工作职责/职位
B. 钱、合作、分配
C. 关系/家庭
D. 身体节律/精神消耗
```

Inference:

```text
career_bias / wealth_bias / relationship_bias / health_bias
```

## Intelligent Brain Rule

Hidden-attribute questions must be embedded into Bazi intelligent Q&A.

They must not become a standalone questionnaire.

Algorithm:

```text
current user question
+ chart structure
+ luck/flow context
+ RBD path
+ ranked decisions
+ latent attributes
+ interaction history
-> decide whether a latent question is needed
```

Ask only if:

- a latent attribute can change the current reading path;
- the attribute is still default or low-confidence;
- the user has not recently skipped this kind of question;
- deterministic chart context is already sufficient enough for the question to matter.
- missing birth/time context has not already claimed priority, unless a policy explicitly boosts latent calibration for this run.

Do not ask if:

- current answer can be given without latent calibration;
- user recently skipped/refused;
- the attribute is already inferred enough;
- the question would distract from the user's Bazi reading.

## Active Strategy Contract

Runtime contract:

```text
v30.latent_question_need_strategy.v1
```

Runtime field:

```text
policy_effect.latent_question_strategy
```

The strategy returns:

```text
ask_now
need_score
target_domain
target_state_tags
target_latent_attributes
question_prompt
answer_options
skip_policy
training_routes
reasons
```

Boundary:

```text
latent_question_strategy_decides_when_to_ask_without_turning_questionnaire_into_primary_flow
```

## Skip / Uncertain / Refusal

Every latent question must allow:

```text
不确定
先按中性看
暂不回答
```

Behavior:

```text
不确定 -> valid answer, no latent update, continue reading
先按中性看 -> valid answer, no latent update, use default value
暂不回答 -> valid answer, no latent update, apply cooldown
```

These answers are not form errors.

They must not:

- update hidden-factor state;
- update latent attributes;
- mutate chart facts.

They may:

- reduce future ask priority;
- train question strategy;
- record skip/uncertainty rate.

## UI Principle

Temporary customer-facing display is allowed on the chart/six-pillar page.

Current temporary product decision:

- Hidden attribute values are shown directly in the six-pillar/time page.
- The section must be labeled `DEBUG · 临时`.
- This is a temporary inspection surface and should be removed or replaced by customer-safe bands later.
- Every structured latent interaction must refresh the related hidden attribute values in the returned view.

Temporary debug surface:

```text
DEBUG · 临时
隐藏属性数值
global_attributes: luck_index / stability_index / execution_index / ...
ten_god_modifiers: authority / resource / wealth / ...
domain_biases: career_bias / wealth_bias / ...
stability_thresholds: pressure_tolerance / event_trigger_sensitivity / ...
```

Future customer-safe display can return to banded wording:

```text
命主校准属性
机会捕捉：中性 / 偏强 / 偏弱
稳定承压：中性 / 偏强 / 偏弱
资源助力：中性 / 偏强 / 偏弱
风险波动：中性 / 偏高 / 偏低
事业偏置：中性 / 偏强 / 偏弱
财务偏置：中性 / 偏强 / 偏弱
```

Admin diagnostics continue to show raw fields. The temporary customer-side debug projection is explicitly marked as non-chart-fact and removable.

Customer reading should keep the language simple and avoid internal terms such as:

```text
hidden factor
latent vector
policy_effect
raw_score
```

## Training

Training signal categories:

### Question Selection Quality

```text
latent_question_usefulness
latent_question_skip_rate
latent_question_answer_validity
```

Question:

- Should the system have asked this latent question?
- Did it help the answer?
- Did the user answer or skip?

### Reverse-Inference Quality

```text
latent_attribute_update_alignment
latent_attribute_delta_stability
```

Question:

- Did the selected answer update the right attributes?
- Was the delta too large or too small?
- Are repeated answers stable?

### Projection Usefulness

```text
same_bazi_divergence_quality
individualized_projection_usefulness
```

Question:

- With the same Bazi, do different latent attributes create meaningful projection differences?
- Does the projection remain bounded and traceable?

## Synthetic Validation

Required same-Bazi divergent cases:

### Case A

Same chart.

Feedback:

```text
career_pressure
pressure_to_resource
strong
repeated
certain
```

Expected:

```text
resource_index up
authority/resource multiplier up
career_bias up
career projection up
base chart facts unchanged
```

### Case B

Same chart.

Feedback:

```text
career_pressure
pressure_to_volatility
strong
repeated
certain
```

Expected:

```text
risk_index up
stability_index down
event_trigger_sensitivity up
volatility projection up
base chart facts unchanged
```

Validation target:

```text
same deterministic chart
different latent answers
different individualized projections
same chart facts
same base M4/M5 output
```

## Current Implementation

Completed:

- `v30.latent_bazi_profile.v1`
- `v30.latent_bazi_attributes.v1`
- `v30.latent_bazi_individualized_model_projection.v1`
- `v30.latent_question_need_strategy.v1`
- skip/uncertain/default handling for structured latent answers
- chart/six-pillar page temporary `DEBUG · 临时` raw-value display for all latent attributes
- `v30.synthetic.latent_bazi_divergence` same-Bazi divergent validation tier
- `v30.training_signal.latent_bazi_attribute_alignment`
- `v30.latent_bazi_attribute_policy.v1` candidate policy consumption in question/rule payloads

Next:

```text
HF-R2.5 latent policy observability and admin validation surface
```

Latest targeted validation:

```text
python3 scripts/run_synthetic_validation.py --tier latent_bazi_divergence
v30.synthetic.latent_bazi_divergence: passed (2/2)

pytest -q tests/unit/test_latent_bazi_divergence_synthetic.py
3 passed

pytest -q tests/unit/test_auto_apply_training.py::test_latent_bazi_attribute_signal_builds_candidate_policy tests/unit/test_auto_apply_training.py::test_runtime_consumes_latent_bazi_attribute_question_policy
2 passed
```
