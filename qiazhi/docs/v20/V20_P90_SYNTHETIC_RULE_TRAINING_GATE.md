# V20 P90 Synthetic Rule Training Gate

P90 clarifies the rule-learning boundary.

The 518K corpus is useful for coverage, clustering, similarity retrieval, and
feature/question ranking priors. It cannot teach rule truth because it contains
structural labels only, not verified rule outcomes.

## Rule Source

Runtime rule candidates come from:

```text
Reviewed KnowledgeUnit
-> KnowledgeRuleProposal
-> ExtractedRuleAtom
-> SyntheticRuleCase collision
-> active rule weight gate
```

LLM may draft rule atoms from reviewed knowledge, but the knowledge base remains
the authority. Neither LLM nor the 518K corpus may create chart facts, mutate
rules, or produce final Bazi conclusions.

## Synthetic Training

`v20.validation.rule_synthetic` defines synthetic rule cases with:

- explicit pillars and optional time pillars
- selected question key
- expected rule domains
- expected feature prefixes
- expected recommended question keys
- forbidden output text

The suite validates that a rule candidate collides with the current chart's
compiled features. This is rule training in the V20 sense: it trains the active
gate and exposes missing atoms/counterexamples. It is not outcome learning.

## Runtime And CLI

Endpoints:

- `GET /api/v20/validation/rule-synthetic-suite`
- `GET /api/v20/learning/rule-synthetic-training`
- `GET /api/v20/learning/rule-synthetic-training?status=true`

Local command:

```bash
python3.12 v20/scripts/run_rule_synthetic_training.py
python3.12 v20/scripts/run_rule_synthetic_training.py --write
python3.12 v20/scripts/run_rule_synthetic_training.py --status
```

`--write` stores a local runtime artifact under:

```text
v20/.runtime/local/training/rule_synthetic/latest.json
```

The artifact is local and ignored by git.

## 518K Role After P90

The full corpus can still carry chart-specific salience labels:

- ten-god focus
- element emphasis
- branch relation focus
- time-layer triggers

Those labels help ranking and coverage analysis, but every rule still needs
synthetic collision validation before it can influence a active rule weight, and
DecisionRegistry approval before any user-visible promotion.
