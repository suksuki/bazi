# V50 Computational Mingli Research Program

Status: active research roadmap

Mission:

```text
docs/V50_MISSION_AND_INTELLIGENCE_DEFINITION.md
```

North star:

```text
Discover. Verify. Evolve.
```

This document is the research layer above V50 engineering mainline.

It does not replace:

```text
docs/V50_MINGLI_RESEARCH_TO_RUNTIME_PROTOCOL.md
```

It tells us which research programs are active and which questions matter.

## First Principle

Code is replaceable.

Theory is the asset.

Chinese:

```text
代码可以重写，理论才是资产。
```

Evidence is how Theory earns trust.

Chinese:

```text
Theory 必须由 Evidence 支撑。
Evidence 不是数据，而是信任机制。
```

## Why This Exists

V50 is no longer only a software project.

It is a Computational Mingli Research Program.

Its purpose is to help DeepBazi discover, verify, and evolve computational mingli theory.

The engineering mainline implements research output.

The research mainline decides what is ready to implement.

Evidence Ontology defines how research signals become trusted support or counter-evidence.

## Active Research Programs

Only these research programs are active for now:

```text
RP001 Timing     Priority: P0
RP002 Mechanism  Priority: P0
RP003 Ziwei      Priority: P1
RP004 Xiangfa    Priority: P1
RP005 Context    Priority: P1
RP007 Semantic Diversity Priority: P0
RP008 Decision Intelligence Priority: P0
```

Everything else is paused unless it directly supports one of these programs.

Evidence foundation:

```text
research/V50_EVIDENCE_ONTOLOGY.md
research/V50_EVIDENCE_LIBRARY.md
```

`V50_EVIDENCE_ONTOLOGY.md` defines evidence semantics.

`V50_EVIDENCE_LIBRARY.md` stores concrete evidence records.

The ontology is stable foundation.

The library is the active research asset.

## Research Program Map

### RP001 Timing

Core question:

```text
What do luck, year, and month actually change?
```

Current status:

```text
Question / Discussion / Observation active
Hypothesis partial
Theory Freeze no
Runtime limited to synthetic TemporalState only
```

Key documents:

```text
research/timing/F001_WHAT_IS_LUCK.md
research/timing/F002_WHAT_IS_YEAR.md
research/timing/F003_WHAT_IS_MONTH.md
research/timing/TIMING_MODEL_RESEARCH_V1.md
```

### RP002 Mechanism

Core question:

```text
Is a mechanism discovered from graph state, or merely named by a rule?
```

Current status:

```text
Mechanism Representation formalized
Mechanism Representation Audit required
Theory Freeze partial
Runtime label expansion must pause
```

Key documents:

```text
V50_MECHANISM_REPRESENTATION.md
V50_MECHANISM_REPRESENTATION_AUDIT_PROTOCOL.md
```

### RP003 Ziwei

Core question:

```text
What does Ziwei compute if Bazi computes flow?
```

Current status:

```text
Palace as state container hypothesis active
Star as behavior modifier hypothesis active
Four transformations as state operators hypothesis active
Theory Freeze partial
Runtime baseline is still material / dynamic evidence
```

Key documents:

```text
research/ziwei/Z001_WHAT_IS_PALACE.md
research/ziwei/Z002_WHAT_IS_STAR.md
research/ziwei/Z003_WHAT_DO_FOUR_TRANSFORMATIONS_CHANGE.md
research/ziwei/Z004_WHY_SANFANG_SIZHENG.md
research/ziwei/Z005_ZIWEI_THEME_DISCOVERY.md
research/ziwei/ZIWEI_STATE_ENGINE_ARCHITECTURE.md
```

### RP004 Xiangfa

Core question:

```text
How can structure and mechanism become a living scene without replacing logic?
```

Current status:

```text
Question / Discussion active
Observation active
Formalization not started
Runtime not allowed
```

Initial hypothesis:

```text
Xiangfa is an explanation layer over Brain-approved structure,
flow, state delta, and mechanism representation.
It must not create judgment.
```

### RP005 Context

Core question:

```text
How does real-world context affect domain landing without mutating natal facts?
```

Current status:

```text
Context Overlay theory drafted
Geography / Profession / Reality Event candidates drafted
Theory Freeze partial
Runtime not broadly active
```

Key documents:

```text
research/context/CONTEXT_OVERLAY_ARCHITECTURE.md
research/context/C001_GEOGRAPHY_OVERLAY.md
research/context/C002_PROFESSION_OVERLAY.md
research/context/C003_REALITY_EVENT_OVERLAY.md
```

### RP007 Semantic Diversity

Core question:

```text
Why does V50 collapse many chart structures into a small number of semantic outputs?
```

Current status:

```text
Observation active
Hypothesis active
Theory Freeze no
Runtime changes not allowed yet
```

Initial hypothesis:

```text
Semantic repetition comes from narrow Brain / UnifiedState / winning-claim semantics,
not primarily from LLM Prompt.
```

Historical runs that motivated the current Agent refoundation:

```text
archived-run: night_model_compare_wealth_career_longrun_v2
archived-run: unified_state_coverage_analysis_v1
```

Required next gate:

```text
Unified State Coverage Analysis
        ↓
Probability Field / DomainState design
        ↓
Synthetic semantic diversity fixtures
```

### RP008 Decision Intelligence

Core question:

```text
What is a good decision in Mingli?
```

Current status:

```text
Question active
Hypothesis seed active
Theory Freeze no
Runtime changes not allowed yet
```

Initial hypothesis:

```text
Probability Field is Engine / Brain semantics.
Decision Field is the product object.
Probe should optimize Decision Convergence, not only probability convergence.
```

Current product documents:

```text
docs/V50_CURRENT_ARCHITECTURE.md
docs/product/V50_CONTENT_PLACEMENT_AND_ABU_DIALOGUE_V1.md
docs/product/V50_ABU_PERSONA_GUIDANCE_AND_MOTION_V1.md
```

## Freeze Criteria

Theory Freeze requires:

```text
[ ] Can explain existing observations
[ ] Can handle or explain counter examples
[ ] Has at least one competing theory seriously compared
[ ] Can form a unified data model
[ ] Can enter Runtime without inventing new theory
[ ] Can design synthetic validation
[ ] Has real-world validation plan
[ ] Has supporting Evidence with reliability / relevance declared
[ ] Has Counter Evidence listed or explicit collection plan
```

If any item is missing, status is:

```text
Theory Freeze: NO
```

or:

```text
Theory Freeze: PARTIAL
```

## Open Questions Registry

Canonical file:

```text
research/V50_OPEN_QUESTIONS.md
```

All serious discussions should attach to an Open Question.

Code should not be the center of discussion.

## Evidence Rule

All serious research claims should attach to Evidence.

Evidence must declare:

```text
collector
evidence_class
reliability
relevance
supports / weakens / does_not_support / falsifies
lifecycle_status
allowed_usage
forbidden_usage
```

Behavior Evidence from Probe can calibrate a person.

It cannot freeze structural theory.

Structural and Simulation Evidence are the primary sources for structural theory validation.

Open Questions should be.

## Theory Library

Open Questions produce Theory Objects.

Runtime implements Theory Objects.

Canonical files:

```text
research/V50_THEORY_LIBRARY.md
research/V50_EVIDENCE_LIBRARY.md
```

Mainline must not implement an Open Question directly.

It must implement a Theory Object whose status is at least:

```text
candidate with explicit runtime boundary
```

and preferably:

```text
frozen
```

Theory Graph is read-only / downgraded reference:

```text
research/V50_THEORY_GRAPH.md
```

Do not expand Theory Graph unless evidence management requires it.

Research emphasis now:

```text
Theory + Evidence
```

not more abstraction.

## Research Gate Before Engineering

Before implementation, each capability must state:

```text
Research Program:
Open Question:
Theory Object:
Protocol Stage:
Theory Freeze status:
Formalization target:
Validation plan:
```

If these fields are missing, do not implement.
