# V40 Phase 21: Conversation Seeds

Date: 2026-06-30

## Goal

Phase 21 adds the first report-followup dialogue layer.

It does not implement full multi-turn chat yet. It creates small, relevant next-question seeds after an accepted report.

## Contract

```text
ConversationSeed
```

Fields:

```text
question
topic
intent
answer_mode
options
source_probe_ids
source_verdict_ids
source_advice_ids
relevance_score
generated_after_report
auto_start=false
```

The contract explicitly prevents automatic dialogue start. The user must click or choose to continue.

## Builder

```text
v40/conversation/seeds.py
```

The builder uses:

```text
ProbeCandidate
DecisionVerdict
AdvicePlan
accepted report text
role_key
```

and returns up to three relevant seeds.

## Runtime Integration

`POST /api/v40/readings/native-report` now returns:

```text
conversation_seeds
runtime.conversation_seeds
```

Seeds are generated only after accepted report text exists.

## UI

`GET /v40/ui` now shows invited follow-up buttons after report generation.

Phase 21 originally only exposed invited follow-up seeds. Phase 22 consumes those seeds through the independent conversation turn runtime. The preserved boundary is:

```text
report first
dialogue invited
conversation separate
```

## Tests

Added:

```text
tests/test_v40_phase21_conversation_seeds.py
```

Coverage:

```text
seeds are generated after report
seeds are not auto-started
seeds bind to probe/verdict/advice sources
native report returns seeds
UI exposes invited seed buttons
```

## Next Phase

Phase 22 adds the first real conversation turn endpoint:

```text
POST /api/v40/conversation/turn
consume one seed or user question
use runtime + accepted report + seed source refs as context
return answer + new seeds + telemetry
keep conversation separate from report runtime
```
