# V19 P27 Domain Completion + Smart Rule Gate

Date: 2026-04-30

Status: implemented

## Goal

Move past small patches by completing the visible knowledge-base directory structure, adding a larger high-value knowledge pack, and converting eligible knowledge into Rule DB candidates with an automated synthetic regression gate.

## Added Knowledge Directories

- `docs/bazi_knowledge/ten_god/ten_god_units_v1.md`
- `docs/bazi_knowledge/strength/strength_units_v1.md`
- `docs/bazi_knowledge/time_context/time_context_units_v1.md`
- `docs/bazi_knowledge/pattern/pattern_units_v1.md`

These are human-readable companions for structured seed packs. They define boundaries and unit indexes without making runtime predictions.

## Added Content Pack

`docs/bazi_knowledge/packs/p27_domain_completion_knowledge_draft_seeds_v1.json`

Coverage:

- 10 ten-god metadata units
- 8 strength evidence units
- 6 time-context units
- 4 branch/stem relation units
- 5 pattern boundary units
- 7 wealth/income-structure units

Total: 40 draft knowledge units.

## Rule Conversion Policy

All P27 drafts can be seeded and ingested into Rule DB as candidates, but P27 engine activation is disabled by default. The activation path is:

```text
seed knowledge drafts
ingest Rule DB candidates
run P11 synthetic collision regression
select R1 synthetic_gate_candidate rules above confidence threshold
activate selected engine-adapter signals
run P11 regression again
rollback if post-activation regression fails
```

## Smart Gate Defaults

- prefix: `p27.`
- max risk: `R1`
- min confidence: `0.72`
- limit: `12`
- blocked categories: advanced pattern/stem fusion models
- runtime scope: structural signals only; no result mutation

## Admin Entry

`POST /api/lab/p27/smart-rule-gate`

Admin UI button: `P27 智能门禁`

## Guardrails

- `P27_SMART_RULE_ACTIVATION_GATE`
- `SYNTHETIC_REGRESSION_REQUIRED`
- `LOW_RISK_ONLY_BY_DEFAULT`
- `TRANSPARENT_ACTIVATION_LOG`
- `NO_RESULT_MUTATION`
- `NO_FORTUNE`

