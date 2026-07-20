# V50 C2A-R OneCanvas Three-State Integration

## 1. Decision

```yaml
phase: C2A-R OneCanvas Three-State Integration
product_name: Mingli OneCanvas / 一图三态
status: prototype_authorized
c1r_role: shared_semantic_projection_proof
full_c2_authorized: false
production_deployment: false
```

The product is one Mingli world, not three synchronized tools:

```text
理 = semantic skeleton of the current OneCanvas
象 = visual mapping of the same nodes and paths
时 = temporal behavior played on the same scene
```

The six semantic pillars and their twelve primary nodes remain the only main
interaction surface. Lab, Xiangfa and temporal playback cannot create a second
node set, a second path studio or a second page.

## 2. Continuous Product Model

```text
expression axis: 理 0 ───────── 100 象
temporal axis:   原局 → 大运进入 → 流年进入 → 路径演化
```

Moving the expression slider changes only the render profile. Every node keeps
the same `node_key`, `semantic_ref`, slot, selection state and path endpoints.

Temporal playback consumes deterministic scene cues:

```text
show_natal
enter_luck
enter_annual
focus_node
trace_path | block_path
```

It stops at the first missing relationship. It never invents a bridge or a
temporal effect that is absent from the fixture.

## 3. Required Continuous Task

```text
1. Enter the formal chart.
2. Create an experiment.
3. Edit an hour or day pillar through legal candidates.
4. Observe linked pillar changes and explicit luck recalculation.
5. Observe the system path reroute on the same twelve nodes.
6. Draw a user PathDraft on those same nodes.
7. Compare A/B in the same node space.
8. Move continuously from Li to Xiang without losing identity or selection.
9. Play the current scene from natal to luck, annual and path cues.
10. Pause, edit, recompile and continue from the same scene.
11. Return to Li with experiment, selection and paths intact.
12. Repeat the core task at 390px without a second mobile workflow.
```

## 4. Permanent Invariants

1. One semantic object has one DOM node and one `semantic_ref`.
2. Xiangfa is a disclosed render binding, not a formal Mingli assertion.
3. Playback cues reference existing nodes and precompiled relations only.
4. The renderer does not infer pillars, ten gods, relations, paths, timing or
   epistemic status.
5. Legal calendar variants and luck recalculation remain precompiled inputs.
6. User paths remain `user_draft` and never promote themselves.
7. Candidate, committed, blocked and hypothetical states remain visually and
   semantically distinct.
8. Pausing and changing expression do not discard selection, experiment,
   PathDraft, A/B snapshots or temporal position.
9. Editing during playback pauses the scene, recompiles the current variant and
   permits explicit continuation.
10. No LLM, TTS, formal-state write, production integration or server 13 deploy.

## 5. C1R Disposition

```yaml
C1R:
  implementation: COMPLETE
  machine_gate: PASS
  semantic_continuity_proof: PASS
  product_gate: DEFERRED
  production_release: BLOCKED
  future_role: OneCanvas render bindings and scene cue discipline
```

The standalone C1R pages remain an archived technical Spike. They are not a
parallel product surface and do not authorize full C2.

## 6. Prototype Gate

```yaml
single_surface:
  primary_canvas_count: 1
  semantic_node_count: 12
  duplicated_path_nodes: 0

continuous_expression:
  same_semantic_refs_across_ratio: required
  selection_preserved: required
  experiment_preserved: required
  path_draft_preserved: required

temporal_behavior:
  natal_luck_annual_cues: required
  pause_and_resume: required
  missing_relation_stops: required
  fabricated_temporal_effects: 0

boundaries:
  frontend_mingli_inference: false
  llm_used: false
  tts_used: false
  formal_state_writes: false
  production_deployment: false
```

