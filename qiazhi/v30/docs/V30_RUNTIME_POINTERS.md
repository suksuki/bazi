# V30 Runtime Pointers

Updated: 2026-05-22

## Current Runtime Consumption

Runtime pointers are no longer only reported as active versions.

Current consumed payload:

```text
structure_policy.payload.weights
-> mechanism path scores
-> StructureState.path_scores
-> Mainline/Question behavior

question_policy.payload.weights
-> recommendation scorer
-> visible next-question ordering

rule_policy.payload.weights
-> rule evidence score reasons
-> structure/mainline/question behavior
```

The current auto-training loop emits structure mechanism weights and promotes them immediately after validation.

Updated: 2026-05-22

## Purpose

Runtime pointers are the bridge between V30 training and V30 runtime behavior.

V30 must support automatic training, validation, artifact publication, and runtime application without making manual review the normal path.

## Core Rule

Runtime reads active policy artifacts through V30 pointers only.

Runtime must not read:

- V20 pointer files.
- V20 Redis keys.
- V20 DB tables.
- Raw training scratch files.
- Candidate artifacts that have not passed validation.

## Pointer Flow

```text
TrainingRun
-> PolicyCandidate
-> ValidationRun
-> PolicyArtifact
-> RuntimePointer
-> RuntimeBehavior
```

## Initial Policy Families

| Family | Runtime effect |
|---|---|
| `feature_policy` | Feature thresholds and weights. |
| `rule_policy` | Rule activation weights and conflict resolution. |
| `knowledge_policy` | Knowledge pack version and retrieval weights. |
| `structure_policy` | Graph weights, path scoring, semantic thresholds. |
| `mainline_policy` | Mainline arbitration weights. |
| `portrait_policy` | Portrait mapping and projection density. |
| `question_policy` | Question recommendation and ranking. |
| `answer_policy` | Answer planning and boundary behavior. |
| `presentation_policy` | Role/client visibility and language density. |
| `model_signal_policy` | Optional future family for ten-god energy/stability/volatility thresholds if it should not live under structure/mainline policy. |

## Pointer Schema

Required fields:

```text
family
active_artifact_id
active_artifact_version
previous_artifact_id
validation_run_id
promotion_reason
env
status
updated_at
updated_by
rollback_pointer
```

Allowed `status`:

```text
active
paused
rollback
canary
retired
```

## Artifact Schema

Required fields:

```text
artifact_id
family
version
candidate_id
payload_uri
checksum
created_at
metrics
validation_summary
compatible_runtime_version
```

## Storage

V30 pointer state can be mirrored across storage layers, but Postgres should be the durable source.

Suggested durable table:

```text
v30_policy_pointers
```

Suggested runtime cache key:

```text
v30:{env}:policy:{family}
```

Suggested artifact table:

```text
v30_artifacts
```

Suggested local runtime path:

```text
.runtime/policies/{family}/active.json
.runtime/artifacts/{family}/{artifact_id}.json
```

## Auto-Apply Contract

Auto-apply is allowed only after required gates pass.

```text
if validation_run.promotion_decision == "promote":
    publish artifact
    update pointer
    record previous pointer
else:
    keep current pointer
    record failure clusters
```

Manual review is not required for ordinary promotion.

Manual controls:

- Pause family.
- Roll back family.
- Raise/lower promotion threshold.
- Force canary mode.
- Block an unsafe artifact.

## Canary Mode

Canary mode is optional and should be used for high-impact policies.

Canary behavior:

```text
percentage or cohort -> candidate artifact
default -> active artifact
```

Canary must remain explicit. It should not complicate the first smoke implementation.

## Rollback

Every pointer update must record:

- Previous artifact ID.
- Previous checksum.
- Validation run ID.
- Rollback reason if used.
- Timestamp.

Rollback should be a pointer update, not file deletion.

## Runtime Loading

Runtime loader requirements:

- Load V30 family pointer by family.
- Verify artifact checksum if available.
- Cache active artifacts for one reading.
- Never change policy during one reading.
- Fall back only to V30 baseline artifacts.
- Emit active policy versions in admin trace.

## Training Integration

Training jobs must output:

```text
candidate_report
validation_report
artifact_report
pointer_update_report
```

Pointer update report should include:

```text
family
previous_artifact_id
new_artifact_id
validation_run_id
metrics_delta
rollback_pointer
```

## Test Strategy

Default tests:

- Pointer schema validation.
- V30 Redis key shape.
- No V20 pointer import.
- In-memory pointer update.

Explicit tests:

- Postgres pointer persistence.
- Redis pointer cache.
- Auto-apply promotion.
- Rollback.
- Canary.

## First Implementation Slice

Start with one family:

```text
structure_policy
```

Minimum behavior:

```text
baseline artifact
-> active pointer
-> synthetic validation candidate
-> pointer update
-> runtime reports active artifact
```

Current implementation status:

- Local JSON baseline pointer store exists.
- Baseline artifacts are created under `.runtime/artifacts/{family}/`.
- Active pointers are created under `.runtime/policies/{family}/active.json`.
- Runtime reports active `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy` artifact IDs.
- Runtime loads active `structure_policy`, `question_policy`, and `rule_policy` artifact payloads into live scoring.
- `PolicyCandidate` and `PromotionResult` schemas exist.
- Policy candidate promotion runs synthetic `all` as the gate.
- Policy candidate promotion also runs 518K sample as the distribution gate.
- Promotion validation injects the candidate payload into synthetic and 518K runtime replay before pointer activation.
- Auto-training now generates and promotes `structure_policy`, `mainline_policy`, `question_policy`, and `rule_policy` candidates without a manual review gate.
- Passing candidates can update local JSON pointer.
- Rollback metadata is recorded in the pointer.
- Manual promotion CLI exists: `python3 scripts/promote_policy_candidate.py --family structure_policy --candidate-id <id>`.
- Current real runtime policy set: `structure_policy.rule-policy-001.structure_policy`, `mainline_policy.rule-policy-001.mainline_policy`, `question_policy.rule-policy-001.question_policy`, `rule_policy.rule-policy-001.rule_policy`.
- Real service trace confirms `question_policy_payload`, `rule_policy_payload`, per-question `policy_weight`, and rule evidence policy weights are present.

## Promotion Lineage Diagnostics

V30 now exposes `v30.promotion_lineage.v1` for active runtime policies.

Lineage links:

- Runtime pointer.
- Active policy artifact.
- Previous artifact and rollback pointer.
- Synthetic and 518K validation summary.
- Unified validation artifacts such as question-policy comparison artifacts.
- Active runtime trace consumption summary.

Admin lookup:

```bash
GET /api/v30/admin/policies/lineage?family=question_policy
```

Lineage is diagnostic only. It does not retrain, promote, update pointers, or create chart facts.
- Training scheduler is still pending.

## Current Completion And Next Pointer Push

| Area | Completion | Current state | Next task |
|---|---:|---|---|
| Pointer spine | 86% | Local JSON pointers, artifacts, rollback metadata, active policy reporting, and lineage diagnostics are active. | Keep contract stable while adding P7/P8/P9 signal summaries. |
| Runtime consumption | 78% | `structure_policy`, `question_policy`, and `rule_policy` payloads influence live runtime behavior. | Add model-fusion and visible-next-question policy effects with diagnostics. |
| Promotion validation | 88% | Synthetic `all` and 518K sample gate candidate promotion. | Add interaction-loop and model-fusion checks before pointer activation. |

Parallel promotion plan:

```text
P7 model-signal candidate
-> synthetic ten_god_energy_fusion + ranked_decision_fusion
-> 518K sample model-signal coverage
-> structure/mainline/model_signal pointer update

P8 question-policy candidate
-> synthetic interaction_loop
-> active-vs-candidate visible/internal next-question comparison
-> question_policy pointer update

P9 calibration candidate
-> real_case_calibration_pack
-> no chart-fact mutation check
-> candidate-only quality/policy signal
```

Open pointer decision:

- Keep `model_signal_summary` tuning inside `structure_policy` first unless synthetic evidence shows it needs an independent `model_signal_policy`.

Current P7 pointer status:

- `structure_policy.weights.dynamic_graph.model_signal_fusion` is the first model-signal tuning hook.
- Auto-training candidates can generate this weight from `ten_god_energy_fusion` and structure dynamic model-signal observations.
- Runtime structure scoring reads the weight as bounded path-score adjustment.
- No active pointer is updated unless promotion is explicitly run.

## Acceptance

- Runtime pointer paths are V30-only.
- Policy family contract is shared.
- Passing validated candidates can auto-apply.
- Rollback is pointer-based.
- Default tests stay fast.
- Runtime trace reports active policy versions.
