# V50 Mechanism Representation Audit Protocol v1

Status: required before Mechanism Discovery v3

## Purpose

Mechanism Representation v1 is the correct direction.

But it is only a representation layer.

It is not yet proof that the system understands mechanism.

This audit prevents:

```text
old labels wrapped in AST
synthetic fields pretending to be discovery
forced eight-part mechanism shape
template state_delta
```

## Audit Question

Does each MechanismRepresentation come from actual Path / Role / Ablation / StateDelta evidence?

Or is it just a structured wrapper around a label?

## Required Audit Sample

Before Mechanism Discovery v3:

```text
sample size: 10 representations minimum
source: mechanism_representation_batch_v1.json
coverage:
  - at least 3 mechanism codes
  - at least 1 classic label
  - at least 1 temporary mechanism
  - at least 1 structural_baseline if present
```

## Required Output Per Representation

Each sampled representation must output:

```yaml
representation_id:
mechanism_code:
mechanism_label_code:
label_is_presentation_only:

raw_path:
  path_refs:
  path_node_ids:
  relation_types:
  path_score:

node_roles:
  source:
  converter:
  bridge:
  anchor:
  target:
  counter_force:

ablation:
  ablation_refs:
  affected_flows:
  mechanism_score_delta:
  state_delta:

state_delta_refs:

field_audit:
  source:
    evidence_refs:
    synthetic_filled: true / false
  path:
    evidence_refs:
    synthetic_filled: true / false
  converter:
    evidence_refs:
    synthetic_filled: true / false
  bridge:
    evidence_refs:
    synthetic_filled: true / false
  anchor:
    evidence_refs:
    synthetic_filled: true / false
  target:
    evidence_refs:
    synthetic_filled: true / false
  counter_force:
    evidence_refs:
    synthetic_filled: true / false
  state_delta:
    evidence_refs:
    synthetic_filled: true / false
```

## Field Rules

### Optional Fields Are Allowed

Not every mechanism needs:

```text
converter
bridge
anchor
counter_force
```

Missing optional fields are better than fake filled fields.

### Required Fields

Every representation must have:

```text
source
path
target
evidence_refs
```

### State Delta

State Delta must be connected to real ablation or timing evidence.

If state_delta is generated only because the template requires it:

```text
synthetic_filled: true
```

and the representation cannot be used for discovery ranking.

## Audit Checks

### 1. Evidence Origin Check

Every component must trace to one of:

```text
raw_path
node_role
node_importance
ablation_result
state_delta
flow_state
```

### 2. Label Authority Check

The label cannot decide the AST.

Bad:

```text
mechanism_code = output_controls_pressure
therefore converter and bridge are filled
```

Good:

```text
path contains output converter
node role classifier marks converter
ablation shows converter sensitivity
therefore converter component exists
```

### 3. Optional Field Check

No component should be filled only to complete the grammar.

Allowed:

```text
converter: empty
bridge: empty
counter_force: empty
```

### 4. State Delta Check

State Delta must carry:

```text
ablation_ref or timing_state_ref
affected_flow
delta value
evidence_refs
```

### 5. Synthetic Fill Check

Any inferred fallback must be explicit:

```text
synthetic_filled: true
reason: fallback_from_flow_state
```

Synthetic-filled components are allowed in representation reports.

They are not allowed to drive Mechanism Discovery ranking.

## Gate Decision

Mechanism Representation Audit can return:

```text
pass
partial
fail
```

### Pass

```text
>= 90% components are evidence-derived
0 label authority violations
0 fake required optional fields
state_delta evidence is real or explicitly marked synthetic
```

### Partial

```text
70-90% components are evidence-derived
fallback fields are marked
no label authority violation
```

### Fail

```text
label authority violation exists
optional fields are hard-filled
state_delta is templated without marking
```

## Boundary

This audit does not:

```text
create new mechanism names
change Brain
change Decision Policy
change Runtime weights
call LLM
```

## Next Step If Pass

```text
Mechanism Discovery v3 from AST shape
```

## Next Step If Partial

```text
Fix representation builder evidence tagging
then rerun audit
```

## Next Step If Fail

```text
Stop Mechanism Discovery
return to Formalization
```

