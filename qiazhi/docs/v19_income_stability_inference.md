# V19 Income Stability Inference MVP

This document describes the first minimal inference adapter after Chart Structure Engine MVP.

Input:

```text
ChartStructure
```

Output:

```text
InferenceSignals
```

Supported theme:

```text
income_stability
```

## Location

```text
v17_rebirth/frontend/lib/v19/incomeStabilityInferenceTypes.ts
v17_rebirth/frontend/lib/v19/incomeStabilityInference.ts
v17_rebirth/frontend/tests/v19IncomeStabilityInference.test.ts
```

## Boundary

This layer is not a prediction engine.

It only maps existing chart structure fields into bounded inference signals.

It does not call LLM.

It does not connect to UI.

It does not connect to API.

It does not connect to DB.

It does not write state.

## Signals

The MVP outputs exactly these signals:

```text
self_capacity
wealth_presence
wealth_accessibility
volatility
structure_binding
income_stability
```

## Rule Mapping

### 1. Day master strength -> self_capacity

Source:

```text
simplified_strength.tendency
```

Mapping:

```text
weak     -> low
balanced -> medium
strong   -> high
```

### 2. Wealth count -> wealth_presence

Source:

```text
ten_god_counts.direct_wealth
ten_god_counts.indirect_wealth
```

Mapping:

```text
0     -> none
1     -> low
2..3  -> medium
4+    -> high
```

### 3. Wealth clashed / combined -> wealth_accessibility

Source:

```text
pillars.*.stem_element
pillars.*.branch_element
branch_relations[type=six_clash|six_combination|three_harmony]
```

Mapping:

```text
no wealth                     -> not_applicable
wealth touched by clash+bind  -> conflicted
wealth touched by clash       -> disrupted
wealth touched by bind        -> bound
wealth not touched            -> clear
```

### 4. Clash count -> volatility

Source:

```text
branch_relations[type=six_clash]
```

Mapping:

```text
0   -> low
1   -> medium
2+  -> high
```

### 5. Three harmony exists -> structure_binding

Source:

```text
branch_relations[type=three_harmony]
```

Mapping:

```text
0   -> none
1+  -> present
```

### 6. Structural stability -> income_stability

Source:

```text
self_capacity
wealth_presence
wealth_accessibility
volatility
structure_binding
```

Mapping:

```text
wealth none -> unstable
self_capacity low -> unstable
volatility high -> unstable
wealth_accessibility disrupted -> unstable
wealth_accessibility conflicted -> mixed
self_capacity high + volatility low -> stable
structure_binding present + volatility not high -> mixed
otherwise -> mixed
```

## Output Shape

```ts
type IncomeStabilityInferenceBundle = {
  status: "ok";
  supported_theme: "income_stability";
  signals: IncomeStabilityInferenceSignal[];
  touched_wealth_pillars: PillarName[];
};
```

Each signal has:

```ts
type IncomeStabilityInferenceSignal = {
  key: IncomeStabilitySignalKey;
  value: IncomeStabilitySignalValue;
  sources: IncomeStabilitySourceBinding[];
};
```

## Forbidden Outputs

This layer must not output:

```text
score
fortune
narrative
一生如何
prediction text
LLM answer
```

## Tests

Unit tests cover:

```text
bounded inference signal generation
self_capacity mapping
wealth_presence mapping
wealth_accessibility mapping
volatility mapping
structure_binding mapping
forbidden output absence
```

## Acceptance Record - 2026-04-28

Scope:

```text
V19 P2 Income Stability Inference MVP read-only acceptance
```

Commands executed:

```text
cd v17_rebirth/frontend
npm run test -- v19IncomeStabilityInference
npm run build
```

Test result:

```text
passed
tests/v19IncomeStabilityInference.test.ts: 6 passed
```

Build result:

```text
passed
Compiled successfully.
TypeScript passed.
/v19/oracle remains generated as static route.
```

Acceptance checklist:

```text
1. Input only accepts ChartStructureOk: passed
2. Output only contains bounded signals: passed
3. Only supports income_stability: passed
4. self_capacity comes from simplified day master strength: passed
5. wealth_presence comes from wealth ten-god counts: passed
6. wealth_accessibility comes from wealth-touching clash / combination relations: passed
7. volatility comes from clash count: passed
8. structure_binding comes from three harmony presence: passed
9. income_stability is aggregated from structure signals: passed
10. no score / fortune / narrative / prediction text: passed
11. no LLM / API / UI / DB integration: passed
12. no V18 change required: passed
```

Boundary scan:

```text
No fetch / API call found in P2 inference files.
No LLM call found in P2 inference files.
No UI import found in P2 inference files.
No database / Redis / PostgreSQL integration found in P2 inference files.
No V17 / V18 UI component reuse found in P2 inference files.
Forbidden output terms only appear in negative test assertions.
```

Issues found:

```text
TypeScript build found two redundant comparisons after prior early-return branches:
1. wealthAccessibility !== conflicted
2. volatility !== high
```

Minimal fixes:

```text
Removed both redundant comparisons.
No rule behavior changed.
No output shape changed.
No new rule added.
```

Conclusion:

```text
V19 P2 Income Stability Inference MVP passes read-only acceptance after TypeScript narrowing cleanup.
```
