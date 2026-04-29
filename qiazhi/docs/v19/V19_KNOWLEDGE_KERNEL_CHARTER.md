# V19 Knowledge Kernel Charter

The V19 Knowledge Kernel is domain-neutral. Wealth is only one knowledge domain.

## Unit Shape

Each knowledge unit has:

- `knowledge_id`
- `domain`
- `title`
- `statement`
- `conditions`
- `feature_mapping`
- `effects`
- `risks`
- `uncertainty`
- `conflicts`
- `source_refs`
- `confidence_prior`
- `status`
- `content_hash`

## Domains

Initial domains:

- `core_structure`
- `ten_god`
- `five_element`
- `strength`
- `luck_flow`
- `theme_mapping`
- `wealth`
- `career`
- `relationship`
- `health`
- `personality`
- `family`
- `study`

## Lifecycle

```text
draft
-> reviewed
-> evidence_template
-> sandbox_candidate
-> test
-> review_pr
-> active_rule
```

The Knowledge Kernel only owns `draft`, `reviewed`, `deprecated`, and evidence template compilation.

Rule activation belongs to the Rule Kernel, not the Knowledge Kernel.

## Hard Rules

- Reviewed knowledge is immutable.
- Deprecated knowledge cannot be compiled.
- Knowledge compilation emits evidence templates only.
- Evidence templates are not production predictions.
- LLM audit can add findings, but cannot change the knowledge unit directly.
- Every template must include provenance and runtime guardrails.

## First Migration Samples

V18 wealth knowledge units may be used as migration samples, but the schema must be validated with non-wealth core units before V19 grows theme adapters.
