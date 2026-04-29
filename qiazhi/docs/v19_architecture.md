# V19 Architecture

V19 is not cleaner legacy code.

V19 is a Bazi reasoning language.

```text
V19 = Core Bazi Engine + Product Experience
```

The current implementation phase is deliberately narrower:

```text
Implement only Core Bazi Engine + Inference Layer.
Do not implement product layers yet.
```

## 1. System Layers

```text
Layer 0: Core Bazi Engine
Layer 1: Inference Layer
Layer 2: Domain Layer
Layer 3: Contract & Verifier
Layer 4: Experience
Layer 5: Governance
```

The mandatory reasoning order is:

```text
Core Feature -> Strength -> Structure -> Inference -> Domain -> Contract -> Experience
```

No layer may skip the layer before it.

## 2. Core Bazi Engine

The Core Bazi Engine is the system moat.

Its job is to compute chart facts and structural evidence. It must not produce theme conclusions.

### Input

```text
chart:
- year pillar
- month pillar
- day pillar
- hour pillar
- luck pillar, optional
- flow pillar, optional
```

### Output

```text
CoreFeatureBundle
CoreStrengthBundle
StructureEffectBundle
```

These outputs are facts, model measurements, and structure effects. They are not user-facing prediction results.

### Module checklist

```text
Day Master
Ten Gods Mapping
Hidden Stems
Root Strength
Month Command
Support / Pressure
Relation Geometry
Structure Effects
```

### Hard boundaries

```text
Do not output wealth conclusions.
Do not output career conclusions.
Do not output relationship conclusions.
Do not output health conclusions.
Do not output good-fate or bad-fate judgments.
Do not output narrative.
```

## 3. Inference Layer

The Inference Layer is the key layer that makes V19 a real Bazi system rather than a domain-specific predictor.

Its job is to understand the chart structure.

Its job is not to judge fate.

Inference output must be directly consumable by Domain Layer.

It must emit structured computable signals, not prose descriptions.

Invalid:

```text
"wealth star is weak and the structure is complex"
```

Valid:

```text
wealth.signal_strength = weak
structure_stability = low
conflict = peer_vs_wealth
```

Every inference signal must have a stable key, bounded value set, and source binding to CoreFeatureBundle, CoreStrengthBundle, or StructureEffectBundle.

### Input

```text
CoreFeatureBundle
CoreStrengthBundle
StructureEffectBundle
```

### Output

```text
BaziInferenceBundle
```

### Required sections

```text
day_master_state
ten_god_structure
energy_flow
structural_stability
internal_conflicts
uncertainty_sources
```

### Day master state

Allowed output concepts:

```text
strong
weak
balanced
leaning_strong
leaning_weak
following_tendency_possible
```

This is a structural state, not a final useful-god judgment.

### Ten gods structure

The Inference Layer must describe the overall relationship among:

```text
wealth
officer
seal
output
peer
```

It may describe distribution, dominance, activity, absence, and interaction direction.

It must not map directly to life outcomes.

### Energy flow

The Inference Layer must describe generation and control paths:

```text
who_generates_who
who_controls_who
who_is_drained
who_is_supported
who_is_pressured
```

Energy flow is structural analysis only.

### Structural stability

The Inference Layer must describe whether the chart structure is:

```text
stable
unstable
mixed
activated
locked
conflicted
```

This must be based on StructureEffectBundle, not domain logic.

### Internal conflicts

The Inference Layer must detect structural tensions, including:

```text
output_vs_officer
peer_vs_wealth
seal_vs_output
clash_vs_combination
support_vs_pressure
```

These are conflict signals, not predictions.

### Uncertainty sources

The Inference Layer must explicitly emit uncertainty when required:

```text
missing_luck_flow
ambiguous_structure
mixed_clash_and_combination
unknown_mapping
weak_signal
requires_domain_mapping
```

## 4. Domain Layer

The Domain Layer is where theme-specific prediction starts.

Current V19 migration may keep Wealth as a calibration adapter, but Wealth is not the system axis.

### Current domain

```text
Wealth
```

### Future domains

```text
Career
Relationship
Health
```

These future domains are explicitly out of scope for the current implementation phase.

### Domain input

```text
CoreFeatureBundle
CoreStrengthBundle
StructureEffectBundle
BaziInferenceBundle
```

### Domain output

```text
DomainBundle
```

Example:

```text
WealthBundle
```

### Domain rule

```text
Domain = mapping, not re-reasoning.
```

A domain may map core structure into theme-specific evidence. It must not bypass the Core Bazi Engine or Inference Layer.

Domain Layer must not introduce new inference logic.

It may only:

```text
weight inference signals
map inference signals
combine inference signals
project inference signals into a domain-specific evidence bundle
```

If a domain needs a new structural judgment, the signal must be added to Inference Layer first.

## 5. Contract & Verifier

Contract and Verifier turn domain outputs into trustworthy product outputs.

### Components

```text
Prediction Contract
Verifier
Ledger
Replay
Feedback
```

### Rules

```text
Conclusion must cite evidence.
LLM must not decide.
All outputs must be replayable.
Unsupported claims must fail closed.
```

This layer is not part of the current implementation phase.

## 6. Experience Layer

Experience is the product layer.

### Planned surfaces

```text
/demo
/oracle
/replay
Trust Metrics
Capability Boundary
```

### UX responsibilities

```text
question guidance
structured result display
evidence display
risk display
uncertainty display
feedback
sharing
```

This layer is not part of the current implementation phase.

## 7. Multilingual System

V19 must support structured multilingual expression.

Supported languages:

```text
zh
en
ko
```

Every user-facing label must support:

```json
{
  "label": {
    "zh": "...",
    "en": "...",
    "ko": "..."
  }
}
```

Multilingual coverage is required for:

```text
UI copy
Capability Boundary
Trust Metrics
Explanation
selected Knowledge Unit statements
```

This is product expression, not reasoning logic. It must not change inference results.

## 8. Role System

V19 separates users by capability and authority.

### Roles

```text
visitor
user
practitioner
admin
```

### Visitor

```text
can access demo
can access public replay
cannot write
```

### User

```text
can request prediction
can provide feedback
can access history
```

### Practitioner

```text
can create Knowledge Unit
can submit rule candidate
can participate in review
```

### Admin

```text
can activate rule
can bootstrap
can cautiously override
can monitor system
```

The role system belongs to Governance and Experience. It is not part of the current implementation phase.

## 9. Knowledge System

The core object is:

```text
Knowledge Unit
```

The intended lifecycle is:

```text
Markdown -> Knowledge Base -> sandbox candidate -> test -> PR -> activate
```

Key rule:

```text
Knowledge is not rule.
Knowledge -> evidence -> rule.
```

Knowledge must be structured. It cannot directly produce production predictions.

## 10. Governance & Evaluation Layer

V19 must keep three evolution loops:

```text
Self-Learning Loop
Practitioner Feedback Loop
Synthetic Validation Loop
```

These loops belong to Governance and Evaluation.

They must not be implemented inside Domain Layer.

They must not bypass:

```text
Knowledge -> Candidate -> Test -> PR -> Activate
```

### Self-Learning Loop

Goal:

```text
learn from real user feedback without automatically changing active rules
```

Inputs:

```text
prediction contract
ledger
user feedback
replay result
inference bundle
domain adapter output
```

Outputs:

```text
learning_signal
aggregated_insight
rule_quality_score
candidate_suggestion
```

Boundaries:

```text
must not directly modify active rule
must not directly modify Knowledge Unit
must not bypass reviewer
learning results can only enter suggestion, draft, or calibration
```

Self-learning discovers problems.

It does not decide rule activation.

### Practitioner Feedback Loop

Goal:

```text
allow practitioners to participate in knowledge and rule review
```

Role:

```text
practitioner
```

Capabilities:

```text
review Knowledge Unit
comment on inference signal
mark mapping as correct, questionable, or wrong
propose correction
submit rule candidate
review synthetic validation results
```

Boundaries:

```text
practitioner cannot activate rule
practitioner cannot directly modify production rule
practitioner feedback must enter audit trail
admin or reviewer approval is required for activation
```

Practitioner feedback judges Bazi correctness.

It does not replace governance.

### Synthetic Validation Loop

Goal:

```text
validate Core, Inference, and Domain Mapping stability with synthetic chart cases
```

Inputs:

```text
synthetic chart cases
expected inference signals
expected domain adapter outputs
expected forbidden outputs
```

Validation targets:

```text
Core Feature correctness
Strength tendency reasonableness
Structure effects expected behavior
Inference signal expected behavior
Domain mapping remains mapping only
forbidden conclusions must not appear
```

Outputs:

```text
validation_run
pass
fail
warning
drift report
regression report
```

Boundaries:

```text
synthetic validation cannot prove real-world accuracy
synthetic validation only proves system behavior matches expectation
synthetic validation cannot replace real user feedback
synthetic validation cannot automatically publish rules
```

Synthetic validation prevents regression.

It does not prove truth.

### Governance signal roles

```text
user feedback = real-world signal
practitioner feedback = professional judgment signal
synthetic validation = engineering regression signal
```

```text
Self-learning discovers.
Practitioner feedback judges.
Synthetic validation guards.
```

All three loops are advisory or evaluative.

None of them can activate rules without the governed lifecycle.

## 11. Core Principles

```text
1. Feature, Evidence, and Conclusion must stay separated.
2. LLM must not decide.
3. Domain only maps; it does not replace core reasoning.
4. Every output must be verifiable.
5. Unsupported content must fail closed.
6. Knowledge must be structured.
```

## 12. Persistence and Runtime Acceleration

V19 keeps both PostgreSQL and Redis, but their roles are not interchangeable.

```text
PostgreSQL = source of truth / persistence / auditability
Redis = accelerator / rate limit / lock / deduplication / queue-ready runtime layer
```

Redis is required for production stability.

Redis is not a source of truth.

Redis must support graceful degradation.

If Redis is unavailable:

```text
prediction may become slower
rate limiting may become weaker
cache may be missed
background jobs may be delayed
data must not be lost
system reasoning must not become incorrect
```

### PostgreSQL responsibilities

The following data must be stored in PostgreSQL:

```text
prediction contract
ledger
feedback source record
knowledge unit
rule version
audit event
user history
```

PostgreSQL stores durable facts, reviewed knowledge, contracts, rule history, audit trails, and user history.

### Redis responsibilities

Redis may be used for:

```text
rate limit
idempotency
distributed lock
cache
queue-ready job coordination
```

### Rate limit

Redis may rate limit:

```text
/demo
/oracle prediction
feedback
replay
```

### Idempotency

Redis may deduplicate:

```text
prediction request_id
feedback request_id
rule review request_id
rule activate request_id
```

Idempotency keys must not replace PostgreSQL source records.

### Distributed lock

Redis may coordinate locks for:

```text
rule activation lock
knowledge review lock
calibration job lock
```

Locks protect concurrent workflows. They do not decide final state.

### Cache

Redis may cache:

```text
active rule snapshot
trust metrics
replay public-safe cache
i18n/static config cache
```

Cached data must be rebuildable from PostgreSQL or static source files.

### Queue-ready runtime layer

Redis may support queue-ready coordination for:

```text
calibration jobs
trust metric recompute
audit chain verification
```

Queue payloads must be recoverable or reproducible from PostgreSQL state.

### Redis forbidden data

Redis must not be the only storage location for:

```text
prediction contract
ledger
feedback source record
knowledge unit
rule version
audit event
user history
```

If losing Redis would lose a business fact, the design is invalid.

## 13. Current Implementation Boundary

The current V19 work is limited to:

```text
Core Bazi Engine
Inference Layer
```

The current V19 work must not implement:

```text
new UI
new agent runtime
new replay system
new feedback system
new trust metrics
new production prediction path
new active rules
new career domain
new relationship domain
new health domain
```

Wealth may remain as a downstream calibration adapter only.

It must not become the V19 architecture center.
