# V19 Standalone Agent Lab Scope Lock

Date: 2026-04-29
Reason: Analyst review boundary correction
Status: accepted and applied

## 1. Rename / Scope Clarification

The current system must be referred to as:

```text
V19 Standalone Agent Lab
```

It must not be confused with the earlier static UI prototype:

```text
frontend/app/v19/oracle
```

Current system shape:

```text
FastAPI backend
Admin
DB configuration
LLM configuration
Knowledge Evidence Store
Session storage
Agent loop
Frontend review lab
```

This is an analyst review lab, not a public prediction product.

## 2. Product Readiness Boundary

Current verdict:

```text
Can be used for analyst review.
Cannot be used as public fortune prediction product.
```

Reasons:

```text
chart algorithm is prototype-grade
solar-term boundaries are approximate
luck-cycle start age is approximate
lunar input is converted to solar before structure calculation
timezone / birthplace not modeled
knowledge store is evidence-only
income_stability is bounded structure signal only
```

## 3. LLM Boundary Correction

Analyst feedback:

```text
bounded signal + LLM final answer raises risk
income_stability main answer must be deterministic
LLM can only be optional follow-up
```

Applied correction:

```text
income_stability query -> deterministic renderer
LLM used=false for primary income_stability answer
LLM cannot override deterministic income_stability output
```

Runtime status now returns:

```text
llm_status.used=false
llm_status.reason=deterministic_income_stability_renderer_is_primary
agent_reply.role=v19_deterministic_income_renderer
```

## 4. Income Stability Boundary

Current `income_stability` is:

```text
wealth-domain structure signal
not wealth prediction
not yearly fortune
not traditional judgement
not good/bad text
```

Current rule contract:

```text
income_stability = f(
  self_capacity,
  wealth_presence,
  wealth_accessibility,
  volatility,
  structure_binding
)
```

Current output example:

```text
self_capacity=high
wealth_presence=medium
wealth_accessibility=clear
volatility=low
structure_binding=none
income_stability=stable
is_prediction=false
scope=static_natal_structure_only
```

## 5. Time Structure Boundary

P4 time structure remains:

```text
context only
not prediction
not direct inference modifier
```

UI must label it clearly:

```text
Time Structure · context only · not prediction · P4 does not change inference
```

Any future use of luck cycle / flow year to change income_stability belongs to:

```text
P5 Time-aware inference
```

## 6. Knowledge System Boundary

Current knowledge system is:

```text
Knowledge Evidence Store
```

It is not yet:

```text
Rule Knowledge Database
```

Current knowledge units are reviewed evidence templates. They may provide evidence context and wording constraints, but they must not directly execute rules or produce predictions.

## 7. Algorithm Status Requirement

Agent output now includes:

```text
algorithm_status
```

Required fields:

```text
system_name=V19 Standalone Agent Lab
public_product_ready=false
chart_structure.status=prototype
time_structure.status=context_only
knowledge.status=evidence_store
income_stability.status=deterministic_structure_signal
llm.status=optional_explanation
```

## 8. Applied Engineering Changes

Files changed:

```text
v19/agent/renderers.py
v19/server.py
v19/llm.py
v19/knowledge/seeds.py
v19/knowledge_store.py
v19/frontend/index.html
v19/frontend/admin.html
v19/frontend/assets/app.js
v19/frontend/assets/styles.css
```

Key applied behavior:

```text
income_stability primary answer is deterministic
LLM no longer overrides income_stability
Knowledge Evidence Store label added
Algorithm Status visible in UI
Time Structure label strengthened
wealth.income_stability_rule_basis promoted in retrieval ranking
```

## 9. Verification Snapshot

Test request:

```text
基于当前结构，说明 income_stability 的规则判断依据，不要讲传统断语。
```

Observed result:

```text
agent_reply.role=v19_deterministic_income_renderer
llm_status.used=false
llm_status.reason=deterministic_income_stability_renderer_is_primary
knowledge top hit=wealth.income_stability_rule_basis
response time=0.017s
```

Signal result:

```text
self_capacity=high
wealth_presence=medium
wealth_accessibility=clear
volatility=low
structure_binding=none
income_stability=stable
```

## 10. Next Review Priorities

Do not expand features before these reviews:

```text
1. Analyst review of 13 seed knowledge units
2. Analyst review of income_stability signal mapping
3. Calendar / solar-term correctness review
4. Luck-cycle start-age algorithm review
5. Deterministic renderer wording review
```
