# V50 OneCanvas Visual Component Contract v1

> Revision 2026-07-19: `DirectNodeStepper` is now the default product control.
> `ConstraintPicker` and `CandidatePreview` remain internal Gallery and audit
> components only; they are not rendered on the primary OneCanvas surface.

## 1. Purpose

This contract prevents OneCanvas refinements from accumulating inside one page
script. It is an implementation discipline, not a new product phase or a new
design-system project.

Components are divided by stable Mingli semantic objects, interaction duties
and visual layers. They are not divided mechanically by page rectangles.

## 2. Dependency Direction

```text
Compiler Contracts
        ↓
OneCanvas ViewModel Adapter
        ↓
OneCanvas Controller
        ↓
SVG Scene Components + HTML Overlay Components
```

Components consume ViewModels and emit UI Intents. They do not modify a Spec,
resolve calendar legality, calculate Mingli meaning or call the Reasoner.

## 3. R1 Components

### Semantic scene components

```text
OneCanvasStage
PillarSlot
StemNode
BranchNode
TemporalNode
```

`PillarSlot` owns semantic position and capability display. `StemNode` and
`BranchNode` render the supplied node state. `TemporalNode` uses explicit
capabilities rather than slot-index assumptions:

```yaml
luck:
  editable: false
  switchable: true
  derived: true

annual:
  editable: false
  switchable: true
  derived: true
```

Annual observation is switchable; its GanZhi is derived from the selected
Gregorian year. It is not an arbitrary GanZhi editor.

### R1 overlay components

```text
DirectNodeStepper
RecomputeIndicator
ContextPopover
UndoRedoControl
```

The stepper emits only a direction and semantic node reference. The Controller
resolves that intent against the supplied closed candidate family and sends a
complete four-pillar candidate to the server compiler. It never increments a
stem or branch by itself. The recompute indicator owns the language for
changed, unchanged and unavailable results.

## 4. Stable Layer Order

```text
1. BackgroundLayer
2. StructuralNodeLayer
3. RootAndRevealLayer
4. RelationLayer
5. TemporalActivationLayer
6. SystemPathLayer
7. UserPathLayer
8. DiffLayer
9. InteractionHintLayer
10. SelectionLayer
```

R1 implements the structural, temporal, interaction and selection layers.
Other layer interfaces remain empty placeholders; R2-R6 functionality is not
implemented early.

## 5. UI Intent Protocol

R1 emits:

```text
node:select
pillar:step
temporal:observe
canvas:reset
history:undo
history:redo
```

`candidate:search` remains available only to bounded observation lookup such as
Gregorian annual-year search. It is not used to edit a natal pillar.

The controller translates intents into Sandbox operations. Components never
write state directly.

Reserved, not implemented in R1:

```text
path:start
path:add-node
path:remove-segment
path:complete
scene:play
scene:pause
scene:seek
```

## 6. SVG and HTML Boundary

SVG scene responsibilities:

- semantic nodes and hit areas;
- relation/path geometry already supplied by ViewModel;
- stable visual anchors;
- selection and temporal emphasis.

HTML overlay responsibilities:

- node-local previous/next controls;
- empty and error states;
- recomputation status;
- exceptional context popover or mobile bottom sheet.

The current prototype may retain HTML semantic nodes while R1 proves the
component contract. The stable layer and event contracts must not depend on the
temporary DOM renderer, so a later SVG renderer does not change authority.

## 7. Render Profiles

```text
lab
theater
xiangfa
inspector
static_export
```

Profiles reuse `semantic_ref`, node state, anchors, path geometry and selection.
They may change presentation and disclosure only. They may not create a second
semantic node.

## 8. Token Files

```text
tokens/foundation.css
tokens/element.css
tokens/epistemic.css
tokens/motion.css
tokens/geometry.css
tokens/typography.css
```

Element, epistemic, selection and warning meaning must not share one token.
Components use tokens for color, line width, geometry, typography and motion.

## 9. Component Gallery

The internal Gallery is a visual regression surface, not another product
prototype. It displays:

```text
formal
experimental
selected
locked
derived
candidate
blocked
recalculating
recalculated_changed
recalculated_unchanged
recalculation_unavailable
```

It must be usable at desktop, tablet and 390px, including reduced-motion and
keyboard-focus states.

## 10. Permanent Boundaries

1. No component imports Reasoner, calendar engine or LifeCase store.
2. No component infers candidate legality or Mingli semantics.
3. No component silently commits a candidate.
4. No filtered semantic object can reappear through component fallback.
5. Components do not write formal state.
6. R1 componentization cannot be used to implement R2-R6 early.
7. No React migration or Experience Shell rewrite is authorized.

## 11. R1 Conformance Result

The R1 implementation conforms to this component contract and is available in
the internal Component Gallery. This is a machine and visual-contract result,
not a product release decision.

```yaml
component_gallery: implemented
stable_layer_order: implemented
ui_intent_boundary: implemented
desktop_rendering: verified
mobile_390_rendering: verified
reduced_motion_contract: implemented
analyst_product_gate: pending
production_release: blocked
```
