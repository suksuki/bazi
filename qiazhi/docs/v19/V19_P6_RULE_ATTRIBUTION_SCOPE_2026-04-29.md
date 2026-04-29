# V19 P6 Rule Attribution Layer Scope

Date: 2026-04-29
System: V19 Standalone Agent Lab
Status: implemented as attribution-only skeleton

## 1. Purpose

P6 adds the missing connector:

```text
feedback -> signal -> rule -> condition/input
```

This is the minimum bridge from Feedback Ledger to future learning governance.

## 2. Hard Boundary

P6 does not:

```text
auto-learn
auto-update rules
auto-promote knowledge
auto-activate rule changes
expand prediction capability
```

P6 only records attribution and candidate impact mappings.

## 3. Signal Evidence Shape

`income_stability` signals now include attribution fields:

```ts
type SignalEvidence = {
  signal: string
  value: string
  rule_id: string
  rule_version: number
  condition: string
  inputs: { path: string; value: any }[]
  confidence: number
}
```

Runtime location:

```text
inference_context.income_stability.rule_attribution.signal_evidence
```

## 4. Income Stability Rule IDs

Current rule IDs:

```text
v19.income_stability.self_capacity
v19.income_stability.wealth_presence
v19.income_stability.wealth_accessibility
v19.income_stability.volatility
v19.income_stability.structure_binding
v19.income_stability.aggregate
```

Each rule has:

```text
rule_version
condition
inputs
confidence
```

## 5. Feedback to Rule Impact Mapping

When feedback is submitted, the system creates candidate rule impact mappings when:

```text
feedback.subject_type=income_stability
or comment/tags mention income_stability / 收入稳定
or payload contains rule_attribution.signal_evidence
```

Impact records are stored as:

```text
rule_impacts[]
```

They contain:

```text
impact_id
feedback_id
subject_type
signal
observed_value
rule_id
rule_version
condition
inputs
confidence
impact_type=candidate_review
status=open
guardrails
```

## 6. New API

```text
GET /api/lab/rule-impacts
GET /api/lab/rule-impacts?feedback_id=...
GET /api/lab/rule-impacts?rule_id=...
GET /api/lab/rule-impacts?signal=income_stability
```

## 7. Admin UI

Admin now exposes:

```text
Rule Impact Mapping
- refresh all impacts
- filter income_stability impacts
- show feedback_id, signal, rule_id, condition, confidence
```

## 8. Review Meaning

This layer lets analysts answer:

```text
Which signal was criticized?
Which rule produced that signal?
Which inputs were used?
Which condition should be reviewed?
```

It still does not decide the fix.

## 9. Next Required Human Review

Analyst should review:

```text
whether rule IDs are stable
whether signal conditions are correctly named
whether inputs are sufficient for attribution
whether confidence values are meaningful
whether aggregate rule should be split further
```
