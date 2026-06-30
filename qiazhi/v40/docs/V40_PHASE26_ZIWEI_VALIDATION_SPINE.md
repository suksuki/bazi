# V40 Phase 26: Ziwei Validation Spine

Date: 2026-06-30

## Goal

Phase 26 folds the Ziwei roadmap into the V40 mainline.

Principle:

```text
Bazi = primary structure engine
Ziwei = second metaphysics engine as Domain Lens
Reality Probe = manifestation calibration
DecisionEngine = only verdict authority
LLM = expression only
CentralBrain = orchestration and training loop
```

Ziwei must be integrated into the framework, not into free-form LLM prose.

## Three-Stage Ziwei Roadmap

### Ziwei V0: Fact Layer

```text
birth input
  -> Ziwei chart facts
  -> life palace / body palace
  -> twelve palaces
  -> major stars
  -> annual transformations
  -> decade luck / flow year
```

V0 does not generate user verdicts or advice.

### Ziwei V1: Signal Sidecar

```text
ZiweiChartFacts
  -> Ziwei features
  -> Ziwei signals
  -> SignalRegistry
```

V1 has:

```text
decision_weight=0
ordinary user report hidden by default
practitioner/admin sidecar visibility
```

### Ziwei V2: Lightweight Decision Aux

Only after validation:

```text
decision_weight=0.05 - 0.15
```

Rules:

```text
Bazi strong + Ziwei aligned -> slight confidence boost
Bazi mixed + Ziwei aligned -> keep mixed and trigger Probe
Bazi supported + Ziwei counter -> show counter-evidence, do not overturn
Ziwei strong but Bazi absent -> candidate/probe only
Reality Probe counter -> lower manifestation weight
```

## Input Contract

New contract:

```text
BirthInputCanonical
```

Fields:

```text
calendar_type
birth_date
birth_time
gender
timezone
location
leap_month
```

It exposes:

```text
can_run_ziwei
ziwei_input_quality = complete | partial | unavailable
```

This prevents the system from fabricating Ziwei output from Bazi pillars alone.

## Ziwei Facts

`ZiweiChartFacts` now supports:

```text
palaces
major_stars
annual_transformations
decade_luck
flow_year
palace_notes
domain_lenses
```

These are immutable facts and cannot be changed by training, feedback, LLM, or admin labels.

## Domain Mapping

Ziwei V1 maps domains to palace clusters:

```text
wealth       -> 财帛 / 官禄 / 迁移 / 田宅 / 交友 / 福德
career       -> 官禄 / 命宫 / 迁移 / 父母 / 交友 / 财帛
relationship -> 夫妻 / 命宫 / 福德 / 财帛 / 迁移 / 交友
health       -> 疾厄 / 福德 / 命宫 / 官禄 / 财帛
family       -> 父母 / 兄弟 / 田宅 / 子女 / 福德
timing       -> 迁移 / 命宫 / 官禄 / 财帛 / 田宅 / 交友
hidden       -> 福德 / 疾厄 / 命宫 / 迁移
```

These mappings produce evidence refs such as:

```text
ziwei.palace.官禄
ziwei.palace.迁移
```

## Probe Trigger

Ziwei sidecar can trigger Probe candidates.

Example:

```text
Ziwei career sidecar
  -> "你的事业压力更常来自平台制度、职责边界、外部机会，还是团队协作？"
```

These probe triggers are not ordinary user verdicts.

They are calibration opportunities.

## Evaluation Metrics

New metrics:

```text
ziwei_sidecar_signal_rate
cross_engine_topic_agreement_rate
```

They observe:

```text
whether Ziwei generated sidecar signals
whether Ziwei topics align with Bazi topics
```

They do not affect release gates yet.

## Boundaries

Ziwei V1 still cannot:

```text
enter DecisionInputBundle
change Verdict
change AdvicePlan
write production weight
appear as a separate ordinary user report
let LLM synthesize raw Bazi + raw Ziwei freely
```

## Tests

Added:

```text
tests/test_v40_phase26_ziwei_validation_spine.py
```

Coverage:

```text
BirthInputCanonical declares Ziwei readiness
Ziwei Domain Lens emits ProbeTrigger candidates
Ziwei evidence refs bind domain palaces
MetricSummary observes Ziwei sidecar signal rate
MetricSummary observes cross-engine topic agreement
```

## Next

Phase 27 should add the practitioner lens:

```text
Bazi signals
Ziwei sidecar signals
agreement/counter-evidence
probe triggers
practitioner calibration actions
```

Ordinary users should still see only the unified report, follow-up questions, and feedback controls.
