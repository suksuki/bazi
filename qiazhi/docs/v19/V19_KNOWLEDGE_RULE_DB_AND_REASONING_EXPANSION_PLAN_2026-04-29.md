# V19 Knowledge Rule DB and Reasoning Expansion Plan

Date: 2026-04-29
Status: Design lock / scope guard
System: V19 Guided Bazi Agent + Analyst Lab + Chinese Governance Console

## 1. Positioning

V19 currently has a Knowledge Evidence Store, deterministic `income_stability`, Feedback Ledger, Rule Attribution, Guided Question governance, and Admin/Lab review workflows.

The next knowledge phase is not immediate prediction expansion. It is the creation of a governed Rule Knowledge Database design that can later support audited inference extensions.

```text
Knowledge Evidence Store
→ Rule Proposal
→ Validation
→ Analyst/Admin Approval
→ Version Record
→ Future Engineering Implementation
```

The system must not become an LLM fortune-telling system.

## 2. Core Boundary

The following are locked:

```text
1. No automatic rule activation
2. No automatic inference expansion
3. No time-aware income_stability until a future approved P5/P12 layer
4. No fortune / good-bad / traditional prediction text
5. No LLM-authored active rules
6. No direct DB rule mutation into runtime inference
7. Knowledge does not override chart structure
8. Time Context remains context only unless a future approved inference layer is implemented
```

## 3. Knowledge Categories

### 3.1 Day Master and Five-Phase Relations

Purpose:
Define structural relationships between day master, stems, branches, and element distribution.

Allowed outputs:

```text
structural_signal
support_pressure_relation
capacity_context
```

Forbidden outputs:

```text
fortune
life outcome
wealth prediction
health prediction
marriage prediction
```

Example safe rule shape:

```json
{
  "rule_id": "v19.bazi.day_master.element_relation.wood_support.v1",
  "domain": "bazi_structure",
  "version": 1,
  "status": "proposal",
  "input_contract": {
    "required": ["chart.day_master", "chart.pillars", "element_distribution"]
  },
  "condition": {
    "day_master_element": "wood",
    "supporting_elements_present": ["water", "wood"]
  },
  "output_contract": {
    "signal": "self_capacity_context",
    "value_set": ["low", "medium", "high", "unknown"]
  },
  "reasoning_path": [
    "identify day master element",
    "inspect support and pressure elements",
    "emit structural context only"
  ],
  "confidence": 0.0,
  "review": {
    "required": true,
    "approved_by": "",
    "approved_at": ""
  },
  "guardrails": ["STRUCTURE_ONLY", "NO_PREDICTION"]
}
```

### 3.2 Structural Relations

Includes:

```text
六合
三合
六冲
刑
害
破
```

Allowed outputs:

```text
relations_with_natal
relation_count
relation_type
structural_volatility_context
```

Forbidden outputs:

```text
bad year
good opportunity
fortune conclusion
traditional omen text
```

Safe wording:

```text
巳亥冲 is a structural relation marker. It may be used as volatility context only after approved inference mapping.
```

### 3.3 Ten Gods

Ten Gods may be stored as relationship metadata.

Allowed:

```text
ten_god_label
ten_god_relation_to_day_master
structural_role
```

Forbidden:

```text
Ten God label directly implies career success
Ten God label directly implies wealth outcome
Ten God label directly implies personality or destiny conclusion
```

Rule boundary:

```text
Ten God labels are relational metadata, not conclusions.
```

### 3.4 Time Structure

Includes:

```text
luck_cycle
flow_year
relations_with_natal
relations_with_luck_cycle
```

Allowed outputs:

```text
time_context
relation_context
time_relation_summary
```

Forbidden outputs:

```text
flow-year prediction
luck-cycle prediction
this year wealth is good/bad
this year opportunity/risk conclusion
```

Locked rule:

```text
Time Context does not directly modify income_stability in the current system.
```

## 4. Rule Knowledge DB Schema

Minimum schema for future executable-rule proposals:

```ts
type BaziRuleKnowledgeUnit = {
  rule_id: string
  version: number
  domain:
    | "day_master_element"
    | "structural_relation"
    | "ten_god_relation"
    | "time_structure"
    | "income_stability"

  status:
    | "draft"
    | "proposal"
    | "validation_ready"
    | "approved"
    | "active_record"
    | "deprecated"

  input_contract: {
    required: string[]
    optional?: string[]
    forbidden?: string[]
  }

  condition: Record<string, unknown>

  output_contract: {
    signal: string
    value_set: string[]
    is_prediction: false
  }

  reasoning_path: string[]

  evidence: {
    source_ids: string[]
    reviewed_by?: string
    notes?: string
  }

  confidence: number

  review: {
    required: true
    approved_by: string
    approved_at: string
    notes: string[]
  }

  validation: {
    required: true
    latest_run_id?: string
    passed?: boolean
  }

  versioning: {
    created_at: string
    updated_at: string
    supersedes?: string
    changelog: string[]
  }

  guardrails: string[]
}
```

## 5. Inference Engine Expansion Policy

New knowledge can only affect runtime inference after this sequence:

```text
1. Evidence collected
2. Rule proposal created
3. Synthetic validation case added
4. Analyst/Admin approval
5. Version record created
6. Engineering implementation maps approved rule into deterministic code
7. Regression tests confirm existing signals unchanged unless explicitly intended
```

Important:

```text
DB active_record does not equal runtime activation.
Runtime activation requires explicit engineering implementation.
```

## 6. Current Runtime Scope

Currently active runtime inference:

```text
income_stability only
```

Currently non-runtime knowledge:

```text
Day Master / Five-Phase expansions
Ten God expansions
Structural relation expansions
Time Structure expansions
```

These may be stored as evidence/proposals but must not change `/oracle` ResultCard.

## 7. Time Context Policy

Current policy:

```text
P4/P8/P10: Time Context is context only.
```

Future policy requires explicit new phase:

```text
P12 or later: Time-aware inference proposal
```

P12 would require:

```text
1. Separate signal namespace
2. TimeContext input contract
3. Regression tests proving static income_stability unchanged
4. UI boundary labels
5. Analyst review
```

## 8. Feedback and Review Flow

Rule and question changes share a governance principle:

```text
Feedback
→ Review Queue
→ Proposal
→ Validation
→ Approval
→ Version Record
→ Future Engineering Implementation
```

Feedback never directly mutates:

```text
QUESTION_LIBRARY
runtime inference
active rule code
ranking weights
```

## 9. Deliverables for the Next Implementation Phase

Recommended next phase:

```text
P12-A: Rule Knowledge DB Proposal Ledger
```

Scope:

```text
1. Add rule proposal ledger for BaziRuleKnowledgeUnit
2. Add validation checks for schema completeness
3. Add Admin review panel
4. Do not connect to runtime inference
```

Not in scope:

```text
1. New predictions
2. Time-aware income_stability
3. LLM-generated active rules
4. Automatic rule activation
```

## 10. Acceptance Criteria

Design acceptance requires:

```text
1. Rule schema exists
2. Knowledge categories are defined
3. Runtime boundaries are explicit
4. Time Context remains context-only
5. Feedback/proposal/review/version path is mandatory
6. No rule can become runtime-active automatically
```

## 11. Final Verdict

V19 is ready to design a governed Rule Knowledge DB.

V19 is not ready to expand public prediction capabilities.

The correct next step is governance-first rule proposal infrastructure, not broader inference.
