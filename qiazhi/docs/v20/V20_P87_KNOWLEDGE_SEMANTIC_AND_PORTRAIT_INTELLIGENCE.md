# V20 P87 Knowledge Semantic And Portrait Intelligence

P87 deepens the V20 intelligence spine after P86.

## What Changed

V20 now has two additional intelligence artifacts:

- `KnowledgeSemanticModel`: turns reviewed knowledge units into a semantic index for feature hooks, question hooks, portrait label candidates, interaction keywords, and rule-atom support.
- `PortraitIntelligence`: turns the raw portrait projection into ranked portrait axes with sub-axis label candidates, calibration prompts, and profile tags.

These are not conclusion engines. They are coordination models for the knowledge, portrait, interaction, and feature-discovery systems.

## Runtime Position

```text
KnowledgeRef[]
-> KnowledgeSemanticModel
-> FeatureDiscovery
-> PortraitIntelligence
-> Questions / Portrait / AnswerPlan
```

The semantic model is built from reviewed knowledge plus deterministic rule extraction. The portrait model consumes semantic labels, feature-discovery scores, and the existing feature-backed portrait axes.

## Intelligence Boundary

Allowed:

- generate portrait sub-axis label candidates
- provide interaction keyword routing
- provide small semantic weights to feature discovery
- expose analyst-visible rule atom counts and derived subrule counts
- prepare LLM draft lanes for structured extraction

Blocked:

- personality verdicts
- chart fact generation
- runtime rule activation
- direct fortune conclusions
- replacing reviewed knowledge with LLM output

## Why It Matters

The portrait system is no longer a passive list of feature domains. It now has a knowledge-backed semantic layer that can learn labels, calibration prompts, and interaction routes over time, while still preserving the V20 rule that features and reviewed knowledge remain the source of truth.
