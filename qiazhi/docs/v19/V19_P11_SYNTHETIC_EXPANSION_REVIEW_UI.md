# V19 P11 Synthetic Expansion + Review UI

## Scope

P11 extends the P10 synthetic collision matrix and connects failure output to the Admin review surface. The flow remains controlled:

- synthetic cases only, no real birth data;
- failures generate audit records and draft proposals only;
- knowledge/rule/expression changes still require analyst review;
- no automatic learning, rule promotion, or runtime mutation.

## Matrix

The guided synthetic matrix now contains 20 cases:

- 12 P10 baseline cases;
- 8 P11 expansion cases covering:
  - clash + harm;
  - combination + break;
  - three harmony + three meeting across natal/time layers;
  - visible ten-god vs hidden-stem ten-god conflict;
  - visible wealth element disrupted by clash;
  - visible wealth element bound by combination;
  - time-layer relation trigger without natal mutation;
  - month-command boundary colliding with income/relation structure.

Each case carries:

- `structure_label`;
- `collision_focus`;
- expected recommended questions;
- standardized `knowledge_tags`;
- baseline vs KB-augmented comparison expectations.

## Review UI

Admin now exposes `Synthetic Collision Review` under Evolution Interfaces.

The UI shows:

- P11 run status and stable/misfire/missing counts;
- every failing synthetic case, including failure reason and text preview;
- audit records grouped by attribution layer;
- draft proposals with target type and suggested next action.

Attribution layers are normalized to:

- `recommendation`;
- `knowledge`;
- `rule`;
- `expression`;
- `synthetic`.

## Result

Current P11 matrix result:

- total: 20;
- passed: 20;
- failed: 0;
- generated audit records: 0;
- generated draft proposals: 0.

This means the current expansion is stable. The failure UI is still wired and covered by regression tests so later failures can enter analyst review immediately.
