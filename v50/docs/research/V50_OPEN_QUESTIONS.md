# V50 Open Questions Registry

Status: active

All V50 theory work should attach to an Open Question.

## Status Legend

```text
Question
Discussion
Observation
Hypothesis
Counter Examples
Theory Freeze
Formalization
Data Model
Runtime
Synthetic Validation
Real-world Validation
Training
```

## OQ001 — What is luck cycle?

Research Program:

```text
RP001 Timing
```

Question:

```text
大运到底是什么？
```

Current stage:

```text
Hypothesis
```

Current hypotheses:

```text
A. Second Month Command Model
B. Long-term Field Model
C. Perturbation Source Model
D. Stage Dominant Variable Model
```

Candidate theories:

```text
T001 Long-term Field Theory
T002 Second Month Command Theory
T003 Stage Dominant Variable Theory
```

What will change if this theory is true?

```text
Timing runtime, StateEvolution, mechanism ranking, and synthetic timing validation.
```

Freeze criteria:

```text
[ ] Can explain existing observations
[ ] Can handle or explain counter examples
[x] Has competing theories
[ ] Can form unified data model
[ ] Can enter Runtime without inventing new theory
[ ] Can design synthetic validation
[ ] Has real-world validation plan
```

Theory Freeze:

```text
NO
```

## OQ002 — What does annual cycle change?

Research Program:

```text
RP001 Timing
```

Question:

```text
流年到底改变什么？
```

Current stage:

```text
Hypothesis
```

Current hypotheses:

```text
A. Trigger Model
B. Short-term Field Model
C. Activation + Event Model
D. Structure Completion Model
```

Candidate theories:

```text
T006 State Evolution Theory
```

What will change if this theory is true?

```text
TemporalState must describe activation, suppression, trend, and state delta.
```

Theory Freeze:

```text
NO
```

## OQ003 — Is mechanism discovered or named?

Research Program:

```text
RP002 Mechanism
```

Question:

```text
Mechanism 是发现，还是命名？
```

Current stage:

```text
Formalization
```

Current hypothesis:

```text
Mechanism must be represented as AST first.
Label is presentation only.
Discovery should operate on AST shape, not on mechanism names.
```

Candidate theories:

```text
T004 Mechanism AST Theory
T005 Mechanism Label Library Theory (rejected)
```

What will change if this theory is true?

```text
Mechanism Discovery must operate on AST shape, not labels.
Runtime cannot add mechanism names as a substitute for discovery.
```

Required next gate:

```text
Mechanism Representation Audit v1
```

Freeze criteria:

```text
[x] Can explain existing observations
[ ] Can handle or explain counter examples
[x] Has competing theories
[x] Can form unified data model
[ ] Can enter Runtime without inventing new theory
[x] Can design synthetic validation
[ ] Has real-world validation plan
```

Theory Freeze:

```text
PARTIAL
```

## OQ004 — What does Ziwei compute?

Research Program:

```text
RP003 Ziwei
```

Question:

```text
紫微到底计算什么？
```

Current stage:

```text
Hypothesis
```

Current hypothesis:

```text
Ziwei computes Palace State Space and activation,
not Bazi-style flow.
```

Candidate theories:

```text
T007 Ziwei Palace State Space Theory
```

What will change if this theory is true?

```text
Ziwei runtime should become a PalaceStateSpace producer, not a second report engine.
```

Theory Freeze:

```text
PARTIAL
```

## OQ005 — What is Xiangfa in V50?

Research Program:

```text
RP004 Xiangfa
```

Question:

```text
象法在 V50 中到底是什么？
```

Current stage:

```text
Discussion
```

Current hypothesis:

```text
Xiangfa is a visual / narrative explanation layer over confirmed structure,
mechanism, state, and state delta.
It cannot create judgment.
```

Candidate theories:

```text
T009 Xiangfa Explanation Theory
```

What will change if this theory is true?

```text
Xiangfa must read MechanismRepresentation and UnifiedState, and it cannot create judgment.
```

Theory Freeze:

```text
NO
```

## OQ006 — How should geography enter the system?

Research Program:

```text
RP005 Context
```

Question:

```text
地理信息如何进入系统？
```

Current stage:

```text
Formalization
```

Current hypothesis:

```text
Geography is Context Overlay.
It affects domain landing, risk priority, timing interpretation,
and Xiangfa scene grounding.
It must not mutate natal facts.
```

Candidate theories:

```text
T008 Context Overlay Theory
```

What will change if this theory is true?

```text
Geography enters as RealityState / ContextOverlay evidence, not Bazi material.
```

Theory Freeze:

```text
PARTIAL
```

## OQ007 — Why is UnifiedState semantically narrow?

Research Program:

```text
RP007 Semantic Diversity
```

Question:

```text
为什么 V50 在 300 个合成 case 中只输出极少数语义状态？
```

Current stage:

```text
Observation
```

Current hypothesis:

```text
Semantic repetition primarily comes from upstream Brain / UnifiedState / winning claim vocabulary,
not from LLM Prompt.
```

Candidate theories:

```text
T010 Semantic Narrowness Theory
```

What will change if this theory is true?

```text
V50 must introduce richer DomainState / ProbabilityField semantics before Prompt tuning.
Theme Discovery, State Evolution, and Decision Support contracts become higher priority.
```

Initial evidence:

```text
EV005 Night Long-Run Semantic Narrowness Evidence
```

Theory Freeze:

```text
NO
```

## OQ008 — What is a good decision in Mingli?

Research Program:

```text
RP008 Decision Intelligence
```

Question:

```text
命理最终怎样帮助用户做一个更好的决定？
```

Current stage:

```text
Question
```

Current hypothesis:

```text
Probability Field is not enough.
DeepBazi must transform structure, probability, timing, risk, and uncertainty into Decision Field.
```

Candidate theories:

```text
T011 Life Decision Intelligence Theory
```

What will change if this theory is true?

```text
V50 product contracts must distinguish ProbabilityField from DecisionField.
Probe should optimize Decision Convergence, not only probability convergence.
User-facing output should answer: Who am I, Where am I, Where should I go, When should I move, What should I do next.
```

Theory Freeze:

```text
NO
```
