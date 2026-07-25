# V50 CAG-04 Relation and Path Provenance Closeout V1

Status: `CLOSED PASS / PROVENANCE RECONCILED / MACHINE PASS`
Date: `2026-07-21`
Implementation commits: `1190a873`, `0225aa1a`
Source commits: `42072034`, `c0502ed9`

## Decision Boundary

CAG-04 establishes identity, version, provenance, lifecycle and historical
stability. It does not decide whether a Mingli relation is professionally
valid, how six pillars act on one another, or how a work path should be scored.

```text
ChartWorldInstance
        -> Graph / Path v1 candidate observation
        -> Reasoner and reliability decision
        -> LifeCase RelationAssertion / PathAssertion
        -> CanonicalScene role-filtered projection
        -> Canvas / Abu / Theater / Xiangfa / Workspace
```

## Commit Chain

```text
af6eb755  V50 source baseline
    -> 8b0178ee  CAG-03 Canonical Scene implementation
    -> 34cc5b17  CAG-03 closeout
    -> e6cfc76e  RA0 payload (source 2ac55900; same patch as f4c5527c)
    -> 1190a873  CAG-04 implementation (source 42072034)
    -> 32a0a0fe  initial machine closeout (source 092f146b)
    -> da0aff4c  RA0 / CAL-01 boundary receipt (source ae1f0856)
    -> 0225aa1a  lifecycle/provenance hardening (source c0502ed9)
    -> efbe9115  replayed closeout (source 4d12ce4d)
```

The lineage receipt commit follows `efbe9115`; CAG-05 is not part of this chain
and is not authorized by this record. RA0 is now an ancestor of the CAG-04
implementation while remaining an independent audit payload that does not
change CAG-04 semantics. The original branch remains untouched.

The earlier `092f146b` count of `467` was a pre-RA0 snapshot. RA0 introduced
one test module with ten tests, producing `477`; lifecycle hardening added two
more tests, producing the reconciled final count of `479`. No RA0 test was
deleted, renamed, moved or excluded from discovery.

## Formal Contracts and Owner

| Contract | Stable meaning |
|---|---|
| `NodeRef` | scene, LifeCase, ChartVersion, world, natal/temporal scope, slot, level and component |
| `RelationKey` | ontology version, relation type, participants, directionality, arity and scope |
| `PathKey` | ordered node refs and ordered relation keys |
| `ProvenanceRecord` | producer, producer version, evidence, source refs and creation time |
| `RelationAssertion` | versioned lifecycle judgment about one stable relation key |
| `PathAssertion` | versioned lifecycle judgment about one stable path key |

LifeCase is the only formal assertion owner. Graph/Path v1 can emit deterministic
candidate observations but cannot commit or promote them. Canonical Scene can
filter and project assertions but cannot create or rewrite them.

## Stable ID Policy

- IDs use deterministic SHA-256 digests of canonical logical identity.
- Symmetric relation participants are normalized before hashing.
- Directed relation order is preserved.
- Three-part and larger relations retain all participants and are not reduced
  to anonymous binary pairs.
- Natal, luck and annual nodes carry distinct scope and temporal snapshot refs.
- Graph producer version is provenance, not logical identity; upgrading an
  algorithm does not mutate an already committed key.
- A new judgment creates a new Assertion and may reference `supersedes`; it
  does not overwrite the earlier Assertion.
- `graph_candidate` provenance is valid only for candidate Assertions; changing
  the status field cannot promote it into LifeCase.
- Persisted `supersedes` links must reference an earlier Assertion in the same
  history. Dangling and out-of-order chains are rejected before projection.

## Historical Compatibility

Old LifeCases are read through one exact adapter:

1. exact candidate-path fact refs with structured node and relation descriptors;
2. otherwise an exact ordered chain of referenced graph-relation facts;
3. otherwise an explicit `legacy_unresolved` assertion.

The adapter never reconnects by label, prose similarity, score proximity or a
new Graph result. Stored assertions are returned unchanged even when the
candidate producer version changes.

Repository-scope migration evidence:

```text
tracked persisted formal case payloads: 0
exact synthetic legacy migration fixtures: 1
synthetic legacy_unresolved negative fixtures: 1
production database legacy_unresolved count: not measured; no database URL was configured
```

The last line is an explicit audit boundary, not a zero count.

## Removed Duplicate Authority

- Canvas anonymous `path-committed-*` identity generation: removed.
- Canvas `_edge_matches_fact` relation-text reconstruction: removed.
- Theater `_legacy_path_signature` path reconstruction: removed.
- Theater score-tolerance rematching: removed.
- Canvas and Theater independent formal-path reconstruction sites: `2 -> 0`.
- Formal relation/path assertion owners: implicit/none -> one (`LifeCase`).
- Formal projection source chains: per-consumer reconstruction -> one
  `LifeCase -> CanonicalScene` chain.

## Retained Transitional Debt

- Graph/Path v1 remains the experimental candidate producer until the later RA
  semantic audit; CAG-04 does not validate its Mingli theory.
- Exact legacy import remains a read adapter for old cases.
- Canvas retains binary geometry endpoints for current rendering while a
  `RelationKey` can preserve all hyperrelation participants.
- Theater `chart_facts_only` remains the non-formal CAG-03 compatibility mode.
- Production case migration count requires a separately authorized, private
  database audit before any remote baseline or migration.

## Slimming and Code Delta

Source commits `42072034` and `c0502ed9`, replayed as `1190a873` and
`0225aa1a`, changed the same 17-file
CAG-04 surface:

```text
all implementation and test code: +2507 / -218 lines
production and support code:       +2084 / -213 lines
tests:                               +423 /   -5 lines
new formal modules: 2
new test modules: 1
duplicate/fuzzy reconnection implementations removed: 2
```

This slice is not represented as total line-count slimming. The codebase grows
because the previously missing formal identity and migration contracts are now
typed and tested. The actual convergence is a reduction in formal owners,
fallbacks and reconstruction paths. Further deletion belongs to CAG-05 only
after this architecture review.

## Performance Evidence

Same fixture and interpreter, medians:

| Probe | CAG-03 baseline | CAG-04 | Change |
|---|---:|---:|---:|
| Canonical projection, persistent owner | 0.3716 ms | 0.0471 ms | -87.3% |
| Canvas issue, persistent service | 24.7013 ms | 3.0562 ms | -87.6% |
| Canonical projection, new owner each call | 0.3755 ms | 0.6689 ms | +0.2934 ms |
| Canvas issue, new service each call | 24.7780 ms | 26.8502 ms | +2.0722 ms |

Production routers and services retain their owner instance, so the persistent
probe is the request path. The one-shot constructor probe is disclosed because
legacy exact migration performs additional validation on first use. No cache
may alter formal content: cache keys include the formal source revision and
candidate selection revision.

Final hardening was also measured against parent `ae1f0856` with the same
interpreter, fixture and machine. Medians across three 200-call rounds:

| Production path | `ae1f0856` | `c0502ed9` | Change |
|---|---:|---:|---:|
| Canonical projection, persistent owner | 0.0525 ms | 0.0509 ms | -3.0% |
| Canvas issue, persistent service | 3.5694 ms | 3.5286 ms | -1.1% |

The lifecycle validation therefore introduces no measured production-path
regression.

The reconciled branch was measured again against `34cc5b17` on the same
machine and interpreter, using three 200-call rounds:

| Production path | `34cc5b17` | Reconciled CAG-04 | Change |
|---|---:|---:|---:|
| Canonical projection, persistent owner | 0.3968 ms | 0.0521 ms | -86.9% |
| Canvas issue, persistent service | 29.1239 ms | 4.1222 ms | -85.8% |

The persistent-service performance improvement therefore remains present
after lineage reconstruction.

## Machine Evidence

```text
RA0 focused realizability tests: 10 passed
CAG-04 focused relation/path tests: 11 passed
V50 full regression: 479 passed
R1 V6 locked assets: 20/20 OK
Constitution SHA-256:
4908c2865e98ba9e35f12358329fffd0b503ce9edc33cac3cf9d736e2e3caeff
V40 worktree fingerprint:
982d5f848ff1a5810cc3488f2158f72d0b9228492cc976593529c90d53cce579
```

The eleven focused tests cover symmetric and directed identity, hyperrelations,
temporal node separation, append-only supersession, candidate rejection,
exact legacy migration, explicit unresolved history, cross-projection identity,
cache invalidation on formal revision, role disclosure, client write rejection,
provenance/status binding and persisted history integrity.

## Deliberately Unchanged

- no relation eligibility or priority rule;
- no Sanhe, Sanhui, punishment or clash algorithm change;
- no temporal activation or energy calculation;
- no path scoring or WholePathValidator change;
- no UI or product feature;
- no CAG-05 schema or database migration work;
- no R1 locked-file change;
- no V40 change;
- no production deployment.

## Gate

Machine recommendation: `PASS` for the CAG-04 implementation boundary.

CAG-04 is closed after architecture review and lineage reconciliation. CAG-05
is authorized; RA1-RA3 and production deployment remain outside this record.
