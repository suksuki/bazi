# V40 Phase 63: System Review And Next Mainline Plan

Date: 2026-07-02

## Current System Review

V40 has reached product-shell maturity, but not mingli-depth maturity.

Observed from live status endpoints:

```text
Project completion: 99%
Current phase: 62 / Reading History And Conversation Layering
Mingli Depth Index: 51%
V30 replacement readiness: candidate_ready / 100%
```

This means:

```text
Architecture, isolation, runtime, UI, LLM expression, training spine, feedback loop and admin control plane are broadly ready.
Real mingli depth, real case acceptance, fact engine depth, domain adapters and hidden-factor probing remain the next bottleneck.
```

## What Is Already Strong

1. V40 is isolated from V30 by package, API prefix, runtime dir, DB prefix and contracts.
2. User-side product flow is now report-first, then conversation, then lightweight Probe.
3. Phase 62 added left-rail reading history and newest-first folded conversation turns.
4. LLM is required in product runtime; no silent fallback is allowed.
5. Training can directly activate policy changes, with impact evidence and rollback materials.
6. Admin is independent control plane and no longer mixed into the main user app.
7. Ziwei exists as sidecar / Domain Lens, not a co-equal verdict engine.

## Main Bottlenecks

The live `Mingli Depth Index` shows the real next work:

| Area | Current | Bottleneck |
| --- | ---: | --- |
| Fact Depth | 45% | Need Bazi Fact Engine Pro |
| Signal Depth | 62% | Need V30 asset migration into RuntimeSignal |
| Domain Depth | 38% | Domain verdict adapters missing |
| Probe Depth | 42% | Hidden Factor Probe Engine required |
| Training Depth | 72% | Needs real cases and before/after acceptance |
| Evaluation Depth | 48% | Needs Real Case Bank / Acceptance Window |

## Next Mainline Principle

Do not keep polishing UI before increasing mingli depth.

The next mainline should be:

```text
Real Case Bank
  -> Bazi Fact Engine Pro
  -> V30 Mingli Asset Migration Gate
  -> Domain Verdict Adapters
  -> Hidden Factor Probe Engine
  -> Acceptance Window + Direct Training Activation
```

## Phase 63 Mainline Scope

Phase 63 should start with the quality loop that every later module can be judged against:

```text
Real Case Bank / Acceptance Window V1
```

Reason:

Without real case acceptance, we can keep adding engines and rules but cannot know whether the output is actually better.

## Phase 63 Tasks

### P63-1 Real Case Contract

Create a first-class real case contract:

```text
RealCaseRecord
ExpectedMingliOutcome
ObservedLifeEvent
PractitionerJudgment
AcceptanceRubric
```

The contract must support:

- chart facts;
- user question;
- known life events;
- expected domain conclusions;
- forbidden overclaims;
- practitioner notes;
- privacy boundary;
- evaluation tags.

### P63-2 Acceptance Window

Build an acceptance window that evaluates current runtime against selected real cases.

It should produce:

- verdict match score;
- advice grounding score;
- overclaim score;
- domain coverage score;
- Probe usefulness score;
- LLM expression clarity score;
- trainable attribution hints.

### P63-3 Admin / Lab Read Model

Admin should show:

- selected real cases;
- current policy version;
- before/after comparison;
- changed weights and thresholds;
- rollback target;
- failed gates.

This is read model first. Do not build a heavy dashboard before the contract works.

### P63-4 Minimal Case Importer

Support plain JSON case import.

Do not import V30 runtime. Do not import user private data without explicit file/source boundary.

### P63-5 Golden Smoke Set

Create a small initial case set:

```text
10-20 synthetic-but-realistic cases
3-5 admin profile cases if available
```

The smoke set is not the final 100-200 case bank, but it gives us repeatable acceptance.

## What To Defer

Defer until after Phase 63:

- Full Bazi Fact Engine Pro implementation.
- Large V30 rule asset migration.
- Full hidden factor probe engine.
- Cross-device persistent reading history.
- Advanced practitioner revision history.
- More UI redesign.

## Acceptance Criteria

Phase 63 is complete when:

1. Real case contracts exist and validate.
2. Acceptance Window can evaluate at least one runtime against multiple cases.
3. Output includes match, overclaim, advice, domain and expression scores.
4. Results can feed training attribution but do not mutate facts.
5. Admin/Lab can read the latest acceptance summary.
6. Existing V40 tests remain green.
7. No V30 runtime import is introduced.

## Next After Phase 63

Phase 64 should be:

```text
Bazi Fact Engine Pro V1
```

It should improve factual depth: solar terms, hidden stems, luck-cycle start, branch relations and useful-god candidate facts.
