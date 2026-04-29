# V19 Bazi System Charter

V19 is a clean Bazi-first system. It is not a wealth-only system and it is not an LLM fortune-telling system.

## Center

The system center is Bazi Core:

- canonical chart facts
- ten-god and five-element models
- strength and root models
- structure effects such as combination, clash, punishment, harm, vault, transformation, regulation, and flow activation
- general evidence that every theme adapter must consume

Wealth, career, relationship, health, personality, family, and study are theme adapters. They are not the core.

## Knowledge

Knowledge is not a rule and not a prompt.

Knowledge units can produce:

- evidence templates
- conflict reports
- sandbox candidates
- test cases
- audit packets

Knowledge units cannot directly produce production predictions.

## Agents

Agents orchestrate work. They do not decide facts.

Planned V19 agents:

- ChartAgent: normalizes birth data into canonical chart input.
- CoreAgent: runs Bazi Core and emits core evidence.
- KnowledgeAgent: retrieves and compiles reviewed knowledge units.
- ThemeAgent: maps core evidence to theme evidence.
- VerifierAgent: checks evidence binding and contract boundaries.
- NarrativeAgent: explains verified contracts only.
- LearningAgent: turns feedback into draft knowledge or sandbox candidates.

## Runtime Boundary

Production prediction must flow through:

```text
chart input
-> bazi core facts
-> core evidence
-> theme adapter
-> active rule resolution
-> prediction contract
-> verifier
-> ledger
-> safe explanation
```

LLM can audit, summarize, and explain. It cannot create facts, change confidence, activate rules, or write ledger records.

## Migration Rule

V17/V18 may be used as reference material, but V19 must not copy legacy runtime coupling into the new core.

Legacy code can be wrapped by adapters during migration. It must not become the architectural center.

## Core Bazi Inference Layer

V19 is a Core Bazi Engine, not a Wealth Engine.

The mandatory reasoning order is:

```text
Core Feature -> Core Strength -> Structure Effect -> Core Bazi Inference -> Domain Mapping
```

Core Bazi Inference outputs structural understanding only:

```text
day_master_state
ten_god_structure
structural_stability
energy_flow
conflicts_and_balance
uncertainty_sources
```

It must not output wealth conclusions, career conclusions, relationship conclusions, health conclusions, final useful-god judgments, ledger records, prediction IDs, or user-facing narrative.

Wealth remains an optional downstream domain adapter for calibration and comparison. It is not the V19 system axis.
