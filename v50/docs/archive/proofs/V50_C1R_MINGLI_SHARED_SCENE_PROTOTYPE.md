# V50 C1R Mingli Shared Scene Prototype

## 1. Decision

```yaml
phase: C1R Shared Semantic Projection Proof
product_name: Mingli Scene Runtime
status: technical_spike_complete
product_gate: deferred_to_onecanvas_integration
production_runtime_authorized: false
full_c2_authorized: false
production_deployment: false
```

C1R tests whether one filtered Mingli semantic world can retain identity across
three render profiles:

```text
理 / Lab       exact nodes, relations and paths
象 / Xiangfa   deterministic scene skeleton and disclosed metaphor bindings
时 / Theater   the same objects and path expressed as ordered scene cues
```

It does not replace the C0 Canvas Compiler and does not create a second
Reasoner. C1 remains the internal Inspector. C2A remains the direct-manipulation
tool proof. C1R only composes their already filtered output into a shared visual
state.

The standalone Lab, Xiangfa and Theater pages are not a product architecture.
Their retained role is to prove shared semantic identity, disclosed metaphor
bindings and deterministic scene cue behavior for Mingli OneCanvas.

## 2. First Vertical Scenario

The prototype reuses the anonymized real formal LifeCase fixture from C2A:

```text
formal 壬午 hour
→ create experiment
→ switch to legal 癸未 hour
→ formal path becomes partial
→ select the break
→ switch from 理 to 象
→ play the same path in 时
→ return to 理 without losing selection or PathDraft
```

The official annual pillar is shown as formal temporal material. Other years
remain hypothetical calendar signals. No temporal path effect is invented.

## 3. Shared Contracts

### MingliVisualObjectSpec

```yaml
visual_object_id:
semantic_ref:
object_type: stem | branch | relation | path | temporal_signal
label:
element:
polarity:
epistemic_status:
source_refs:
interaction_capabilities:
disclosure_profile:
```

### MingliSceneState

```yaml
scene_state_id:
render_profile: lab | xiangfa | theater
variant_ref:
temporal_stage:
visual_objects:
active_path:
user_path_draft:
selected_semantic_ref:
diff_focus:
camera_state:
metaphor_bindings:
```

### MingliSceneCue

```yaml
cue_id:
action: focus | connect | trace_path | block_path | compare | narrate
semantic_refs:
at_step:
label:
```

### MingliMetaphorBinding

```yaml
semantic_ref:
motif:
binding_type: canonical_symbol | tradition_supported | analyst_authored | illustrative_only
visual_asset_ref:
mapping_explanation:
source_ref:
author:
disclosure_level:
```

The prototype may implement these as local JavaScript view models. A future
production runtime requires independently reviewed typed contracts and a
server-side Scene Composer.

## 4. Permanent Invariants

1. The same `semantic_ref` identifies the same object in Lab, Xiangfa and
   Theater.
2. Role filtering happens before Scene composition. A filtered object cannot
   reappear in state, DOM, debug output or fallback content.
3. Renderer and Scene Composer do not infer Mingli relations, paths or
   epistemic status.
4. Xiangfa motifs are disclosed metaphors and never become formal facts.
5. User edits remain in Sandbox and PathDraft remains `user_draft`.
6. Switching render profile preserves selected object, active path, temporal
   signal and user draft.
7. Theater cues reference existing semantic objects; they do not introduce new
   conclusions.
8. Missing temporal evidence remains missing in every profile.

## 5. Prototype Gate

```yaml
shared_identity:
  one_semantic_ref_across_three_profiles: required
  selection_survives_profile_switch: required
  path_draft_survives_profile_switch: required

shared_change:
  one_hour_change_updates_three_profiles: required
  path_break_location_consistent: required
  no_renderer_side_relation_inference: required

xiangfa_boundary:
  stable_scene_skeleton: required
  clickable_semantic_hotspots: required
  metaphor_binding_disclosed: required

theater_boundary:
  cue_targets_exist_in_scene_state: required
  playback_stops_at_missing_segment: required
  no_new_mingli_claims: required

product_quality:
  desktop_coherent: required
  mobile_coherent: required
  primary_path_visible_without_full_graph: required
```

Passing C1R selects a shared visual architecture direction. It does not
authorize production integration, classroom authoring, video export, full
Temporal Sandbox or public deployment.

## 6. Explicit Non-goals

- no change to Chart, LifeCase, Reasoner, Graph or Canvas Compiler;
- no LLM, TTS or generated Mingli explanation;
- no new formal path or temporal conclusion;
- no separate Xiangfa reasoning engine;
- no production Theater API integration;
- no arbitrary four-pillar mutation;
- no persistence beyond the local prototype;
- no deployment to server 13.
