# V40 Phase 24: User Surface Productization

Date: 2026-06-30

## Goal

Phase 24 folds the latest product design feedback into the V40 user surface.

V40 user-side product positioning:

```text
report-first
conversation-after
feedback-to-training
```

The user page is not a generic chat product, not a raw report dump, and not an engineering test console.

## Product Flow

```text
input chart facts
  -> generate core reading report
  -> show relevant follow-up seeds
  -> user explicitly enters conversation
  -> optional probe / feedback
  -> feedback becomes trainable local signal
```

## User-Side Information Architecture

```text
Input Workspace
Reading Surface
Follow-up Hub
Conversation Surface
Feedback Layer
```

Practitioner mode can later add:

```text
Practitioner Lens
```

Admin remains separate and must not leak into the main user app.

## Ordinary User Surface Rules

Hide by default:

```text
provider
model
acceptance status
thinking trace chars
telemetry
runtime mode
SignalRegistry
DecisionEngine
claim_key
policy_key
training event
raw prompt
raw LLM output
```

Translate to product language:

```text
结构分析完成
表达已生成
可以继续追问
智能测算服务已连接
```

## UI Changes

`GET /v40/ui` now includes:

```text
topic selector: 综合命盘 / 今年财运 / 事业方向 / 感情关系 / 健康压力 / 大运流年 / 用神喜忌
ordinary wording: 智能表达 / 快速预览
human status chips
report feedback buttons
conversation feedback buttons
```

The page no longer exposes concrete provider/model/base URL in the ordinary user surface.

## Feedback Mapping

Report feedback:

```text
很像     -> TrainingLabelEvent(label=matches_reality, target_type=verdict)
部分像   -> TrainingLabelEvent(label=supports, target_type=verdict)
不太像   -> TrainingLabelEvent(label=mismatch, target_type=verdict)
```

Conversation feedback:

```text
有帮助   -> TrainingLabelEvent(label=expression_good, target_type=llm_output)
一般     -> TrainingLabelEvent(label=probe_helpful, target_type=llm_output)
不准确   -> TrainingLabelEvent(label=expression_bad, target_type=llm_output)
```

All feedback is local by default:

```text
local_only=true
chart_fact_mutation_allowed=false
```

## Visual Direction

Current alpha keeps the existing dark, quiet surface, but the target direction is:

```text
modern consulting report
subtle eastern metaphysics
clear hierarchy
low engineering exposure
restrained motion
```

Avoid:

```text
large bagua motifs
temple/gold/red-heavy style
raw telemetry
debug chips
chatbot-first layout
```

## Tests

Updated:

```text
tests/test_v40_phase20_user_report_ui.py
```

Coverage:

```text
user UI exposes topic selection
user UI exposes feedback entry
user UI does not hardcode Gemma/provider/IP in ordinary surface
```

## Next

The next UI phase should add:

```text
human-readable thinking summary drawer
practitioner lens drawer
report topic cards
mobile single-column polish
```
