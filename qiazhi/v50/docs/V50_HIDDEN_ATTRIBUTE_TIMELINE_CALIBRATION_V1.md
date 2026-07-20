# V50 Hidden Attribute & Timeline Calibration v1

Status: implementation contract

## Purpose

Hidden attributes explain how one person repeatedly carries the possibilities of a chart. They are not chart facts, luck scores, personality labels, or a questionnaire product.

```text
Locked Chart Facts
        +
Prior Mingli Cognition
        +
Historical / Behavior Evidence
        +
Case Reality Beliefs
        =
Posterior Case Cognition
```

## Four Layers

1. `ChartWorldInstance`: pillars, relations, timing and Ziwei facts. Probe cannot mutate it.
2. `HiddenAttributeBelief`: stable response patterns such as pressure conversion, execution, recovery and decision style.
3. `CurrentContext`: changing reality such as occupation, family responsibility, resources and location.
4. `CaseRevision`: what the LLM now understands differently after reviewing evidence.

## Evidence-first Probe Loop

```text
Seal prior reading
-> choose one discriminating target
-> ask one observable question
-> collect structured answer
-> update case-local belief
-> LLM re-reasons only affected claims
-> preserve what did not change
-> remove the completed Probe from the task canvas
```

A response may update hypothesis ranking, assertion status, hidden-attribute belief, domain interpretation, timing manifestation and the next question. It may not update chart facts, global theory, runtime rules, model weights or another case.

## Historical Timeline Evidence

Timeline questions should declare the predicted window before receiving the answer. A useful answer separates:

- year or year range;
- event domain;
- change direction;
- recurrence or duration;
- the person's response pattern;
- no-event and uncertain answers.

`year + domain + direction` is stronger than a generic statement that a year was good or bad. A missing predicted event is negative evidence and must be retained.

## Hidden Attribute Lifecycle

```text
unknown -> candidate -> supported -> stable
                    \-> contradicted
stable -> stale when evidence is old or context has materially changed
```

One answer can create a candidate. Repeated independent observations are required for `supported` or `stable`.

## Product Behavior

- Only one active Probe is visible.
- On submit, its question and options leave the main page.
- A short revision notice explains what changed and what remained fixed.
- Raw question/answer text is not repeated in the reading canvas.
- Structured evidence remains private and auditable through Abu, Practitioner and Research modes.
- Users can ask what Abu remembers and can later correct or remove evidence.

## LLM Role

The deterministic layer locks chart facts, stores evidence and applies update boundaries. The LLM compares the prior cognition with the new evidence and writes a typed case revision. It must not use the answer to invent a new chart fact or retroactively pretend the prior prediction was different.

## Definition of Done

1. Probe plans declare evidence kind and hidden-attribute targets.
2. Responses persist structured historical/behavior evidence.
3. Case-local hidden-attribute beliefs have lifecycle and contradiction handling.
4. The LLM produces a posterior revision with changed and unchanged parts.
5. The active Probe disappears after a successful response and stays consumed after reload.
6. Chart facts and global theory remain byte-for-byte unchanged.
7. Guest, Member, Practitioner and Research projections preserve their different depths.
