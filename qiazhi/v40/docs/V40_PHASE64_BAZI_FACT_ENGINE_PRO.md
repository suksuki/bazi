# V40 Phase 64: Bazi Fact Engine Pro

Date: 2026-07-02

## Mainline Goal

Phase 64 upgrades the native Bazi fact layer from a thin adapter into `Bazi Fact Engine Pro V1`.

The goal is not to let the fact engine make final verdicts. The goal is to make the ingredients cleaner and deeper before DecisionEngine, LLM expression, Probe and training consume them.

```text
Chart Facts
  -> Bazi Fact Engine Pro
  -> Runtime facts/features/signals
  -> SignalRegistry
  -> DecisionEngine
  -> ProductProjection
  -> LLM expression
```

## Boundary

```text
Facts are immutable.
Facts are verified, not trained.
Training may only adjust weights, thresholds, ranking, claim score, advice priority and probe VOI.
LLM does not create or rewrite chart facts.
DecisionEngine remains the only verdict generator.
```

## V1 Fact Model

`build_fact_engine_pro_profile(chart)` now produces:

- hidden stems for each natal branch;
- weighted hidden-stem ten-god counts;
- weighted hidden-stem element counts;
- day-master root profile;
- month authority profile;
- advanced branch relations;
- dynamic luck/year branch triggers;
- trainable policy target hints for downstream weighting only.

## Deterministic Algorithms

### Hidden Stems

Every branch is expanded into standard hidden stems with weighted layers:

```text
本气 -> high weight
中气 -> medium weight
余气 -> low weight
```

These weights support evidence strength, but they are deterministic fact weights, not trained user policy.

### Root Profile

The day master is checked against hidden stems:

```text
same stem
same element
supporting element
```

The output is:

```text
root_score
root_level
root_branches
day_master_has_root
```

### Month Authority

The month branch is mapped to season and element, then compared with the day element:

```text
same
resource
output
wealth
officer_pressure
neutral
```

This becomes a structural evidence input for strength and useful-god review.

### Advanced Branch Relations

V1 adds sidecar detection for:

```text
三合
三会
刑
害
破
```

六合/六冲 remain in the existing branch relation adapter. Phase 64 does not remove it; it adds the deeper layer beside it.

## Runtime Binding

Native Bazi runtime now exposes:

```text
adapter.fact_engine_pro
adapter.hidden_stems
feature.hidden_ten_god_counts
feature.root_profile
feature.month_authority
feature.advanced_branch_relation_counts
```

And adds Bazi signals from:

```text
native_bazi_fact_engine_pro
```

These signals enter SignalRegistry and can be consumed by DecisionEngine. They never carry verdict authority by themselves.

## Product Impact

The product output should gradually become less empty because verdict and advice can now bind to:

- hidden ten-god evidence, not only visible stems;
- root strength, not only rough element counts;
- month authority, not only month branch label;
- complex branch relations, not only six clash/six harmony;
- dynamic luck/year branch triggers.

## Acceptance Criteria

Phase 64 V1 is complete when:

1. Fact Engine Pro profile validates hidden stems, root, month authority and advanced relations.
2. Native Bazi runtime exposes Pro facts/features.
3. Runtime signals include `native_bazi_fact_engine_pro`.
4. Decision evidence can trace user-visible verdicts back to `adapter.fact_engine_pro`.
5. Tests prove facts are not trainable policy and chart facts are not mutated.
6. V40 test suite remains green.

## Next After Phase 64

Phase 65 should focus on:

```text
V30 Mingli Asset Migration Gate
```

That phase should migrate mature V30 rules/portraits/path assets into V40 RuntimeSignal and keep them behind DTO gates.
