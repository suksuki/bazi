# V50 OneCanvas Refinement R1 Implementation Design

> Revision 2026-07-19 (automatic first-operation anchor): Year and Day no
> longer expose an edit button, finish button or manual lock switch. Hover or
> focus only reveals local previous/next controls. The first actual step on a
> stem or branch establishes that component as the session anchor; the other
> component is kept inside its server-owned legal counterpart set. Every step
> compiles a complete legal target immediately. Leaving the pillar, focusing a
> different pillar, tapping outside or pressing Escape ends the session.

> Superseded revision 2026-07-19 (WYSIWYG composition): Year and Day use node-local
> previous/next controls as a two-part composition gesture. The first changed
> glyph is temporarily locked; the other glyph is constrained to compatible
> counterparts. Month and Hour select a complete dependent pillar, Annual
> selects one Gregorian year, and DaYun remains derived. Every completed target
> is validated and compiled by the server before it replaces the Sandbox.

> Revision 2026-07-19: the retained-branch dependency model described in the
> prior revision is also superseded. Month and hour are dependent **choice
> sets** of 12 legal pillars, not non-editable linked results. DaYun sequence
> and exact timing are separate authorities. See
> `V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md`.

> Revision 2026-07-18: the nearby-date `calendar_valid` candidate model in
> this original R1 design is superseded by
> archived `../archive/product/V50_ONECANVAS_PILLAR_DEPENDENCY_MODEL_V1.md`. R1 now exposes year/day as
> complete 60-Jiazi choice axes; month/hour are deterministic linked results.
> All other formal-state, renderer-authority and release boundaries remain in
> force.

## 1. Authorization

```yaml
slice: OneCanvas Refinement R1
name: Authority and Constrained Selection
status: implemented_machine_verified
authorized_scope: R1_only
r2_to_r6_authorized: false
full_c2_authorized: false
production_deployment: false
```

Machine implementation is now complete. This authorization header remains the
scope contract; completion and gate results are recorded separately in section
10 so machine success cannot silently become product approval.

R1 answers one product question:

> Can a user create a structurally legal experiment, understand each immediate
> linked change and distinguish editable inputs from derived timing results?

It does not add path guidance, root/reveal visualization, temporal flow,
path assessment or new Xiang/Theater behavior.

## 2. Authority Chain

```text
PillarTargetDraft
  desired four pillars
  optional automatic pillar edit session
        ↓
server-owned closed candidate catalog
        ↓
year/day legal first-operation anchor or month/hour dependent whole-pillar choice
        ↓
server target solver compiles the complete four-pillar structural state
        ↓
immediate Sandbox Snapshot replacement
        ↓
relations, Graph candidate, timing recalculation and Diff
```

The browser may conduct the automatic first-operation anchor session using the
server-provided counterpart catalog. It may not generate that catalog, declare
the result legal, infer a dependent pillar, or silently select a server result.

## 3. Formal and Experimental State

```yaml
formal_chart:
  source: ChartVersion
  mutable: false

experimental_chart:
  source: server_compiled_structural_state
  write_target: local_sandbox_snapshot
  writes_chart_version: false
  writes_life_case: false
```

Selecting an experimental pillar means defining a target intent. The browser
may prepare a complete legal preview from the closed catalog, but only a target
accepted by the server becomes the visible experimental world. No incomplete
pillar is ever rendered as a chart state.

## 4. Selection Disclosure

After each immediate Sandbox selection, the user sees the updated six-pillar
world itself. Additional disclosure remains available without interrupting the
selection:

```text
complete four pillars
changed and linked slots
DaYun derived / unresolved state
current annual observation
source and constraint details on inspection
```

The production contract supports full Gregorian date and time. Structural
OneCanvas does not invent those facts when only a GanZhi target is available.
The anonymized review Fixture must not contain raw birth date or time.

There is no pillar-level confirmation command and no hidden preview world.
Undo, redo and restore provide correction. A birth-year reverse lookup may
contain multiple private datetime candidates; they resolve the current DaYun
only when their current-DaYun signatures agree. The UI never silently chooses
a real birth datetime for the user.

## 5. Luck and Annual Time

### Luck

```text
luck sequence: derived, never editable
observed luck: switchable only among compiled sequence entries
```

R1 must distinguish:

```text
recalculated_changed
recalculated_unchanged
recalculation_unavailable
```

When a non-current luck period lacks a compiled temporal path effect, the UI may
show the selected period as observation context but may not invent relations or
path changes.

### Annual signal

Annual selection is identified by Gregorian year first and GanZhi second:

```text
2026 · 丙午
```

Changing the observed year or luck period updates volatile observation state.
It may be used while viewing either the formal chart or an experimental chart;
it does not mutate ChartVersion, LifeCase or the experimental natal pillars and
does not fabricate a typed temporal path effect.

## 6. R1 User Task

```text
1. Open the formal chart.
2. Select a natal glyph.
3. Use previous or next once; Sandbox is created automatically.
4. See the complete legal pillar and all linked slots update in place.
5. Read luck recalculation status.
6. Step through the derived luck sequence without editing it.
7. Step the observed Gregorian annual year; GanZhi remains derived.
8. Undo, redo or restore the formal baseline.
```

Target interaction counts:

```text
step to an adjacent legal year/hour value: 2 primary actions on touch, 1 on desktop hover
repeat adjacent steps without reopening a panel: 1 primary action each
restore formal baseline: 1 primary action
```

## 7. Missing-data Behavior

```text
illegal year/month or day/hour combination
→ server rejects it; the browser cannot construct it from closed selectors

zero reverse-lookup matches
→ retain structural sequence but leave exact timing and current DaYun unresolved

multiple reverse-lookup matches with different current-DaYun signatures
→ leave current DaYun unresolved; never silently select a birth datetime

luck unavailable
→ show recalculation_unavailable and reason; do not show a synthetic sequence

candidate lacks full calendar disclosure because review data is anonymized
→ show anonymized relative context and inherited timezone policy
```

The authoritative human gate protocol is
`V50_ONECANVAS_R1_UNGUIDED_HUMAN_PRODUCT_REVIEW_V1.md`.

## 8. Machine Gate

```yaml
authority:
  formal_chart_mutated: false
  luck_directly_editable: false
  frontend_calendar_inference: false

legal_selection:
  candidates_from_solver_output: true
  browser_generated_candidate: false
  immediate_sandbox_compile: true
  separate_pillar_confirmation: false
  dependent_cascade_visible: true

recomputation:
  changed_explicit: true
  unchanged_explicit: true
  unavailable_explicit: true
  unavailable_result_fabricated: false

components:
  stable_semantic_ref: true
  ui_intents_only: true
  reasoner_imports: false
  fixed_layer_order: true
  visual_tokens_externalized: true

responsive:
  desktop_supported: true
  mobile_390_supported: true
  keyboard_selection_supported: true
  free_text_pillar_candidate_input: false
```

## 9. Product Gate

R1 machine success does not pass the product gate. The review must establish
that a first-time user can tell:

1. the formal chart is protected;
2. selecting a value immediately changes only the complete experimental world;
3. linked pillar changes are visible on the same canvas;
4. luck was recalculated and whether it changed;
5. luck is derived rather than editable;
6. annual year is observation context rather than a natal edit.

## 10. Implementation Outcome

### 10.1 Typography-node refinement

The six-pillar surface now treats stems and branches as typography rather than
round cards. Arrow controls remain inside each control's continuous hit area,
so moving from a glyph to an arrow cannot collapse the operation. Month, Hour
and DaYun expose one whole-pillar stepper pair instead of duplicating controls
on both stem and branch. This is a presentation and interaction refinement only;
calendar authority, target compilation and formal-state boundaries are unchanged.
The glyph keeps its Five-Element hue, while Yang uses a firmer weight and solid
baseline and Yin uses a lighter weight and broken baseline. Polarity therefore
remains readable without inventing a second color code or relying on color alone.

```yaml
implementation: COMPLETE
machine_gate: PASS
analyst_product_gate: PENDING
full_c2: BLOCKED
production_deployment: BLOCKED

verification:
  focused_tests: 44_passed
  full_regression: 381_passed
  browser_console_errors: 0
  browser_console_warnings: 0
  desktop_visual_check_1440x1000: PASS
  mobile_visual_check_390x844: PASS
  mobile_horizontal_overflow: false
  annual_catalog_count: 201

protected_boundaries:
  formal_chart_writes: false
  life_case_writes: false
  reasoner_modified: false
  runtime_modified: false
  llm_used: false
  r2_to_r6_implemented: false
```

The machine result proves authority separation, globally solved target
composition, derived timing behavior, component boundaries and responsive rendering. It does
not prove that first-time users understand the workflow. That decision remains
with the task-based analyst and human review packet.
