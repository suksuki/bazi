# V40 Phase 27: Practitioner Lens

Date: 2026-06-30

## Goal

Phase 27 adds the first practitioner-only professional surface.

It keeps the ordinary user experience clean:

```text
ordinary user -> unified report + follow-up + feedback
practitioner -> evidence lens + sidecar signals + probes + calibration actions
admin        -> raw telemetry / storage / model configuration
```

Practitioner Lens is not Admin, and it is not a second report.

## Surface

The lens is attached to:

```text
SurfaceBundle.surfaces[calibration].practitioner_lens
```

Ordinary users receive:

```text
available=false
```

Practitioners receive:

```text
bazi_signal_count
ziwei_signal_count
branch_count
probe_count
ziwei_probe_trigger_count
agreement_topics
ziwei_sidecar_topics
ziwei_signals
probe_triggers
calibration_actions
boundaries
```

## Calibration Actions

User-facing professional wording:

```text
更像这个表现
作为辅助参考
暂不采用
需要追问确认
用户反馈不符合
```

Internal training labels:

```text
supports
probe_helpful
weakens
needs_probe
mismatch
```

These actions do not directly mutate chart facts or global weights.

## Ziwei In Practitioner Lens

Ziwei remains a sidecar in Phase 27.

The lens can show:

```text
ZiweiSignal
domain topic
claim
confidence label
evidence refs
probe triggers
agreement with Bazi topics
```

But Ziwei still does not enter:

```text
DecisionInputBundle
Final Verdict authority
ordinary user report by default
```

## Boundaries

Practitioner Lens records:

```text
changes_verdict=false
changes_chart_facts=false
writes_global_weight=false
ordinary_user_visible=false
```

The lens can produce feedback signals later, but only through explicit calibration APIs and training events.

## Tests

Added:

```text
tests/test_v40_phase27_practitioner_lens.py
```

Coverage:

```text
ordinary user cannot see practitioner lens
practitioner sees Bazi/Ziwei summary
Ziwei probe triggers are visible to practitioner
calibration actions use human wording
Ziwei still does not enter DecisionInputBundle
native report returns lens for practitioner role
```

## Next

Phase 28 should add actual practitioner calibration persistence from lens actions:

```text
professional action
  -> TrainingLabelEvent
  -> LocalOverlay candidate
  -> Evaluation impact
  -> optional candidate weight
```
