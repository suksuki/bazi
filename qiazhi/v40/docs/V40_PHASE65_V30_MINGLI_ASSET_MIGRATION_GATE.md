# V40 Phase 65: V30 Mingli Asset Migration Gate

Date: 2026-07-02

## Mainline Goal

Phase 65 starts the real V30 mingli-depth migration path.

The goal is not to import V30 runtime. The goal is to let mature V30 mingli assets enter V40 as plain JSON assets, pass a deterministic gate, and become V40 sidecar `RuntimeSignal` material.

V1 can be summarized as:

```text
plain JSON asset -> RuntimeSignal sidecar
```

```text
V30 rules / portrait / path / knowledge / probe assets
  -> plain JSON asset DTO
  -> Mingli Asset Migration Gate
  -> RuntimeSignal sidecar
  -> SignalRegistry
  -> DecisionEngine / Acceptance Window / Training attribution
```

## Implemented Contracts

```text
MigratedMingliAsset
MingliAssetMigrationGateResult
MingliAssetType
MingliAssetTargetType
MingliAssetMigrationStatus
```

## API

```text
POST /api/v40/migration/mingli-assets/gate
```

The endpoint returns:

```text
gate
signals
persisted=false
writes_v30_state=false
writes_v40_production=false
```

V1 is intentionally read/convert only. It does not persist, enable, or write production policy.

## Asset Status Flow

```text
draft -> sidecar -> evaluating -> enabled
```

V1 allows signal conversion only for:

```text
sidecar
evaluating
enabled
```

`draft`, `disabled` and `rejected` are blocked and reported with reasons.

## Runtime Signal Boundary

A V30 asset can become a V40 `RuntimeSignal` only when:

- it has an `asset_id`;
- it identifies its `source_v30_module`;
- it has a readable `claim`;
- it has `evidence_refs`;
- it does not carry raw V30 runtime path / database ref / Redis key;
- its target is `runtime_signal`;
- its migration status is runnable.

The resulting signal always has:

```text
decision_authority=false
chart_fact_mutation_allowed=false
source_ref=v30_asset:{module}:{ref}
```

## What Is Still Deferred

Phase 65 V1 does not yet:

- import actual V30 asset files automatically;
- persist migrated assets;
- run before/after diff;
- enable assets into production policy;
- convert non-signal targets such as KnowledgeCard or ProbeTemplate;
- resolve duplicate/conflicting assets.

Those belong to the next migration pass after the gate is stable.

## Product Impact

This phase gives V40 the missing bridge from “V30 has lots of mingli material” to “V40 can consume that material safely”.

It also protects the product from the old failure mode:

```text
asset exists
but no downstream output consumes it
```

Every migrated asset must answer:

```text
What do I produce?
Who consumes me?
Which user-visible verdict/advice/probe can I influence?
Which trainable policy refs receive feedback?
```

## Acceptance Criteria

Phase 65 V1 is complete when:

1. Plain JSON migrated assets validate.
2. Bad assets with raw V30 refs are rejected.
3. Sidecar/evaluating/enabled runtime-signal assets convert to `RuntimeSignal`.
4. Draft/disabled/rejected assets are blocked with reasons.
5. API returns gate result and signals without persistence.
6. Contract manifest exposes the migration contracts.
7. V40 test suite remains green.

## Next After Phase 65

Phase 66 should focus on:

```text
Domain Verdict Adapters
```

That phase should consume native Bazi Pro facts plus migrated V30 signals and produce topic-specific decision hints for wealth, career, relationship, health, timing and hidden attributes.
