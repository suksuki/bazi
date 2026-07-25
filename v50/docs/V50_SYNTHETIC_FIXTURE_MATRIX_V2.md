# V50 Synthetic Fixture Matrix v2

Status: Implemented
Scope: Taxonomy-backed structural validation

## Purpose

Synthetic Fixture Matrix v2 turns Synthetic Chart Taxonomy v1 into a runnable
validation matrix.

It validates:

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
```

It does not validate final fortune-telling.

## Source

```text
data/validation/fixtures/synthetic_chart_taxonomy_v1.json
```

## Matrix Fixture

```text
data/validation/fixtures/synthetic_fixture_matrix_v2.json
```

## Runner

```bash
PYTHONPATH=v50/packages:v50/apps:v50 \
v50/.runtime/venv/bin/python \
v50/scripts/v50_run_synthetic_fixture_matrix.py \
--group synthetic_fixture_matrix_v2 \
--write-report
```

## Result

```text
total: 17
passed: 17
failed: 0
expected_gap_count: 10
llm_used: false
brain_used: false
training_performed: false
node_importance_policy_version: node_importance_policy_v2
path_score_policy_version: path_score_policy_v2
```

## What Passed

The matrix confirms that current V50 can run all 17 taxonomy families through
the structural computation chain.

Stable cases include:

- month command dominant
- bridge node dominant
- converter dominant
- day branch anchor
- hidden stem / storage baseline
- broken triple combination
- output to wealth baseline
- output controls pressure baseline
- mixed no-obvious-main-path baseline

## Expected Algorithm Gaps

These gaps are intentional report outputs.

They must not be hidden by weight tuning.

```text
path:combination_future_scope
path:clash_pressure_path
path:output_controls_pressure
path:pressure_path
path:resource_to_body
path:output_path_under_pressure
path:wealth_generates_officer
path:peer_competes_for_wealth
path:timing_resource_reroute_candidate
path:year_activation_existing_node
```

## Interpretation

V2 shows that the structural chain is runnable across taxonomy families, but
the algorithm layer still lacks:

- non-si-you-chou combination recognition
- clash pressure modeling
- officer/killing pressure path refinement
- resource backflow / output disruption modeling
- wealth-generates-officer mechanism discovery
- peer-competes-for-wealth mechanism discovery
- luck reroute model
- year activation model

## Boundary

This phase did not:

- tune Node Importance weights
- tune Path Score weights
- create Brain verdicts
- call LLM
- train any policy
- change runtime rules

## Next Mainline

```text
Timing Model Candidate v1
        ↓
Mechanism Discovery v1
        ↓
Unified Theme Discovery v1
```
