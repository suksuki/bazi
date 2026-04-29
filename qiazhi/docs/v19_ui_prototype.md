# V19 UI Prototype v1

This prototype implements the first static V19 Oracle UI surface.

It is intentionally isolated from V18 UI.

## Entry

```text
/v19/oracle
```

Frontend file:

```text
v17_rebirth/frontend/app/v19/oracle/page.tsx
```

## Scope

Implemented:

```text
static /v19/oracle page
mock V19 Oracle state
mobile-first single-column layout
desktop two-column reasoning workspace
SectionContainer
LayerDivider
TrustBar
StateGate
BirthInputPanel
ChartStructureSummary
InferenceSignalList
ThemeSelector
ResultCard
EvidenceCardList
FeedbackPanel
ReplayCard
```

Not implemented:

```text
backend API
LLM call
database write
real prediction
login
V18 UI compatibility
Domain Contract
production integration
```

## Files

```text
v17_rebirth/frontend/app/v19/oracle/page.tsx
v17_rebirth/frontend/components/v19/types.ts
v17_rebirth/frontend/components/v19/mockOracleState.ts
v17_rebirth/frontend/components/v19/primitives.tsx
v17_rebirth/frontend/components/v19/oracleComponents.tsx
v17_rebirth/frontend/components/v19/OraclePrototype.tsx
```

## Data Rules

The page renders mocked V19 state machine data.

The mock data follows the frontend contracts from:

```text
docs/v19_component_architecture.md
```

The UI does not locally generate:

```text
score
conclusion
narrative
LLM answer
domain reasoning
```

## Supported Theme States

Enabled:

```text
wealth_structure
income_stability
risk_opportunity
```

Disabled with reason:

```text
career
relationship
health
full_chart_general_reading
```

Reason:

```text
not yet supported by reviewed rules
```

## Visual Direction

The prototype follows:

```text
calm
structured
trust-first
non-mystical
non-chat-like
```

It uses:

```text
warm paper background
mineral blue primary actions
slate structure surfaces
soft amber uncertainty
verified green trust
muted red risk
```

## Boundaries

This prototype is a visual and interaction shell only.

It must not be used as a production prediction path.

It must not connect to V18 demo routes.

It must not bypass:

```text
Core
Inference
Mapping Registry
Contract
Verifier
Ledger
```

## Next Step

After visual acceptance:

```text
V19 UI Prototype v1 visual QA
```

Suggested checks:

```text
iPhone SE 375x667
iPhone 14/15 390x844
Android 412x915
Desktop 1440x900
zh / en / ko label expansion
long hash wrapping
inference collapsed by default
disabled theme reasons visible
```

## Acceptance Record - 2026-04-28

Scope:

```text
V19 UI Prototype v1 read-only acceptance
route: /v19/oracle
```

Commands executed:

```text
npm run build
```

Build result:

```text
passed
Compiled successfully.
TypeScript passed.
/v19/oracle generated as static route.
```

Browser open check:

```text
http://127.0.0.1:3000/v19/oracle
title: V19 Oracle Prototype
result: opened successfully
```

Viewport checks:

```text
375x667   passed
390x844   passed
430x932   passed
1280x900  passed
1440x900  passed
```

Observed layout results:

```text
no horizontal scroll
long technical ids do not overflow
section order is correct
Inference Signals collapsed by default
Inference detail content hidden initially
disabled unsupported themes show reason
Result section is not chat-bubble style
no on-chain claim present
```

Verified section order:

```text
Birth Input
Chart Structure Summary
Inference Signals
Choose a supported theme
Result
Evidence
Feedback
Replay & Verification
```

Boundary scan:

```text
no fetch / API call in V19 prototype code
no LLM call in V19 prototype code
no V17 / V18 UI component reuse in V19 prototype code
no local forbidden state keys:
- wealth_type
- career_type
- relationship_type
- health_type
- destiny_score
- fortune_score
- llm_answer
- free_text_prediction
```

Disabled theme reason:

```text
not yet supported by reviewed rules
```

TrustBar placement:

```text
confirmed inside Result section before verified result content
```

Minimal fix made during acceptance:

```text
Fixed TypeScript narrowing for ThemeSelector onSelect.
The fix only ensures disabled ThemeId cannot be passed as SupportedThemeId.
No UI behavior or business logic was changed.
```

Known non-blocking notes:

```text
No zh / en / ko expansion QA yet.
No screenshot artifact saved in this acceptance pass.
No backend integration tested by design.
```

## Visual QA Record - 2026-04-28

Scope:

```text
V19 Visual QA v1
route: /v19/oracle
mode: visual and interaction pressure check only
```

Screenshots saved:

```text
docs/ui/v19_visual_qa/v19_oracle_375x667_first_after.png
docs/ui/v19_visual_qa/v19_oracle_390x844_first_after.png
docs/ui/v19_visual_qa/v19_oracle_390x844_full_after.png
docs/ui/v19_visual_qa/v19_oracle_430x932_first_after.png
docs/ui/v19_visual_qa/v19_oracle_1440x900_first_after.png
```

Viewport checks:

```text
375x667   passed
390x844   passed
430x932   passed
1280x900  passed
1440x900  passed
```

Visual QA checklist:

```text
1. mobile-first reading order: passed
2. section hierarchy clarity: passed
3. trust-first visibility: passed
4. Chart Structure Summary prominence: passed
5. Inference collapsed and visually secondary: passed
6. Result Card restrained / non-fortune / non-chat: passed after icon fix
7. Evidence readability: passed
8. Replay readability: passed
9. disabled themes clear and non-misleading: passed
10. color avoids purple-black mystical style: passed
11. mobile Chrome spacing: passed after nav overlay fix
```

Measured layout results:

```text
no horizontal scroll on all checked viewports
disabled theme reason count: 4
Inference collapsed by default
technical ids and hashes wrap safely
```

Issues found:

```text
1. Mobile bottom navigation was fixed and visually overlapped first-screen content on 375px / 390px.
2. Result Card used a sparkle icon, which could be misread as magical or mystical.
```

Minimal fixes applied:

```text
1. MobileUserNav changed from fixed overlay to static page-bottom navigation card.
2. Removed extra bottom padding that only existed for fixed navigation.
3. Result Card decorative icon changed from sparkle to Activity.
```

Files changed during Visual QA:

```text
v17_rebirth/frontend/components/v19/OraclePrototype.tsx
v17_rebirth/frontend/components/v19/oracleComponents.tsx
docs/v19_ui_prototype.md
```

Boundaries preserved:

```text
no API integration
no LLM call
no business logic change
no V18 UI change
no component architecture rewrite
no multilingual expansion
```

Visual QA conclusion:

```text
V19 UI Prototype v1 passes Visual QA v1 for structure, trust-first hierarchy, mobile readability, and non-mystical product direction.
```

## P3 Integration Record - 2026-04-28

Scope:

```text
V19 P3: Oracle Prototype local P1 + P2 integration
route: /v19/oracle
```

Goal:

```text
Birth Input
-> Chart Structure Engine
-> Income Stability Inference
-> structured UI signals
```

Implemented:

```text
BirthInputPanel now accepts local user input:
- year
- month
- day
- hour
- calendar_type: solar | lunar
- gender: male | female

/v19/oracle now computes:
- Chart Structure Summary from P1 Chart Structure Engine
- Inference Signals from P2 Income Stability Inference
- income_stability ResultCard from bounded inference signals
- EvidenceCardList from signal source bindings
- ReplayCard with mock technical metadata
```

Unsupported behavior:

```text
lunar input returns unsupported BoundaryCard
```

Theme support:

```text
enabled:
- income_stability

disabled:
- wealth_structure
- risk_opportunity
- career
- relationship
- health
- full_chart_general_reading
```

Commands executed:

```text
cd v17_rebirth/frontend
npm run test -- v19OracleEngineAdapters
npm run build
```

Test result:

```text
passed
tests/v19OracleEngineAdapters.test.ts: 3 passed
```

Build result:

```text
passed
Compiled successfully.
TypeScript passed.
/v19/oracle remains generated as static route.
```

Boundary scan:

```text
No backend API integration.
No LLM call.
No DB write.
No V18 UI change.
No score / fortune / narrative / traditional verdict generation.
ResultCard displays bounded signals only.
EvidenceCard displays rule/source bindings, not fortune-telling copy.
```

Issue found:

```text
Build found one missing TypeScript import for ChartStructureSummaryProps after component signature changes.
```

Minimal fix:

```text
Restored the missing type import.
No business logic changed.
No rule changed.
```

Files added:

```text
v17_rebirth/frontend/components/v19/oracleEngineAdapters.ts
v17_rebirth/frontend/tests/v19OracleEngineAdapters.test.ts
```

Files changed:

```text
v17_rebirth/frontend/components/v19/OraclePrototype.tsx
v17_rebirth/frontend/components/v19/oracleComponents.tsx
docs/v19_ui_prototype.md
```

Conclusion:

```text
V19 P3 local structured loop is implemented:
Birth Input -> ChartStructure -> IncomeStabilityInference -> /v19/oracle structured UI.
It remains local-only and non-production.
```

## V19 P3 Acceptance Record + Scope Lock

### P3 当前能力（确认）

- `/v19/oracle` 已接入本地 `Chart Structure Engine`。
- `/v19/oracle` 已接入 `Income Stability Inference`。
- 已形成本地静态计算闭环（输入 -> 结构排盘 -> 稳定性推断 -> 结构化 UI 展示）。
- lunar input 走 `BoundaryCard` 的 unsupported 边界路径。
- 当前仅支持 `income_stability` 一类。

### P3 明确边界（No新增）

- no API
- no LLM
- no DB
- no V18 reuse
- no score
- no fortune
- no narrative
- no traditional prediction text
- no multi-theme inference yet

### P3 验收命令与结果

```text
npm run test -- v19OracleEngineAdapters
npm run build
```

结果：

```text
tests/v19OracleEngineAdapters.test.ts: 3 passed
build passed
Compiled successfully.
TypeScript passed.
Route remains static and build-safe at /v19/oracle.
```

### 下一阶段建议

- V19 P4: Time Structure Layer (Flow Year / Luck Cycle)
- P4 仍只做时间维度结构，不做 narrative prediction（继续保持无文本化占卜输出）

## V19 P4 Scope Definition - Time Structure Layer

```text
V19 P4: Time Structure Layer (Flow Year / Luck Cycle)

目标：
只生成时间维度结构，不生成任何预测结论。

作用：
为后续 inference 提供上下文，而不是直接输出结果。

禁止：
- 不生成 fortune
- 不生成 narrative
- 不生成“今年如何”
- 不直接影响 ResultCard
```

P4 scope lock:

```text
时间只是 context，不是结论。
P4 不做流年预测。
P4 不修改 income_stability inference。
P4 不改变 ResultCard 输出。
P5 才允许引入 time-aware inference。
```

### P4 Structure Contracts

```ts
type LuckCycle = {
  start_age: number
  end_age: number
  pillar: {
    stem: string
    branch: string
  }

  relations_with_natal: {
    clashes: string[]
    combinations: string[]
  }
}
```

```ts
type FlowYear = {
  year: number
  pillar: {
    stem: string
    branch: string
  }

  relations_with_natal: {
    clashes: string[]
    combinations: string[]
  }

  relations_with_luck_cycle?: {
    clashes: string[]
    combinations: string[]
  }
}
```

```ts
type TimeContext = {
  natal: ChartStructure
  luck_cycle?: LuckCycle
  flow_year?: FlowYear
}
```

P5 rule:

```text
P5 inference 必须基于 TimeContext，而不是直接看 natal。
```

### P4 UI Impact

Current P3 route flow:

```text
Birth Input
-> Chart
-> Inference
-> Result
```

P4 route flow:

```text
Birth Input
-> Chart Structure
-> Time Selection
-> Time Structure
-> Inference（仍只 income_stability）
```

Only allowed new UI components:

```text
1. FlowYearSelector
2. TimeStructureSummary
```

`TimeStructureSummary` is structure display only. It is not a result component.

Forbidden UI text:

```text
“2025年财运很好”
“今年机会多”
```

Allowed UI text:

```text
Flow Year: 2025 (乙巳)
Relations:
- clash: 巳亥
- combination: 子丑
```

### P4 MVP Acceptance Scope

```text
1. 用户可以选择流年（year picker）
2. 系统生成：
   - FlowYear pillar
   - 与 natal 的冲 / 合
3. UI 展示 TimeStructureSummary
4. 不接入 inference（或只作为扩展字段存在）
5. 不影响 ResultCard
```

### P4 Implementation Instruction

```text
开始实现 V19 P4：Time Structure Layer MVP。

目标：
生成 Luck Cycle 和 Flow Year 的结构数据，不做预测。

范围：

1. 输入：
   - ChartStructureOk
   - selected_year: number

2. 输出：
   - FlowYear
   - (可选) LuckCycle（先允许 stub）

3. 实现：
   - 年柱计算（FlowYear）
   - 与 natal 的：
     - 六合
     - 六冲
     - 三合
   - 返回结构化 relations

4. UI：
   - 新增 FlowYearSelector
   - 新增 TimeStructureSummary
   - 展示：
     year pillar + relations

5. 不做：
   - 不生成任何 inference signal
   - 不生成 income_stability 变化
   - 不写 narrative
   - 不接 API / LLM / DB

6. 验收：
   - 选择年份 -> UI 更新 TimeStructureSummary
   - npm run build 通过
```

## V19 P4 Implementation Record - 2026-04-28

Scope:

```text
V19 P4 MVP: Time Structure Layer
FlowYear only
LuckCycle type contract only, no calculation yet
```

Implemented:

```text
FlowYear Engine:
- selected_year -> FlowYear pillar
- relations_with_natal.clashes
- relations_with_natal.combinations
- six combination
- six clash
- three harmony as structural combination

UI:
- FlowYearSelector
- TimeStructureSummary
- Structure only · no prediction guard text
```

Hard isolation:

```text
InferenceInput contains chart only.
inferIncomeStability remains chart-only.
Time Structure does not enter inference.
Time Structure does not affect ResultCard.
TODO(P5): extend to TimeContext.
```

Forbidden fields preserved:

```text
FlowYear does not contain:
- meaning
- summary
- conclusion
- fortune
- narrative
```

Commands executed:

```text
npm run test -- v19TimeStructureEngine
npm run build
```

Result:

```text
tests/v19TimeStructureEngine.test.ts: 2 passed
build passed
Compiled successfully.
TypeScript passed.
/v19/oracle remains generated as static route.
```

P4 conclusion:

```text
P4 introduces time as context only.
It does not perform flow-year prediction.
It does not modify income_stability.
It does not change ResultCard.
P5 is the first allowed stage for time-aware inference.
```
