# Plugin Governance Model (0.13)

## Plugin Categories
- Base Plugins: non-optional runtime foundations.
- Functional/Classical: traditional schools on top of L1.
- Functional/Modern: socio-semantic inference plugins.

## Registry Fields
- `plugin_id`: unique id (e.g. `classical.blind_school.v1`)
- `category`: plugin group
- `dependencies`: required base plugins
- `priority`: semantic weight for execution order
- `audit_source`: protocol/document source

## Hook Lifecycle
- `on_physics_complete`: run after L1 tensor is ready
- `on_verdict_ready`: run after final verdict generation

## Standard PluginOutput
- `verdict`: short plugin conclusion
- `evidence`: evidence array
- `confidence_score`: numeric confidence
- `payload`: full plugin payload

