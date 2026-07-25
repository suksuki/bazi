# V50 Research Driven Development

Status: active research rhythm

Mission:

```text
docs/V50_MISSION_AND_INTELLIGENCE_DEFINITION.md
```

Research memory:

```text
docs/V50_LESSONS_LEARNED.md
```

RDD serves the V50 north star:

```text
Discover. Verify. Evolve.
```

Implementation KPI:

```text
Increase Human Decision Confidence.
```

V50 has entered Research Driven Development.

This is not TDD.

This is not DDD.

This is RDD:

```text
Research Driven Development
```

## Core Shift

V50 daily review should not start with:

```text
What should we build next?
```

It should start with:

```text
What did we actually learn yesterday?
```

Chinese:

```text
不要先问今天写什么。
先问昨天最大的发现是什么。
```

## Success Metric

V50 progress is not measured by:

```text
new modules
new files
new adapters
new prompts
```

V50 progress is measured by:

```text
one less unknown
one clearer theory
one stronger evidence link
one falsified assumption
one better bottleneck definition
one improved path to Discover / Verify / Evolve
```

Even when nothing is implemented, V50 can still move forward if an unknown becomes clearer.

## Daily Morning Review

Every morning review should include:

```text
1. Yesterday's Discoveries
2. Current Bottleneck
3. Unknowns
4. Theory Confidence Changes
5. Evidence Added
6. What Not To Build Yet
7. Next Research Move
8. Decision Confidence Impact
```

## Daily Implementation Review

Once V50 enters implementation work, each day must also answer:

```text
Which Research Program moved forward?
Which Theory gained or lost Evidence?
How did this move V50 closer to Decision Intelligence / Decision Confidence?
```

Current implementation authority is defined by `docs/V50_CURRENT_ARCHITECTURE.md` and `docs/V50_RUNTIME_MODULE_AUTHORITY_MAP_V1.md`.

## Yesterday's Discoveries

Format:

```yaml
discovery:
evidence:
confidence:
impact:
need_more_research: true | false
affected_theories:
affected_runtime:
```

Example:

```yaml
discovery: Probe is not Evidence; Probe is an Evidence Collector.
evidence:
  - discussion.evidence_ontology
  - V50_EVIDENCE_ONTOLOGY.md
confidence: 0.92
impact:
  - Evidence Ontology
  - Probe / Twin boundary
  - Behavior Evidence classification
need_more_research: false
affected_theories:
  - T008 Context Overlay Theory
affected_runtime:
  - none yet
```

## Current Bottleneck

Mainline should not be organized around:

```text
Next Task
```

It should be organized around:

```text
Current Bottleneck
```

Examples:

```yaml
bottleneck: Timing Theory lacks Evidence.
type: research
severity: high
blocks:
  - State Evolution
  - Timing Model Candidate
  - real-world reading accuracy
next_move: collect Structural / Simulation / Historical Evidence
```

```yaml
bottleneck: Case readings may collapse into repeated patterns despite diverse chart facts.
type: cognition
severity: medium
blocks:
  - professional reading quality
  - trustworthy domain inference
next_move: audit Pattern attention, hypothesis diversity, context retrieval and model reasoning separately
```

## Unknowns

Unknowns should be explicit.

They are not failures.

They are the fuel of research.

Format:

```yaml
unknown_id:
domain:
question:
confidence:
status: open | narrowed | blocked | resolved
needed_evidence:
next_probe:
```

Examples:

```yaml
unknown_id: U001
domain: Timing
question: Is year primarily Activation or Short-term Field?
confidence: 0.42
status: open
needed_evidence:
  - structural timing variants
  - historical event timelines
next_probe: build competing timing evidence cases
```

```yaml
unknown_id: U002
domain: Theme
question: Can Theme be discovered from Mechanism AST + UnifiedState?
confidence: 0.31
status: open
needed_evidence:
  - theme taxonomy
  - semantic coverage report
next_probe: design Unified Theme Discovery evidence cases
```

```yaml
unknown_id: U003
domain: Ziwei
question: Can Palace State Space produce useful domain state without star-level overfitting?
confidence: 0.18
status: open
needed_evidence:
  - palace state fixtures
  - four transformation state transition cases
next_probe: Ziwei Palace State Space v1 evidence design
```

## Theory Confidence Changes

Theory confidence should change only when Evidence changes.

Format:

```yaml
theory_id:
previous_confidence:
new_confidence:
delta:
evidence_ids:
reason:
```

If there is no new Evidence, Theory confidence should not move.

## Evidence Added

Each morning review should list:

```yaml
evidence_id:
evidence_class:
supports_theories:
weakens_theories:
reliability:
relevance:
lifecycle_status:
```

This keeps the project evidence-driven instead of opinion-driven.

## What Not To Build Yet

Every morning review must include a short list of things to avoid.

Examples:

```text
Do not tune Prompt until semantic repetition is understood.
Do not implement Timing Runtime until Timing Theory has enough evidence.
Do not add Ziwei report UI before Palace State Space is validated.
Do not train weights before Synthetic Validation and Real-world Validation are separated.
```

## Next Research Move

The next move should reduce an unknown.

It should not merely add a feature.

Good:

```text
Build a Timing evidence matrix comparing Long-term Field vs Second Month Command.
```

Weak:

```text
Add Timing API.
```

Good:

```text
Run Semantic Coverage to determine whether repetition is Expression-level or UnifiedState-level.
```

Weak:

```text
Improve Prompt diversity.
```

## RDD Gate

Before any major implementation, ask:

```text
Which unknown does this reduce?
Which theory does this support or falsify?
Which evidence will it produce?
Does this make V50 better at discovering, verifying, or evolving theory?
Why is this not just engineering motion?
```

If these cannot be answered, pause implementation.

## Final Principle

V50 is not feature driven.

V50 is not module driven.

V50 is research driven.

Chinese:

```text
今天什么都不实现，也可以是一次有效推进。
前提是：我们减少了一个未知，或者更清楚地知道了未知在哪里。
```
