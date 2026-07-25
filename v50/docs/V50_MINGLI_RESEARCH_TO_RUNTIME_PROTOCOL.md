# V50 Mingli Research to Runtime Protocol

Status: constitutional rule

## Purpose

This protocol prevents three failures:

1. turning an untested idea into a global rule;
2. reducing case reasoning to deterministic templates;
3. treating user feedback or LLM fluency as proof of theory.

## Epistemic Roles

```text
Fact engines
  own immutable chart calculations

Mingli World Model
  stores curated theory, knowledge, cases and evidence

Deterministic analysis tools
  expose observations and counterfactuals

LLM Mingli Agent
  discovers patterns and forms case-level judgments

Epistemic Review
  performs peer-review-style checks

Human research authority
  promotes or rejects global theory and policy
```

The LLM is the case-level cognitive authority. It is not the authority for changing global theory, facts, runtime rules or model weights.

## Two Kinds Of Hypothesis

### Case hypothesis

A provisional explanation of one chart. The LLM may create, compare, reject and revise it during cognition.

Required properties:

- traceable to chart facts or retrieved knowledge;
- explicit support and counter-evidence;
- ranked against plausible alternatives;
- uncertainty retained;
- revision recorded in case memory.

### Research hypothesis

A general claim intended to affect more than one case. It must enter the research program and may not become a runtime rule merely because one reading was persuasive.

## Global Promotion Flow

```text
Open question
→ observations
→ research hypothesis
→ controlled counterexamples
→ structural / historical / statistical evidence
→ theory review
→ formal representation
→ tool or runtime candidate
→ regression and real-world validation
→ explicit promotion decision
```

Promotion is always explicit. Night runs, probes, model suggestions and case selections cannot promote anything automatically.

## Case Cognition Flow

```text
Birth profile
→ Bazi / Ziwei facts
→ Chart World Instance
→ relevant knowledge and tools
→ Pattern discovery
→ competing hypotheses
→ work path and conditional use logic
→ whole-chart and domain assertions
→ Epistemic Review
→ role-aware delivery
→ Probe and case-level revision
```

The system provides the world, tools, memory and review. The LLM performs the holistic synthesis.

## Evidence Semantics

Evidence must state what it supports and how it may be used.

```yaml
evidence:
  type: structural | simulation | historical | behavior | statistical | counter
  target: theory_id | case_hypothesis_id | assertion_id
  reliability: 0.0-1.0
  relevance: 0.0-1.0
  lifecycle: collected | verified | referenced | archived
  allowed_usage: []
  forbidden_usage: []
```

- Synthetic evidence is primary for controlled structural validation.
- Historical evidence calibrates timing and reality mapping when provenance is adequate.
- Behavior Probe evidence updates the current case; it does not validate structural theory by itself.
- Population data becomes evidence only after a defined statistical analysis.

## Runtime Promotion Gate

A global capability may enter the production path only when all are true:

1. its authority and user value are explicit;
2. facts and theory sources are traceable;
3. counterexamples and failure conditions exist;
4. tests cover what should change and what should remain invariant;
5. it does not duplicate the LLM cognitive role;
6. rollback and version boundaries are defined;
7. a human promotion decision is recorded.

Research-only modules remain outside production judgment until this gate passes.

## Probe Rules

A Probe must:

- distinguish live case hypotheses or hidden attributes;
- ask one high-information question at a time;
- explain why the question matters when needed;
- update only the case belief state and affected assertions;
- disappear from the task canvas after completion while remaining in case history.

A Probe must not rewrite natal facts, increase global theory confidence directly, or reward the system merely because the user agreed.

## Training Rules

Training is not the default name for validation or data collection.

```yaml
training_performed: false
weights_modified: false
runtime_rules_modified: false
theory_modified: false
```

These values remain false unless the run explicitly declares a training or promotion scope. Any true value must be visible in the first screen of the audit report.

Training may calibrate a defined target. It may not hide a weak world model, poor context selection or template-like reasoning.

## Long-Run Rules

Autonomous runs may collect data, execute regressions, compare models and generate candidates. They may not change core facts, theory, runtime policy, verifier redlines or weights without prior authorization.

Every long run must separate:

```text
Observed Data
Interpretation
Recommendation
```

It must leave a reproducible command, artifact manifest, redline status and explicit next-slice recommendation. It must not auto-promote the recommendation.

## Final Invariant

```text
LLM decides how to understand this chart.
The system decides what facts, knowledge, tools and checks are available.
Human research authority decides what becomes global Mingli knowledge.
User feedback revises the case, not the world.
```
