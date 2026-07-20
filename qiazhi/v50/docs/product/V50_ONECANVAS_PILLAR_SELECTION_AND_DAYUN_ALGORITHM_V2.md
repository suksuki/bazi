# V50 OneCanvas Pillar Composition and DaYun Algorithm v6

```yaml
status: IMPLEMENTED_MACHINE_VERIFIED
decision_state: R1_HUMAN_PRODUCT_GATE_PENDING
supersedes: ../archive/product/V50_ONECANVAS_PILLAR_DEPENDENCY_MODEL_V1.md
scope: OneCanvas WYSIWYG pillar selection, birth-year anchoring and DaYun derivation
supersedes_behavior:
  - v4_destructive_local_cascade
  - v5_manual_composition_controls
ui_implementation_in_this_change: true
production_deployment: false
verification:
  targeted_regression: 44_passed
  full_regression: 381_passed
  desktop_visual_check: PASS_1440x1000
  mobile_visual_check: PASS_390x844
  horizontal_overflow: false
  human_product_gate: pending
```

## 0.1 v6 Interaction Contract

The v6 contract removes all explicit edit, finish and lock-switch controls from
Year and Day. The first **actual previous/next operation**, never hover alone,
creates a short-lived editing session and makes that operated component the
session anchor:

```text
closed server catalogs
→ hover or focus only reveals local controls
→ first Year / Day step establishes the stem or branch anchor
→ the other component is constrained to legal counterparts
→ every visible preview remains one complete legal Jiazi
→ complete Month / Hour dependent selection
→ deterministic target compile
→ immediate Sandbox render
→ Gregorian Annual selection
→ derived DaYun only
```

The anchor remains stable while the pointer or keyboard focus stays inside the
same pillar. Both sides may be stepped repeatedly: stepping the anchor cycles
the full server-provided stem or branch catalog, while stepping its counterpart
cycles only the compatible set. Moving to another pillar, leaving the pillar,
tapping outside on touch devices, or pressing Escape ends the session. There is
no pencil, checkmark, central lock button, Apply page or hidden invalid chart.

The product gate is deliberately not closed by these machine results. An
unguided analyst and first-time-user review is still required before R1 can be
treated as a released product interaction.

## 0. Final Conclusion

The previous model correctly identified the legal candidate families but used
the wrong editing model: each local choice immediately replaced the compiled
chart and cascaded a dependent pillar. Operation order could therefore prevent
the user from reaching an intended complete four-pillar target.

The corrected model separates **target intent**, **legal composition**, and
**compiled Sandbox state**:

```text
Year pillar: first operated stem or branch becomes the automatic session anchor
        ↓
Month pillar: choose one complete pillar from 12 options derived from year stem

Day pillar: first operated stem or branch becomes the automatic session anchor
        ↓
Hour pillar: choose one complete pillar from 12 options derived from day stem

Annual observation: select a Gregorian year only; annual Jiazi is derived

Sexagenary year anchor: choose a cycle year compatible with the selected year pillar
Actual Gregorian birth year: remains a calendar candidate until full reverse lookup confirms it

Gender / chart type: choose explicitly as 乾造 or 坤造

DaYun sequence: derive from chart type, year polarity and month pillar; never edit directly
Current DaYun: locate only after a Gregorian birth-year anchor resolves the full four pillars to calendar time
```

In product language:

```text
年柱、日柱由第一次实际增减自动确定锚点，连续操作始终保持合法甲子；
月柱与时柱只选完整合法柱，分别受年干与日干约束；
流年只选择公历年份，流年干支由时间引擎派生；
所有修改先进入目标草稿，再由服务端一次求解完整四柱；
乾坤明确后计算大运序列，真实年份与历法候选一致后才定位当前大运。
```

"Follow" means **reduce the legal option set to 12**, not permanently make
month or hour read-only. A parent change may suggest the dependent pillar with
the same branch, but that suggestion is not committed until the global target
solver returns a legal complete variant.

The user still receives a WYSIWYG result without an Apply page. The important
distinction is internal:

```text
first node step edits PillarTargetDraft and establishes an automatic anchor
→ the nearest legal counterpart keeps the visible pillar complete
→ every complete target is compiled by the server
→ successful compile replaces the visible Sandbox scene
→ conflict or multiple candidates remain explicit
→ Undo / redo / reset operate on target and compiled snapshots together
```

## 1. Two Validity Modes Must Not Be Mixed

### 1.1 Structural sandbox

OneCanvas is allowed to construct a hypothetical GanZhi structure without
claiming that it is a real birth datetime.

```text
60 year choices
× 12 year-compatible month choices
× 60 day choices
× 12 day-compatible hour choices
```

This mode is appropriate for teaching, pattern experiments, path comparison,
hypothesis testing and synthetic chart research. Its epistemic label is always:

```yaml
source_mode: hypothetical
validity: ganzhi_structural
real_datetime_verified: false
```

### 1.2 Real chart mode

A real chart starts from calendar facts:

```text
date + time + place + timezone + calendar convention
        ↓
calendar engine
        ↓
four pillars
```

The year changes at the exact LiChun boundary; the month changes at the exact
Jie boundary; the late-Zi-hour day convention must also be explicit. Therefore
an arbitrary structural combination must not be saved as a real profile until
the calendar engine finds and the user confirms a matching datetime.

The official `lunar-python` reverse lookup, `Solar.fromBaZi`, first validates
the year/month stem dependency and then searches for actual dates matching all
four pillars. Its result can be empty or contain multiple dates.

## 2. Slot Authority

| Slot | User choice | Legal options | Recomputed from | Product status |
| --- | --- | ---: | --- | --- |
| Year | step either glyph; the first operated glyph anchors the current session | 10 stems / 12 branches constrained to 60 legal pairs | server Jiazi catalog and solver | editable |
| Sexagenary year anchor | cycle-year label compatible with selected Year | rolling 120-year list | server calendar catalog | optional structural time anchor |
| Actual Gregorian birth year | candidate civil year compatible with full pillars | zero, one or several calendar candidates | full reverse lookup | required with resolved datetime to locate current DaYun |
| Month | dependent whole-pillar choice | 12 | selected year stem + solar-month branch | editable after year |
| Day | step either glyph; the first operated glyph anchors the current session | 10 stems / 12 branches constrained to 60 legal pairs | server Jiazi catalog and solver | editable |
| Hour | dependent whole-pillar choice | 12 | selected day stem + hour branch | editable after day |
| Annual observation | choose a concrete Gregorian year only | supported calendar-year range | Temporal Core derives annual Jiazi | editable observation, never a natal pillar edit |
| Gender / chart type | independent explicit fact | 乾造 / 坤造 | profile fact or Sandbox choice | required before DaYun |
| DaYun | none | derived | gender + year polarity + month pillar; exact timing also needs datetime | never editable |

The frontend may display options, but it must not generate or validate them.
All candidate lists come from the deterministic calendar/compiler boundary.

For Year and Day composition:

```text
stem stepped first
→ stem is the automatic anchor for this edit session
→ keep or select the nearest compatible branch
→ subsequent branch steps traverse only six compatible branches

branch stepped first
→ branch is the automatic anchor for this edit session
→ keep or select the nearest compatible stem
→ subsequent stem steps traverse only five compatible stems
```

The anchor is a short-lived interaction affordance, not a new Mingli fact. It
is shown as a passive marker on the anchored node and cannot be clicked or
switched manually. Ending the session keeps the latest successfully compiled
Sandbox result; a failed compile restores the previous complete pillar.

## 3. Month Pillar: Five Tigers

The month branch order is:

```text
寅 卯 辰 巳 午 未 申 酉 戌 亥 子 丑
```

These are solar-term months, not Gregorian months and not ordinary lunar-month
labels. For each selected year stem, the compiler emits exactly 12 complete
month pillars:

| Year stem | 12 legal month pillars |
| --- | --- |
| 甲 / 己 | 丙寅 丁卯 戊辰 己巳 庚午 辛未 壬申 癸酉 甲戌 乙亥 丙子 丁丑 |
| 乙 / 庚 | 戊寅 己卯 庚辰 辛巳 壬午 癸未 甲申 乙酉 丙戌 丁亥 戊子 己丑 |
| 丙 / 辛 | 庚寅 辛卯 壬辰 癸巳 甲午 乙未 丙申 丁酉 戊戌 己亥 庚子 辛丑 |
| 丁 / 壬 | 壬寅 癸卯 甲辰 乙巳 丙午 丁未 戊申 己酉 庚戌 辛亥 壬子 癸丑 |
| 戊 / 癸 | 甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申 辛酉 壬戌 癸亥 甲子 乙丑 |

Interaction rule:

```text
choose year
→ compiler returns 12 month candidates
→ user chooses one month
```

When the year changes, the UI may preserve the previously selected **month
branch** as a convenience and update its stem, but it must still expose all 12
legal choices. Preservation is a presentation default, not an authority rule.

## 4. Day and Hour: Five Rats

The day pillar is independently selectable from all 60 Jiazi in structural
mode. After the day is chosen, the hour branch order is:

```text
子 丑 寅 卯 辰 巳 午 未 申 酉 戌 亥
```

The compiler emits exactly 12 complete hour pillars:

| Day stem | 12 legal hour pillars |
| --- | --- |
| 甲 / 己 | 甲子 乙丑 丙寅 丁卯 戊辰 己巳 庚午 辛未 壬申 癸酉 甲戌 乙亥 |
| 乙 / 庚 | 丙子 丁丑 戊寅 己卯 庚辰 辛巳 壬午 癸未 甲申 乙酉 丙戌 丁亥 |
| 丙 / 辛 | 戊子 己丑 庚寅 辛卯 壬辰 癸巳 甲午 乙未 丙申 丁酉 戊戌 己亥 |
| 丁 / 壬 | 庚子 辛丑 壬寅 癸卯 甲辰 乙巳 丙午 丁未 戊申 己酉 庚戌 辛亥 |
| 戊 / 癸 | 壬子 癸丑 甲寅 乙卯 丙辰 丁巳 戊午 己未 庚申 辛酉 壬戌 癸亥 |

Interaction rule:

```text
choose day
→ compiler returns 12 hour candidates
→ user chooses one hour
```

The late Zi hour convention remains a real-calendar concern. A structural 子时
choice is valid as a GanZhi experiment; mapping it to 23:00 or 00:00 requires a
declared sect and real datetime validation.

## 5. Annual Observation

Annual observation does not modify the natal four pillars. R1 exposes exactly
one input:

```text
closed Gregorian-year dropdown
→ select once; dropdown closes immediately
→ Temporal Core
→ annual Jiazi
→ update the visible Annual pillar
```

There is no lock, confirmation, modal, toast, or explanatory interruption in
this selection flow. The dropdown displays Gregorian years; the pillar itself
may display the selected year together with the derived Jiazi.

A Jiazi alone is cyclical and cannot locate the current DaYun. The selected
Gregorian year is the observation point used to locate the active period after
the natal chart, gender, real calendar anchor, and DaYun windows are resolved.

An unrestricted annual-Jiazi selector may exist later in a clearly labeled
research Sandbox, but it is outside R1 and must not share the production
timeline control.

## 6. DaYun Must Be Split Into Two Results

"Calculate DaYun last" is correct as a product sequence, but DaYun has two
different levels of computability.

### 6.0 Gender is authoritative input, never an inferred result

DaYun direction cannot be computed until the chart is explicitly identified
as 乾造 or 坤造. The deterministic direction contract is:

| Year-stem polarity | 乾造 | 坤造 |
| --- | --- | --- |
| Yang | forward | reverse |
| Yin | reverse | forward |

The system must never infer gender from a stored DaYun sequence, a display
label, a previous fixture, a role, a name, or a fallback default. When gender
is unknown:

```yaml
chart_type: 命造未定
direction: unresolved
luck_sequence: []
luck_pillar: null
status: recalculation_unavailable
missing_inputs:
  - gender_required_for_luck_direction
```

The read-only canvas may still show the natal four pillars and the selected
annual observation. It must not manufacture the two DaYun nodes merely to keep
a twelve-node visual layout. Selecting 乾造 or 坤造 is an explicit Sandbox fact;
changing it recompiles the DaYun sequence without changing the natal pillars.

### 6.1 Structural DaYun sequence

Given the selected year stem, selected month pillar and gender, the
deterministic engine can derive:

- forward or reverse direction;
- the ordered DaYun pillar sequence.

The official implementation uses the exact year-stem polarity and gender to
choose direction, then advances or reverses from the exact month pillar.

### 6.2 Exact start age and year windows

Exact timing additionally needs:

```text
real birth datetime
previous / next Jie timestamp
selected start-luck calculation sect
```

Without those facts, the system must not claim exact start age, exact start
date, exact start/end Gregorian years, or which DaYun is active in a target
calendar year.

Therefore:

```yaml
structural_sequence:
  status: available
  direction: forward | reverse
  pillars: [...]

exact_timing:
  status: available | unresolved_real_datetime | multiple_datetime_candidates
  start_age: null
  start_time: null
```

Any natal pillar mutation invalidates the original chart's exact start timing
until a matching real datetime is resolved. The old implementation's practice
of inheriting the formal chart's age window or active sequence index is not a
true recalculation and must not be presented as one.

### 6.3 Year anchor and actual birth year are different fields

A sexagenary-cycle anchor materially narrows the search and can be shown in a
simple rolling 120-year list. For example, a structural 丁巳 anchor may offer:

```text
1917 · 丁巳
1977 · 丁巳
```

This is a cycle-year anchor, not yet proof of the actual civil birth year. A
Ganzhi year begins at LiChun rather than January 1, so a person born before
LiChun in the following Gregorian year may still have the previous year
pillar. The product must therefore use two explicit labels:

```text
干支纪年锚点
实际公历出生年份候选
```

The second value comes only from full calendar reverse lookup.

The server then performs:

```text
birth year + complete four pillars + 乾/坤造
        ↓
Solar.fromBaZi(..., sect=2)
        ↓
filter candidates to the selected Gregorian year
        ↓
calculate start-luck phase and DaYun windows for every candidate
        ↓
commit a current DaYun to the Sandbox only when all candidates agree
```

This is a Sandbox timing resolution, not a write to the formal birth profile.
If there is no matching datetime or candidates disagree on the current DaYun,
the structural sequence remains visible but the current DaYun stays unresolved.

Concrete regression invariant:

```text
乾造 · 1977 · 丁巳 乙巳 乙丑 乙酉 · analysis year 2026
→ reverse sequence: 甲辰 癸卯 壬寅 辛丑 庚子 ...
→ current DaYun: 庚子
→ calendar window: 2018–2027
```

## 7. Correct OneCanvas Interaction

### 7.1 Year and Day

```text
hover or focus a Year / Day pillar
→ reveal previous and next controls without changing data
→ step one visible stem or branch
→ that component becomes the automatic session anchor
→ the other component is immediately constrained to a legal counterpart
→ both components can be stepped repeatedly while the anchor remains stable
→ update PillarTargetDraft
→ server solves the whole target and returns the next Sandbox snapshot
→ leaving this pillar ends the interaction session
```

Desktop may reveal previous/next controls on hover. Mobile must expose the same
operation on tap; no essential control may depend on hover.

There is no separate edit mode button or finish command. On touch devices, a
tap focuses the pillar and exposes the same controls; tapping another pillar or
outside ends the current session.

### 7.2 Month and Hour

Month and Hour are selected only as complete pillars:

```text
resolved Year stem → 12 legal Month pillars
resolved Day stem  → 12 legal Hour pillars
```

Their stem and branch are not independently edited because their stems are
dependent results. A parent change refreshes the dependent candidate set. It
does not silently finalize one candidate if the target is ambiguous.

### 7.3 Full flow

```text
Choose 乾造 / 坤造
→ edit the target draft through visible six-pillar nodes
→ globally solve Year/Month/Day/Hour constraints
→ return zero, one, or many complete legal variants
→ render the unique/selected variant immediately
→ derive DaYun direction and structural sequence
→ choose a cycle-year anchor if exact timing is needed
→ reverse-check complete pillars against real calendar candidates
→ only then locate exact start age and current DaYun
→ choose one Gregorian year from a dropdown; close and derive its annual Jiazi immediately
```

No field accepts free text. Search may filter a closed legal list, but cannot
create a new value.

No ordinary successful single-result edit needs a separate Apply page.
Explicit choice is required only when the solver returns multiple complete
candidates.

### Dependency invalidation

| Change | Immediate effect |
| --- | --- |
| Year target changes | refresh legal month targets; invalidate incompatible year anchor and timing |
| Month target changes | invalidate DaYun sequence and exact timing until global compile succeeds |
| Day target changes | refresh legal hour targets; invalidate exact timing |
| Hour changes | invalidate exact timing |
| Annual changes | recompute only the temporal overlay; natal chart and DaYun remain unchanged |

The UI may suggest a compatible counterpart or dependent branch, but target
intent and the last compiled snapshot remain separate until the solver
succeeds. The visible scene never contains an incomplete or illegal pillar.

## 8. Required Contracts

```yaml
PillarTargetDraft:
  draft_id:
  base_snapshot_id:
  mode: structural | calendar_resolution
  gender: male | female | unknown
  desired:
    year_pillar:
    month_pillar:
    day_pillar:
    hour_pillar:
  pillar_edit_session:
    slot: year | day | null
    anchor_component: stem | branch | null
    anchor_value:
    counterpart_component: stem | branch | null
    counterpart_value:
    legal_counterpart_values: []
    preview_pillar:
  sexagenary_year_anchor:
  actual_birth_year_candidate:
  annual_observation:
    gregorian_year:
    derived_pillar:
    temporal_source_ref:
  late_zi_sect:
  real_datetime_anchor:

ChartConstraintResolution:
  status: incomplete | conflict | unique | multiple
  target_draft_id:
  legal_variants: []
  conflict_reasons: []
  invalidated_anchor_reasons: []
  compiler_version:
  source_refs: []

CompiledSandboxSnapshot:
  snapshot_id:
  target_draft_id:
  selected_variant_ref:
  pillars: []
  structural_validity: valid
  calendar_resolution_status:
  formal_state_writes: false

CandidateSet:
  target_slot: year | month | day | hour
  parent_slot: year | day | null
  parent_value:
  candidates:
  compiler_version:
  source_refs:

DaYunDerivation:
  direction:
  direction_basis:
  sequence:
  sequence_status:
  exact_timing_status:
  real_datetime_candidates:
  start_time:
  start_age:
  limitations:
```

## 9. Current Implementation Audit

R1 v6 replaces the former manual composition UI with one automatic editing
session. The browser consumes only server-owned catalogs; every complete target
is sent to the deterministic server solver before replacing the visible
Sandbox scene.

| Current behavior | Finding | Required correction |
| --- | --- | --- |
| Year and day candidate sets | implemented | 60 closed Jiazi choices each |
| Month and hour dependency | implemented | server emits 12 legal dependent whole pillars |
| Automatic first-operation anchor | implemented and browser verified | passive marker; no manual lock or finish control |
| Global target reachability | implemented | server target solver compiles the complete target |
| Gender / chart-type authority | implemented | explicit 乾/坤; unknown blocks DaYun |
| Structural DaYun sequence | implemented | recomputed from explicit gender, year polarity and month pillar |
| Exact DaYun age window | conditionally implemented | only resolved calendar candidates may locate timing |
| Current DaYun | implemented or explicitly unavailable | never defaults to sequence index zero |
| Pillar interaction | implemented | complete legal targets render immediately |
| Year anchor semantics | implemented | sexagenary anchor remains separate from real birth datetime |
| Annual observation | implemented | one Gregorian-year dropdown; derived Jiazi; no confirmation layer |
| Request ordering | implemented | latest structural intent wins; stale responses cannot overwrite it |
| Undo / redo | implemented | compiled Annual and pillar changes enter Sandbox history |

The v6 tests replace the prior local-cascade assumptions. Human usability and
professional product review remain outside machine verification.

## 10. Machine Gate for v6

### Candidate correctness

1. All 60 year pillars are present once in canonical order.
2. Every year pillar produces exactly 12 unique legal month pillars.
3. All 60 day pillars are present once in canonical order.
4. Every day pillar produces exactly 12 unique legal hour pillars.
5. No candidate is generated in browser code.

### State correctness

6. A stem-first edit session offers exactly six legal branch counterparts.
7. A branch-first edit session offers exactly five legal stem counterparts.
8. Every visible edit-session preview is a complete legal Jiazi.
9. Target reachability is independent of edit order.
10. Changing year refreshes month constraints and invalidates incompatible
    anchors explicitly.
11. Changing day refreshes hour constraints and exact timing explicitly.
12. Annual input is a single closed Gregorian-year dropdown, closes after one
    selection, and never mutates natal pillars.
13. DaYun is never user-editable.
14. Structural, calendar-resolved and active-DaYun validity are distinct.

### Epistemic correctness

15. A structural combination is always marked hypothetical.
16. Exact DaYun timing is absent without a consistent calendar candidate.
17. Reverse lookup supports zero, one and multiple candidate outcomes.
18. Cycle-year anchor and actual Gregorian birth year are never conflated.
19. No formal LifeCase or ChartVersion write occurs.

### UX correctness

20. Year/day target selection takes no more than four primary operations.
21. Month/hour selection takes no more than two primary operations after its
    parent is chosen.
22. Desktop and 390px mobile expose the same legal candidates and dependency
    state.
23. Unknown gender produces no direction, sequence or DaYun nodes.
24. 乾造 and 坤造 with the same pillars produce the correct opposite direction.
25. Gender changes never mutate the natal four pillars or formal LifeCase.
26. A unique legal solver result immediately becomes the rendered Sandbox state.
27. Multiple legal solver results require explicit candidate choice.
28. The passive anchor is established by the first actual step, never by hover;
    it clears when the user leaves the pillar, focuses another pillar or presses
    Escape.
29. No edit, finish or manual lock-switch button exists in the rendered UI.
30. `1977 · 丁巳 乙巳 乙丑 乙酉 · 乾造 · 2026` resolves to `庚子 2018–2027`.
31. Without a real calendar anchor, the first sequence item is never labeled current.

## 11. Research Sources

Primary implementation references:

- [`lunar-python` official repository](https://github.com/6tail/lunar-python)
- [`Lunar.py`: exact LiChun/Jie month calculation and Five-Rats hour formula](https://github.com/6tail/lunar-python/blob/master/lunar_python/Lunar.py)
- [`Solar.py`: reverse lookup from four pillars to real datetime](https://github.com/6tail/lunar-python/blob/master/lunar_python/Solar.py)
- [`Yun.py`: direction and start-luck calculation](https://github.com/6tail/lunar-python/blob/master/lunar_python/eightchar/Yun.py)
- [`DaYun.py`: sequence from the month pillar](https://github.com/6tail/lunar-python/blob/master/lunar_python/eightchar/DaYun.py)
- [`6tail` official GanZhi documentation](https://6tail.cn/calendar/lunar.ganzhi.html)
- [`Tyme` official ChildLimit and DaYun documentation](https://6tail.cn/tyme.html)

## 12. Decision

The R1 calendar catalogs and DaYun authority correction remain valuable, but
the local-cascade interaction is superseded:

```text
temporary glyph lock with globally solved complete targets;
separate sexagenary anchor and real Gregorian birth candidate;
explicit 乾造 / 坤造 authority;
structural-sequence / exact-timing separation;
calendar-consistent current-DaYun reverse lookup;
unknown gender never invents DaYun.
```

Implementation and machine verification are complete. Human product review is
pending. R2-R6, Relation Atlas, Reasoner, LifeCase, LLM, TTS and production
deployment remain outside this correction.
