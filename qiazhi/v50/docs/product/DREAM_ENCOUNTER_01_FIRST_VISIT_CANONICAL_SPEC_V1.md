# DREAM-ENCOUNTER-01 First Visit Canonical Spec v1

```yaml
status: FROZEN_IMPLEMENTATION_BASELINE
scope: shots_01_to_07
implementation_target: DREAM-ENCOUNTER-01-FIRST-VISIT-VERTICAL-SLICE
mingli_owner: CanonicalScene
viewer_projection_owner: DreamProjectionCompiler
canvas_owner: ReadOnlySixPillarCanvasService
frontend_semantic_authority: none
```

## Product Loop

```text
Fog gate
-> the user's tree recognizes the user
-> the user leads and Abu follows
-> the user touches actual tree geometry
-> one authorized fact is revealed
-> the user separately touches the root mirror
-> the same fact is verified in OneCanvas
-> the user pulls across the visible mirror boundary
-> the living grove resumes at its current scene time
```

The experience is one continuous grove. It is not a sequence of pages, tree cards,
selection controls, or a Dream-specific astrology engine.

## State Machine

| State | Entry event | Allowed exit |
| --- | --- | --- |
| `FOG_GATE_WAITING` | visit and encounter ready | `FOLLOW_ABU` |
| `FOG_GATE_CROSSING` | first deliberate ground touch | timeline completion |
| `TREE_RECOGNITION` | fog boundary crossed | recognition timeline completion |
| `FREE_EXPLORATION` | user's tree settles | direct ground movement |
| `TOUCH_READY` | one resident tree is within touch distance | new discrete tree touch |
| `TREE_REVEALING` | server-selected reveal projection returned | reveal timeline completion |
| `MIRROR_AVAILABLE` | reveal settled or natural-contact-only settled | new discrete mirror touch |
| `MIRROR_OPENING` | server view reference revalidated | transition completion |
| `MIRROR_VERIFYING` | verification projection rendered | mirror withdrawal gesture |
| `MIRROR_WITHDRAWING` | visible boundary pull completed | transition completion |
| `FOREST_RETURNED` | observation anchor restored | next new gesture |
| `FAIL_CLOSED` | authorization is withdrawn or source is unavailable | masked return to grove |

State transitions are explicit. Gestures are fully consumed by their owning state.
No pointer-up event can perform two transitions.

## Server-Owned Disclosure

Tree touch does not create a fact or relationship. It requests one viewer-scoped
`DreamRevealProjection`. The server chooses at most one renderable authorized fact:

```text
committed PathAssertion
-> committed effective RelationAssertion
-> authorized canonical node or pillar fact
-> no revealable fact
```

The returned opaque `onecanvas_view_ref` binds:

- viewer and visit;
- DreamProjection revision;
- resident LifeCase and Chart versions;
- assertion or fact version when present;
- canonical six-pillar coordinate version;
- target stage and one of the existing six Lens values;
- authorization and privacy policy versions.

The client cannot create, rank, replace, or reinterpret the reference. A null reveal
still permits an authorized quiet OneCanvas overview.

## OneCanvas Verification

The root mirror reuses the existing OneCanvas renderer and its fixed six-column,
twelve-node coordinate space. It does not add a Dream Lens.

The first view contains only:

1. the authorized six-pillar coordinate skeleton;
2. the nodes, relation, or path bound to the same reveal;
3. approved fixed copy and the already authorized source statement.

No potential relations, candidate paths, Lab metadata, inspector, navigation,
editing, generated explanation, or second fact are present.

If the focus cannot be rendered exactly, the mirror uses a quiet overview and never
substitutes a nearby fact. Revoked authorization masks content before the return
transition begins.

## Gesture Ownership

- Ground movement starts only on visible walkable ground.
- Walking into a tree does not count as tree touch.
- Tree touch requires a new pointer-down and pointer-up on painted tree geometry.
- Mirror opening requires a later discrete touch on visible root-mirror geometry.
- Mirror withdrawal starts in visible mirror water, crosses the visible root edge,
  and ends on visible forest ground.
- Incomplete gestures restore the current visual state without semantic effects.
- Browser Back, Escape, and the screen-reader `Return to grove` action use the same
  withdrawal transition.

## Continuous Scene Time

`TreeObservationAnchor` stores only visit-local position, camera direction, resident,
and root-mirror reference. It does not freeze or rewind the world.

The scene clock continues while OneCanvas is open. Hidden rendering may be throttled,
but returning reconstructs the current scene phase. Ambient motion, Abu, mist, leaves,
and residents are never reverse-played. The first reveal is not replayed on return.

## Visual and Audio Production Rules

- One full-bleed 2.5D grove serves desktop and mobile compositions.
- Three trees are irregularly placed at different depths and phases.
- No equal-choice layout, cards, labels before approach, hotspots, rewards, or automatic
  selection is allowed.
- Abu leads only through the fog gate. After yielding, he follows the user's actual
  route with delay and never overtakes or signals a preferred resident.
- Tree response uses `LOCAL_WHISPER`: one local fact, 2-4 seconds, no whole-scene effect.
- The root mirror is a physical scene object, not a button skin.
- Environment sound and the registered opening music must yield to narration and
  `prefers-reduced-motion` / user audio preferences.

## Current Engineering Assets

The first vertical slice uses replaceable production assets:

- `porch-v5/grove-clean-approved-v5-e97ec6b5.png`
- 候选树必须使用 `porch-v5/tree-*-actor-v5-*.png` 独立透明演员层，不得把背景焊入树图，也不得回退到已退役的 `tree-*-v1.webp`。
- `abu_dream_standard_cycle_v1.webm`
- `abu_dream_seated_observe_v1.webm`
- `abu_enter_and_notice_v1.webm` as a temporary movement action

The old three-card Dream encounter, visible `Open mirror` button, full Workspace mirror,
and Dream Lens-like controls conflict with this spec and are retired from the active
Dream route.
