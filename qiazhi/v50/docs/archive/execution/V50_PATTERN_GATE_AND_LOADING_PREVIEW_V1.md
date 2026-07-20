# V50 Pattern Gate and Loading Preview v1

Status: implementation contract

## Problem

The product previously treated research-record completeness as a first-reading safety gate. A Pattern could be factually useful yet trigger up to two complete 35B regenerations because an evidence id was not copied into a hypothesis array. The user waited through every regeneration and received no Mingli content.

Observed live behavior:

```text
prompt evaluation: about 2–2.5s / 5,500 tokens
generation: about 19–26s / 1,400–1,800 tokens
maximum old Pattern calls: 3
visible reading before completion: none
```

## Two Gates

### Hard Safety Gate

These failures may block the unsafe field, but do not trigger a model rewrite:

- selected hypothesis is missing;
- primary hypothesis ownership is contradictory;
- active work and following structure are merged into one primary claim;
- chart facts, ten-god roles or element cycles conflict with the immutable ledger;
- a claim cites a fact that does not exist;
- the output crosses a prohibited safety boundary.

### Soft Epistemic Review

These issues must remain auditable but may not block the first reading or trigger complete regeneration:

- an evidence id is present in salient phenomena but not repeated in a hypothesis array;
- an alternative hypothesis lacks a detailed rejection reason;
- a hypothesis lacks a complete failure-condition list;
- salient-evidence coverage is incomplete;
- competing explanations need stronger differentiation;
- high-priority attention coverage is incomplete.

Soft issues are carried in the Hypothesis Comparison Receipt. They may be repaired by a later field-level patch or professional review. They never erase a fact-safe first look.

## Product Flow

```text
35B compact Pattern preview (420-token ceiling)
→ sanitize preview against immutable facts
→ Hard Safety Gate
→ pattern_preview_ready
→ loading preview types one concise line
→ full competing-hypothesis Pattern continues in background
→ Soft Epistemic Review is recorded
→ pattern_candidates_ready
→ work-path cognition continues
→ full reading canvas opens when the next accepted artifact arrives
```

## Loading Preview

The preview is not chain-of-thought and not raw JSON. It is a fact-safe user-facing sentence already present in `first_look`.

UI behavior:

- stays inside the existing loading scene;
- shows the label `Abu 刚看到`;
- types at most one concise line;
- uses `aria-live="polite"`;
- respects `prefers-reduced-motion`;
- later results replace the line instead of stacking messages;
- no internal evidence ids, verifier names or research warnings are shown.

## Retry Budget

```yaml
soft_review_full_regeneration: 0
hard_safety_full_regeneration: 0
transport_failure_retry: 0
schema_retry_default: 1
```

First-reading semantic repair never calls the LLM again. It uses three outcomes:

```text
deterministically repairable shape or wording → repair locally
unsafe optional field → quarantine that field
no fact-safe Pattern remains → stop before displaying a false reading
```

Prediction and Probe presentation issues use no LLM retry. The system may safely:

- soften an overconfident phrase without changing its subject or causal direction;
- remove duplicate predictions;
- cap repetitive predictions at three;
- fill missing traceability from an already accepted portrait assertion;
- add existing hypothesis ids to a Probe;
- quarantine a prediction that still conflicts with immutable facts.

The accepted Pattern and work path must survive a downstream Prediction problem.

## Constraints Removed

The following requirements were producing templates and unnecessary regeneration, so they are no longer blocking contracts:

- exactly three prior predictions;
- exactly four steps in every domain causal chain;
- exactly two assertions or list items per section;
- a Probe on every domain reading;
- complete failure-condition bookkeeping as a prerequisite for showing a fact-safe result.

Semantic completeness is still reviewed, but content determines length. Immutable chart facts, element cycles, ten-god ownership, evidence existence and public safety boundaries remain hard constraints.

## Prompt And Result Pipeline Debt

The current prompt plus regex sanitation is a transitional implementation, not the target architecture. The next refactor must separate:

```text
Task Prompt Compiler
→ typed field generation
→ field-level fact validation
→ local structural repair
→ unsafe-field quarantine
→ accepted artifact
```

Target rules:

- prompts contain the minimum context needed for one cognitive task;
- validators report a field path and fact conflict, not a keyword hit on the complete JSON string;
- a safe field is never regenerated because another field is incomplete;
- deterministic repair may fix wording, references and shape, never invent Mingli reasoning;
- regex remains only as a narrow high-risk fallback;
- accepted upstream artifacts are never erased by a downstream optional-stage failure.

## Live Baseline

The first local live run after introducing the compact preview observed:

```text
chart_ready: about 2s
pattern_preview_ready: about 4s
full Pattern: about 33s
work path: about 59s
```

The old final Prediction contract still failed at about 125s because it demanded exactly three items and rejected one soft phrase. This is the failure addressed by local Prediction normalization and the removal of arbitrary cardinality gates.

After eliminating first-reading LLM rewrite loops, the final local live run observed:

```text
chart_ready: 1.0s
safe loading preview: 4.1s
full Pattern available: 34.5s
unsafe work-path field quarantined: 59.8s
remaining prior/probe artifact: 78.0s
reading_completed: 78.0s
```

The accepted Pattern opened the result canvas immediately. Work, Ziwei and Prediction are append-only stages and no longer hold the first useful result hostage. A quarantined work path is an explicit partial result, not a successful professional work-path judgment.

## Invariants

- no false fact may be displayed to gain speed;
- no research bookkeeping issue may cause minutes of silent waiting;
- no soft warning may be silently promoted into certainty;
- no preview may expose hidden reasoning or incomplete model JSON;
- an accepted preview survives a later-stage failure in the job event history.
