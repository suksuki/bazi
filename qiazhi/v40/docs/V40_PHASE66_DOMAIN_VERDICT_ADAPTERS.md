# V40 Phase 66: Domain Verdict Adapters

Date: 2026-07-02

## Mainline Goal

Phase 66 adds the first product-grade domain layer between raw signals and final verdicts.

The adapter does not replace DecisionEngine. It reorganizes native Bazi Pro facts and migrated V30 asset signals into topic-specific decision material.

```text
RuntimeSignal
  -> Domain Verdict Adapter
  -> domain adapter signal
  -> DecisionEngine
  -> Verdict / Advice / Probe
```

## Implemented Module

```text
v40/decision/domain_adapters.py
build_domain_adapter_signals
```

DecisionEngine now inserts adapter signals after selecting decision topics and before building branches/verdicts.

## Covered Domains

V1 covers:

- career;
- wealth;
- relationship;
- health;
- timing;
- useful_god;
- hidden_attribute.

## Boundary

```text
Domain adapter signals are still RuntimeSignal.
They do not have decision authority.
They do not mutate chart facts.
They do not use LLM.
They are trainable only through downstream weights and claim scores.
```

## Why This Matters

Before Phase 66, DecisionEngine mostly consumed raw fact/path/rule signals directly. That kept the architecture clean, but the product output could still feel generic because it lacked a domain-specific organizing layer.

After Phase 66:

```text
facts + V30 migrated assets + native signals
  -> topic-specific claim
  -> verdict evidence
  -> advice priority
```

This helps the final output speak in domain language:

- career: responsibility, platform, delivery, stability/breakthrough;
- wealth: resource entry, output, distribution boundary, risk owner;
- relationship: relationship star, branch interaction, rhythm, boundary;
- health: pressure, rhythm, feedback, no illness overclaim;
- timing: luck/year trigger background;
- useful god: candidates, root, month authority, feedback;
- hidden attribute: Probe only when surface explanation is insufficient.

## Trainable Targets

Each adapter signal emits:

```text
domain_adapter.{topic}.claim_score
advice_priority.{topic}
signal_weight.domain_adapter.{topic}
```

This keeps the user-facing behavior trainable while preserving immutable facts.

## Acceptance Criteria

Phase 66 V1 is complete when:

1. Domain adapter signals are generated for selected topics.
2. Adapter signals enter DecisionEngine input.
3. Final verdict evidence can trace back to `domain-adapter:{topic}`.
4. Migrated V30 asset signals can be consumed by the adapter.
5. Adapter signals cannot mutate chart facts or own verdict authority.
6. V40 test suite remains green.

## Next After Phase 66

Phase 67 should focus on:

```text
Hidden Factor Probe Engine
```

That phase should make hidden-attribute probing goal-directed, option-based and feedback-bound, instead of generic follow-up questions.
