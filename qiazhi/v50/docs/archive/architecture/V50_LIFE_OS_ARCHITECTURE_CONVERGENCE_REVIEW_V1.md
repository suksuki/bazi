# V50 Life OS Architecture Convergence Review v1

## 0. Review decision

```yaml
review_scope: architecture_convergence_and_legacy_cut
decision: B
decision_meaning: >-
  The new Life Case architecture supports the baseline and on-demand domain journey
  without the retired full-reading pipeline, but application orchestration and data
  authority have not converged. A concentrated application/data refactor is required;
  a full architecture rewrite is not justified.
professional_accuracy_proven: false
public_release_proven: false
core_reasoner_change_required_by_this_review: false
```

The present system is not secretly running the old report pipeline as its production
backbone. The main production route is already:

```text
Birth material
-> ChartWorldInstance
-> first_baseline_reading
-> FormalInsight validation
-> LifeCase baseline commit
-> on-demand domain exploration
-> FormalInsight validation
-> LifeCase domain commit
```

The convergence failure is narrower and more concrete:

> `LifeCase` is intended to be the formal cognitive commit center, but production reads
> and writes still treat the mutable `MingliCognitiveRecord`, `CaseCognitiveWorkspace`,
> and `LifeCase` as overlapping sources of truth.

This review recommends **Life Case Application Convergence v1**, not a new reasoner,
a new framework, or a wholesale rewrite.

---

## 1. Authority rule

`LifeCase` must not become a God object. It is the formal cognitive commit center,
while other authorities remain distinct:

| Concern | Authoritative owner | Required relationship to `LifeCase` |
|---|---|---|
| Birth material and chart facts | Profile + `ChartWorldInstance` | Referenced through an immutable chart version |
| Baseline and domain cognition | Validated `FormalInsight` inside `LifeCase` | Formal committed conclusion |
| Candidate model output | Immutable `MingliCognitiveRecord` / run artifact | Traceable input, not public current truth |
| Case-level belief state | `CaseCognitiveWorkspace` | Mutable working state derived from evidence |
| Reality evidence | One canonical evidence ledger | Referenced by workspace and revisions, not copied |
| Temporal state | Versioned `TemporalPrior` | Committed against chart and case versions |
| Product rendering | Role/mode projection | Derived from active formal state |
| UI interaction state | Browser/session UI state | Never a cognitive authority |

---

## 2. Observed data

### 2.1 Production no longer depends on the retired full-reading route

- Baseline production calls `first_baseline_reading`, then validates and commits a
  baseline `LifeCase` (`apps/product/agent_api.py:210`, `:276`, `:340`).
- The non-progressive route follows the same authority chain
  (`apps/product/agent_api.py:525`, `:569`).
- Domain work is requested on demand through `explore_domain`, validated, then committed
  with `commit_domain_insight` (`apps/product/agent_api.py:795`, `:815`, `:892`).
- The older `first_reading` remains reachable from research and benchmark scripts, but
  is not called by the current product API.
- Product app boundaries explicitly exclude the retired alpha session, deterministic
  Brain, and template product APIs (`apps/product/app.py:55`).

### 2.2 Formal state and mutable run state are still mixed

- A case is persisted as a single mutable JSONB document in
  `v50_mingli_agent_cases.case_json` (`apps/product/agent_case_store.py:54`).
- Domain execution writes the raw exploration into `record.domain_explorations` and
  also commits a validated `FormalInsight` into `life_case.domain_insights`
  (`apps/product/agent_api.py:795`).
- The public reading projection is still primarily assembled from
  `record.cognition`, raw domain explorations, and workspace state; the projected
  `LifeCase` is attached afterward (`apps/product/agent_api.py:1221`).
- Probe response records the same user evidence in workspace history, record evidence,
  record revisions, `LifeCase.reality_evidence`, and `LifeCase.revisions`
  (`apps/product/agent_api.py:1094`, `:1174`).

### 2.3 Formal temporal and revision contracts exist but are not wired

- `commit_temporal_prior` and `commit_case_revision` exist in
  `packages/core/life_case/service.py:392` and `:409`.
- Production APIs do not call either contract.
- Abu can resolve `timeline.select_period` and `reality.record`, but both are declared
  as incomplete boundaries (`packages/core/abu_runtime/runtime.py:124`, `:174`).
- The browser handles month switching by offering "view current stage" instead of
  selecting a persisted temporal period (`apps/product/static/l5/app.js:275`).

### 2.4 Chart invalidation is written but not enforced on read

- Editing birth material marks related `LifeCase` rows as `superseded` and marks their
  chart versions inactive (`apps/product/app.py:190`, `:225`).
- Current-record and domain-eligibility checks do not reject a superseded `LifeCase` or
  an inactive chart version (`apps/product/agent_api.py:1526`, `:1555`).
- A runtime test confirmed that a superseded case remains restorable and listable.

This is the highest-risk defect found by this review because it can present a formally
invalidated conclusion as current.

### 2.5 Abu and page actions converge only for implemented domain actions

- Abu domain commands and page domain buttons both reach the same client action and the
  same `/cases/{case_id}/domains/{domain}` endpoint
  (`apps/product/static/l5/app.js:224`, `:297`, `:1430`).
- Timeline and reality commands currently stop at a product boundary message and do not
  reach a shared server command.

### 2.6 Domain cache is semantically bound but not implementation-version bound

The domain request fingerprint includes:

```text
world_id
record_id
baseline semantic signature
case version
domain
normalized user question
```

(`packages/core/mingli_agent/reliability.py:86`). Cache reuse also checks baseline
record, insight, case version, and semantic signature
(`packages/core/mingli_agent/reasoner.py:744`).

It does not include:

```text
model version
prompt version
reasoner protocol version
knowledge/context compiler version
```

Changing one of these can therefore reuse an output generated under a previous cognitive
implementation unless the baseline signature changes.

---

## 3. Six-journey trace

| Journey | Result | Evidence and interpretation |
|---|---|---|
| New profile -> chart -> baseline -> commit | **PASS** | New baseline path completes without `first_reading`; baseline is validated and committed into `LifeCase`. |
| Baseline -> wealth -> save -> reopen | **PASS WITH DEBT** | On-demand domain result survives reopen, but raw exploration and formal insight remain dual current representations. |
| Month switch -> temporal state -> page + Abu sync | **NOT IMPLEMENTED** | Abu recognizes intent, but no persisted selected period or committed `TemporalPrior` is produced. |
| Reality evidence -> case revision candidate | **PARTIAL** | Evidence is saved, but duplicated; there is no production `commit_case_revision` flow. |
| Birth edit -> chart version -> old insight invalidation | **FAIL** | Invalidation marker is written, but old case remains restorable/listable and can still pass current-record checks. |
| Abu natural-language action and page button call paths | **PASS FOR DOMAIN / PARTIAL GLOBALLY** | Domain actions converge; timeline and reality actions do not yet have executable server paths. |

---

## 4. Legacy Cut Test

A repeatable test was added at:

```text
tests/test_v50_life_os_legacy_cut.py
```

It makes the retired `first_reading` method fail immediately, then executes:

```text
register member
-> create profile
-> baseline
-> Abu wealth command
-> wealth domain exploration
-> reopen case
-> answer probe
-> edit birth material
-> verify superseded marker
```

The test passes. This proves the implemented baseline, domain, reopen, and probe slice can
operate without the retired full-reading method. It does **not** prove temporal selection,
formal case revision, or active-version enforcement, which are separately classified.

---

## 5. Classification

### KEEP

- Deterministic Bazi and Ziwei fact engines.
- `ChartWorldInstance` compiler and fact authority boundary.
- `first_baseline_reading` and on-demand `explore_domain` cognitive routes.
- Reliability Gate and `FormalInsight` validation.
- `LifeCase` baseline/domain commit contracts.
- Account/profile ownership and claim boundaries.
- Progressive jobs, stage events, and preview streaming.
- Abu command registry and action ownership constraints.
- Role projection boundaries.

### REFACTOR

- Extract case orchestration from the large product router into explicit application
  commands/services. HTTP endpoints should remain thin adapters.
- Introduce a typed case repository with atomic operations instead of whole-row mutable
  dictionary replacement.
- Make candidate model records immutable run artifacts; make the active `LifeCase` the
  formal source used by product projection.
- Create one canonical `RealityEvidence` write and reference it from workspace and
  revisions by ID.
- Wire `TemporalPrior` and `CaseRevision` into production commands.
- Enforce `LifeCase.status == active` and `chart_version.active == true` on list,
  restore, domain, probe, and projection reads.
- Add an implementation fingerprint to domain cache identity.
- Move executable Abu and page actions toward one server-side application command
  boundary while keeping Abu a navigator rather than a judgment source.

### RETIRE

- Any future production reachability of `first_reading`; retain it only under explicit
  research/benchmark ownership until benchmark migration is complete.
- Legacy record-v2 compatibility after persisted rows have been migrated.
- Precomputed optional-domain fields in baseline artifacts after formal domain insight
  migration.
- Client-only timeline/reality commands that imply an action without executing it.

### DELETE

No immediate code deletion is authorized by this review. Deletion requires:

1. production and research reachability evidence;
2. persisted-row migration or expiration evidence;
3. replacement tests;
4. a separate deletion manifest.

This avoids turning an architecture review into an unsafe cleanup sweep.

---

## 6. Interpretation

The correct conclusion is **B**, not A or C:

```text
A: New architecture is fully independent; cleanup only.       No.
B: New architecture largely works; concentrated refactor.     Yes.
C: Product still depends on the old pipeline; rebuild app.     No.
```

Why not A:

- formal and mutable state still overlap;
- temporal and case-revision contracts are not wired;
- superseded conclusions can still be served;
- the application router owns too much state transition logic.

Why not C:

- baseline and domain cognition run successfully with the old full-reading path cut;
- chart facts, cognitive reasoning, reliability review, formal commits, product
  projection, and Abu domain navigation are already separable;
- replacing the reasoner or rewriting the entire modular monolith would add risk without
  addressing the observed defects.

---

## 7. Recommended next slice

### Life Case Application Convergence v1

Execute in this order:

1. **Close the invalidation defect.** Reject superseded/inactive chart versions on every
   current-case read and action.
2. **Freeze data authority.** Publish one authority matrix and encode it in repository
   methods and tests.
3. **Canonicalize evidence.** One evidence record, multiple references; no repeated
   payload writes across record/workspace/LifeCase.
4. **Move orchestration into application commands.** Start with `CreateBaseline`,
   `ExploreDomain`, `RecordRealityEvidence`, `CommitCaseRevision`, and
   `SelectTemporalPeriod`.
5. **Wire the dormant formal contracts.** Temporal selection creates a `TemporalPrior`;
   accepted evidence can create a revision candidate and a separately committed
   `CaseRevision`.
6. **Switch product reads to formal active state.** Raw cognitive runs remain visible
   only where professional traceability requires them.
7. **Version cache identity.** Add reasoner/prompt/model/context-policy fingerprints.
8. **Migrate persisted rows, then retire compatibility.** Deletion is last, not first.

### Explicitly out of scope

```yaml
reasoner_logic_modified: false
prompt_modified: false
model_policy_modified: false
mingli_algorithm_modified: false
reliability_gate_relaxed: false
ui_redesign: false
professional_blind_test_protocol_modified: false
```

The professional blind-test reasoning version should remain frozen while this
application/data convergence work is performed. The refactor must preserve cognitive
inputs and outputs byte-for-byte wherever possible.

---

## 8. Acceptance conditions for the next slice

- A superseded case cannot be listed as current, restored as current, projected, probed,
  or expanded into a domain.
- One user evidence submission produces one canonical evidence ID.
- Public projections read active formal insights, not unvalidated candidate output.
- A selected historical/current period resolves to one persisted temporal state shared
  by page and Abu.
- A case revision cannot silently overwrite baseline cognition; it must be proposed,
  reviewed, committed, and versioned.
- Domain cache cannot cross a cognitive implementation version.
- The legacy cut test and all existing reliability/cognitive tests remain green.
- No old full-report route becomes production-reachable.

---

## 9. Final statement

> V50 does not need another architecture invention. It needs to finish adopting the
> architecture it already designed: immutable chart facts, candidate reasoning runs,
> validated formal insights, a versioned active LifeCase, canonical evidence, and thin
> product projections.

The next meaningful progress is not more modules. It is making each piece own exactly
one truth.

