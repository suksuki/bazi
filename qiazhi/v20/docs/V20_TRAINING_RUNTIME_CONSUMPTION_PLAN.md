# V20 Training Runtime Consumption Plan

## Goal

Training is complete only when the active pointer is consumed by runtime code.
Writer readiness alone is not enough.

## Current Principle

`training artifact -> machine gate -> active pointer -> runtime consumer -> observable effect`

Every family must expose:

1. Candidate and active policy version.
2. Machine gate or blocking gate.
3. Runtime consumer module.
4. Policy payload counts.
5. Observable runtime effect.
6. Rollback baseline.

## Phase 1: Consumption Audit

| Family | Pointer | Expected Runtime Consumer | Audit Status |
|---|---|---|---|
| orchestrator | `orchestrator_policy_versions/active_pointer.json` | orchestrator mainline and question focus | audit now |
| role_view | `role_view_policy_versions/active_pointer.json` | role view projection | audit now |
| question | `question_policy_versions/active_pointer.json` | question ranker | audit now |
| corpus | `corpus_policy_versions/active_pointer.json` | similar case retrieval | audit now |
| rule | `rule_policy_versions/active_pointer.json` | rule runtime weighting | consumed |
| portrait | `portrait_policy_versions/active_pointer.json` | portrait projection weighting | consumed |
| knowledge | `knowledge_policy_versions/active_pointer.json` | knowledge bridge/rule mapping | consumed |

## Phase 2: Runtime Consumer Gaps

1. Connect rule pointer to rule runtime weighting. Done on 2026-05-15.
2. Connect portrait pointer to portrait projection weighting. Done on 2026-05-15.
3. Connect knowledge pointer to knowledge bridge mapping priority. Done on 2026-05-15.
4. Keep every consumer read-only and rollback-safe.
5. Add runtime-visible `policy_effect` summaries for each family.

## Phase 3: Gate Strengthening

1. Replace smoke-only gates with scheduled synthetic batches.
2. Track negative boundaries and counterexamples per family.
3. Require replay deltas before activation when a policy changes ordering or weight.
4. Persist compact audit rows without user text or secret values.

## Phase 4: Admin UI

Admin Training should show:

1. Active runtime pointer status.
2. Candidate status.
3. Runtime consumer status.
4. Payload counts.
5. Blocking gate.
6. Last activation task and rollback version.

## Completion Target

The full runtime consumption target is complete.
The next mainline completion target is stronger synthetic replay gates:

`7 pointer families consumed / 7 pointer families audited`
