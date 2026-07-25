# V50 Synthetic Work-System Validation

Status: active design / first runner implemented
Scope: synthetic chart lab for work-system modeling

## 1. Purpose

Synthetic Chart Lab is not only a testing tool.

It is an algorithm design tool.

The goal is not:

```text
generate charts and check whether final fortune-telling sounds right
```

The goal is:

```text
construct charts with controlled structural variables
        ↓
expose what the engine must detect
        ↓
force Path Explorer / Role Classifier / Importance / Ablation to stay honest
```

## 2. Core Principle

```text
Work-system is not a label.
Work-system is path + role + flow + state change.
```

Therefore:

```text
Mechanism Candidate must come after Path Explorer, Role Classifier, Importance, Ablation, and State Delta.
```

If mechanism labels are added too early, the system will become:

```text
old formula matching wrapped in graph terminology
```

## 3. Required Pipeline

Every synthetic case must run:

```text
Bazi Material Store
        ↓
Graph Builder
        ↓
Path Explorer
        ↓
Node Role Classifier
        ↓
Importance Scoring
        ↓
State Builder
        ↓
Ablation Simulator
        ↓
Diff Report
```

Forbidden in this phase:

```text
Brain
LLM
UI
training
final user judgment
```

## 4. Golden Sample Strategy

First version uses 10 golden samples.

Do not start with 30-50 cases.

Quality matters more than count.

The 10 cases should include:

```text
1. bridge node type
2. converter node type
3. month-command genuinely dominant type
4. day-branch anchor type
5. hidden-stem dark-line type
6. complete triple-combination type
7. broken triple-combination type
8. luck changes main path type
9. year activates key node type
10. mixed structure with no obvious main path
```

At least half of the cases must not be variants of:

```text
丁巳 乙巳 乙丑 乙酉
```

This prevents:

```text
month-command mechanical bias
        ↓
si-you-chou mechanical bias
```

## 5. Expected Structure Contract

Each case validates structure, not destiny.

Example:

```yaml
expected_top_roles:
  hour_branch:
    - bridge_node
    - single_failure_node

expected_top_paths:
  - mechanism_hint.output_controls_pressure
  - mechanism_hint.combination_bridge

expected_critical_nodes:
  - label: 酉
    position: hour_branch
  - label: 丁
    position: year_stem

expected_ablation_order:
  - 酉:hour_branch
  - 丁:year_stem
  - 巳:month_branch

must_not_roles:
  巳:month_branch:
    - unconditional_master_controller
```

## 6. Diff Report

The runner should report:

```text
case_id
chart
structural_variable
top_paths
node_roles
critical_nodes
ablation_order
unexpected_roles
missing_roles
path_mismatch
ablation_mismatch
```

## 7. Success Definition

This phase succeeds when:

```text
Different chart structures produce different key nodes, roles, and paths.
```

It fails if:

```text
month branch always wins
酉-like bridge always wins
converter role is attached by visible-stem shortcut only
all charts produce the same mechanism hints
```

## 8. Next Step After Lab v1

Only after the Lab is stable:

```text
Mechanism Candidate from Path / Role / State v1
```

Mechanism Candidate must consume:

```text
ranked_paths
node_roles
node_importance
ablation_result
state_delta
```
