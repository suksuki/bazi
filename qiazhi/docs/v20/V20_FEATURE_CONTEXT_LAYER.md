# V20 Feature Context Layer

## Final Position

V20 keeps `BaziFeature` but changes its responsibility:

```text
BaziFeature / BaziFeatureContext
= computation metadata layer
!= user portrait layer
!= rule title layer
!= question copy layer
```

The runtime chain is now:

```text
Knowledge Base
-> Rule Match / Rule Decision
-> BaziFeatureContext
-> DomainDecisionReport
-> TopicProjection
-> PortraitSummary
-> QuestionCandidate
-> EvidencePack
-> AnswerPlan
-> Deterministic Answer / LLM Practitioner Rewrite
-> Verifier
```

## Layer Boundaries

### Knowledge Base

Knowledge Base answers:

```text
What theory exists?
Where does it come from?
What are its applicable boundaries?
```

It does not directly create user-facing conclusions.

### Rule Layer

Rule Layer answers:

```text
Did this proposition match the chart?
What evidence supports it?
What counter-evidence weakens it?
What state should the rule decision hold?
```

It does not directly create portrait wording.

### Feature Context Layer

`BaziFeatureContext` answers:

```text
What structured computational context was produced after rule/fact matching?
Which domains can consume it?
How strong is it?
Which blockers, amplifiers, activations, and hooks does it expose?
```

Core fields:

```text
context_id
feature_id
feature_type
domain
mechanism
source_rule_ids
evidence_atoms
counter_evidence_atoms
strength_score
confidence_score
decision_state
readiness
blockers
amplifiers
affected_domains
time_scope
activation_sources
projection_hooks
question_hooks
answer_hooks
boundary_flags
trace_nodes
```

This layer is the computation bus for:

```text
PortraitProjection
QuestionCandidate
AnswerPlan
LLM context
feedback learning
question ranking
synthetic validation
corpus diff
Bayesian / LTR calibration
```

### Portrait Layer

Portrait answers:

```text
How should a practitioner label and summarize this chart by topic?
```

Portraits consume `TopicProjection` and `BaziFeatureContext`. They must not directly reuse:

```text
rule title
feature debug title
raw score label
source key
```

### Question Layer

Questions answer:

```text
What should the user naturally ask next from this chart's strongest structural path?
```

Question generation should follow:

```text
DecisionReport / RuntimeDecisionFusion
-> PortraitAxis
-> BaziFeatureContext
-> UserIntentTemplate
-> QuestionCandidate
```

It must not follow:

```text
rule_title -> question_title
feature_title -> question_title
```

## Strong Decision Policy

V20 avoids blank or pending user experience by requiring every safe enabled domain to emit a structural direction:

```text
confirmed
candidate
weak_candidate
mixed
volatile
countered
blocked
```

High-risk topics can still keep internal boundaries, but user-facing output should become:

```text
direction + confidence + boundary + next question
```

not:

```text
out_of_scope
requires_review
cannot decide
```

## Practitioner Revision

Practitioner input is a revision layer, not a replacement layer:

```text
System decision
-> practitioner revision
-> fused runtime decision
-> refreshed portrait/question/answer
```

Practitioner can revise:

```text
decision_state
confidence delta
counter-evidence
projection weight
question priority
display tone
```

Practitioner must not mutate:

```text
ChartFacts
CalendarFacts
TenGodFacts
BranchRelationFacts
Rule truth
```

## Learning Position

Learning models can optimize:

```text
FeatureContext ranking
rule collision weights
counter-evidence strength
TopicProjection weight
QuestionCandidate ranking
AnswerPlan focus order
```

Learning models must not directly create:

```text
new chart facts
hard fortune conclusions
unguarded health/lifespan/disaster claims
rule truth mutation at runtime
```

The default rollout remains:

```text
deterministic baseline
-> shadow learning report
-> validation diff
-> promotion gate
-> active runtime policy
```

