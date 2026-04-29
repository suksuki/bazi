# V19 P14 Bazi Knowledge Expansion Drafts

## Decision

The knowledge base is ready for new Bazi content, but the new material should enter as reviewed drafts first, not as active runtime inference.

P14 adds 10 draft seeds:

- five ten-god family boundaries:
  - peer / 比劫
  - output / 食伤
  - wealth / 财
  - officer / 官杀
  - resource / 印
- month-command seasonal group boundary
- heavenly-stem combination boundary
- branch penalty source-version boundary
- twelve growth phase archive boundary
- useful-god boundary

## Risk Levels

- R1: stable relationship metadata and plain-language boundaries
- R2: relation rules that need source/version review before activation
- R3: high-level interpretive systems that stay analyst-reference only until separately modeled

The R3 items are:

- `p14.twelve_growth_phase.boundary.v1`
- `p14.useful_god.boundary.v1`

These require analyst review before any proposal conversion.

## Guardrails

- New content is draft seed material.
- No runtime inference mutation.
- No fortune or good/bad verdicts.
- High-risk content stays archive/reference until promoted through P12/P13.

## Validation

The draft seed JSON validates, and regression tests confirm:

- 10 P14 draft IDs exist;
- IDs are unique;
- high-risk content remains R3;
- forbidden usage blocks prediction/fortune activation.
