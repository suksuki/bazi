# V40 Phase 25: Ziwei Domain Lens V1

Date: 2026-06-30

## Answer

Before this phase, Ziwei was only present as a contract boundary:

```text
EngineKey.ZIWEI
ZiweiEngine V1 decision_weight must be 0
```

It was not yet a real runtime engine.

Phase 25 adds the first Ziwei runtime integration as a sidecar Domain Lens.

## Position

V40 engine hierarchy:

```text
BaziEngine = primary engine
ZiweiEngine = domain lens / sidecar context
RealityProbe = calibration layer
DecisionEngine = only verdict authority
LLM = expression / dialogue only
```

Ziwei is not equal to Bazi in V40 V1.

It does not produce final verdicts and does not directly change advice.

## Contract

New contract:

```text
ZiweiChartFacts
```

Fields:

```text
chart_id
life_palace
body_palace
major_stars
palace_notes
domain_lenses
immutable=true
```

Like Bazi chart facts, Ziwei facts are not trainable policy and cannot be mutated by feedback, LLM, or training.

## Engine

New engine:

```text
v40/engines/ziwei_native.py
run_native_ziwei_engine
```

Output:

```text
EngineRunResult(engine=ziwei)
facts
features
RuntimeSignal(source=ziwei_engine)
decision_weight=0
```

The generated signals are practitioner/admin-visible sidecar signals:

```text
role_visibility=["practitioner", "admin"]
```

## Runtime Integration

`build_native_bazi_runtime` now accepts:

```text
ziwei_chart: ZiweiChartFacts | None
```

API requests now accept:

```text
ziwei_chart_facts
```

When provided:

```text
Bazi engine runs normally
Ziwei engine runs as optional sidecar
MultiEngineRunResult contains both results
SignalRegistry contains Bazi + Ziwei signals
DecisionEngine input filters out Ziwei signals in V1
```

## Boundary

DecisionEngine ignores Ziwei signals in Phase 25:

```text
signal.source != ziwei_engine
```

This is intentional.

Ziwei V1 is useful for:

```text
practitioner lens
future domain explanation
future cross-engine validation
future probe generation
future evaluation
```

It is not yet used for:

```text
final verdict generation
advice priority
global weight updates
ordinary user report text
```

## Future Evolution

Phase 26+ can add:

```text
Ziwei fact importer from V30 or external parser
Ziwei palace/star structured adapters
Cross-engine agreement / conflict metrics
Practitioner drawer showing Bazi + Ziwei comparison
Ziwei-informed probe suggestions
Evaluation cases for Ziwei sidecar usefulness
```

Only after evaluation proves stable should Ziwei move from:

```text
SIGNAL_SIDECAR
```

to:

```text
DECISION_AUX
```

Even then, final verdict authority remains with DecisionEngine.

## Tests

Added:

```text
tests/test_v40_phase25_ziwei_domain_lens.py
```

Coverage:

```text
Ziwei engine result appears when ziwei_chart_facts are provided
Ziwei decision_weight remains 0
Ziwei signals enter SignalRegistry
Ziwei signals do not enter DecisionInputBundle
Native report accepts optional ziwei_chart_facts
```
