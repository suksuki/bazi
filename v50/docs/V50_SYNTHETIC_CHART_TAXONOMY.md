# V50 Synthetic Chart Taxonomy v1

Status: Mainline Taxonomy Draft
Owner: V50 Mingli Core
Boundary: This taxonomy defines expected structures, not expected fortunes.

## 1. Purpose

Synthetic charts are not random charts.

They are controlled structural samples with explicit expectations.

The goal is to validate:

```text
Graph
        ↓
Path
        ↓
Role
        ↓
Importance
        ↓
Ablation
        ↓
FlowState
        ↓
StateDelta
```

The goal is not to validate:

```text
good fortune
bad fortune
career success
wealth size
marriage outcome
```

## 2. Hard Boundary

```text
Node Importance / Path Score weights cannot be tuned from one chart.
Synthetic Chart Taxonomy must define what kinds of structures exist
before algorithms are tuned against them.
```

Every synthetic chart must carry:

```text
case_type
chart
expected_structure
expected_top_node
expected_path
expected_ablation
must_not
```

## 3. First Taxonomy Set

V1 defines 17 structural families:

```text
1. month_command_dominant
2. bridge_node_dominant
3. converter_dominant
4. day_branch_anchor
5. hidden_stem_dark_line
6. complete_triple_combination
7. broken_triple_combination
8. clash_breaks_main_path
9. output_to_wealth
10. output_controls_pressure
11. mixed_officer_killing_with_control
12. resource_disrupts_output
13. wealth_generates_officer
14. peer_competes_for_wealth
15. mixed_no_obvious_main_path
16. luck_changes_main_path
17. year_activates_key_node
```

## 4. What Each Case Tests

### 4.1 Month Command Dominant

Tests whether month branch can rank first when it is truly the environment node.

Must not become:

```text
month_branch_always_first
```

### 4.2 Bridge Node Dominant

Tests whether a node that connects a structural subgraph can outrank month command.

Must not become:

```text
all_combination_nodes_are_bridge
```

### 4.3 Converter Dominant

Tests whether a visible converter can become the key node when it is the main energy-turning point.

Must not become:

```text
all_output_stems_are_first
```

### 4.4 Day Branch Anchor

Tests whether the day branch can become the structural anchor in rooted charts.

Must not become:

```text
day_branch_always_anchor_first
```

### 4.5 Hidden Stem Dark Line

Tests whether hidden stems and storage branches remain visible to the engine without becoming user-facing fortune claims.

Must not become:

```text
hidden_line_fortune_claim
```

### 4.6 Complete Triple Combination

Tests whether a complete combination structure is recognized as a connected graph.

Must not become:

```text
si_you_chou_only_bias
```

### 4.7 Broken Triple Combination

Tests whether replacing one structural node breaks bridge assumptions.

Must not become:

```text
bridge_role_survives_after_required_node_removed
```

### 4.8 Clash Breaks Main Path

Tests whether a clash can interrupt a previously strong path.

Must not become:

```text
clash_always_bad
```

### 4.9 Output To Wealth

Tests whether output can form a wealth path through earth / wealth-bearing targets.

Must not become:

```text
any_earth_equals_wealth_success
```

### 4.10 Output Controls Pressure

Tests whether output can control officer/killing pressure through a coherent path.

Must not become:

```text
any_output_plus_metal_equals_control
```

### 4.11 Mixed Officer/Killing With Control

Tests whether mixed pressure can be separated from controlled pressure.

Must not become:

```text
guan_sha_mixed_always_bad
```

### 4.12 Resource Disrupts Output

Tests whether resource can reroute flow away from output.

Must not become:

```text
resource_always_good
```

### 4.13 Wealth Generates Officer

Tests whether wealth can feed officer/killing pressure instead of only meaning money.

Must not become:

```text
wealth_star_always_money
```

### 4.14 Peer Competes For Wealth

Tests whether peer nodes can compete for wealth path resources.

Must not become:

```text
peer_always_bad
```

### 4.15 Mixed No Obvious Main Path

Tests whether the engine can stay uncertain and avoid forcing a named mechanism.

Must not become:

```text
always_name_a_mechanism
```

### 4.16 Luck Changes Main Path

Tests whether long-term timing overlay can shift path ranking.

Must not become:

```text
luck_is_second_month_command_by_default
```

### 4.17 Year Activates Key Node

Tests whether annual timing can activate an existing structural node.

Must not become:

```text
year_rewrites_natal_structure
```

## 5. Structured Canon

The machine-readable taxonomy lives in:

```text
data/validation/fixtures/synthetic_chart_taxonomy_v1.json
```

The taxonomy is a design asset.

It is not yet a runtime rule source.

## 6. Next Use

The taxonomy should feed:

```text
Synthetic Fixture Matrix v2
        ↓
Node Importance / Path Score Review v3
        ↓
Timing Model Candidate v1
        ↓
Mechanism Discovery v1
```

Do not tune weights until taxonomy coverage is reviewed.
