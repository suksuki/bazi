# V50 C2A Mingli Lab Direct Manipulation Prototype

## 1. Decision

```yaml
phase: C2A Direct Manipulation Prototype
product_name: Mingli Lab / 命局实验台
status: prototype_authorized
full_c2_authorized: false
production_implementation: false
production_deployment: false
```

C1 machine fidelity remains valid, while its default user product remains
failed. The existing Renderer is retained as the internal `Mingli Canvas
Inspector`. C2A does not reopen that page for cosmetic work.

The prototype must prove a complete tool loop:

```text
Create an isolated variant
-> change one legal birth-time state
-> deterministically rebuild the chart structure
-> show exactly what changed
-> inspect path continuity or interruption
-> draw a user path
-> compare, undo, reset and save A/B
```

## 2. First Real Scenario

> **Birth-hour calibration + annual dial + path comparison**

The source is an anonymized real LifeCase whose committed path has typed graph
evidence and depends on the hour pillar. The prototype stores no name, birth
date, location, account ID or raw case ID.

The default mode is `calendar_valid`. Year, month and day remain locked when a
candidate time preserves those three formal pillars. A legal time that crosses
a calendar boundary must be marked incompatible instead of silently forcing
the lock.

## 3. Authority Model

```text
Formal chart
  canonical facts + committed LifeCase path

Experiment variant
  calendar-derived pillars + deterministic Graph
  no committed professional judgment

Graph candidate
  experimental route evidence only

User path
  user draft only
```

Changing the natal chart invalidates automatic transfer of the formal path.
The original committed path remains a reference. The experiment may only say
whether an analogous structural segment is present, partial or absent.

It may not say that a new chart has a committed main path, useful god, pattern
or real-world event outcome.

## 4. Prototype Contracts

### SandboxWorldVariant

```yaml
sandbox_id:
base_chart_version_id:
mode: calendar_valid
pillar_mutations:
temporal_mutations:
calendar_compatible:
dependency_recalculations:
source_mode: hypothetical
writes_chart: false
writes_life_case: false
```

### PathDraft

```yaml
draft_id:
node_keys:
segments:
status: empty | open | complete
authority: user_draft
```

### PathComparisonSpec

```yaml
formal_reference:
variant_structural_continuity:
graph_candidate:
user_draft:
preserved_segments:
missing_segments:
explanation_refs:
```

The prototype may implement these as local view-model data. Production C2
requires separate reviewed contracts and server-side compilation.

## 5. Interaction Contract

The clickable prototype must include:

1. Formal chart, Experiment A, Experiment B and A/B Compare modes.
2. Locked year/month/day and direct legal-hour selection.
3. Immediate pillar, hidden-stem, ten-god, relation and structural Diff update.
4. A compact six-pillar strip with luck and year visually separated as time.
5. One focused path by default; never the complete relation web.
6. Step-by-step path playback.
7. User path drawing by selecting graph nodes.
8. Lookup-based segment feedback: available relation, conditional candidate or
   missing connection.
9. Undo, redo, reset and in-memory save to A/B.
10. A year dial that distinguishes the official year from hypothetical years.
11. Desktop and 390px mobile layouts.

## 6. Visual Semantics

```text
five-element hue     node material identity
solid ink path       committed formal reference
vermilion pulse      current experimental change
dashed path          Graph candidate
dotted path          user draft
terminal gap         missing structural segment
ghost trace          previous state
```

No color represents good or bad fortune. No uncalibrated percentages or
absolute energy scores are shown.

## 7. Explicit Non-goals

- no production API or Experience Shell change;
- no write to ChartVersion, LifeCase or case memory;
- no LLM or Abu free reasoning;
- no arbitrary structural-free mutation in the first slice;
- no automatic candidate promotion;
- no teacher editor, multiplayer Live or video export;
- no claim that a hypothetical year has a formal temporal effect;
- no reuse of old `tool_score` or numeric path-strength UI.

## 8. Prototype Gate

```yaml
tool_loop:
  create_variant: required
  manipulate: required
  immediate_recompile_evidence: required
  understand_change: required
  undo_reset_compare: required

epistemic_safety:
  formal_and_hypothetical_distinct: required
  committed_path_not_transferred: required
  graph_candidate_not_promoted: required
  no_formal_write: required

product_quality:
  useful_for_hour_calibration: required
  primary_path_visible_without_spider_web: required
  desktop_coherent: required
  mobile_coherent: required
  visual_identity_present: required
```

Passing this prototype gate only selects a product direction. It does not close
C1, authorize full C2 or authorize deployment.

