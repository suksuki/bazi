# V50 Guided Mingli Deliberation v1

## Mission

Guided Mingli Deliberation lets a practitioner or researcher participate in case interpretation without editing chart facts, runtime rules, or global theory.

It is not a form for manually configuring a chart. It is a dependency-aware comparison of system-generated hypotheses.

```text
Core Cognition (immutable)
        ↓
Case Deliberation Workspace
        ↓
Effective Case Reading
        ↓
Practitioner / Research Projection
```

## Role Boundary

```text
Member          → Member only
Practitioner    → Practitioner only
Research Master → Research only
Admin           → Guest / Member / Practitioner / Research preview
```

Admin preview never changes the Admin account identity. Future upgrades change mode entitlements, not the reading architecture.

## Epistemic Levels

```text
L0 Presentation choice
L1 Case interpretation branch
L2 Case evidence and Probe response
L3 Birth-fact correction and chart recomputation
L4 Research proposal awaiting independent review
```

This slice implements L1 and connects it to existing L2 evidence. It does not permit L3 or global L4 promotion.

## Deliberation Order

```text
Pattern / Whole-chart Hypothesis
        ↓
Useful-God Logic
        ↓
Work-Path Assessment
        ↓
Ziwei Focus
        ↓
Domain Assertion
        ↓
Probe / Historical Evidence
```

A later stage is locked until its required earlier stage has a case-local selection. The system baseline remains visible and recoverable throughout.

## Choice Grammar

### Exclusive Branch

Used only when hypotheses compete and cannot all be primary. Support values are normalized within the current candidate set and are labelled case-relative, not truth probabilities.

### Independent Support

Used for mechanisms that may coexist. Support indices do not sum to 100.

### Assessment

Used when the system has one structured candidate, such as the current work path. A professional can support, challenge, or defer it. Challenge does not erase the system candidate.

### Research Fork

Research mode may preserve an existing candidate as a research fork. It remains case-local and cannot modify runtime or theory.

## Confidence Semantics

Every option exposes:

```text
current support
confidence band
support reasons
counter evidence
what it explains
downstream impact
what evidence would change the judgment
```

Selection alone never changes support. Support changes only through evidence, Probe, or a separately reviewed cognitive rerun.

## Case State

The system always preserves:

```text
System Baseline
Professional Selection
Research Fork
Revision History
```

Every revision records actor role, action, target option, rationale, changed downstream surfaces, and explicit non-effects.

## Product Experience

The page remains a reading canvas. Professional interaction appears as a compact guided panel at the point where a real epistemic choice exists.

Abu must:

```text
explain the current question
show no more than three useful candidates at once
state why the system currently prefers one
warn about prerequisite or consistency conflicts
explain what a selection changes and does not change
offer the next eligible step
```

Abu may not invent an option, increase confidence because of a click, or promote a case selection globally.

## Acceptance

1. Non-admin accounts cannot request another role's experience depth.
2. Admin can preview all modes without changing identity.
3. Pattern selection unlocks dependent stages.
4. Invalid or stale options are rejected server-side.
5. Selection changes only the case workspace and effective projection.
6. Chart facts, cognitive record, runtime rules, and theory remain unchanged.
7. Confidence does not increase from selection alone.
8. Practitioner and Research surfaces expose different depth.
9. Undo restores the prior case interpretation.
10. Desktop and mobile flows remain readable and operational.
