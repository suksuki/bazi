# V19 Chart Structure Engine MVP

This document describes V19 P1: Chart Structure Engine MVP.

The engine converts standard birth input into structured Bazi chart information.

It does not produce prediction text.

It does not produce narrative.

It does not call LLM.

## Location

```text
v17_rebirth/frontend/lib/v19/chartStructureTypes.ts
v17_rebirth/frontend/lib/v19/chartStructureEngine.ts
v17_rebirth/frontend/lib/v19/chartStructureExamples.ts
v17_rebirth/frontend/tests/v19ChartStructureEngine.test.ts
```

## Input

```ts
type BirthInput = {
  year: number;
  month: number;
  day: number;
  hour: number;
  calendar_type: "solar" | "lunar";
  gender: "male" | "female";
  flow_year?: number;
};
```

## MVP Calendar Scope

Supported:

```text
solar birth input
year pillar
month pillar
day pillar
hour pillar
day master
```

Unsupported:

```text
lunar conversion
real solar-term ephemeris
daylight saving correction
true local solar time
great luck cycles
flow year derivation
```

Lunar input returns:

```json
{
  "status": "unsupported",
  "reason": "lunar_calendar_not_supported"
}
```

## Calendar Assumptions

This MVP uses approximate fixed jie boundaries for solar month calculation.

```text
Li Chun: Feb 4
Jing Zhe: Mar 6
Qing Ming: Apr 5
Li Xia: May 6
Mang Zhong: Jun 6
Xiao Shu: Jul 7
Li Qiu: Aug 8
Bai Lu: Sep 8
Han Lu: Oct 8
Li Dong: Nov 7
Da Xue: Dec 7
Xiao Han: Jan 6
```

This is enough for prototype structure verification.

It must not be presented as a full almanac-grade calendar engine.

## Output

For supported solar input:

```ts
type ChartStructureOk = {
  status: "ok";
  input: BirthInput;
  calendar_note: "solar_mvp_approximate_jie_boundaries";
  pillars: Record<"year" | "month" | "day" | "hour", Pillar>;
  day_master: DayMaster;
  five_element_counts: FiveElementCounts;
  ten_god_counts: TenGodCounts;
  branch_relations: BranchRelation[];
  simplified_strength: SimplifiedStrength;
  chart_structure_summary: ChartStructureSignal[];
};
```

## Implemented Structure Signals

```text
pillars
day_master
five_element_counts
ten_god_counts
branch_relations
simplified_strength
chart_structure_summary
```

## Branch Relations

Implemented:

```text
六合
六冲
三合
```

Not implemented:

```text
三会
刑
害
破
```

## Simplified Strength

The MVP strength tendency is only a structure signal.

It uses:

```text
same_kind_count
support_count
pressure_drain_exhaust_count
```

Output:

```text
weak | balanced | strong
```

This is not a useful-god decision.

This is not a full strength model.

## Forbidden Outputs

The engine must not output:

```text
score
fortune
narrative
prediction text
LLM answer
domain result
```

## Example

```ts
import { evaluateChartStructure } from "@/lib/v19/chartStructureEngine";

const result = evaluateChartStructure({
  year: 1990,
  month: 5,
  day: 12,
  hour: 10,
  calendar_type: "solar",
  gender: "male",
});
```

## Tests

Unit tests cover:

```text
solar date generates four pillars
day master can be identified
five element counts are emitted
ten god counts are emitted
branch relations can be detected
lunar input returns unsupported
structure result does not expose prediction fields
```

Test file:

```text
v17_rebirth/frontend/tests/v19ChartStructureEngine.test.ts
```

## Acceptance Record - 2026-04-28

Scope:

```text
V19 P1 Chart Structure Engine MVP read-only acceptance
```

Commands executed:

```text
cd v17_rebirth/frontend
npm run test -- v19ChartStructureEngine
npm run build
```

Test result:

```text
passed
tests/v19ChartStructureEngine.test.ts: 6 passed
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
1. Solar input generates four pillars: passed
2. Lunar input returns explicit unsupported: passed
3. day_master is stable: passed
4. five_element_counts is populated: passed
5. ten_god_counts is populated: passed
6. 六合 / 六冲 / 三合 can be detected: passed
7. chart_structure_summary contains structure signals only: passed
8. no score / fortune / narrative / prediction text: passed
9. no UI / API / LLM / DB integration in engine: passed
10. no V18 UI change required: passed
```

Boundary scan:

```text
No fetch / API call found in V19 chart structure engine files.
No LLM call found in V19 chart structure engine files.
No database / Redis / PostgreSQL integration found in V19 chart structure engine files.
No V17 / V18 UI component reuse found in V19 chart structure engine files.
Forbidden output terms only appear in negative test assertions.
```

Issue found:

```text
The initial test expected 2000-01-01 month pillar to be 丁丑.
Under the MVP fixed jie boundary documented here, Jan 1 is before Xiao Han Jan 6, so it remains 子 month.
The engine output 丙子 was consistent with the documented MVP assumption.
```

Minimal fix:

```text
Updated the test expectation from 丁丑 to 丙子.
No engine behavior was changed.
No business logic was changed.
```

Conclusion:

```text
V19 P1 Chart Structure Engine MVP passes read-only acceptance after test expectation alignment.
```
