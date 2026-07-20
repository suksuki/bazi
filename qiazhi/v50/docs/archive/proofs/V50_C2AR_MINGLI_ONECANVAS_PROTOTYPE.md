# V50 C2A-R Mingli OneCanvas Prototype

## 1. Decision

```yaml
phase: C2A-R
product_name: Mingli OneCanvas / 六柱一图
status: high_fidelity_prototype_authorized
c2a_functional_fixture: preserved
c2a_product_review: failed
full_c2_authorized: false
production_integration: false
production_deployment: false
```

C2A proved the deterministic experiment operations but failed as a product
surface because the six pillars, path editor, Inspector, year dial and A/B
comparison were separate panels. C2A-R keeps that evidence and rebuilds only
the user operation surface.

> Six semantic pillars are the graph and the only primary operation surface.

## 2. OneCanvas Language

```text
所见即所改

六个 fixed semantic slots
年 / 月 / 日 / 时 / 大运 / 流年
        ↓
十二个 unique primary nodes
六个天干 + 六个地支
        ↓
同一空间内完成
看盘 / 改柱 / 选时间 / 画路径 / 比较 / 播放 / 入象
```

The same stem or branch is never duplicated in a Path Studio. Hidden stems are
collapsed satellite nodes of their branch. Context appears as a local lens on
desktop and a bottom sheet on mobile.

## 3. Authority

```yaml
calendar_candidates:
  authority: existing birth calendar engine
  constraint_mode: legal calendar only
derived_chart:
  authority: existing deterministic Bazi material and Graph pipeline
luck_recalculation:
  authority: existing personal timing engine
formal_path:
  authority: committed LifeCase reference
variant_path:
  authority: experimental Graph candidate
user_path:
  authority: user_draft
renderer:
  authority: none
```

Changing a natal pillar does not directly mutate a GanZhi string. The
prototype selects a legal calendar candidate, resolves all four pillars,
rebuilds ten gods, hidden stems, relations and Graph, and recalculates the luck
material for the same analysis year.

## 4. Prototype Task

One anonymized real formal LifeCase must support this continuous loop:

```text
create experiment
→ edit the hour through a local legal-candidate lens
→ edit the day and observe linked hour changes
→ see explicit luck recalculation status
→ see the system candidate path reroute on the same twelve nodes
→ draw a user path directly on those nodes
→ overlay system and user paths
→ save A and B
→ compare A/B through one-space crossfade
→ complete the same core task at 390px
```

## 5. Interaction Contract

### Formal state

- natal values are immutable;
- selecting a node opens inspection and an explicit create-experiment action;
- the committed LifeCase path is shown only when typed evidence exists.

### Experiment state

- semantic slots remain fixed;
- legal candidate values may change;
- selecting a candidate previews the complete precompiled chart variant;
- Enter or Apply commits the preview to the local experiment history;
- Escape or Cancel restores the previous experiment state;
- double-clicking a natal node restores the formal variant;
- undo and redo operate only on local experiment history.

### Path state

- system paths and user drafts use the same node coordinates;
- system path uses solid lines;
- user path uses dashed lines;
- missing relations remain broken;
- comparison uses discrete relation availability, timing material status and
  continuity; it does not produce an energy percentage.

### A/B state

- A and B are snapshots of the local experiment only;
- the comparison never renders duplicate charts;
- one-space crossfade preserves semantic slot positions;
- changed values show the other state as a ghost label.

## 6. Permanent Boundaries

1. No LLM, TTS or generated Mingli explanation.
2. No write to ChartVersion, LifeCase, TemporalSnapshot or case memory.
3. No Graph candidate or PathDraft promotion.
4. No frontend calendar, ten-god, relation, path or luck inference.
5. No arbitrary free-structure mode in C2A-R.
6. No fabricated luck change; unchanged results say `recalculated_unchanged`.
7. No fabricated temporal path effect when typed evidence is absent.
8. No uncalibrated percentage, energy score or destiny grade.
9. No permanent Inspector, candidate strip, Path Studio or year dial.
10. All nodes and paths retain stable `semantic_ref` for Theater and Xiangfa.
11. Passing C2A-R does not authorize full C2 or production integration.
12. Do not deploy the prototype to server 13.

## 7. Product Gate

```yaml
single_surface:
  unique_primary_nodes: required
  duplicated_path_nodes: forbidden
  permanent_side_panels: forbidden

legal_editing:
  hour_candidate_is_calendar_legal: required
  day_candidate_is_calendar_legal: required
  linked_pillars_recompiled: required
  luck_recalculation_status_visible: required

path_interaction:
  system_path_on_primary_nodes: required
  user_path_on_primary_nodes: required
  discrete_segment_feedback: required
  same_space_overlay: required

comparison:
  explicit_save_a_and_b: required
  same_space_crossfade: required
  duplicated_chart_pages: forbidden

responsive:
  desktop_core_task_without_page_hunt: required
  mobile_390px_core_task_without_horizontal_overflow: required
```

