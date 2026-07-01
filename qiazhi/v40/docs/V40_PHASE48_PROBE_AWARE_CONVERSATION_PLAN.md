# V40 Phase 48 Plan: Probe-Aware Conversation Context

Date: 2026-07-01

## Goal

Make later intelligent conversation consume the user's Probe calibration results.

Phase 47 made Probe answers structured:

```text
ProbeAnswerResult
  -> AnswerSignal
  -> HiddenAttributeUpdate
  -> TrainingLabelEvent
  -> LocalOverlay
  -> refined advice
```

Phase 48 must make conversation aware of those results:

```text
Report
→ Probe answer
→ ProbeAnswerResult
→ later conversation turn
→ answer uses calibrated reality signal
```

## Product Rule

If the user already told the system:

```text
事业更像「平台资源」
```

then the next answer must not behave as if that information does not exist.

The conversation answer should say, in user language:

```text
结合你刚才补充的「平台资源」线索，本轮事业建议更适合先看平台承接、资质资源和职责边界。
```

## Architecture

### Request Contract

Extend:

```text
ConversationTurnRequest
```

with:

```text
probe_answer_results: list[ProbeAnswerResult]
```

The request still must not:

- rerun the reading
- mutate verdicts
- mutate chart facts
- write production weights
- write V30 state

### Conversation Runtime

Extend:

```text
build_conversation_turn
build_conversation_prompt
render_local_conversation_answer
```

to consume:

- answer signal interpreted claims
- hidden attribute values
- refined advice points

### ConversationTurn Output

Add source tracking fields:

```text
source_answer_signal_ids
source_hidden_attribute_update_ids
calibration_context
```

These are internal structured fields. Ordinary UI should show only user-language answers.

### UI

After `/api/v40/probes/answer` returns, store its `result` locally.

Every later `/api/v40/conversation/turn` call sends:

```text
probe_answer_results: currentCalibrationResults
```

The UI should not show raw names such as:

- AnswerSignal
- HiddenAttributeUpdate
- ProbeAnswerResult
- TrainingLabelEvent
- LocalOverlay

## Tests

Add/update tests to verify:

1. Conversation API accepts `probe_answer_results`.
2. Local conversation answer references the calibrated answer.
3. Conversation prompt includes calibrated reality signal and refined advice.
4. ConversationTurn records source answer signal ids and hidden attribute update ids.
5. UI sends `probe_answer_results` after Probe answer.
6. No verdict/chart fact/production/V30 mutation.

## Done Criteria

Phase 48 is done when:

- `ProbeAnswerResult` can influence the next conversation answer.
- No ordinary user engineering leakage is introduced.
- Full V40 test suite passes.
- `/v40/ui` and project status endpoints smoke cleanly after restart.

## Implementation Result

Implemented in this phase:

```text
ConversationTurnRequest.probe_answer_results
ConversationTurn.source_answer_signal_ids
ConversationTurn.source_hidden_attribute_update_ids
ConversationTurn.calibration_context
```

Updated runtime:

```text
build_conversation_turn
build_conversation_prompt
render_local_conversation_answer
```

The local and LLM conversation paths now receive:

- calibrated reality claims from `AnswerSignal`
- hidden attribute values from `HiddenAttributeUpdate`
- refined advice points from `ProbeAnswerResult`

The UI stores Probe answer results locally after `/api/v40/probes/answer` and sends them with every later `/api/v40/conversation/turn` request.

The ordinary user still sees only natural language such as:

```text
结合你刚才补充的线索：事业校准线索更偏向「平台资源」...
```

and does not see:

- AnswerSignal
- HiddenAttributeUpdate
- ProbeAnswerResult
- TrainingLabelEvent
- LocalOverlay

## Tests Added

```text
tests/test_v40_phase48_probe_aware_conversation.py
```

Coverage:

1. Conversation API consumes `probe_answer_results`.
2. Local conversation answer includes the calibrated answer.
3. ConversationTurn records source answer signal and hidden attribute update ids.
4. LLMExpressionTask includes calibration claims in allowed assertions.
5. UI forwards stored Probe answers to later conversation without exposing internal type names.
