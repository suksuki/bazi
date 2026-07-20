# V50 OneCanvas R1 v5 Unguided Human Review

```yaml
status: READY_FOR_UNGUIDED_EXECUTION
machine_prerequisite: PASS
product_projection: ZERO_ONE_MANY_EXPOSED
review_build: V6_HASH_LOCKED
professional_analysts: 2
first_time_users: 5
desktop: all_tasks
mobile_390px: core_tasks
verbal_guidance: forbidden
production_deployment: blocked
```

## 1. Question

Can a first-time user change a Sandbox chart safely and understand:

```text
what they requested
what the global solver resolved
what the temporal service derived
what never changed the formal chart
```

This is not a review of paths, Relation Atlas, Xiangfa, Theater or professional
Mingli accuracy.

### Preparation resolution

The 2026-07-20 dry run found that the active surface reduced the Solver to its
single-result path. The v6 review build closes that product projection gap:

```text
single solution   → apply the server-selected complete chart
many solutions    → show complete variants; require explicit selection
no solution       → show conflict and server-provided release choices
cancel            → preserve the current chart
```

The browser does not calculate legality, rank candidates or fabricate fallback
charts. Tasks 4 and 5 are now executable. The build lock and evidence are in
`reports/mingli-onecanvas-r1/review-v6-ready/`.

Internal task routes:

```text
/experience-static/active/onecanvas-r1/index.html?r1ReviewTask=4
/experience-static/active/onecanvas-r1/index.html?r1ReviewTask=5
```

## 2. Frozen Authority Model

```text
formal chart     immutable
Sandbox          editable and disposable
year / day       first-operated stem or branch anchors a TargetDraft gesture
month / hour     whole-pillar choices from server-owned legal candidate sets
birth year       Gregorian anchor compatible with the resolved year pillar
annual           Gregorian observation year only
DaYun            derived only; never editable
```

Every effective edit is server compiled. Browser preview and animation are not
chart facts.

## 3. Scenarios

Prepare four anonymized or consented fixtures:

| Scenario | Required temporal result |
|---|---|
| A | `recalculated_unchanged` |
| B | `recalculated_changed` |
| C | `recalculation_unavailable` because gender is unknown |
| D | structurally valid sequence but no active DaYun because no compatible real-time anchor exists |

Fixtures must be machine checked before a participant session. Do not retain
names, raw birth datetimes, locations or conversation text in review records.

## 4. Unguided Tasks

### Task 1 — Formal versus experiment

Prompt: “Create a version you can change without changing the formal chart.”

Pass: participant enters Sandbox, can return to formal, and does not believe A/B
save writes LifeCase.

### Task 2 — Year, stem first

Prompt: “Reach the specified legal year pillar by changing the stem first.”

Pass: first action anchors the stem, counterpart choices stay legal, effective
result arrives from server compile, and no explicit lock-management lesson is
needed.

### Task 3 — Year, branch first

Repeat with the branch first. The final target must be the same as Task 2 when
the requested constraints are the same. Record confusion, retries and whether
the user understands the anchor is temporary UI intent.

### Task 4 — Multiple legal solutions

Prompt: “This target has more than one legal complete chart. Inspect the
differences and choose one explicitly.”

Pass: all candidates come from `ChartResolution`, no candidate is silently
selected, presentation order is not described as professional ranking, and the
chosen complete variant is clearly distinguished from the draft.

### Task 5 — No solution and constraint release

Prompt: “Reach the requested target, or explain why it cannot be reached under
the current constraints and release one conflicting constraint.”

Pass: the participant can see the conflict, identify a server-provided
releasable constraint, change or release it, and does not see a fabricated chart
or generic failure message.

### Task 6 — Dependent month and hour

Prompt: “Select the specified month pillar, then the specified hour pillar.”

Pass: participant uses whole-pillar previous/next controls, sees only twelve
legal choices for the current year/day, and does not try to edit their glyphs
independently.

### Task 7 — Day edit and linked candidate set

Prompt: “Change the day pillar, then explain what happened to the available
hour choices.”

Pass: participant distinguishes selected day from server-constrained hour set.

### Task 8 — Birth-year anchor

Prompt: “Choose the specified birth year for the current year pillar.”

Pass: only compatible Gregorian years are shown; an incompatible prior anchor
is visibly invalidated; the participant does not confuse birth-year anchor with
annual observation.

### Task 9 — Gender and DaYun

Start with unknown gender, then choose Qian and Kun in separate runs.

Required understanding:

```text
natal pillars do not change
direction and sequence are recomputed
unknown gender never reuses old DaYun
DaYun cannot be manually edited
```

### Task 10 — Three DaYun outcomes

Across scenarios A–D ask:

```text
Did the system calculate?
Did the result change?
Is the active DaYun actually resolved?
Why or why not?
```

### Task 11 — Annual observation

Prompt: “Observe the specified Gregorian year.”

Pass: participant selects one year once; Jiazi is understood as derived display,
not an editable natal pillar or DaYun input.

### Task 12 — Undo, redo and reset

Make two changes, undo, redo, reset, and return to formal. Formal state must be
unchanged throughout.

### Task 13 — 390px mobile core flow

First-time users repeat Tasks 1, 6, 9, 11 and 12 on a 390px viewport. Controls
must be operable without hover and without horizontal loss of semantic slots.

## 5. Zero-tolerance Authority Failures

Any one blocks R1:

```text
participant believes formal chart was edited
participant believes DaYun is directly editable
participant believes annual year determines DaYun sequence
unknown gender displays or inherits an old DaYun
multiple solutions are silently committed
invalid chart is assembled in the browser
Sandbox writes ChartVersion or LifeCase
hidden or filtered facts reappear in client state
```

## 6. Task Thresholds

```yaml
first_time_users:
  create_experiment_without_help: 4_of_5
  complete_year_target_without_help: 4_of_5
  explicitly_choose_multiple_solution: 4_of_5
  understand_and_release_no_solution_constraint: 4_of_5
  complete_month_and_hour_without_help: 4_of_5
  distinguish_birth_year_from_annual: 4_of_5
  undo_and_restore_without_help: 4_of_5
  know_dayun_is_not_editable: 5_of_5
  know_formal_chart_is_unchanged: 5_of_5
  know_unknown_gender_has_no_trusted_dayun: 5_of_5

analysts:
  legal_candidates: unanimous
  qian_kun_direction: unanimous
  no_stale_dayun: unanimous
  temporal_three_levels: unanimous
  sandbox_authority: unanimous
```

## 7. Record

One structured record per participant:

```yaml
participant_type: analyst | first_time_user
device: desktop | mobile_390px
tasks_completed: []
completion_time_seconds: {}
misclicks: {}
verbal_help_required: false
authority_misunderstandings: []
observed_blockers: []
key_quotes: []
```

Retain task recordings and screenshots only under consent and anonymization.

## 8. Issue Routing

```text
P0 authority / calendar defect → failing fixture → L2 correction → full regression
P1 task cannot complete       → R1 interaction rework
P2 copy / hierarchy / touch   → R1 presentation fix
P3 relation / path / Xiangfa  → backlog; never expand R1
```

Passing R1 authorizes a separate decision on RA1. It does not authorize RA1,
full C2 or production by itself.
