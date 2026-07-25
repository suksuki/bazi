# OneCanvas Selection and Path Finishing Patch v1

> Revision 2026-07-19: the sentence below saying month and hour are
> non-editable is superseded by
> `V50_ONECANVAS_PILLAR_SELECTION_AND_DAYUN_ALGORITHM_V2.md`. The interaction
> remains closed-list selection, but month/hour each expose 12 compiler-issued
> candidates after year/day is selected.

> Selection revision: the closed-select and explicit-confirm interaction is
> retained, but the five nearby-date candidates described below are superseded
> by archived `../archive/product/V50_ONECANVAS_PILLAR_DEPENDENCY_MODEL_V1.md`. The select now contains all
> 60 Jiazi for year or day; month and hour are linked, non-editable results.

Date: 2026-07-18  
Status: implemented interaction refinement

## 1. Purpose

This patch addresses two narrow usability issues without changing Mingli
authority or authorizing full R2.

```text
natal pillar candidate selection
→ controlled dropdown of Solver-returned complete chart variants

existing PathDraft interaction
→ continuous node selection with explicit, discoverable finish actions
```

## 2. Pillar Candidate Selection

The natal-pillar editor no longer exposes a free-text search field. It renders a
native select whose options are the complete candidates already returned by the
Calendar Constraint Solver.

```yaml
free_text_candidate_input: false
browser_constructs_candidate: false
candidate_source: precompiled_calendar_constraint_solver
complete_variant_preview: required
explicit_confirmation: required
```

Changing the dropdown only previews the complete candidate. It does not commit
until the user confirms the full variant and its linked changes.

## 3. Path Finishing

The existing single PathDraft remains a continuous ordered node sequence. This
patch adds no path recommendation, relation inference or professional path
assessment.

While drawing, the user can finish by:

```text
reselecting the current endpoint
clicking “完成路径”
pressing Enter
pressing Escape
```

After finishing, the draft remains visible. “继续画线” resumes from the current
endpoint. Clearing remains a separate explicit action.

The endpoint receives a restrained breathing ring and the Canvas displays a
short drawing-status cue. Reduced-motion rules continue to apply.

## 4. Boundary

```yaml
new_mingli_reasoning: false
new_relation_inference: false
path_guidance: false
path_assessment: false
formal_state_write: false
life_case_write: false
r2_product_gate: still_blocked
production_deployment: blocked
```

Full R2 still owns legal-target guidance, segment-level explanation, path
branching and professional assessment. This patch only makes the already
present draft interaction unambiguous.
