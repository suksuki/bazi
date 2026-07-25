# V50 CAG-03 Canonical Scene Closeout V1

Status: `CLOSED / PASS / AUTHORITY HARDENED`
Date: `2026-07-20`

## Decision

V50 now has one server-owned product scene compiler:

```text
ChartWorldInstance + committed LifeCase
        -> CanonicalSceneOwner
        -> role-filtered CanonicalScene
        -> CanonicalProjectionEnvelope
        -> OneCanvas / Abu / Theater / Xiangfa / Workspace
```

`CanonicalScene` is a projection authority, not a second Reasoner. It cannot
create Mingli facts, promote a candidate, infer a missing relation, or write
`ChartVersion` or `LifeCase`.

## Implemented Boundary

- The API accepts only an authenticated, server-owned `case_id`.
- Client query or body data cannot replace formal chart or LifeCase facts.
- Role disclosure is applied before serialization.
- All five projections share one Scene identity and source hash.
- A projection can reference only semantic objects disclosed by its Scene.
- Legacy `record` data cannot alter Canonical Scene identity or content.
- Theater delegates to `CanonicalSceneOwner` through a compatibility adapter.
- The compatibility envelope defaults to member-safe disclosure; professional
  premises, evidence refs and hypotheses cannot leak through its fallback.
- Read-only OneCanvas requests only its `onecanvas` projection from that owner.
- Abu narration and voice validation consume only the `abu` projection.
- Abu narration no longer reads `record` or calls `formal_projection_record`.
- A single-projection request no longer compiles all five projection payloads.
- Static S0 and Xiangfa prototypes remain isolated presentation fixtures.

## Deliberately Deferred

- Graph v1 and Path v1 semantics were not changed.
- Existing Canvas relation/path assembly remains a transitional CAG-04 adapter.
- No R1 V6 locked asset was modified.
- No production Workspace migration or legacy route retirement was performed.

## Machine Evidence

```text
CAG-03 targeted regression: 49 passed
V50 full regression: 458 passed
R1 V6 locked assets: 20/20 OK
Constitution SHA-256:
4908c2865e98ba9e35f12358329fffd0b503ce9edc33cac3cf9d736e2e3caeff
```

## Slimming Evidence

- Narrated Workspace legacy `record` fallback readers: `1 -> 0`.
- Narration case-store reads per manifest request: `2 -> 1`, protected by regression.
- Requested projection compilation: `5 -> 1` for Canvas, Abu and direct API consumers.
- Local 500-iteration mean: single projection `0.4590 ms`, five-projection bundle
  `0.5276 ms` (`0.87x`); this is a regression probe, not a production SLA.
- New application modules in this hardening pass: `0`.
- The phase retains the L0/L1 physical reduction baseline: repository bytes
  `-71.39%`, files `-69.84%`, runtime duplicate media `309700981 -> 0` bytes.

The retained Theater `chart_facts_only` path is explicitly non-formal and cannot
claim Canonical Scene identity. It remains a compatibility boundary, not a
second Scene owner.

## Next Slice

`CAG-04 Formal Relation and Path Provenance` is the next architecture slice but
was not started by this task. It requires an explicit next-task authorization.
