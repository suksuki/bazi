# DeepBazi Key Component Refinement Protocol v1

## 1. Purpose

DeepBazi will refine every key product component through a visible, reviewable
sequence instead of moving directly from an idea to implementation.

```text
真实任务与问题
→ 产品讨论
→ Markdown 合同
→ 单一纵向切片
→ 机器验证
→ 浏览器与真人产品审阅
→ 精修
→ 发布裁决
```

The purpose is not to slow implementation. It is to prevent a strong idea from
quietly turning into a second Reasoner, a disconnected page, an overloaded
control panel or an unreviewed product claim.

## 2. Required Contract for Every Key Component

Before implementation, the component Markdown must answer:

1. What exact user task does this component complete?
2. What is the single primary interaction object?
3. Which layer owns each fact, decision and action?
4. What is visible to each role, and what must not reach the client?
5. What state may change, and what state is immutable?
6. What happens on desktop and mobile?
7. What happens when data or evidence is missing?
8. What is explicitly out of scope?
9. What constitutes machine success?
10. What constitutes product success?

Every contract must separate:

```text
Observed Data
Interpretation
Decision
Implementation Boundary
Acceptance Evidence
```

## 3. Stage Model

```yaml
concept_discussed:
  implementation_allowed: false

contract_frozen:
  implementation_allowed: false

prototype_authorized:
  implementation_allowed: only_the_named_slice

machine_gate_passed:
  product_passed: false
  production_allowed: false

product_review_passed:
  production_allowed: only_by_explicit_release_decision

production_authorized:
  deployment_allowed: true
```

Machine success never silently becomes product success. A technically correct
component can still fail because the task is unclear, the interface is crowded,
the visual hierarchy is weak or the user cannot understand the result.

## 4. Refinement Rules

### One component, one primary task

Do not open several independent product surfaces because the underlying system
has several capabilities. Prefer one primary object and progressively disclose
the supporting controls.

### Authority before appearance

For every displayed or editable object, freeze its authority before styling it.
The frontend may project and animate; it may not invent missing Mingli meaning.

### Local context before permanent panels

Use selection lenses, anchored menus, drawers and mobile bottom sheets for
contextual controls. A control becomes permanent only when it is continuously
necessary for the primary task.

### Missing evidence stays missing

No fallback, animation, LLM expression or UI completion may reconstruct an
object filtered by role policy or absent from the formal compiler output.

### Contract defects return to fixtures

```text
semantic or authority defect
→ add a failing fixture
→ repair the compiler or contract
→ rerun protected regression

pure presentation defect
→ repair only the renderer
```

### Refinement is sequential

Each slice must be reviewable on its own. The next slice does not begin merely
because the previous slice compiled; it begins after its named gate is met.

## 5. Review Packet

Every meaningful slice leaves one small review packet:

```text
Decision / Contract Markdown
Reproduce URL or command
Desktop and mobile evidence
Machine results
Boundary status
Observed problems
Analyst questions
Next authorized slice
```

Generated reports must distinguish technical proof, product proof and release
permission. They must never describe a prototype as a completed product.

## 6. Permanent Product Discipline

1. Mingli value comes before engineering display.
2. Pages expose user-relevant state, not internal architecture.
3. Abu explains and guides but does not silently acquire new authority.
4. LLM expression cannot replace typed facts, formal state or tool results.
5. Multi-role disclosure is enforced before data reaches the renderer.
6. Mobile is a first-class task flow, not a compressed desktop page.
7. Visual polish follows information hierarchy and interaction clarity.
8. New modules do not receive production status without explicit product review.

## 7. First Application

The first component governed by this protocol is `Mingli OneCanvas`. Its next
work is defined in `V50_ONECANVAS_REFINEMENT_SPEC_V1.md`.
