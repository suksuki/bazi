# V40 Phase 22: Conversation Turn Runtime

Date: 2026-06-30

## Goal

Phase 22 turns report follow-up seeds into a real, independent dialogue runtime.

The conversation layer is not a reading step. It does not rerun chart analysis, does not refresh the report, and does not mutate verdicts or chart facts.

```text
accepted report
  -> invited seed or user question
  -> conversation turn
  -> accepted answer
  -> next seeds
```

## Contracts

New contract:

```text
ConversationTurn
```

It records:

```text
turn_id
reading_id
question
selected_option
source_seed_id
source_probe_ids
source_verdict_ids
source_advice_ids
answer_text
raw_thinking
provider/model
acceptance_status
next_seeds
```

Hard boundaries:

```text
can_change_verdict=false
can_create_chart_facts=false
writes_v30_state=false
writes_v40_production=false
```

## Runtime

New module:

```text
v40/conversation/turns.py
```

The turn builder consumes:

```text
RuntimeResult
ConversationSeed or free user question
accepted report text
DecisionVerdict
AdvicePlan
ProbeCandidate
```

It produces:

```text
ConversationTurn
LLMExpressionTask
LLMExpressionResult
AcceptanceResult
ExpressionTelemetry
```

The same acceptance layer used by report expression is applied to conversation answers.

## LLM Role

LLM can answer the turn in natural Chinese and can use thinking mode.

LLM cannot:

```text
create new pillars
create new luck-cycle or flow-year facts
create hidden facts
guarantee outcomes
change verdict
change advice boundary
write training weight
```

Ollama mode uses the same V40 provider configuration:

```text
V40_LLM_HOST
V40_LLM_PORT
V40_LLM_MODEL
think=true
/api/chat
```

No fallback is used when Ollama is requested and unavailable.

## API

New endpoint:

```text
POST /api/v40/conversation/turn
```

Request:

```text
turn_id
runtime
question
seed_id
selected_option
role_key
topic
execution_mode=local|provider_text|ollama
```

Response:

```text
turn
answer_text
accepted
next_seeds
expression.task/result/acceptance/telemetry
reruns_reading=false
```

## UI

`GET /v40/ui` now keeps a separate conversation area under the accepted report.

Behavior:

```text
start report
show accepted report
show seed buttons
click seed
call /api/v40/conversation/turn
append answer
replace next seed buttons
allow direct follow-up question
```

The left-side chart form remains the report input. The conversation area does not resubmit the report form.

## Tests

Added:

```text
tests/test_v40_phase22_conversation_turn_runtime.py
```

Coverage:

```text
conversation turn answers one round
conversation does not rerun reading
conversation does not write V30 or V40 production
conversation output avoids engineering language
turn/task telemetry keep LLM decision authority false
UI exposes independent conversation endpoint and area
```

## Next Phase

Phase 23 adds conversation persistence and trainable feedback:

```text
save ConversationTurn as V40 artifact
record user selected option / free reply as TrainingLabelEvent
support practitioner calibration from a turn
evaluate turn usefulness and leakage rate
```
