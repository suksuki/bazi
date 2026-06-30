# V40 Phase 13: Native Decision Output Runtime

Date: 2026-06-30

## Goal

Phase 13 turns the V40 native runtime from "engine can emit signals" into a product output pipeline:

```text
BaziChartFacts
  -> BaziEngine facts/features/signals
  -> SignalRegistrySnapshot
  -> DecisionEngineOutput
  -> ProductProjectionBundle
  -> SurfaceBundle
  -> TrainingLabelEvent from practitioner calibration
```

The boundary is deliberate:

```text
Engine produces material.
SignalRegistry collects material.
DecisionEngine produces verdict, advice, branch and probe contracts.
Presentation projects product cards.
SurfaceBundle separates reading, calibration, conversation and thinking surfaces.
LLM can rewrite expression later, but cannot decide.
Practitioner calibration writes labels, not chart facts or global weights.
```

## What Changed

### 1. DecisionEngineOutput

New contract:

```text
DecisionEngineOutput
```

It records:

```text
DecisionInputBundle
BranchCandidate[]
DecisionVerdict[]
AdvicePlan[]
ProbeCandidate[]
policy_version
```

This makes the output chain auditable. A runtime result can answer:

```text
Which signals were consumed?
Which branches were kept?
Which verdict did they produce?
Which advice came from that verdict?
Which probe should be invited, but not auto-started?
```

### 2. Decision Engine

New module:

```text
v40/decision/engine.py
```

Responsibilities:

```text
select decision topics
consume signal registry
rank signals by strength/confidence/polarity
preserve uncertainty as branch candidates
generate verdicts with evidence refs
generate advice plans from verdict boundaries
generate invited-only probe candidates
```

It does not:

```text
read V30 runtime
call LLM
mutate chart facts
write global weights
start dialogue automatically
```

### 3. Native Bazi Runtime Boundary

`v40/engines/bazi_native.py` no longer builds verdict/advice/probe locally.

It now only builds:

```text
EngineRunResult
RuntimeSignal[]
SignalRegistrySnapshot
```

Then it calls:

```text
build_decision_output()
build_product_projection()
build_surface_bundle()
```

### 4. Product Projection

`ProductProjectionBundle` now supports practitioner-only `BranchCard`.

Normal users see:

```text
verdict cards
advice cards
invited-only conversation probes
```

Practitioners additionally see:

```text
branch cards
probability labels
key calibration question
calibration endpoint
```

### 5. Surface Separation

`SurfaceBundle` now separates:

```text
reading       = result and advice first
calibration   = practitioner branch selection
conversation  = probe ids, invited only, not auto-started
thinking      = requested only
```

This prevents the old V30 problem where page analysis, probe dialogue and open conversation appeared in the same place.

### 6. Practitioner Calibration API

New API:

```text
POST /api/v40/calibration/practitioner-selection
```

It converts a practitioner selection into:

```text
TrainingLabelEvent(source=practitioner_selection)
```

It writes only to V40 training labels when `persist=true`.

It does not:

```text
mutate chart facts
write global weights
write V30 state
```

## Runtime Completion Impact

Before Phase 13:

```text
native engine produced signals
temporary verdict/advice lived inside engine
surface separation was incomplete
practitioner branch selection had no direct endpoint
```

After Phase 13:

```text
signals are consumed by DecisionEngine
branches are preserved as first-class output
verdict/advice/probe have a single authority
user and practitioner output surfaces are separated
calibration enters the training spine
```

## Still Not Done

Phase 13 is still not the final product runtime.

Remaining work:

```text
native Bazi fact layer is still skeletal
ten-god / useful-god / branch relation adapters need expansion
LLM expression tasks are defined but not executed in V40 runtime
real golden cases and larger synthetic batches need to run through native runtime
frontend V40 user flow is not yet built
admin native-run buttons are not yet added
```

## Tests

Added:

```text
tests/test_v40_phase13_decision_output_runtime.py
```

Coverage:

```text
DecisionEngine consumes SignalRegistry without LLM authority
native runtime separates user report from practitioner calibration
practitioner calibration endpoint records TrainingLabelEvent without weight write
```
