# V50 Development Principle

Status: active mainline rule

## Product Goal

DeepBazi must first understand a chart professionally, then help a person understand life and make a better decision. Architecture, tests and UI are means, not the product.

```text
Mingli cognition quality
→ truthful case judgment
→ useful explanation
→ guided exploration
→ user value
```

## Cognitive Authority

- Fact engines own calendar, Bazi and Ziwei facts.
- The Mingli World Model owns curated knowledge, theories, cases and evidence.
- Deterministic tools expose graph, path, role, ablation and timing observations.
- The LLM Mingli Agent owns whole-chart synthesis and case-level judgment.
- Epistemic Review checks facts, evidence, counter-evidence, uncertainty and safety.
- Abu owns guidance and interaction, never Mingli judgment.

No deterministic module may quietly become a second cognitive brain. No LLM may invent chart facts.

## Capability Gate

Every implementation slice must answer:

1. What real user or practitioner capability improves?
2. What part of Mingli cognition becomes more accurate, complete or testable?
3. What evidence will distinguish improvement from cosmetic change?

Pure infrastructure is allowed only when it directly unblocks a named capability. Do not stack abstractions without a user-visible or research-visible gain.

## Research And Case Reasoning

Two different processes must not be confused.

### Global theory promotion

```text
Question → Observation → Hypothesis → Counter examples
→ Evidence → Theory review → Formalization → Tool/runtime promotion
```

Global rules, knowledge and model policies require evidence and human research review.

### Case-level cognition

```text
Chart facts → Pattern discovery → Competing hypotheses
→ Comparative reasoning → Assertions → Review → Probe → Case revision
```

The LLM may form, compare and revise case hypotheses. A case hypothesis does not become global theory, runtime law or model training data automatically.

## Training And Validation

- Synthetic charts validate structural sensitivity and metamorphic behavior.
- Curated expert cases evaluate whole-chart cognition and domain usefulness.
- Probe feedback calibrates the current case belief state.
- Training may calibrate retrieval, ranking, policies or models only after the target and evidence contract are explicit.
- Passing a schema or verifier is not proof of Mingli quality.

## Product Rule

Do not expose engineering artifacts as user content. The page shows the current life task and accepted Mingli result; Abu explains, asks the next useful question and moves the journey forward. Professional and research depth is available only to authorized roles.

## Stop Rule

Stop or redesign a slice when it produces templates, repeated semantics, unsupported certainty, duplicate navigation, or more internal machinery without better readings.

Current authority:

- `V50_CURRENT_ARCHITECTURE.md`
- `V50_MINGLI_COGNITIVE_ARCHITECTURE_V1.md`
- `V50_RUNTIME_MODULE_AUTHORITY_MAP_V1.md`
- `V50_MINGLI_RESEARCH_TO_RUNTIME_PROTOCOL.md`
