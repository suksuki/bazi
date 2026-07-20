# V50 Life Case Application Convergence v1

Status: frozen application contract  
Date: 2026-07-17

## 1. Purpose

This convergence makes the established Life OS path the only current application path. It does not change professional Mingli cognition.

The governing rule is:

> One user action creates at most one formal business record; one case version has one current cognition; page, Abu, login recovery, and export read the same formal source.

## 2. Authority Map

| Concern | Sole authority | Explicitly not authoritative |
| --- | --- | --- |
| Birth data and chart facts | `ChartVersionRef` and its referenced chart world | Workspace copy, report text, conversation text |
| Formal whole-chart and domain cognition | `LifeCase` plus committed `FormalInsight` revisions | `RunRecord`, old report, rendered text |
| User-reported reality | `RealityEvidence` | Conversation transcript, probe history copy, monthly review copy |
| Month and stage cognition | `TemporalSnapshot` | Selected month label alone, generic current-date copy |
| Current interaction position | `WorkspaceState` | `LifeCase` cognition and chart facts |
| Model execution and diagnostics | `RunRecord` | Formal result restoration |
| User-facing rendering and export | Projection from the authorities above | New business truth |

In short:

```text
RunRecord  = what the system executed
LifeCase   = what the system currently believes about this case
Workspace  = what the user is currently viewing
```

## 3. Case Lifecycle

### 3.1 Active case

An active chart version has one active case. Current lists, default recovery, Abu context, and writable actions may only use that case.

### 3.2 Birth-data change

```text
Edit birth data
-> supersede old chart version
-> supersede old LifeCase
-> create a new chart version
-> create a new active LifeCase when reading starts
```

The old case remains auditable but is not returned by the default current-case list.

### 3.3 Historical case

A historical case requires an explicit historical read. It is marked read-only in both API and UI. It cannot:

- run a new domain exploration;
- answer a probe;
- switch the selected month;
- add reality evidence;
- complete a monthly review;
- commit a case revision.

The UI may display its previously committed cognition and evidence only.

## 4. Reality Evidence

All reality recording paths call the same application command. A stable `idempotency_key` identifies the user's event across:

- page form submission;
- Abu natural-language submission;
- retry after a network interruption;
- repeated click;
- replay by an application runner.

The first command creates one `RealityEvidence`. A replay returns the same `evidence_id` with `created=false`. Conversation and run records may reference that ID, but may not copy the event as a second business record.

Corrections are represented by `RealityEvidenceRevision`; they do not silently overwrite history.

## 5. Time Context

Two periods are always separate:

```text
system_period   = the real current month
selected_period = the month the user is viewing
```

`WorkspaceState.selected_period`, `TemporalSnapshot.period_key`, the visible page, Abu guidance, and newly recorded reality evidence must agree.

- Past periods may combine prior and recorded evidence for review.
- The current period describes the current observation theme.
- Future periods remain conditional priors and cannot cite future reality evidence.
- Period selection never rewrites the whole-chart baseline.

## 6. Monthly Revision Loop

```text
TemporalSnapshot
-> RealityEvidence
-> MonthlyReview
-> CaseRevisionCandidate
-> explicit commit
-> LifeCase vN+1
```

Supported verdicts are:

- `supported`
- `partially_supported`
- `not_observed`
- `contradicted`
- `insufficient_evidence`

Recording an event never changes formal cognition by itself. A monthly review creates a candidate, not a revision. A separate explicit commit creates the next case version. The previous version is preserved in `LifeCaseVersionSnapshot`.

The baseline chart cognition is not silently replaced by a monthly correction. The new case revision is an additional, traceable cognition layer.

## 7. Formal Projection and Recovery

Committed `FormalInsight.projection_payload` holds the typed projection necessary to restore the user-facing reading. Page and Abu restoration read from the `LifeCase` projection.

The following are prohibited as restoration authorities:

- a recently completed `RunRecord`;
- old report output;
- conversation memory;
- UI workspace state.

Tampering with a run record therefore cannot change the restored formal thesis.

## 8. Workspace Boundary

`WorkspaceState` may contain:

- active case;
- selected and system periods;
- active domain and product mode;
- language;
- expanded sections;
- conversation focus;
- draft input.

It may not contain authoritative chart facts, formal insight content, reality evidence content, temporal priors, or case revisions.

Legacy persisted `workspace` payloads are read once and mapped into the new compatibility view. New writes persist `case_belief_state` and canonical LifeCase data; they do not continue the legacy dual write.

## 9. Cognitive Cache Identity

The domain request fingerprint covers:

```text
case_id
case_version
chart_version_id
domain
temporal_scope
input_context_hash
reasoner_version
prompt_version
model_version
knowledge_version
gate_version
context_compiler_version
```

An exact request may reuse the cache. A change in chart, case revision, selected temporal scope, context, Prompt, Reasoner, model, knowledge, or gate creates a different identity.

Language and role remain projection concerns when the underlying cognition is unchanged.

## 10. UI Contract

- The casebook separates current charts from `历史版本`.
- A historical case presents an explicit `历史命盘版本 · 只读` notice.
- Read-only mode disables all actions capable of producing or requesting new cognition.
- Month selection is visible and shared with Abu.
- `记录这个月发生的事` invokes the canonical reality command directly; it is not reclassified by conversational intent routing.
- A monthly review first shows a revision candidate. `确认写入案例理解` is a separate user action.
- After commit, the current case version and latest revision are visible immediately.

## 11. Non-goals

This slice does not:

- change the LLM Reasoner;
- change the professional Prompt;
- change chart calculation or Mingli algorithms;
- change global theory;
- train or modify model weights;
- redesign the main visual system;
- add Daily, Weekly, narrative theatre, or new public domains;
- claim professional accuracy or public-launch readiness.

The next authorized product step is `Professional Blind Test v1` after analyst review of this convergence.
