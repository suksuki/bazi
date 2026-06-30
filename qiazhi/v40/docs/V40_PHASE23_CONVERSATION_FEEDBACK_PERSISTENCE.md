# V40 Phase 23: Conversation Feedback Persistence

Date: 2026-06-30

## Goal

Phase 23 turns conversation turns into trainable assets.

The purpose is not to change weights immediately. The purpose is to preserve what the user clicked or asked, which runtime evidence it was bound to, and whether the answer passed acceptance.

```text
ConversationTurn
  -> persisted V40 artifact
  -> TrainingLabelEvent(local_only=true)
  -> later attribution / evaluation / candidate update
```

## Storage

New table:

```text
v40_conversation_turns
```

Fields:

```text
turn_id
reading_id
version
topic
accepted
turn_json
created_at
updated_at
```

Index:

```text
idx_v40_conversation_turns_reading
```

Repository methods:

```text
save_conversation_turn
list_conversation_turns
```

The table lives only in the V40 database and uses only the `v40_` prefix.

## Feedback Label

New builder:

```text
v40/conversation/feedback.py
build_training_label_from_conversation_turn
```

It maps a turn into:

```text
TrainingLabelEvent
source=probe_answer | user_answer
target_type=probe | verdict | advice | llm_output
label=probe_helpful | needs_probe
local_only=true
chart_fact_mutation_allowed=false
```

This records the fact that the user found a seed useful enough to click, or that the user entered a direct follow-up question.

## API

`POST /api/v40/conversation/turn` now returns:

```text
training_label
persisted
training_label_persisted
```

New optional flags:

```text
persist=false
persist_training_label=false
```

When `persist=true`, the endpoint saves the `ConversationTurn`.

When both `persist=true` and `persist_training_label=true`, it also saves the generated `TrainingLabelEvent`.

New read endpoint:

```text
GET /api/v40/conversation/turns?reading_id=...&limit=...
```

## Boundaries

The persisted turn and generated label cannot:

```text
write V30 state
write V40 production weight
mutate chart facts
change verdict
grant LLM decision authority
```

## UI

The user page does not persist by default yet.

Reason:

```text
The report and conversation should remain usable when the local database is unavailable.
```

Later, authenticated user sessions can turn persistence on and attach turns to user/profile history.

## Tests

Added:

```text
tests/test_v40_phase23_conversation_feedback_persistence.py
```

Coverage:

```text
conversation turn returns a local-only training label
label targets probe/verdict/advice/llm output
label cannot mutate chart facts
conversation persistence schema is V40-only
repository uses v40_conversation_turns
```

## Next Phase

Phase 24 should connect UI feedback controls:

```text
thumbs up / useful
not accurate
ask again
practitioner confirm / downgrade
persist chosen feedback as TrainingLabelEvent
show conversation history for a reading
```
