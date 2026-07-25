# V50 Mingli OneCanvas Refinement Spec v1

## 1. Current Decision

```yaml
component: Mingli OneCanvas
current_state: direction_validated_refinement_required
primary_object: six_semantic_pillars_and_twelve_nodes
product_model: one_canvas_three_states
implementation_authorized: false
full_c2_authorized: false
production_deployment: false
```

The current prototype has established the correct direction: the six pillars
are the interface. The next phase is refinement, not another redesign and not
another collection of panels.

```text
理：同一画布的语义骨架
象：同一节点的连续视觉映射
时：同一场景上的播放行为
```

`结构 / 时间 / 象` must not return as three pages or three competing top-level
tools. Structure may be a relation layer, Xiang remains a continuous render
axis, and Time remains playback over the current scene.

## 2. Product Goal

Turn the current six-pillar proof into a Mingli operation table on which the
user can complete one understandable task:

```text
选择一个节点
→ 看见哪些关系值得观察
→ 形成或比较一条路径
→ 看见通根、透干和时间引动为何支持或阻断它
→ 在同一张图上理解变化
```

The user must not need a separate Path Studio, Inspector, timing page or Xiang
page to complete this task.

## 3. Frozen Authority

| Object | Authority | User Operation |
| --- | --- | --- |
| Formal natal pillars | Canonical chart facts | Read-only |
| Experimental natal pillars | Calendar-constrained engine candidates | Select in local experiment |
| Luck sequence | Deterministic luck engine | Never hand-edit |
| Observed luck period | Existing calculated sequence | Switch observation only |
| Annual signal | Temporal engine or disclosed hypothetical candidate | Switch in experiment |
| Relations and paths | Canvas Compiler / LifeCase / Graph candidate | Inspect or compare |
| User PathDraft | User draft | Draw without promotion |
| Xiang binding | Disclosed render profile | Change expression only |
| Temporal cues | Precompiled Spec and Diff | Play, pause and inspect |

The frontend does not calculate legal pillars, luck, ten gods, roots, revealed
stems, relations, path closure or temporal activation.

## 4. Refinement Slices

### R1: Authority and constrained selection

Goal: make it immediately clear what can change and what is derived.

- Formal pillars remain immutable.
- Creating an experiment enables only legal candidates.
- Luck uses a locked or `自动推导` treatment.
- Clicking luck opens sequence and observation controls, never an editor.
- Pillar and annual selection use a locally anchored constrained selector.
- Previous/next remains a fast adjustment, with search, keyboard and touch
  navigation added only where the underlying engine can supply legal options.
- A natal change must report whether linked pillars and luck were recalculated
  with changes or recalculated unchanged.

Gate:

```text
No user can mistake luck for a free input.
No illegal GanZhi combination can be created by the client.
No claimed recalculation can be displayed without engine evidence.
```

### R2: Guided path construction

Goal: remove the blank-canvas problem.

Selecting a node puts the scene into an assisted-connect state. Compiler-supplied
targets are visually classified as:

```text
formal_supported
candidate_supported
observable_not_recommended
unsupported
```

- The default mode is assisted drawing.
- Relationship labels explain why a target is available.
- Expert free drawing may create a `user_draft`, but an unsupported segment
  stays visibly broken and never becomes a formal relation.
- `系统建议` may expose an existing committed or candidate path; it may not
  synthesize a new path in the renderer.

Gate:

```text
A first-time user can draw or select one meaningful path without instructions.
Every offered target is traceable to Compiler output.
```

### R3: Root, reveal and local structural expansion

Goal: make `通根` and `透干` visible without creating a spider web.

- Root relation: a light internal connection from a stem to a supporting branch.
- Hidden stems expand only for the selected branch.
- Revealed-stem relation: a light upward connection from a hidden stem to its
  corresponding visible stem.
- Root quality labels are discrete and shown only when the formal contract
  supplies them.
- Default view remains the primary path; selecting a node reveals only its
  local structural neighborhood.

Gate:

```text
Users can identify whether a selected stem is rooted or revealed.
The default canvas does not show all structural relations simultaneously.
```

### R4: Temporal activation and path flow

Goal: make luck and annual signals visibly participate in the same structure.

- Static lines mean a relation exists.
- Directional flow means a currently played path or temporal effect.
- Temporal effects use the existing discrete vocabulary:
  `introduced`, `activated`, `reinforced`, `weakened`, `blocked`, `reopened`.
- Luck and annual nodes point only to compiler-identified affected objects.
- Affected nodes may pulse; path segments may light in deterministic sequence.
- Missing typed temporal evidence remains `unchanged` or undisclosed; animation
  cannot imply an effect.

Gate:

```text
Users can explain what entered, what changed and why a path continued or stopped.
Animation never crosses a missing relation.
```

### R5: Discrete path assessment

Goal: provide useful structural feedback without false precision.

The first assessment vocabulary is:

```text
relationship_continuity
temporal_activation
node_support
obstruction
closure
```

Each dimension uses disclosed discrete states such as:

```text
strong | present | partial | weak | missing | blocked | not_evaluated
```

No energy percentage, destiny grade or uncalibrated probability is allowed.
Every assessment item carries reason and source references.

Gate:

```text
The user can compare two paths without mistaking the result for a physical score.
Every displayed assessment is reproducible from typed evidence.
```

### R6: Visual and multi-terminal refinement

Goal: make the completed task calm, legible and distinctive.

- Default node: GanZhi, polarity/element and role only.
- Selected node: roots, revealed stems, path role and temporal effect.
- Professional disclosure: sources and epistemic state on demand.
- Desktop uses a local lens; mobile uses an anchored bottom sheet.
- The primary task remains possible at 390px without horizontal overflow.
- Motion follows `prefers-reduced-motion` and never carries unique meaning.
- Li-Xiang movement preserves node position, selection and path endpoints.

Gate:

```text
Desktop and mobile complete the same semantic task.
No permanent secondary panel competes with the six pillars.
```

## 5. Required Discussion Before Each Slice

Each slice begins with a short Markdown decision answering:

```text
Observed user problem
Exact user task
Authority and required source data
Visible interaction
Missing-data behavior
Desktop/mobile behavior
Hard boundaries
Machine gate
Product review question
```

Only the named slice may be implemented. Findings from later slices are recorded
but do not expand the current implementation.

## 6. Open Questions Requiring Analyst Review

1. Which natal pillars should be editable in the first product release, rather
   than merely in an internal research experiment?
2. Which engine currently owns every legal candidate and linked-pillar update?
3. Does the formal Graph already expose typed root and revealed-stem relations,
   or must that contract be added through fixtures first?
4. Which relation types qualify as assisted-connect targets?
5. Can an expert create an unsupported PathDraft segment, and how should the
   product explain that it is a hypothesis rather than a relation?
6. What typed evidence supports each discrete path-assessment dimension?
7. Which temporal changes are currently computable, and which remain only
   observational?

## 7. Current Recommendation

Do not implement all six slices together. Review and authorize `R1` first, then
proceed in order. The highest-value product correction after R1 is `R2`, because
the current user-visible problem is not a missing panel but uncertainty about
what can be connected and why.

## 8. Current Boundary Status

```yaml
training_performed: false
weights_modified: false
runtime_rules_modified: false
brain_logic_modified: false
mingli_algorithm_modified: false
theory_modified: false
llm_used: false
formal_state_modified: false
ui_modified: false
production_deployed: false
```
