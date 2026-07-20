# V50 C1 Time Structure Lens Product Redesign

## 1. Objective

The C1 user experience must help a person answer three questions:

```text
What is the chart's primary formal structure?
What changed when the luck period or year entered?
Why is that change shown?
```

It must not expose the Canvas contract as the product interface.

## 2. Frozen Boundary

```yaml
existing_renderer: retained_as_internal_inspector
user_product: redesign_required
new_mingli_judgment: forbidden
frontend_semantic_inference: forbidden
contract_changes: fixture_first_only
production_deployment: blocked
c2_temporal_sandbox: blocked
```

All three prototypes consume the same role-projected `MingliCanvasSpec`,
`CanvasDiffSpec` and `CanvasContextPack`. They differ only in information
architecture, interaction rhythm and visual composition.

## 3. Current Real-data Constraint

The local formal dataset currently provides:

```yaml
records_with_life_case_field: 16
formal_cases_renderable_by_c1: 6
cases_with_uniquely_resolved_committed_path: 4
renderable_cases_without_typed_visual_path: 2
cases_without_formal_baseline: 10
formal_temporal_path_updates:
  activated: 0
  reinforced: 0
  weakened: 0
  blocked: 0
  reopened: 0
```

The six renderable cases currently support formal time-pillar introduction and
contract-level path `unchanged`; they do not support a formal claim that a path
was activated, reinforced, blocked or reopened.

Therefore prototypes must not invent those states. To test those experiences
with real LifeCases, an analyst must first select and formally commit at least:

- one case with a typed luck-period path change;
- one case with a typed annual `blocked` or `reopened` change.

This is a professional data-preparation task, not a Renderer shortcut.

## 4. Shared Product Grammar

### Primary hierarchy

```text
Current time and one-sentence change
        ↓
One committed path
        ↓
Up to three formal changes
        ↓
Why / source / epistemic status
        ↓
Compact six-pillar coordinates
        ↓
Professional Inspector, on demand
```

### Visual semantics

```text
deep ink       committed structure
vermilion      current temporal trigger
soft ghost     previous stage
dashed line    candidate
terminal mark  blocked
open joint     reopened
```

The palette encodes status, not fortune or strength. No red/green destiny
score and no uncalibrated percentages are allowed.

### Progressive disclosure

- No full relation web on entry.
- Relation labels appear only for the focused path or selected relation.
- Supporting evidence unfolds step by step.
- Candidate and blocked objects require an explicit professional-layer action.
- The full generation/control graph remains in the internal Inspector.

## 5. Prototype A — Temporal Story

### Product idea

Treat natal chart, luck period and year as three acts. Each act introduces only
the change supplied by its formal Diff.

```text
Act 1: The natal structure is established
Act 2: The luck pillar enters
Act 3: The annual pillar enters
```

### First screen

```text
2026 丙午 · 时间结构

This year formally adds the 丙午 time position.
The committed natal path remains unchanged at the current evidence level.

[Play the three stages]  [Why no stronger conclusion?]
```

### Interaction

- Tap next/previous or scrub a three-stop timeline.
- New nodes enter from the time edge.
- Previous state remains as a low-opacity trace.
- Only formal Diff items animate.
- Abu explains one sentence per act from the current Context Pack.

### Best for

Ordinary users, teaching introductions and narration.

### Risk

Narrative motion can imply causality. Every act must preserve the distinction
between “a time pillar entered” and “a professional temporal effect was
committed.”

## 6. Prototype B — Path Focus

### Product idea

Place the committed path at the center. Pillars become compact source anchors
around it rather than six equal cards.

```text
source node → transformation node → target node
```

### First screen

```text
The path currently worth understanding

[source] ── [mechanism] ── [target]

Supported by: 2 formal relations
Current temporal status: unchanged at the contract level
```

### Interaction

- Select a path step to reveal its source pillar and typed evidence.
- Switch natal/luck/year while keeping the path spatially stable.
- Show only the affected segment when a formal temporal change exists.
- Open “professional structure” for the complete Inspector.

### Best for

Users who want to understand how a conclusion is formed and practitioners who
need a fast main-line view.

### Risk

Some formal cases have no uniquely mapped path. The prototype must present a
clear unavailable state rather than constructing one from prose.

## 7. Prototype C — Before/After Compare

### Product idea

Compare two stages directly, with the Diff as the center of the composition.

```text
Before                 Change                 After
Natal or luck      introduced / ...       Luck or year
```

### First screen

```text
Luck → 2026 丙午

Before: five formal pillars
Change: 丙 and 午 introduced
After: six formal pillars

Committed path: no formal status change
```

### Interaction

- Toggle natal/luck, luck/year or natal/year.
- Added objects appear in vermilion.
- Removed objects leave a short-lived ghost only when the formal Diff says
  `removed`.
- Selecting a change focuses the exact source refs and explanation.

### Best for

Professional comparison, research review and users who prefer direct evidence
over narrative playback.

### Risk

Side-by-side layouts become cramped on mobile. Mobile uses a vertical
before/change/after stack rather than two compressed canvases.

## 8. Real-case Prototype Set

The first review packet should use anonymized IDs only.

```yaml
prototype_case_1:
  requirement: committed path resolves uniquely
  purpose: compare all three concepts on the same valid main path

prototype_case_2:
  requirement: renderable formal case without a typed visual path
  purpose: test honest unavailable-path presentation

prototype_case_3:
  requirement: formal baseline unavailable
  purpose: test refusal clarity and safe next action
```

This set can be produced immediately from current data. A second review set for
`activated / blocked / reopened` must wait for formally committed real temporal
examples.

## 9. Clickable Prototype Deliverables

Each concept must include desktop and 390px mobile flows for:

1. entering the time structure;
2. moving through natal, luck and year;
3. identifying one primary path;
4. opening one change explanation;
5. opening source/epistemic status;
6. handling missing typed path;
7. handling missing formal baseline;
8. opening the internal professional Inspector without confusing it with the
   default user view.

The prototypes are review artifacts only. They do not write formal state, call
an LLM, add temporal judgment or ship to production.

## 10. Review Tasks

### Task A — Identify the structure

Without reading raw JSON, the reviewer can state the committed primary path and
distinguish it from supporting relations.

### Task B — Identify the temporal change

The reviewer can state what was introduced and whether any path change was
formally committed.

### Task C — Find the reason

The reviewer can select an object or change and explain its source, stage and
epistemic status.

### Task D — Understand refusal

The reviewer understands that unavailable visualization means insufficient
formal baseline, not a system crash.

## 11. Prototype Gate

Only one of three decisions is allowed:

```text
PASS
PASS WITH PRESENTATION FIXES
FAIL — CONTRACT DEFECT FOUND
```

Selection criteria:

```yaml
utility:
  primary_question_answered_within_first_screen: required
  one_primary_path_identifiable: required
  temporal_change_identifiable: required

comprehension:
  fact_candidate_committed_blocked_not_confused: required
  source_and_reason_recoverable: required
  refusal_state_understandable: required

design:
  visual_hierarchy_clear: required
  desktop_composition_coherent: required
  mobile_composition_coherent: required
  deepbazi_visual_identity_present: required

boundary:
  no_new_mingli_judgment: required
  no_frontend_semantic_inference: required
  no_formal_writes: required
```

Passing the prototype gate authorizes one chosen direction for C1 user-product
implementation. It does not authorize C2.
