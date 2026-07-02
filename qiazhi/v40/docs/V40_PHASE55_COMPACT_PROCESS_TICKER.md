# V40 Phase 55: Compact Staged Process Ticker

## Objective

Phase 55 adds a compact visible staged process display to the user report flow.

The product decision remains:

```text
Do not bring back V30 multi-step interaction for ordinary users.
Do show a small sense of staged deduction.
```

The user sees a three-line typewriter-style process summary:

```text
定盘...
取象...
合参...
```

This creates a professional and slightly mysterious sense of process without forcing users through many pages.

## Boundary

The process ticker is not:

- a clickable step flow;
- a debug trace;
- hidden chain-of-thought;
- provider/model/prompt telemetry;
- V30 multi-step UI revival.

It is a user-facing projection of staged material preparation:

- Bazi chart and timing facts;
- ten-god and useful-god candidates;
- rule/path/domain signals;
- Ziwei sidecar calibration;
- final verdict/advice/next-question assembly.

## UI Contract

The ticker has exactly three visible lines:

1. `定盘` line;
2. `取象` line;
3. `合参` line.

During report generation, the lines show "正在..." text.

After the report is accepted, the lines are rewritten from the actual runtime:

- day master;
- month branch;
- current luck;
- current year;
- signal count;
- whether Ziwei sidecar entered the runtime.

## Acceptance

- `/v40/ui` contains `processTicker` and `renderProcessTicker`.
- The process display is visible during generation and after report acceptance.
- It uses separate typewriter timers and does not interrupt the hero title typing.
- It contains no provider/model/debug/Admin terms.
- It does not create new user actions or rerun readings.
- Focused UI tests, visual QA and full V40 tests pass.

