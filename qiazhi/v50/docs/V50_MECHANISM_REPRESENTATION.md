# V50 Mechanism Representation v1

Status: architecture contract implemented

## Core Principle

Mechanism is not a label.

Mechanism is a structured representation of:

```text
Source
        ↓
Path
        ↓
Converter / Bridge / Anchor
        ↓
Target / Counter Force
        ↓
State Delta
```

The label is presentation only.

Examples:

```text
食伤制杀
食伤生财
资源回流
官杀压力
```

These are labels. They help humans read the mechanism, but they are not the mechanism itself.

## Why This Exists

Mechanism Discovery v2 expanded semantic coverage from three mechanism names to seven mechanism names.

That was useful, but it created a risk:

```text
mechanism discovery becomes a mechanism library
```

V50 must avoid that.

The next layer must represent mechanism as an AST / grammar before creating more labels.

## Runtime Contract

Implemented package:

```text
core/mechanism/
  contracts.py
  builder.py
```

Primary objects:

```text
MechanismComponent
MechanismRepresentation
```

Component roles:

```text
source
path
converter
bridge
anchor
target
counter_force
state_delta
```

Boundary:

```text
MechanismRepresentation does not create judgment.
MechanismRepresentation does not call Brain.
MechanismRepresentation does not call LLM.
Mechanism label must remain presentation-only.
```

## Data Flow

```text
FlowState
GraphAnalysisResult
SimulationReport
        ↓
MechanismRepresentation
        ↓
future Mechanism Discovery / Ranking
        ↓
Brain
```

## What This Changes

Before:

```text
mechanism_code = output_controls_pressure
```

After:

```text
mechanism_code = output_controls_pressure
label = mechanism.label.output_controls_pressure
components:
  - source
  - path
  - converter
  - bridge
  - target
  - state_delta
```

The label can change later.

The AST is what Brain and validation should trust.

## Validation

Implemented tests:

```text
tests/test_v50_mechanism_representation.py
```

Validated:

```text
classic mechanism uses AST, not label authority
temporary mechanism uses the same grammar
label_is_presentation_only=false is rejected
no Brain / LLM / judgment boundary
```

## Next

Do not add more mechanism names before using this representation in the discovery pipeline.

Before Mechanism Discovery v3, run:

```text
docs/V50_MECHANISM_REPRESENTATION_AUDIT_PROTOCOL.md
```

Audit must prove:

```text
AST fields come from Path / Role / Ablation / StateDelta evidence.
Optional fields can remain empty.
Synthetic-filled fields are explicitly marked.
Labels do not decide the AST.
```

Next algorithm step:

```text
Mechanism Representation Audit v1
        ↓
Mechanism Discovery v3 from AST shape
        ↓
Semantic Coverage on AST-derived mechanisms
```
