# V50 Staged Cognition and Accepted-Artifact Streaming v1

Status: implementation contract

## Product Promise

The user must receive the first accepted Mingli cognition as soon as it passes factual review. The product must not wait for unrelated life domains to finish.

```text
Chart facts
→ accepted Pattern
→ accepted work path
→ accepted Ziwei peer lens
→ accepted prior assertions
→ complete whole-chart core
→ user-selected domain on demand
```

## Streaming Semantics

Streaming means accepted-artifact streaming, not exposing incomplete JSON, hidden chain-of-thought, unreviewed claims or token fragments.

Each stage may become visible only after its deterministic checks pass. Later stages extend the case cognition; they do not silently replace an accepted earlier stage.

## First Reading Boundary

The first reading produces:

- chart-specific first look;
- salient phenomena;
- competing hypotheses and the current leader;
- work path, conditional useful-god reasoning and portrait;
- optional Ziwei cross-lens synthesis;
- prior assertions and one discriminating Probe;
- an Epistemic Review receipt.

It does not automatically generate career, wealth or every other life domain.

## Domain Boundary

A domain is generated when the user or Abu selects a real question. It reuses the sealed whole-chart cognition and retrieves only domain-relevant facts and knowledge.

```text
Whole-chart core
  ├─ career, on demand
  ├─ wealth, on demand
  ├─ relationship, on demand
  ├─ life timing, on demand
  └─ other supported domains, on demand
```

Opening another domain must not recompute Pattern, work path or natal facts. A previously accepted domain is reused.

## UI Contract

1. Chart facts appear immediately.
2. Pattern appears as real reading content, not as a percentage update.
3. Work path, Ziwei and prior assertions are appended in place.
4. Abu explains that deeper checking continues without blocking reading.
5. On completion, the canvas offers life-domain exploration.
6. Mobile and desktop show the same epistemic stage and accepted content.

## Model Boundary

Model identity is a routing policy, not part of the product contract. Gemma4 and qwen3.5:35b must be compared on the same context, schema and sealed chart set. Promotion requires non-inferior professional cognition, lower effective latency and no higher repair rate.

Deployment must run the routing audit before a model assignment is promoted:

```text
PYTHONPATH=packages:apps ../.venv/bin/python scripts/v50_audit_model_routing.py \
  --registry config/model_registry.json \
  --env-file .env.v50.production
```

The audit reports drift; it never rewrites the environment or promotes a candidate.

## Latency Targets

```yaml
time_to_chart_ready_p50: <= 1s
time_to_first_accepted_pattern_p50: <= 30s
time_to_whole_chart_core_p50: <= 60s
time_to_selected_domain_p50: <= 90s
cached_stage_p50: <= 2s
```

## Invariants

- no template fallback;
- no downgrade from accepted cognition to progress copy;
- no domain generation before user intent unless explicitly prefetched at idle priority;
- no Probe update may recompute natal facts;
- no unreviewed stage may be presented as accepted;
- old v2 cases remain readable while new staged records use v3.
