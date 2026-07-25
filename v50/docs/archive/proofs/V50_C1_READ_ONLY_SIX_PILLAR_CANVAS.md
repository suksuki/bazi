# V50 C1 Read-only Six-pillar Canvas

## 1. Phase Definition

```yaml
phase: C1 Read-only Six-pillar Canvas
status: product_rework_required
business_scene: formal LifeCase detail
renderer: native TypeScript + SVG
llm_used: false
formal_state_writes: false
sandbox_mutations: false
public_deployment: false
implementation: complete
machine_gate: pass
regression_gate: pass
product_semantic_review: fail
c2_entry: not_approved
```

C1 is the first production-shaped use of the C0 Canvas contracts. It proves
that a real, committed `LifeCase` can be projected into a readable temporal
structure without creating a second Mingli reasoner in the browser.

The user sees one continuous question:

```text
What exists in the natal chart?
        -> What formal luck pillar is now added?
        -> What formal annual pillar is then added?
        -> What changed, and what did not receive a formal judgment?
```

## 2. Authority Chain

```text
BirthInputCanonical / ChartWorldInstance
        +
committed LifeCase / reviewed cognitive record
        +
official timing context
        |
        v
product-side read-only adapter
        |
        v
MingliCanvasCompileInput
        |
        v
C0 deterministic compiler
        |
        v
role-projected Spec / Diff / ContextPack
        |
        v
native TypeScript + SVG renderer
```

The renderer may position, focus, filter approved visual layers and animate
between supplied states. It may not infer a relation, path, epistemic status,
change type or disclosure rule.

## 3. Real Data Rules

### 3.1 Natal chart

The four natal pillars come from the stored canonical birth input and active
chart version. Structural nodes and relations are rebuilt with the existing
deterministic Bazi graph tool. They remain computational structure, not a
professional verdict.

### 3.2 Committed main path

A committed visual path is emitted only when the reviewed cognitive record
contains typed `graph_relation` evidence refs and each ref resolves uniquely
to a deterministic graph edge.

```text
typed evidence refs resolve uniquely -> committed CanvasPath
missing / ambiguous / prose-only refs -> no CanvasPath
```

The adapter must never parse `path_statement`, `transformations` or other
natural-language prose to invent graph edges. The user receives an explicit
availability message when a committed reading has not yet stored a typed
visual path.

### 3.3 Luck and annual pillars

The luck and annual pillars come from `ChartWorldInstance.timing_context` and
its calculation refs. C1 may display these formal calendar positions. It may
not infer their effect on a path unless an existing formal typed temporal
source supplies that change.

For current cases without typed temporal path updates, the honest output is:

```text
luck/year pillar introduced
natal path unchanged at the contract level
temporal effect not yet committed
```

This is not a UI fallback. It is the correct epistemic result.

## 4. Server Disclosure Boundary

Role projection occurs before serialization. Objects filtered for a role must
not appear in:

- the API response;
- stage specs or diffs;
- layer indexes;
- context packs;
- browser state;
- DOM attributes;
- debug output.

Account roles map to Canvas roles as follows:

```text
member          -> member
practitioner    -> practitioner
research_master -> research
admin           -> admin
```

The browser receives only projected data. CSS hiding is not an authorization
mechanism.

## 5. Read-only Experience

The C1 section is embedded in the existing Experience Shell. It contains:

1. a stage control for natal, luck and year;
2. a six-pillar semantic rail;
3. server-approved layer controls for generation/control, combination,
   conflict and committed work paths;
4. an SVG relation surface;
5. a precomputed diff summary;
6. a structured inspection panel backed by `CanvasContextPack`.

The four natal slots are immutable. Responsive reflow or horizontal scrolling
may change visual position but never semantic slot identity.

## 6. C1a Explanation Boundary

C1a does not call an LLM. Clicking an object shows only:

- supplied label and type;
- semantic and epistemic status;
- current stage;
- disclosed source count and optional source refs;
- supplied uncertainty or block reasons;
- supplied change reasons.

Abu natural-language narration is reserved for C1b after object-to-context
binding is proven.

## 7. Failure Policy

```text
contract defect
  -> add a failing C0 fixture
  -> repair Compiler
  -> rerun C0 and C1

real-data adapter gap
  -> fail or degrade explicitly on the server
  -> never patch semantics in Renderer

presentation defect
  -> fix only in C1 Renderer
```

The initial real-data audit found that reviewed `LifeCase` records can contain
an LLM-composed path statement without `candidate_path_refs`. This is not a C0
contract defect. C1 resolves a committed path only through typed
`graph_relation` evidence; prose-only cases remain visibly unavailable.

## 8. Gate

C1 passes only when a real formal case can be loaded and all of the following
are true:

```yaml
renderer_created_semantic_objects: false
filtered_objects_present_anywhere_client_side: false
original_pillars_mutable: false
client_side_diff_inference: false
client_side_relation_inference: false
formal_state_writes: false
sandbox_mutations: false
desktop_supported: true
mobile_supported: true
stage_switching_supported: true
layer_switching_supported: true
selected_object_context_bound: true
```

C1 may close as `partial` if the renderer and safety boundaries pass but the
current formal data cannot provide a typed committed path or typed temporal
effect. That result is evidence for the next data-contract slice, not a reason
to fabricate a green UI.

## 9. Machine Validation Result

The C1 machine gate passed on 2026-07-18:

```yaml
formal_life_cases_found: 16
real_cases_rendered_end_to_end: 6
cases_explicitly_refused_without_formal_baseline: 10
c0_c1_targeted_tests: 12_passed
full_regression: 325_passed
desktop_mobile_visual_evidence: passed
database_state_changed_by_audit: false
production_deployed: false
```

This closes implementation and machine validation only. The subsequent
analyst-product review failed because the faithful Inspector projection does
not yet form a useful, comprehensible or visually resolved user product.

## 10. Product Review Decision

```yaml
review: C1 Analyst-Product Semantic Review
decision: FAIL
resolution: REWORK_REQUIRED
contract_defect_found: false
production_release: blocked
c2_entry: blocked
```

The current Renderer is retained as the internal `Mingli Canvas Inspector`.
It is useful for checking contract output, role disclosure and source traces,
but it must not remain the default user experience.

The user-facing redesign must begin from one question:

> What did this luck period or year actually change?

Its default view may contain one committed path and no more than three formal
changes. Full relation layers belong to the professional Inspector. The next
deliverable is three differentiated clickable product prototypes, not CSS
polish on the existing Inspector.
