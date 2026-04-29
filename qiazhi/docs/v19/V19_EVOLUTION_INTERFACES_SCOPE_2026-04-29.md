# V19 Evolution Interfaces Scope

Date: 2026-04-29
System name: V19 Standalone Agent Lab
Status: interface skeleton implemented

## 1. Purpose

This scope adds the first self-evolution interface skeleton without expanding prediction capability.

The goal is not automatic learning yet. The goal is to create auditable entry points for:

```text
feedback -> ledger -> analyst review queue -> synthetic validation -> possible future promotion
```

## 2. Hard Boundary

Feedback must not directly modify:

```text
active knowledge
reviewed evidence templates
income_stability rules
chart algorithms
LLM prompts used as primary output
```

Promotion requests are review records only.

Synthetic validation is regression support only, not domain truth.

## 3. Implemented Interfaces

### Feedback Ledger

```text
POST /api/lab/feedback
GET  /api/lab/feedback
```

Purpose:

```text
Collect analyst / practitioner / user / admin feedback as review signals.
```

Guardrails:

```text
FEEDBACK_IS_SIGNAL_NOT_RULE
REQUIRES_ANALYST_REVIEW
NO_AUTO_LEARNING
```

### Analyst Review Queue

```text
POST /api/lab/promotions
GET  /api/lab/promotions
POST /api/lab/promotions/{promotion_id}/status
```

Purpose:

```text
Create review requests such as feedback_to_knowledge, knowledge_to_rule, rule_activation.
```

Current behavior:

```text
request only
no auto promotion
no active rule mutation
```

### Synthetic Validation Harness

```text
POST /api/lab/validation/seed
GET  /api/lab/validation/cases
POST /api/lab/validation/run
GET  /api/lab/validation/runs
```

Current seeded cases:

```text
syn.income_stability.1990_05_12_male_2025
syn.income_stability.lunar_conversion_boundary
```

Validation scope:

```text
deterministic income_stability regression
lunar-to-solar conversion boundary behavior
```

### Role Boundary

Current accepted roles:

```text
user
analyst
practitioner
admin
system
```

This is not full auth yet. It is a role-tagged interface boundary for review data.

### Multilingual Label Contract

```text
GET /api/lab/labels?locale=zh|en|ko
```

Purpose:

```text
Expose stable labels and descriptions without changing underlying rules.
```

Initial terms:

```text
income_stability
time_structure
knowledge_evidence_store
analyst_review_required
```

Guardrail:

```text
LABELS_ONLY
NO_TRANSLATED_RULE_CHANGE
```

## 4. Admin UI

Admin now includes:

```text
Evolution Interfaces
- Feedback Ledger
- Analyst Review Queue
- Synthetic Validation
- Multilingual Labels
```

## 5. Storage

Runtime file:

```text
v19/.runtime/lab_interfaces.json
```

Optional PostgreSQL table when DB is enabled:

```text
v19_lab_ledger
```

The file remains a fallback / mirror.

## 6. Verification Snapshot

Smoke test result:

```text
/api/lab/status -> evolution_interfaces_only_no_auto_rule_activation
POST /api/lab/feedback -> ok
POST /api/lab/promotions -> draft_review
POST /api/lab/validation/seed -> 2 cases
POST /api/lab/validation/run -> 2 / 2 passed
GET /api/lab/labels?locale=en -> ok
```

## 7. Current Non-Goals

Not implemented yet:

```text
full authentication
permission enforcement
rule mutation
knowledge diff editor
automatic promotion
automatic model learning
large synthetic case generator
analyst comment threading
multi-user account management
```

These remain future work.
