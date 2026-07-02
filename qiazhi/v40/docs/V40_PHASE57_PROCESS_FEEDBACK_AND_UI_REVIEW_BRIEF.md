# V40 Phase 57: Process Feedback And UI Review Brief

Date: 2026-07-02

## Goal

V40 already has the right product direction:

```text
档案 -> 报告 -> 必要校准 -> 一问一答
```

The remaining user-side problem is not architecture, but perceived flow:

1. When the model is working, the user must see that the system is actually推演中.
2. The UI still needs a stronger visual hierarchy so the user knows what to read first.
3. External UI review should be possible without mixing V40 back into V30 or exposing Admin internals.

## Waiting-State Process Feedback

The report page keeps the Phase 55 rule:

```text
Only three process lines are visible.
No clickable V30-style step flow.
No provider/model/prompt/debug/Admin text.
User-facing report and conversation requests use the LLM expression path.
No silent local fallback is allowed when the LLM is unavailable.
```

But the waiting state is upgraded from one static three-line hint into a live process loop.

While the report is waiting for the intelligent service, the page cycles through compact three-line groups:

```text
定盘: fixed chart facts, day master, month command, luck/year layer
取象: ten gods, useful-god candidates, rules, portraits, paths, signals
合参: Bazi verdict spine, Ziwei sidecar, branch/counter-evidence cleanup
```

Each group is rendered with a typewriter effect. This gives the user a visible working state without turning the report into an interactive multi-step flow.

After the report returns, the ticker stops looping and is rewritten from the real runtime:

```text
日主 / 月令 / 大运 / 流年
signal count
Ziwei sidecar or hidden clue calibration status
```

LLM role:

```text
Bazi / Ziwei / DecisionEngine = verdict and advice spine
LLM = expression and conversation language
Acceptance scanner = rejects leakage, overclaim, verdict mutation, chart-fact mutation
```

The user app sends the report and follow-up conversation through the `ollama` execution path without showing the internal execution-mode field. If the model is unavailable, the user sees a clear failure state. V40 must not quietly substitute local template text in the product flow.

## UI Review Strategy

Do not deploy to 13 just to ask for UI feedback unless live interaction is required.

Recommended first pass:

1. Generate Playwright screenshots for desktop / practitioner / mobile.
2. Maintain a concise ChatGPT / design-analyst brief in this document.
3. Ask for critique on hierarchy, report-first flow, conversation placement, and profile sidebar.
4. Apply local changes and verify with screenshots.

If external live clicking is needed later, use a V40 staging route:

```text
staging service: V40 only
domain path: https://dblife.com/v40-staging/
admin console: separate port/path, not linked from user app
database: qiazhi_v40 only
```

This is better than exposing the whole local development environment. A temporary tunnel is acceptable for short visual reviews, but a 13-server staging route is cleaner for repeated product testing.

## Brief For External UI Review

Product name:

```text
掐指一算 V40
```

Audience:

```text
ordinary users, practitioners, and the single project admin acting as practitioner
```

Core user flow:

```text
login/register
select Bazi profile
run dual-engine report
see three-line live process feedback while waiting
read verdict/advice/risk
answer only necessary Probe questions
continue one-question-one-answer conversation
```

Design intent:

```text
modern, quiet, high-trust, professional metaphysics
not antique-heavy
not dashboard-heavy
not engineering-heavy
```

What to critique:

```text
1. Is the first screen too busy?
2. Does the user know where to start?
3. Does the report area have a clear reading order?
4. Is the waiting process visible enough without becoming fake thinking?
5. Are profile, report, Probe, conversation, and practitioner lens visually separated?
6. Does mobile still feel like a product rather than a compressed desktop page?
```

Boundaries:

```text
Do not reintroduce V30 multi-step interaction.
Do not expose raw model/provider/prompt/debug text.
Do not mix Admin controls into the user app.
Do not let Ziwei replace the Bazi verdict spine.
```

## Acceptance

- User sees an animated three-line process loop immediately after clicking测算.
- The process loop continues while the report is waiting.
- The loop stops when the real report is rendered.
- The finished ticker is generated from runtime facts.
- Visual QA still passes on desktop, practitioner, and mobile.
- V40 service remains isolated on `/v40/ui` and `/api/v40`.
