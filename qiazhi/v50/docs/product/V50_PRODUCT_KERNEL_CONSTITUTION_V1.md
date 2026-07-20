# DeepBazi V50 Product Kernel Constitution v1

> Status: `FROZEN PRODUCT CONSTITUTION`
>
> Phase: `PRODUCT VALIDATION FREEZE`
>
> Product target: `LIFE SCRIPT CASE WORKSPACE`
>
> Implementation authorization: `NONE`

## 0. Purpose

This constitution defines the product kernel that every DeepBazi experience,
UI, algorithm and engineering change must serve.

It is not an architecture roadmap, an implementation specification or an
authorization to migrate production. Gate state and execution order remain
owned by `config/v50_execution_state.yaml`.

During Product Validation Freeze, the only active product task is the
hash-locked R1 human review. This document does not reopen R1, RA1, Mingli Lab
engineering, production Workspace migration or Legacy retirement.

## 1. North Star

DeepBazi is one Mingli product, not a collection of adjacent features.

```text
one Case
→ one formal cognition history
→ one Canonical Scene
→ one Case Workspace
→ multiple consistent Projections
```

The permanent product principle is:

> **One Case Workspace, one Canonical Scene, one formal provenance chain.**

The professional source chain is:

```text
deterministic facts
→ Reasoner synthesis
→ LifeCase commitment
→ Canonical Scene
→ role-filtered Projection
```

No Projection, Renderer, character, Sandbox or visual effect may reverse this
chain or become an independent source of Mingli truth.

## 2. The Eight Kernel Objects

### 2.1 Case

A Case is the long-lived identity of one person or one explicitly anonymous
teaching subject.

A Case contains versions and history. It is not a single report, chat session,
chart screenshot or browser page.

A Case preserves the distinction between:

```text
formal chart facts
formal LifeCase cognition
temporal state
reality feedback
Sandbox experiments
presentation history
```

Experiments and presentations may refer to a Case. They may not silently
rewrite it.

### 2.2 Workspace

The Case Workspace is the only target product container.

It preserves the current:

```text
Case
LifeCase revision
time stage
selected semantic object
focused path
Sandbox session
role and disclosure policy
Abu context
```

Changing modes changes how the current Case is experienced. It does not create
a new Case, reset semantic identity or switch to a parallel Mingli world.

The Workspace Target Reference is a design target only. It is not a production
route, Scene owner or independent product branch.

### 2.3 Projection

A Projection is a role-approved view of the same Canonical Scene.

The product projections are:

| Projection | Product question |
|---|---|
| Overview | What matters in this Case now? |
| OneCanvas | What is the precise structure? |
| Xiangfa | How can the same structure be understood through imagery? |
| Theater | How does the same structure unfold through time? |
| Mingli Lab | How can an authorized user experiment and compare safely? |
| Abu Context | What may Abu explain or operate at this moment? |

A Projection may select, arrange, simplify, animate, narrate and progressively
disclose approved Scene content.

A Projection may not:

- create a relation or path;
- promote a candidate;
- repair a missing fact by inference;
- expose an object filtered by role;
- write formal Case state;
- describe visual emphasis as professional probability or strength.

### 2.4 Scene

The Canonical Scene is the single product-level semantic state from which all
Projections are produced.

It preserves stable identity for:

```text
semantic objects
relations
paths
time stages
epistemic status
source references
selection and focus
formal versus hypothetical origin
```

Scene is not a second Reasoner. It carries approved meaning into product
experiences; it does not decide what the chart means.

Role filtering must happen before a Projection is delivered. Once an object is
filtered, fallback, default selection, context completion or debug output may
not restore it.

### 2.5 Role

Role determines disclosure and permitted actions, not the underlying Case
facts.

```text
Member
Practitioner
Researcher
Admin
```

The same semantic object keeps the same identity across roles. A role may see
less detail or receive fewer commands, but a role-specific UI may not invent a
different Mingli result.

Admin role switching is a product testing and future upgrade mechanism. It
does not weaken server-side disclosure boundaries for other users.

### 2.6 Abu

Abu is the companion across the current Case Workspace.

Abu may:

- explain the current selected object;
- navigate between approved Projections;
- preserve conversational continuity across modes;
- invoke approved product commands;
- distinguish fact, commitment, candidate, uncertainty and hypothesis;
- narrate the same formal cognition shown by the page.

Abu may not:

- become a second navigation tree;
- create missing Mingli semantics;
- replace the Reasoner or LifeCase commit process;
- speak a conclusion absent from the current role-filtered context;
- turn uncertainty into certainty for dramatic effect;
- treat engagement, cuteness or conversational fluency as evidence.

Abu's character performance supports understanding. It never outranks Mingli
accuracy or provenance.

### 2.7 Sandbox

Sandbox is the only place where a user may alter, compare or replay a
hypothetical state.

Every Sandbox state must be:

```text
explicitly identified
derived from a known formal base
replayable
discardable
separate from formal state
clear about legal versus free structural research mode
```

User intent changes a target or experiment request. Domain authorities decide
legality and derived facts.

No Sandbox action may silently modify ChartVersion, LifeCase, formal path,
reality history or global theory.

### 2.8 Lab

Mingli Lab is the professional and research Sandbox mode of the same Workspace.
It is not a second Graph, Reasoner, Relation system or Path system.

Lab has two separately governed layers:

```text
Lab Shell
Workspace, Sandbox, A/B comparison, time scan, save, restore and shared focus

Lab Intelligence
Relation lenses, path assistance, validation, evidence comparison and research
```

Lab Shell requirements may inform the future Scene contract. Lab Intelligence
engineering remains blocked until its Relation and Path authorities are
formally authorized.

## 3. Formal Product Invariants

The following rules may not be traded for speed, convenience or visual polish:

1. One fact has one authority.
2. One professional judgment has one provenance chain.
3. One semantic object keeps one identity across Projections.
4. The page and Abu describe the same committed cognition.
5. Renderer behavior never becomes Mingli reasoning.
6. User intent never directly mutates a Mingli fact.
7. Sandbox never silently writes formal state.
8. Role filtering occurs before Projection and cannot be reversed downstream.
9. Theater and Xiangfa add expression, never new professional meaning.
10. Historical LifeCase cognition remains readable after implementation
    upgrades and is never silently rewritten.

## 4. Product Modes Are Not Products

The product has one Workspace and several modes. It does not have separate
OneCanvas, Xiangfa, Theater, Abu and Lab products.

```text
Li / OneCanvas: semantic structure
Xiang / Xiangfa: visual mapping of that structure
Time / Theater: temporal behavior of that Scene
Abu: explanation and approved action across the Scene
Lab: isolated experimentation over the same Scene
```

This constitution supersedes the categorical statement in
`PRODUCT_CONSTITUTION_V1_1.md` that Life Theater is simply a current-stage
non-goal. Theater is permitted only as a controlled Projection of approved
Case cognition. This clarification does not authorize new Theater production,
feature expansion or public release.

## 5. Product Validation Freeze

The current phase proves the product before changing the implementation under
review.

> **Freeze applies to implementation, not to product thinking.**

The freeze protects evidence and authority. It does not prohibit exploration
that remains outside the active review build and formal product runtime.

```yaml
phase: Product Validation Freeze
goal:
  prove:
    - users understand formal versus Sandbox state
    - users understand system-derived versus user-selected state
    - the current product interaction is usable without guidance
not_goal:
  - change the R1 implementation under review
  - use new test counts as a substitute for human evidence
  - ship unvalidated animation or UI changes
  - implement future algorithms early
  - create a parallel production owner
```

### 5.1 Always Allowed

The following work may continue throughout Product Validation Freeze:

```text
product thinking
UX and interaction discussion
information architecture
brand and business-model exploration
Abu character and companion planning
Workspace and Lab planning
Blueprints
architecture discussion and research
isolated low- or high-fidelity design studies
future-world and product-kernel exploration
```

These outputs are references for later Gates. They are not evidence that the
current Gate passed and they do not authorize implementation.

An isolated design study is allowed only when it:

- does not modify the R1 review build, tasks, routes or presentation;
- does not become an active or production product route;
- does not write formal state or create Mingli facts;
- does not become a new Scene, Relation, Path or Reasoner owner;
- is explicitly marked as planning, Blueprint or Target Reference;
- can be discarded without changing the current product.

### 5.2 Frozen Implementation

The following work remains frozen until its Gate authorizes it:

```text
R1 code and presentation changes
Relation Core V2 and Path Core V2 implementation
RA1–RA3 engineering
Canonical Scene production implementation
new runtime Projection implementation
production UI and route migration
Legacy retirement changes
formal-state contract changes
```

Discussion and design for these areas are allowed. Writing them into the
active product, formal authority chain or production runtime is not.

### 5.3 Promotion Boundary

Thinking may produce a design. A design may produce a Target Reference. A
Target Reference may inform a later authorized engineering slice. None of
these transitions is automatic.

```text
Thinking
→ Blueprint
→ isolated Design Study
→ future Gate decision
→ authorized implementation
```

Every promotion requires the then-current execution state to authorize the
next step.

During the hash-locked R1 review:

- all participants use the same review assets and task wording;
- ordinary usability findings are recorded and not repaired mid-study;
- only a P0 authority or fact failure may invalidate the build;
- RA1, Scene implementation and Workspace migration do not begin early;
- thinking and isolated design work may continue, but it cannot alter the
  Workspace Target Reference's authority status or the active review evidence.

## 6. Admission Test for Every Future Change

Every proposed feature, algorithm, page, asset or refactor must answer:

1. **Which Workspace mode owns this user task?**
2. **Which Canonical Scene does it consume?**
3. **How does it preserve the formal chain from facts to Reasoner to LifeCase
   to Projection?**

It must also pass three rejection checks:

```text
Does it directly close the current authorized Gate?
Does it create a parallel owner, Scene, route or Prototype?
Can it wait until the next Gate without harming current validation?
```

If the first answer is no, the second is yes, or the third is yes, the work
enters the backlog instead of implementation.

## 7. Change Governance

This constitution governs product identity and authority boundaries.

```text
Product Kernel Constitution
→ defines what the product is

v50_execution_state.yaml
→ defines what work is currently authorized

Roadmap and Gate evidence
→ define the ordered proof required to advance

Target References
→ demonstrate desired experience without becoming production authority
```

No Markdown document may silently authorize engineering that the machine
execution state blocks.

Changes to this constitution require:

- a named product conflict;
- the affected invariant;
- the proposed replacement rule;
- explicit approval;
- no silent retroactive reinterpretation of prior evidence.

## 8. Frozen Direction

The long-term convergence line is:

```text
R1 human product validation
→ Canonical Scene and formal provenance convergence
→ Relation and Path authority implementation
→ Case Workspace production integration
→ Legacy retirement
```

The direction is frozen. The timing of each engineering slice remains governed
by the active Gate.

> **Do not pursue more features. Prove that one Case Workspace, one Canonical
> Scene and one formal provenance chain are correct, then carry that product
> all the way into production.**
