# Qiazhi V40

V40 is an independent, evaluation-first multi-engine destiny runtime.

It must stay isolated from V30:

- Python package: `v40`
- API prefix: `/api/v40`
- Admin prefix: `/admin/v40`
- UI prefix: `/v40/ui`
- Runtime directory: `v40/.runtime`
- Postgres database: `qiazhi_v40`
- Postgres table prefix: `v40_`
- Redis key prefix: `v40:`

V40 may migrate mature V30 capabilities through migration-only importers and DTO fixtures, but V40 runtime code must not directly import `v30.*`, read V30 runtime files, mutate V30 tables, or use V30 Redis keys.

Canonical spec:

```text
docs/V40_SPEC.md
docs/V40_PHASE1_CONTRACTS_AND_TRAINING_SPINE.md
docs/V40_PHASE2_MIGRATION_IMPORTER_AND_SHADOW_COMPARE.md
docs/V40_PHASE3_API_AND_SCHEMA.md
docs/V40_PHASE4_REPOSITORY_HISTORY.md
docs/V40_PHASE5_EVALUATION_TRAINING_REPOSITORY.md
docs/V40_PHASE6_EVALUATION_RUN_AND_IMPACT_DIFF.md
docs/V40_PHASE7_LAB_ARTIFACTS.md
docs/V40_PHASE8_BATCH_EVALUATION.md
docs/V40_PHASE9_CANDIDATE_WEIGHT_VERSION.md
docs/V40_PHASE10_RELEASE_READINESS_AND_ACTIVATION_REVIEW.md
docs/V40_PHASE11_ADMIN_AND_ACTIVATION_EXECUTION.md
docs/V40_PHASE12_NATIVE_BAZI_AND_SYNTHETIC_CASES.md
docs/V40_PHASE13_NATIVE_DECISION_OUTPUT_RUNTIME.md
docs/V40_PHASE14_NATIVE_BAZI_FACT_SIGNAL_ADAPTERS.md
docs/V40_PHASE15_NATIVE_BATCH_EVALUATION.md
docs/V40_PHASE16_LLM_EXPRESSION_ACCEPTANCE.md
docs/V40_PHASE17_OLLAMA_EXPRESSION_PROVIDER.md
docs/V40_PHASE18_LLM_OBSERVABILITY_AND_EVALUATION.md
docs/V40_PHASE19_NATIVE_REPORT_RUNTIME.md
docs/V40_PHASE20_USER_REPORT_UI.md
```

Initial principle:

```text
Contract first.
Evaluation first.
Migration by DTO import, not big-bang rewrite.
```

Start order:

1. Define contracts.
2. Define evaluation and training spine.
3. Define migration DTO boundaries.
4. Add shadow compare fixtures.
5. Only then migrate runtime behavior.

Current phase:

```text
Phase 20: User Report UI
```
