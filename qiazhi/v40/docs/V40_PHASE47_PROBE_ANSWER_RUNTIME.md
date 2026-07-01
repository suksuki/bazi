# V40 Phase 47: Probe Answer Runtime

Date: 2026-07-01

## Goal

Upgrade Probe from a UI-local feedback shortcut into a formal V40 runtime surface.

Before this phase, the user page could show a Probe card and record a training label. That was useful, but incomplete:

```text
Probe answer
  -> TrainingLabelEvent only
```

Phase 47 turns the answer into structured calibration material:

```text
Probe answer
  -> AnswerSignal
  -> HiddenAttributeUpdate
  -> TrainingLabelEvent
  -> LocalOverlay
  -> refined advice points
```

## New Contracts

Added:

```text
v40/contracts/probe.py
```

Contracts:

- `AnswerSignal`
- `HiddenAttributeUpdate`
- `ProbeAnswerResult`

Boundary:

- No chart fact mutation.
- No verdict mutation.
- No V40 production weight write.
- No V30 state write.
- User reality feedback is local calibration material until training/evaluation consumes it.

## Runtime

Added:

```text
v40/probes/answer.py
build_probe_answer_result
```

The builder consumes:

- `RuntimeResult`
- optional `probe_id`
- selected option or short answer text
- optional mismatch area
- created role

It returns:

- answer signal bound to the current reading
- hidden attribute update
- training label
- local overlay
- refined advice points
- user-facing confirmation message

## API

Added:

```text
POST /api/v40/probes/answer
```

Request:

```text
ProbeAnswerRequest
```

The endpoint can optionally persist:

- `TrainingLabelEvent`
- `LocalOverlay`

Default persistence is off for tests and local UI speed. The runtime result still returns the structured material so later training batches can consume it.

## UI

`/v40/ui` now calls:

```text
POST /api/v40/probes/answer
```

instead of directly posting a raw training label from the Probe card.

The user sees:

```text
已校准：事业判断会更贴近「平台资源」。
```

plus the first refined advice points.

The ordinary user still does not see:

- AnswerSignal
- HiddenAttributeUpdate
- TrainingLabelEvent
- LocalOverlay
- internal ids
- provider/model/debug/policy/telemetry

## Recovery Probe

The endpoint also accepts mismatch recovery without an existing `ProbeCandidate`.

Example:

```text
mismatch_area = 财富来源
selected_option = 项目客户
```

This creates:

```text
HiddenAttributeUpdate(attribute_key="wealth.money_mode")
TrainingLabelEvent(target_type="hidden_attribute")
```

This lets "不太像" feedback become useful calibration material instead of a dead-end negative label.

## Tests

Added:

```text
tests/test_v40_phase47_probe_answer_runtime.py
```

Coverage:

- Builder creates `AnswerSignal / HiddenAttributeUpdate / LocalOverlay / refined advice`.
- API returns current-reading calibration without rerun or production write.
- Recovery mismatch creates hidden attribute update.
- UI calls `/api/v40/probes/answer`.

## Remaining Work

1. Feed `ProbeAnswerResult` into conversation context so later answers use the calibrated reality signal.
2. Persist Probe answer events by default once auth/user history storage is finalized.
3. Replace temporary URL role hook with auth-derived role context.
4. Run desktop/mobile browser visual QA after the next UI pass.

## Boundary

Phase 47 does not:

- rerun the reading.
- change verdict authority.
- mutate chart facts.
- write production weights.
- write V30 state.
- expose internal calibration objects to ordinary users.
