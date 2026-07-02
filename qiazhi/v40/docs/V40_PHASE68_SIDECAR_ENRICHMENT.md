# V40 Phase 68: Knowledge Portrait Ziwei Sidecar Enrichment

## Goal

Phase 68 adds a controlled enrichment layer between raw engine signals and product runtime surfaces.

It does not add a new verdict authority. It turns existing bazi and ziwei material into three kinds of sidecar signals:

1. `knowledge_card_enrichment_v1`
2. `portrait_signal_enrichment_v1`
3. `ziwei_sidecar_enrichment_v1`

## Runtime Flow

```text
Bazi engine signals
Ziwei sidecar signals
  -> Sidecar Enrichment Builder
  -> SignalRegistry
  -> DecisionEngine filter / Practitioner Lens / Conversation context
```

## Boundaries

### Knowledge Cards

Knowledge cards are explanation-only.

They may appear in the `SignalRegistry` and user/practitioner surfaces, but DecisionEngine filters them out through `EXPLANATION_ONLY_SOURCE_REFS`.

They train:

```text
knowledge_card.*.acceptance
explanation_basis.*.priority
```

They do not train verdict weights directly.

### Portrait Signals

Portrait signals are low-weight runtime signals.

They may enter DecisionEngine as weak candidate material, but they cannot become strong assertions by themselves. They train:

```text
portrait_weight.*
signal_weight.portrait.*
claim_score.portrait.*
```

### Ziwei Sidecar Enrichment

Ziwei remains a Domain Lens.

The enrichment layer can summarize agreement between bazi topics and ziwei topics, but every ziwei enrichment signal keeps `source = ziwei_engine`, role visibility limited to practitioner/admin/lab, and zero direct decision weight.

## Why This Is Needed

V40 already had facts, rules, paths, domain adapters, probe answers, and Ziwei sidecar signals. The missing product layer was controlled enrichment:

- knowledge should help explain, not judge;
- portrait should provide tendency, not strong verdict;
- Ziwei should help practitioners calibrate, not compete with bazi.

Phase 68 makes these distinctions executable.

## Files

```text
v40/enrichment/sidecar.py
v40/engines/bazi_native.py
v40/decision/engine.py
tests/test_v40_phase68_sidecar_enrichment.py
```
