# V40 Phase 14: Native Bazi Fact and Signal Adapters

Date: 2026-06-30

## Goal

Phase 14 expands the V40 native Bazi runtime from a skeleton into a clearer fact/signal layer.

It adds adapters for:

```text
visible heavenly-stem ten-god profile
useful-god candidate profile
original branch harmony/clash profile
timing branch relation profile
domain signals for wealth, relationship and health
```

These adapters do not make final destiny decisions.

They produce structured material for:

```text
SignalRegistrySnapshot
DecisionEngineOutput
ProductProjectionBundle
EvaluationCaseSpec
TrainingLabelEvent attribution
```

## New Module

```text
v40/engines/bazi_adapters.py
```

The adapter module owns reusable native Bazi facts:

```text
stem element
stem polarity
branch element
generating / controlling relation
ten-god relation
six harmony
six clash
```

This keeps `bazi_native.py` smaller and prevents the runtime engine from becoming a mixed rule dump.

## Ten-God Adapter

Function:

```text
build_ten_god_profile(chart)
```

Output:

```text
rows
counts
dominant_ten_gods
wealth_count
officer_count
resource_count
output_count
peer_count
```

Current scope:

```text
visible heavenly stems only
no hidden-stem expansion yet
no final verdict
```

This is enough for Phase 14 because it lets the runtime form structured domain signals without pretending to have completed a full traditional hidden-stem analysis.

## Useful-God Adapter

Function:

```text
build_useful_god_profile(day_element, structure, useful_candidates)
```

Output:

```text
strategy
candidates
reason
```

Boundary:

```text
candidate profile, not final 用神 verdict
```

The DecisionEngine can use this as evidence, and practitioner calibration can later raise or lower candidate branches.

## Branch Relation Adapter

Function:

```text
build_branch_relation_profile(chart)
```

Output:

```text
original branch relations
timing relations from current luck/current year
clash_count
harmony_count
```

Current relation set:

```text
六合
六冲
```

Future phases can add:

```text
三合
三会
刑
害
破
藏干
旬空
神煞 as low-priority lens
```

## Domain Signals

Phase 14 adds native domain signals:

```text
wealth
relationship
health
advice
```

They are still `RuntimeSignal`.

They do not:

```text
grant verdict authority
start dialogue
write training weights
mutate chart facts
```

They let the DecisionEngine answer topic-specific questions with topic-specific evidence instead of falling back to structure-only material.

## Runtime Change

Engine version changed:

```text
v40.bazi_native.adapter.v1
```

The runtime still uses:

```text
BaziChartFacts supplied by caller
no calendar conversion
no V30 runtime reads
no LLM verdict authority
```

## Product Impact

Before Phase 14:

```text
wealth / relationship / health questions could fall back to structure and useful-god context
ten-god and branch relation material was not explicit
```

After Phase 14:

```text
wealth questions can bind to wealth signal
relationship questions can bind to gender-aware relationship indicator
health questions can bind to branch relation pressure signal
DecisionEngine still keeps one focused verdict for the requested topic
```

## Tests

Added:

```text
tests/test_v40_phase14_native_bazi_adapters.py
```

Coverage:

```text
ten-god visible stem profile
branch relation original/timing profile
adapter facts/features/domain signals in EngineRunResult
wealth question uses wealth signal as primary runtime topic
```

## Next Phase

Phase 15 added native batch evaluation:

```text
native runtime batch evaluation using synthetic seeds
one RuntimeResult per seed
one EvaluationRunResult per generated case
EvaluationBatchSummary and release gates
API and CLI entry
```

Phase 16 should add:

```text
LLMExpressionTask execution adapter
AcceptanceResult scan for expression output
Admin native run and synthetic import actions
hidden-stem and branch relation expansion after evaluation coverage exists
```
