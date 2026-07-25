# V50 OneCanvas R1 Unguided Human Product Review v1

```yaml
status: SUPERSEDED_BY_R1_V5_PROTOCOL
frozen_at: 2026-07-19
r1_implementation: COMPLETE
r1_machine_gate: PASS
r1_human_product_gate: PENDING
relation_atlas_implementation: BLOCKED_PENDING_R1
assisted_path_drawing: BLOCKED
production_deployment: BLOCKED
```

> Do not execute this v1 human protocol. R1 v5 machine verification is now
> complete, and the executable protocol is
> `V50_ONECANVAS_R1_V5_UNGUIDED_REVIEW_PROTOCOL.md`. This file remains only as
> design history. The architecture audit found
> that local pillar cascades are order-dependent and cannot guarantee a target
> four-pillar chart. The current interaction contract is now defined by
> `V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md` (document title
> v5): Year and Day use temporary two-glyph composition locks, Month and Hour
> use dependent whole-pillar choices, and Annual accepts a Gregorian year only.
> A revised human protocol is required after that behavior is implemented and
> machine-verified.

## 0. Purpose

R1 has already proved machine authority and calendar constraints. This review
answers one remaining question:

> Can a first-time user safely operate the WYSIWYG six-pillar experiment and
> understand what they changed, what the system derived, and what never changed
> the formal chart?

This is a product and human-understanding gate. It is not a review of Relation
Atlas, work-path assistance, root/reveal visualization, Xiangfa or Theater.

## 1. Frozen Interaction Contract

The current R1 interaction is WYSIWYG:

```text
choose a closed legal value
        ↓
server compiler validates and recompiles
        ↓
the Sandbox six-pillar scene updates immediately
        ↓
undo / redo / reset provide correction
```

There is no second preview chart and no pillar-level Apply or Confirm command.
Immediate update is safe because it writes only the local Sandbox snapshot.

The six slots do not share one authority model:

```text
birth year + year pillar  closed joint calendar-backed choice
month pillar              12 legal choices dependent on year stem
day pillar                60 independent Jiazi choices
hour pillar               12 legal choices dependent on day stem
annual year               independent observation by Gregorian year
DaYun                     derived result, never directly editable
```

## 2. Corrections to the Earlier Review Draft

The analyst goals are retained, but three old-flow tasks must not be brought
back into R1.

### 2.1 Preview and confirmation

Old wording such as "preview candidate" and "confirm candidate" is replaced
by:

```text
select legal value
→ immediate Sandbox update
→ inspect cascade and recomputation disclosure
→ undo or reset when needed
```

The review checks whether immediate state and authority are understandable. It
must not ask the team to recreate a shadow preview state.

### 2.2 Multiple reverse-lookup dates

An absolute birth year plus four pillars can reverse-resolve to zero, one or
multiple real datetimes. R1 uses those private candidates only to locate the
current DaYun when every candidate produces the same current-DaYun signature.

```text
all candidates agree
→ current DaYun may be resolved

candidates disagree or no candidate exists
→ current DaYun remains unresolved
```

The user is not asked to choose a real birth datetime that the system does not
know. The human task is to understand the unresolved disclosure, not to select
between hidden dates.

### 2.3 Lock conflicts and illegal combinations

R1 does not expose arbitrary pillar locks. Year/month and day/hour use closed
dependent catalogs, so a first-time user cannot construct an illegal pair in
the UI. Server rejection of a tampered illegal payload remains a machine test.

The corresponding human task is instead:

> When the selected birth year and four pillars do not resolve to a consistent
> real datetime, can the user understand why current DaYun is not claimed?

## 3. Participants and Devices

```yaml
professional_analysts: 2
first_time_users: 5
desktop: all_tasks
mobile_390px: core_tasks
verbal_guidance: forbidden
observer_may_read_task_goal: true
observer_may_point_to_controls: false
```

Use synthetic or explicitly consented charts. Review records must not retain
raw names, birth datetimes, locations or conversation text.

## 4. Review Scenarios

Prepare four controlled scenarios before recruiting participants:

| Scenario | Required state | Purpose |
| --- | --- | --- |
| A | formal chart with known gender and resolved current DaYun | baseline and unchanged/changed comparison |
| B | chart type unknown, no DaYun nodes | gender authority and no stale fallback |
| C | birth-year anchored structure with no consistent reverse lookup | honest unresolved state |
| D | birth-year anchored structure whose candidates agree | resolved current DaYun |

All scenarios must carry explicit `formal`, `hypothetical` and temporal source
labels. Scenario fixtures are reviewed separately from participant results.

## 5. Unguided Tasks

### Task 1: Create an experiment

Goal shown to participant:

> Create a version that you can change without changing the formal chart.

Pass evidence:

- participant enters `实验盘` without help;
- participant can identify the protected `正式盘`;
- participant does not believe `存 A / B` writes to LifeCase.

### Task 2: Change a legal hour pillar

Goal:

> Change the hour pillar to the specified legal choice.

Pass evidence:

- opens the hour node or its direct selector;
- sees only the 12 choices allowed by the current day stem;
- selection updates the same canvas immediately;
- understands that DaYun timing may be recomputed or become unresolved.

### Task 3: Change birth year and year pillar

Goal:

> Select the specified Gregorian birth year and year pillar.

Before selection, ask what they expect to change. After selection, ask them to
identify:

```text
active choice       birth year + year pillar
automatic cascade   month stem, while preserving a compatible branch when possible
derived recompute   relations and DaYun resolution
unchanged            day, annual observation and formal chart
```

### Task 4: Change day pillar

Goal:

> Select the specified day pillar and find the linked hour change.

The participant should distinguish the independently selected day from the
dependent hour candidate set and see the updated hour directly on the canvas.

### Task 5: Understand unresolved real-time matching

Use Scenario C. Ask:

```text
Did the system compute a DaYun sequence?
Did it identify the current DaYun?
Why are those answers different?
Did it silently reuse the formal chart's old DaYun?
```

Required answer: structural direction/sequence may exist, while exact timing
and current DaYun remain unresolved; no old result is reused.

### Task 6: Resolve chart type

Start with Scenario B, then select `乾造` and `坤造` in separate runs.

The participant must understand:

- natal four pillars do not change;
- direction and sequence are recalculated;
- chart type is an explicit Sandbox condition;
- unknown chart type never inherits or fabricates DaYun.

### Task 7: Select an annual observation

Goal:

> Observe the specified Gregorian year.

The participant must identify the Gregorian year as the input and its GanZhi as
a calendar-derived display. Annual observation must not be understood as a
natal edit or as an input that generates the DaYun sequence.

### Task 8: Read the three DaYun outcomes

Across prepared scenarios, show:

```text
recalculated_changed
recalculated_unchanged
recalculation_unavailable
```

Ask whether recalculation occurred, whether the result changed, and whether
DaYun can be edited directly.

### Task 9: Undo, redo and restore

After two changes:

```text
undo
redo
restore formal chart
return to experiment
```

Verify that history affects only the Sandbox and that the formal chart remains
byte-for-byte unchanged.

## 6. Mobile Core Tasks

At 390px, every first-time user repeats Tasks 1, 2, 3, 7 and 9. Verify:

- legal options fit without text clipping;
- dependent changes remain visible without horizontal confusion;
- chart type and DaYun disclosure are reachable;
- undo and restore remain one-hand accessible;
- semantic slot identity survives responsive reflow.

## 7. Hard Gate

Any of the following is an automatic R1 failure:

```text
formal chart is believed or observed to be directly mutated
DaYun is believed or observed to be freely editable
annual year is believed to determine the DaYun sequence
unknown chart type exposes an inherited or fabricated DaYun
the browser constructs an illegal year/month or day/hour pair
an unresolved reverse lookup is presented as a resolved current DaYun
an experiment writes ChartVersion or LifeCase
```

First-time-user targets:

```text
4 / 5 complete experiment creation without guidance
4 / 5 complete a legal hour change without guidance
4 / 5 explain year→month and day→hour cascade
4 / 5 complete Gregorian annual observation
4 / 5 complete undo and restore

5 / 5 know DaYun is not directly editable
5 / 5 know the formal chart was not changed
5 / 5 know unknown chart type cannot produce trusted DaYun
```

Both professional analysts must confirm calendar legality, direction, sequence,
no stale DaYun fallback, accurate three-state disclosure and formal/Sandbox
separation.

## 8. Structured Record

Create one record per participant:

```yaml
participant_id:
participant_type: analyst | first_time_user
device: desktop | mobile_390
tasks_completed: []
completion_seconds: {}
misclicks: {}
verbal_help_required: false
authority_misunderstandings: []
key_quotes: []
observed_blockers: []
privacy_reviewed: true
```

Retain task-level screenshots or recordings, but redact raw birth facts and
identity data before analysis.

## 9. Issue Routing

| Class | Meaning | Action |
| --- | --- | --- |
| P0 | authority, calendar or derivation defect | failing Fixture, fix R1/core derivation, full regression |
| P1 | a primary task cannot be completed | interaction rework inside R1, rerun task |
| P2 | copy, hierarchy, touch or responsive defect | targeted R1 fix, rerun affected task |
| P3 | relation, path, root/reveal, timing lens or Xiangfa request | record for Relation Atlas/R2+, do not expand R1 |

## 10. Decision Output

The review closes with exactly one result:

```text
PASS
PASS WITH PRESENTATION FIXES
FAIL — INTERACTION REWORK
FAIL — AUTHORITY OR ALGORITHM DEFECT
```

Only `PASS`, or a completed and rerun `PASS WITH PRESENTATION FIXES`, may
authorize RA1. Human review results must be real; machine tests, screenshots and
internal opinions cannot be substituted for participant evidence.
