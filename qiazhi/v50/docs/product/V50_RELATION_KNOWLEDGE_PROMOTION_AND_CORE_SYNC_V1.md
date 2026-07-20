# V50 Relation Knowledge Promotion and Core Synchronization v1

```yaml
status: FROZEN_DESIGN_BASELINE
frozen_at: 2026-07-19
implementation_started: false
current_gate: R1_HUMAN_PRODUCT_REVIEW
ra1_authorized: false
reasoner_contract_change_authorized: false
life_case_migration_authorized: false
production_deployment: false
```

## 0. Principle

> Visual experience exposes a problem. Relation Atlas defines the knowledge.
> Fixtures prove the rule. Core algorithms absorb deterministic knowledge.
> Reasoner handles comparative interpretation. OneCanvas only presents the
> resulting authority.

OneCanvas is both a product surface and a microscope for the core algorithms.
It may reveal missing, over-generated or incorrectly typed relations, but it
has no authority to turn an observation into a rule.

## 1. Authority Boundary

```text
Chart / temporal facts
        ↓
Relation Core
        ↓
validated relation instances
        ↓
Path Core
        ↓
candidate paths + discrete evidence
        ↓
LLM Reasoner comparative interpretation
        ↓
professional gate
        ↓
LifeCase committed cognition
        ↓
OneCanvas / Abu / Theater / Xiangfa
```

### Core algorithm authority

- calendar and four-pillar facts;
- atomic and composite relation recognition;
- temporal stage and completion/removal behavior;
- path transition eligibility and direction;
- whole-path continuity, temporal coherence, blocking and closure;
- deterministic provenance and version references.

### LLM Reasoner authority

- compare validated candidate paths;
- interpret competing mechanisms and conditions;
- combine Pattern, counter-evidence and the user's current question;
- produce a proposal that cites relation and evidence IDs.

The LLM may not create a relation absent from Relation Core, bypass path policy,
claim an unvalidated path is closed, or directly promote a proposal to
`committed`.

### Visual authority

OneCanvas may render, focus, animate and explain supplied semantics. It may not
infer relations, repair missing graph objects, promote candidates or write
formal cognition.

## 2. What Belongs in Deterministic Core

Candidate knowledge for deterministic promotion includes:

```text
five-element generating, draining, controlling, consuming and peer relations
stem combinations and their conditions
branch harmony, clash, harm and break
three-harmony, half-harmony, three-meeting, three-punishment and self-punishment
hidden stems, root support, stem reveal and same-pillar relations
luck/year interaction with natal structure
temporal completion, activation, weakening, blocking and reopening
```

Core relations must preserve:

- binary versus hyperrelation arity;
- multiple relations between the same semantic objects;
- natal, luck, annual and cross-stage identity;
- formation, support and blocking conditions;
- `school_profile` and provenance;
- candidate versus committed epistemic status.

## 3. What Must Not Become an Unversioned Global Rule

### School-specific knowledge

Disputed rules enter a versioned `SchoolProfile`, not a universal table.

### Whole-chart professional judgment

Questions such as primary work path, bind versus transformation, activation
versus destruction, and pattern commitment remain comparative reasoning tasks.
Core supplies candidates and evidence; Reasoner and the professional gate make
the case-level judgment.

### Presentation choices

Line style, animation timing, node glow, mobile layout and visual metaphors
belong to the Presentation Grammar. They never define a Mingli relation.

### User PathDraft and product telemetry

Repeated user attempts are `ResearchObservation`, not training labels or formal
rules. They may open a promotion item only after professional triage.

## 4. Knowledge Promotion Lifecycle

```text
OBSERVED
→ DEFINED
→ FIXTURE_READY
→ CORE_IMPLEMENTED
→ CORPUS_AUDITED
→ ANALYST_APPROVED
→ VERSIONED_RELEASE
```

Items may also become `DEFERRED`, `SCHOOL_SCOPED` or `REJECTED`.

### 4.1 Observed

Sources may include OneCanvas review, a real LifeCase, professional review,
Reasoner/Graph conflict, Relation Atlas traversal or recurring PathDrafts.

An observation states the discrepancy without prescribing a rule.

### 4.2 Defined

The proposal must answer:

```text
What relation is this?
How many participants does it have?
Is it directed or symmetric?
When does it form?
When does it fail?
How does time complete, weaken or remove it?
Can it participate in a work path?
Which school owns the claim?
```

### 4.3 Fixture ready

Every proposed deterministic rule requires at least:

```text
minimal positive case
minimal negative case
one-condition-missing case
luck completion case
annual completion case
temporal disruption case
removal-and-restoration case
multiple-relations-coexist case
```

No core implementation begins until the new Fixture fails for the intended
reason.

### 4.4 Core implemented

The smallest owning module is changed. Renderer, prompts and post-processing
must not be used to hide an unimplemented relation rule.

### 4.5 Corpus audited

Every core rule change runs a differential audit across the available LifeCase
corpus:

```text
relations added or removed
formal paths invalidated
candidate paths changed
historical cognition requiring review
role disclosures changed
```

Passing unit tests is not sufficient.

### 4.6 Analyst approved and released

The analyst reviews fixtures and corpus differences. A release records rule,
policy, validator and school-profile versions. Historical LifeCases retain the
versions that produced them and are never silently rewritten.

## 5. Knowledge Promotion Register Contract

```yaml
knowledge_id:
title:
discovered_from:
observation:
classification: deterministic_core | school_scoped | reasoner_protocol | presentation
relation_family:
school_profile:
definition_ref:
positive_fixtures: []
negative_fixtures: []
temporal_fixtures: []
path_eligibility: true | false | conditional | not_applicable
affected_modules: []
corpus_diff_ref:
analyst_decision:
status: observed | defined | fixture_ready | implemented | analyst_approved | released | deferred | rejected
versions:
  relation_rule_version:
  path_policy_version:
  whole_path_validator_version:
```

## 6. Initial Register

These entries record current audit findings only. None is authorized for core
implementation before R1 passes.

| Knowledge ID | Finding | Classification | Status |
| --- | --- | --- | --- |
| REL-HYPER-001 | three-harmony is currently sample-specialized and flattened | deterministic core | observed |
| REL-HYPER-002 | three-meeting needs a complete multi-node model | deterministic core | observed |
| REL-HYPER-003 | three-punishment and self-punishment need complete coverage | deterministic core | observed |
| REL-MULTI-001 | multiple relation types on one node pair must coexist | deterministic core | observed |
| REL-TIME-001 | relation stages and temporal completion/removal need stable provenance | deterministic core | observed |
| PATH-POLICY-001 | current path eligibility is too broad | deterministic core | observed |
| PATH-VALID-001 | segment existence does not prove whole-path closure | deterministic core | observed |
| PATH-EVIDENCE-001 | uncalibrated aggregate scores must not imply precision | path/reasoner contract | observed |

## 7. Unified Post-R1 Delivery Sequence

The `RA` identifier is used only for Relation Atlas and core synchronization.
This sequence supersedes earlier conflicting RA1–RA5 package labels.

### RA1: Ontology, provenance and Fixtures

- RelationDefinition;
- BinaryRelation and HyperRelation;
- ContextModifier and TemporalActivation;
- RelationProvenance;
- stable `relation_type_id`;
- `school_profile`;
- positive, negative and temporal Fixtures.

RA1 adds no ordinary-user UI and does not change the Reasoner contract.

### RA2: Relation Core

- typed temporal multigraph;
- hyperrelation instances;
- multiple-edge preservation;
- stage-aware relation compilation;
- graph health audit.

### RA3: Path Core

- PathTransitionPolicy;
- Candidate Path Generator;
- WholePathValidator;
- discrete PathEvidenceVector;
- isolation of legacy uncalibrated scores.

### RA4: Historical differential audit

- full LifeCase relation/path diff;
- invalidated commitment list;
- analyst review queue;
- old-version replay proof.

### RA5: Reasoner Contract

Reasoner consumes validated `RelationGraphSpec`, `CandidatePaths` and
`PathEvidenceVector`, and must cite relation/evidence IDs.

### RA6: LifeCase versioned write

Formal paths store node/edge references, provenance, validation versions,
Reasoner source, analyst gate and commit time.

### RA7: Shared projections

OneCanvas, Abu, Theater and Xiangfa consume the versioned formal output. They do
not reimplement relation or path logic.

## 8. Gates

```text
R1 human product PASS
        ↓
RA1 ontology Fixtures PASS
        ↓
RA2 relation determinism and provenance PASS
        ↓
RA3 path validation PASS
        ↓
RA4 corpus differential audit and analyst disposition PASS
        ↓
RA5 Reasoner citation contract PASS
        ↓
RA6 versioned LifeCase write PASS
        ↓
RA7 projection fidelity PASS
        ↓
assisted path and production remain separately authorized
```

## 9. Non-negotiable Invariants

1. A UI observation never becomes a core rule directly.
2. A user PathDraft never becomes training truth or committed cognition.
3. Every new deterministic rule starts with a failing Fixture.
4. Hyperrelations never masquerade as unrelated binary edges.
5. Relation existence never automatically grants path eligibility.
6. Segment validity never automatically grants whole-path validity.
7. LLM proposals cite existing relation and evidence IDs.
8. A core upgrade always produces a corpus differential audit.
9. Historical LifeCases retain replayable rule versions.
10. OneCanvas, Abu, Theater and Xiangfa remain projections, not shadow engines.

