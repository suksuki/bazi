# V20 Intelligence Brain And Full Corpus

V20 treats the knowledge base as the source layer, the feature spine as the
runtime language, and learning systems as a shadow brain that can improve
retrieval, ranking, calibration, clustering, and proposal generation.

## Service Configuration

LLM, Postgres, and Redis are configured by environment variables only. No
secret value belongs in the repository.

LLM:

- `V20_LLM_ENABLED`
- `V20_LLM_EXECUTE`
- `V20_LLM_PROVIDER`
- `V20_LLM_HOST`
- `V20_LLM_PORT`
- `V20_LLM_BASE_URL`
- `V20_LLM_MODEL`
- `V20_LLM_EMBEDDING_MODEL`
- `V20_LLM_API_KEY`
- `V20_LLM_AUDIT_MODEL`
- `V20_LLM_AUDIT_BASE_URL`
- `V20_LLM_AUDIT_API_KEY`

Postgres and Redis keep the existing V20 env contract:

- `V20_DATABASE_URL` or `V20_POSTGRES_HOST` / `V20_POSTGRES_PORT` /
  `V20_POSTGRES_DB` / `V20_POSTGRES_USER` / `V20_POSTGRES_PASSWORD`
- `V20_REDIS_URL` or `V20_REDIS_HOST` / `V20_REDIS_PORT` / `V20_REDIS_DB`

Readiness endpoints do not attempt network calls by default:

- `GET /api/v20/runtime/dependencies`
- `GET /api/v20/storage/schema`

## 518K Full Corpus

The full corpus space is the valid pillar-combination space:

`60 year pillars * 12 month branches * 60 day pillars * 12 hour branches = 518,400`.

V20 now has deterministic enumerators for this space and a precompute preview:

- `GET /api/v20/corpus/full-precompute/manifest`
- `GET /api/v20/corpus/full-precompute/preview?start=0&limit=4`
- `GET /api/v20/corpus/full-precompute/status`

Local job command:

```bash
python3.12 v20/scripts/run_full_precompute.py --run-id v20_full_518k_main --limit 518400 --status-every 500
```

The job writes:

- `v20/.runtime/corpus/full_precompute/<run_id>/snapshots.jsonl`
- `v20/.runtime/corpus/full_precompute/<run_id>/errors.jsonl`
- `v20/.runtime/corpus/full_precompute/<run_id>/progress.json`
- `v20/.runtime/corpus/full_precompute/latest_status.json`

After the full run, build the usable data artifacts:

```bash
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_20260501_main
```

Artifact outputs:

- `artifacts/coverage_summary.json`: coverage distributions, top clusters,
  evidence-density averages.
- `artifacts/corpus_index.sqlite`: local query index for case lookup and
  similar-chart retrieval. It stores feature ids, cluster keys, and structural
  tag signatures for weighted similarity search.
- `artifacts/flat_labels.jsonl`: flat training/export rows.
- `artifacts/cluster_model.json`: deterministic structural clusters with
  centroid tags, feature signatures, portrait-axis priors, and rare-cluster
  gap hints.
- `artifacts/similarity_index_manifest.json`: similarity-search contract and
  candidate/scoring policy.
- `artifacts/portrait_axis_learning.json`: portrait axis frequencies,
  co-occurrence priors, and clustering scope.
- `artifacts/portrait_axis_training.json`: portrait calibration model with
  axis priors, feature-based sub-axis hints, and cluster lift diagnostics.
- `artifacts/rule_proposal_support.json`: rule-proposal support counts across
  the full corpus.
- `artifacts/rule_proposal_training.json`: shadow-training view for proposals,
  including selectivity, exact feature signatures, cluster priors, and next
  training actions.
- `artifacts/postgres_import_manifest.json`: explicit Postgres import plan.
- `artifacts/parquet_export_manifest.json`: Parquet conversion plan. Current
  local environment lacks `pyarrow`, so flat JSONL is the authoritative export
  source until the Parquet dependency is installed.

Artifact endpoints:

- `GET /api/v20/corpus/artifacts/status`
- `GET /api/v20/corpus/artifacts/coverage-summary`
- `GET /api/v20/corpus/artifacts/cluster-model`
- `GET /api/v20/corpus/artifacts/training`
- `GET /api/v20/corpus/similar?case_id=v20.full_corpus.case.000000`
- `GET /api/v20/intelligence/generation-manifest`
- `GET /api/v20/validation/intelligence-generation`

Explicit export/import commands:

```bash
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_20260501_main --clusters
python3.12 v20/scripts/build_corpus_artifacts.py --run-id v20_full_518k_20260501_main --training
python3.12 v20/scripts/import_corpus_postgres.py --run-id v20_full_518k_20260501_main
python3.12 v20/scripts/import_corpus_postgres.py --run-id v20_full_518k_20260501_main --apply
python3.12 v20/scripts/export_corpus_parquet.py --run-id v20_full_518k_20260501_main
```

Postgres import requires `V20_DATABASE_URL` and `--apply`. Parquet export
requires `pyarrow`; without it the script returns a blocked dependency report.

The label snapshot contains structural labels only:

- chart facts
- core capacity bucket
- feature ids and domains
- macro feature domains
- measurement domains
- question keys
- knowledge ids
- portrait domains
- relation types
- visible and hidden ten-god labels

It explicitly does not contain destiny truth labels, guaranteed events,
personality verdicts, or outcome labels.

Local deterministic precompute does not require DGX. DGX or GPU clusters should
be reserved for later embedding, graph representation, GNN, Transformer, or
large-scale ranking experiments.

## Knowledge To Rule Proposals

Reviewed knowledge can now generate rule-path proposals:

`KnowledgeUnit -> KnowledgeRuleProposal -> shadow training -> promotion review`.

Endpoints:

- `GET /api/v20/knowledge/rule-proposals/{domain}`
- `GET /api/v20/knowledge/first-wave-rule-proposals`
- `GET /api/v20/knowledge/rule-proposal-preflight/{domain}`
- `GET /api/v20/knowledge/first-wave-rule-proposal-preflight`
- `GET /api/v20/knowledge/rule-extraction`
- `GET /api/v20/knowledge/rule-extraction-validation`
- `GET /api/v20/knowledge/llm-rule-extraction`
- `GET /api/v20/knowledge/llm-rule-extraction-validation`

Per the current product direction, proposals are not blocked from shadow
training. Static contract failures can still block malformed proposals, but
synthetic validation and DecisionRegistry approval are promotion requirements
for user-visible runtime, not prerequisites for learning.

Rule extraction itself is driven by the reviewed knowledge base, not by the
518K corpus. The corpus is only a validation and refinement layer that reports
whether extracted conditions are too broad, too sparse, or good enough for
shadow ranking. LLM assistance is similarly bounded: it may draft candidate
atoms from reviewed knowledge text, but it cannot create chart facts, activate
rules, or produce final Bazi conclusions.

The LLM draft endpoint is executable only under explicit env flags. If the LLM
provider is not ready, V20 records `provider_not_ready` and uses the
deterministic extractor as fallback. This keeps rule extraction useful on local
machines while making the real LLM lane ready for configured environments.

This keeps V20 open to self-training while preserving a clear boundary between
shadow intelligence and public-facing Bazi conclusions.
