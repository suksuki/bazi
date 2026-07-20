# V50 CAG-03 Canonical Scene Closeout V1

Status: `CLOSED / PASS`
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
- Read-only OneCanvas verifies and carries the same Canonical Scene identity.
- Static S0 and Xiangfa prototypes remain isolated presentation fixtures.

## Deliberately Deferred

- Graph v1 and Path v1 semantics were not changed.
- Existing Canvas relation/path assembly remains a transitional CAG-04 adapter.
- No R1 V6 locked asset was modified.
- No production Workspace migration or legacy route retirement was performed.

## Machine Evidence

```text
CAG-03 targeted regression: 42 passed
V50 full regression: 456 passed
R1 V6 locked assets: 20/20 OK
Constitution SHA-256:
4908c2865e98ba9e35f12358329fffd0b503ce9edc33cac3cf9d736e2e3caeff
```

## Next Slice

`CAG-04 Formal Relation and Path Provenance` is now authorized. It must add
stable relation/path identity and historical adapters without silently
rewriting committed LifeCase cognition.
