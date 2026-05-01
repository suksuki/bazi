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

Per the current product direction, proposals are not blocked from shadow
training. Static contract failures can still block malformed proposals, but
synthetic validation and DecisionRegistry approval are promotion requirements
for user-visible runtime, not prerequisites for learning.

This keeps V20 open to self-training while preserving a clear boundary between
shadow intelligence and public-facing Bazi conclusions.
