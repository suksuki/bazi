# V50 Evidence Ontology

Status: active research foundation

This document defines what evidence means in V50.

It is not a storage document.

It is the semantic contract between:

```text
Collector
        ↓
Evidence
        ↓
Theory
        ↓
Runtime / Validation / Training
```

## Core Principle

Evidence is not just data.

Evidence is the trust model that tells V50:

```text
what source produced this signal
what theory it supports or weakens
how reliable it is
how relevant it is
what it is allowed to change
what it must never change
```

## First Rule

Evidence supports or weakens Theory.

Evidence does not directly become Runtime behavior.

Runtime can only change through:

```text
Evidence
        ↓
Theory confidence / theory status
        ↓
Formalization
        ↓
Data Model
        ↓
Runtime
        ↓
Validation
```

## Evidence Semantic Model

Each evidence item must be understood through these dimensions:

```yaml
evidence_id:
collector_id:
evidence_class:
source_category:
target_scope:
supports_theories:
weakens_theories:
does_not_support_theories:
reliability:
relevance:
lifecycle_status:
allowed_usage:
forbidden_usage:
source_ref:
case_refs:
runtime_refs:
validation_refs:
notes:
```

## Evidence Collector

A collector is the process or component that produces evidence.

The collector is not the evidence itself.

Examples:

```text
Synthetic Chart Generator
        ↓
Structural Evidence

State Simulator
        ↓
Simulation Evidence

Probe System
        ↓
Behavior Evidence

Historical Timeline
        ↓
Historical Evidence

Population Analysis
        ↓
Statistical Evidence
```

Probe is therefore not evidence.

Probe is an evidence collector.

The evidence produced by a Probe is usually Behavior Evidence.

## Evidence Classes

### Structural Evidence

Source:

```text
synthetic charts
controlled chart variants
ablation cases
taxonomy fixtures
```

Primary use:

```text
structural theory validation
graph / path / role / mechanism validation
single-variable experiment
```

Trust profile:

```yaml
source_category: engine_generated
reliability: 1.0
typical_relevance:
  mechanism_theory: high
  timing_theory: medium
  reality_mapping: low
```

Principle:

```text
Synthetic Charts are the primary evidence source for structural theory validation.
```

Chinese:

```text
合成八字是结构理论验证的第一证据来源。
```

### Simulation Evidence

Source:

```text
state simulator
path explorer
node importance engine
ablation runner
state delta runner
```

Primary use:

```text
state transition validation
mechanism representation validation
timing candidate comparison
runtime behavior audit
```

Trust profile:

```yaml
source_category: engine_generated
reliability: 0.9-1.0
typical_relevance:
  simulation_theory: high
  mechanism_theory: high
  expression_style: low
```

### Historical Evidence

Source:

```text
known past event
confirmed timeline event
documented life milestone
```

Example:

```text
User says: I divorced in 2023.
```

Semantic meaning:

```yaml
event: relationship_changed
evidence_class: historical
supports:
  - timing_theory
  - state_evolution_theory
does_not_support:
  - structural_mechanism_theory
```

Primary use:

```text
timing validation
reality mapping calibration
domain landing calibration
```

Trust profile:

```yaml
source_category: reality_generated
reliability: medium_high
relevance: theory_dependent
```

Historical Evidence can validate whether a timing model maps to real events.

It must not directly rewrite structural theory.

### Behavior Evidence

Source:

```text
probe answer
conversation answer
self-description
preference answer
```

Primary use:

```text
individual confidence update
probe policy calibration
twin overlay update
domain mapping calibration
```

Trust profile:

```yaml
source_category: reality_generated
reliability: medium_low
relevance: high for the current person, low for structural theory
```

Principle:

```text
Behavior Evidence calibrates reality mapping.
It does not validate structural theory by itself.
```

Chinese:

```text
Probe 产生的是行为证据，用于校准现实映射，而不是验证理论本身。
```

### Statistical Evidence

Source:

```text
large-scale cleaned case population
aggregated feedback
aggregated historical timelines
validated cohort analysis
```

Primary use:

```text
policy calibration
population-level theory support
model comparison
confidence calibration
```

Trust profile:

```yaml
source_category: reality_generated
reliability: depends_on_cleaning
relevance: high if cohort is well-defined
```

Population data is not evidence by itself.

Only cleaned and analyzed population results become Statistical Evidence.

### Counter Evidence

Source:

```text
synthetic counter case
real-world counter case
runtime contradiction
failed prediction
unexplained validation miss
```

Primary use:

```text
theory weakening
theory falsification
promotion blocking
counter-example tracking
```

Counter Evidence has special priority.

A small amount of strong Counter Evidence can block Theory Freeze even when supporting evidence exists.

## Engine-generated vs Reality-generated Evidence

V50 distinguishes two major sources.

### Engine-generated Evidence

Includes:

```text
Structural Evidence
Simulation Evidence
Synthetic Counter Evidence
```

Allowed to support:

```text
structural theory
mechanism theory
simulation theory
formalization readiness
synthetic validation readiness
```

### Reality-generated Evidence

Includes:

```text
Historical Evidence
Behavior Evidence
Statistical Evidence
Real-world Counter Evidence
```

Allowed to support:

```text
reality mapping
timing calibration
domain landing
probe strategy
confidence calibration
```

Reality-generated Evidence must not mutate:

```text
natal facts
engine-generated facts
raw chart structure
confirmed material facts
```

## Reliability and Relevance

V50 must not collapse trust into one score.

Each evidence item has at least two scores.

### Reliability

Reliability answers:

```text
How trustworthy is the evidence source?
```

Example:

```yaml
historical_event:
  reliability: 0.85
  reason: confirmed past event
```

### Relevance

Relevance answers:

```text
How relevant is this evidence to this specific theory?
```

Example:

```yaml
historical_event_2023_divorce:
  relevance:
    T001_long_term_field: 0.40
    T006_state_evolution: 0.70
    T004_mechanism_ast: 0.05
```

The same evidence can be reliable but irrelevant to a theory.

That distinction is mandatory.

## Theory Support Semantics

Evidence can relate to theory in four ways:

```yaml
supports_theories:
  - theory_id

weakens_theories:
  - theory_id

does_not_support_theories:
  - theory_id

falsifies_theories:
  - theory_id
```

Definitions:

```text
supports       increases confidence when reliability and relevance are sufficient
weakens        reduces confidence but does not reject the theory
does_not_support marks explicit non-applicability
falsifies      blocks or rejects the theory in a defined scope
```

## Evidence Lifecycle

Evidence must have lifecycle state.

```text
Collected
        ↓
Verified
        ↓
Referenced
        ↓
Promoted / Archived
```

### Collected

Evidence has been captured but not checked.

It cannot affect Theory confidence.

### Verified

Evidence source, schema, and scope have been checked.

It can affect Theory confidence within allowed usage.

### Referenced

Evidence is attached to a Theory, Runtime report, validation report, or training report.

### Promoted

Evidence has been used in a Theory confidence update or promotion decision.

### Archived

Evidence is preserved but no longer active.

Reasons:

```text
duplicate
low reliability
low relevance
superseded
invalidated
```

## Allowed Usage Matrix

```text
Structural Evidence
  allowed:
    - structural theory validation
    - graph/path/role/mechanism validation
    - synthetic validation
    - formalization gate
  forbidden:
    - direct user judgment
    - direct Brain policy training without validation

Simulation Evidence
  allowed:
    - state transition validation
    - mechanism representation audit
    - timing candidate comparison
  forbidden:
    - replacing real-world validation

Historical Evidence
  allowed:
    - timing validation
    - domain landing calibration
    - reality mapping calibration
  forbidden:
    - rewriting structural theory directly
    - mutating natal facts

Behavior Evidence
  allowed:
    - current-session confidence update
    - Twin Overlay update
    - Probe policy calibration
  forbidden:
    - Theory Freeze
    - structural theory validation by itself
    - mutating chart facts

Statistical Evidence
  allowed:
    - policy calibration
    - population-level validation
    - confidence calibration
  forbidden:
    - use before cohort cleaning
    - use without relevance scope

Counter Evidence
  allowed:
    - theory weakening
    - theory falsification
    - promotion blocking
  forbidden:
    - being ignored because it is inconvenient
```

## Evidence Target Scope

Evidence must declare what it is allowed to affect.

Allowed target scopes:

```text
theory_confidence
theory_status
runtime_validation
brain_confidence
decision_policy_calibration
probe_policy_calibration
twin_overlay
expression_quality
```

Forbidden target scopes for all evidence:

```text
raw_birth_input
immutable_chart_facts
engine_material_facts
verified_historical_event_facts
```

## Canonical Relationship

```text
Theory
        ▲
        │
Evidence
        ▲
        │
Collector
```

This is the canonical V50 research relationship.

Collector gathers signals.

Evidence assigns semantic meaning, reliability, relevance, lifecycle, and allowed usage.

Theory receives support, weakening, or falsification.

Runtime only receives promoted and formalized theory.

## Boundary

This ontology does not implement Runtime.

It does not introduce a new engine.

It defines the semantic contract for future evidence objects.

The concrete evidence records remain in:

```text
docs/research/V50_EVIDENCE_LIBRARY.md
```

