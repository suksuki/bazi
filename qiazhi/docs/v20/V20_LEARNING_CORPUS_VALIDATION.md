# V20 Learning, Corpus, And Synthetic Validation

V20 treats learning as a governed dry-run system until validation and decision
records approve a scoped promotion.

## Corpus Plan

The first full-coverage target is `518,400` structural Bazi cases. V20 exposes
this as a sharded coverage plan, not as automatic conclusions:

- `GET /api/v20/corpus/coverage`
- `FULL_CORPUS_TARGET_COUNT = 518_400`
- each shard records case ranges, batch size, and batch count
- precompute snapshots store feature counts, measurement topic counts, question
  counts, and answer-plan versions

The corpus is a structural map. It does not store destiny truth labels.

## Synthetic Validation

Synthetic validation is centralized through:

- `v20.validation.suite.run_synthetic_suite`
- `GET /api/v20/validation/synthetic-suite`

The suite verifies expected feature domains, expected question keys, forbidden
answer text, and runtime mutation invariants.

## Learning Evolution

`GET /api/v20/learning/evolution-plan` exposes the current dry-run tracks:

- embedding retrieval recall
- Bayesian confidence calibration
- learning-to-rank question ordering
- coverage gap clustering

GNN, reinforcement learning, and neural conclusion generation remain deferred.
They can support research later, but they cannot mutate core Bazi truth or
produce black-box fortune verdicts.
