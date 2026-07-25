# V50 Lessons Learned

Status: active research memory

This document stores V50 research lessons.

It is not an architecture document.

It is not a protocol.

It is the research memory of DeepBazi.

## Why This Exists

Code can be rewritten.

Theory can evolve.

But research lessons should not be lost.

V50 now has three long-term research books:

```text
Book 1: Theory
Book 2: Evidence
Book 3: Lessons Learned
```

Theory says:

```text
What do we currently believe?
```

Evidence says:

```text
Why do we trust or doubt it?
```

Lessons Learned says:

```text
What research habits and discoveries should we never forget?
```

## Lesson Schema

Each lesson should follow:

```yaml
lesson_id:
title:
summary:
why_it_matters:
source:
impact:
related_theories:
related_evidence:
status: active | revised | retired
```

## Lesson 001 — Runtime Cannot Invent Theory

```yaml
lesson_id: L001
title: Runtime cannot invent Theory.
summary: Runtime implements frozen theory; it must not create theory while executing.
why_it_matters: This prevents engineering momentum from becoming hidden theory creation.
source:
  - V50_MINGLI_RESEARCH_TO_RUNTIME_PROTOCOL.md
  - discussion.research_first
impact:
  - Research and Engineering are separated.
  - Runtime requires Theory Freeze / Formalization before implementation.
related_theories:
  - all
related_evidence:
  - none
status: active
```

Principle:

```text
Theory -> Runtime
```

Not:

```text
Runtime -> Theory
```

## Lesson 002 — Synthetic Charts Are the First Evidence Source for Structural Theory

```yaml
lesson_id: L002
title: Synthetic Charts are primary Structural Evidence.
summary: Controlled synthetic charts are better than noisy real charts for structural theory validation.
why_it_matters: Synthetic charts allow single-variable experiments such as bridge removal, converter removal, and path rerouting.
source:
  - V50_EVIDENCE_ONTOLOGY.md
  - V50_SYNTHETIC_CHART_TAXONOMY.md
impact:
  - Synthetic validation becomes the first gate for structural theory.
  - Real-world cases are used later for mapping and calibration.
related_theories:
  - T004
  - T006
related_evidence:
  - EV001
status: active
```

Principle:

```text
合成八字是结构理论验证的第一证据来源。
```

## Lesson 003 — Probe Does Not Validate Theory

```yaml
lesson_id: L003
title: Probe produces Behavior Evidence, not Theory Evidence.
summary: Probe answers calibrate reality mapping and Twin Overlay; they do not validate structural theory by themselves.
why_it_matters: This prevents user self-description from mutating chart facts or freezing theory.
source:
  - V50_EVIDENCE_ONTOLOGY.md
impact:
  - Probe is classified as Evidence Collector.
  - Behavior Evidence has limited allowed usage.
related_theories:
  - T008
related_evidence:
  - none
status: active
```

## Lesson 004 — Theory Must Be Allowed To Fail

```yaml
lesson_id: L004
title: Theory must be allowed to fail.
summary: A theory system needs Rejected Theory, Counter Evidence, and Open Questions.
why_it_matters: The goal is not more theories; the goal is better theories.
source:
  - V50_THEORY_LIBRARY.md
  - V50_OPEN_QUESTIONS.md
impact:
  - Rejected theories are preserved.
  - Counter Evidence can block promotion.
related_theories:
  - T005
related_evidence:
  - EV002
status: active
```

## Lesson 005 — Research and Engineering Must Stay Separated

```yaml
lesson_id: L005
title: Research and Engineering are separate loops.
summary: Discussion should produce Theory and Formalization before Runtime.
why_it_matters: This keeps implementation from getting ahead of theory.
source:
  - V50_MINGLI_RESEARCH_TO_RUNTIME_PROTOCOL.md
  - V50_RESEARCH_DRIVEN_DEVELOPMENT.md
impact:
  - Engineering implements research output.
  - Research decides what is ready to implement.
related_theories:
  - all
related_evidence:
  - none
status: active
```

## Lesson 006 — A Shared State Schema Was Useful but Not a Cognitive Brain

```yaml
lesson_id: L006
title: Shared state schemas help integration but cannot replace whole-chart cognition.
summary: The retired Unified State work proved that Bazi, Ziwei and context need compatible semantics, while later validation showed that state aggregation collapses meaning when treated as the final judgment layer.
why_it_matters: Keep typed facts and interoperable observations, but let the LLM Mingli Agent compare patterns and hypotheses rather than consuming a pre-flattened verdict.
source:
  - archived deterministic cognition experiments
  - V50_MINGLI_COGNITIVE_ARCHITECTURE_V1.md
impact:
  - Fact engines keep typed outputs.
  - Research state modules remain non-authoritative.
  - Production cognition must preserve chart-specific structure and counter-evidence.
related_theories:
  - T006
  - T007
  - T008
related_evidence:
  - EV003
status: revised
```

## Lesson 007 — Evidence Is Not Data

```yaml
lesson_id: L007
title: Evidence is a Trust Model.
summary: Evidence defines reliability, relevance, lifecycle, allowed usage, and theory support.
why_it_matters: Data without semantics cannot drive theory confidence responsibly.
source:
  - V50_EVIDENCE_ONTOLOGY.md
impact:
  - Evidence links Collector to Theory.
  - Evidence can support, weaken, falsify, or explicitly not support a theory.
related_theories:
  - all
related_evidence:
  - all
status: active
```

## Lesson 008 — Mechanism Is Representation Before Label

```yaml
lesson_id: L008
title: Mechanism must be represented before it is named.
summary: Mechanism should first be an AST from path, role, ablation, and state delta. Labels are presentation.
why_it_matters: Without representation, Mechanism Discovery collapses back into a rule-name library.
source:
  - V50_MECHANISM_REPRESENTATION.md
  - V50_MECHANISM_REPRESENTATION_AUDIT_PROTOCOL.md
impact:
  - Mechanism labels are not authoritative.
  - Mechanism Representation Audit is required before discovery expansion.
related_theories:
  - T004
  - T005
related_evidence:
  - EV001
  - EV002
status: active
```

## Lesson 009 — Research Culture Is the Real Framework

```yaml
lesson_id: L009
title: Research Culture is the real framework.
summary: The most important shift is the habit of asking why, seeking counter examples, demanding evidence, and pausing before implementation.
why_it_matters: Tools and architecture can be copied. Research culture compounds.
source:
  - V50_RESEARCH_DRIVEN_DEVELOPMENT.md
impact:
  - Morning Review starts with discovery, not tasks.
  - Unknowns become research fuel.
  - Nothing implemented can still be progress if an unknown is reduced.
related_theories:
  - all
related_evidence:
  - none
status: active
```

## Add New Lessons Carefully

New lessons should be added when a research habit or principle has survived:

```text
discussion
counter example
evidence
repeat use
```

Do not add a lesson merely because an idea sounds good.

Lessons are research memory, not slogans.
