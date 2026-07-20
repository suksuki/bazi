from __future__ import annotations

import sys
from pathlib import Path


V50_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = V50_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from v50_run_synthetic_fixture_matrix import run_group


def test_v50_synthetic_fixture_matrix_validates_flow_state_and_state_delta_chain() -> None:
    summary = run_group()

    assert summary["total"] == 10
    assert summary["passed"] == 10
    assert summary["failed"] == 0
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["node_importance_policy_version"] == "node_importance_policy_v2"
    assert summary["path_score_policy_version"] == "path_score_policy_v2"
    assert summary["checks"]["flow_state_adapter"] is True
    assert summary["checks"]["state_delta"] is True

    cases_by_id = {result["case_id"]: result for result in summary["results"]}
    bridge_case = cases_by_id["matrix_bridge_node_si_you_chou_complete"]
    assert {flow["mechanism"] for flow in bridge_case["flow_states"]} == {"output_controls_pressure", "output_to_wealth"}
    assert bridge_case["state_evolution"]["trend"] == "volatile"
    assert bridge_case["state_evolution"]["delta_by_dimension"]["timing_mechanism_shift"] < 0

    removed_case = cases_by_id["matrix_bridge_removed_no_you"]
    assert {flow["mechanism"] for flow in removed_case["flow_states"]} == {"output_to_wealth"}
    assert removed_case["state_evolution"]["trend"] == "increasing"

    mixed_case = cases_by_id["matrix_mixed_no_obvious_main_path"]
    assert {flow["mechanism"] for flow in mixed_case["flow_states"]} == {"structural_baseline"}
    assert mixed_case["state_evolution"] is None


def test_v50_synthetic_fixture_matrix_v2_covers_taxonomy_without_tuning_weights() -> None:
    summary = run_group("synthetic_fixture_matrix_v2")

    assert summary["source_fixture"] == "synthetic_chart_taxonomy_v1.json"
    assert summary["total"] == 17
    assert summary["passed"] == 17
    assert summary["failed"] == 0
    assert summary["llm_used"] is False
    assert summary["brain_used"] is False
    assert summary["training_performed"] is False
    assert summary["node_importance_policy_version"] == "node_importance_policy_v2"
    assert summary["path_score_policy_version"] == "path_score_policy_v2"
    assert summary["expected_gap_count"] == 10

    cases_by_id = {result["case_id"]: result for result in summary["results"]}
    assert set(cases_by_id) == {
        "matrix_v2_month_command_dominant",
        "matrix_v2_bridge_node_dominant",
        "matrix_v2_converter_dominant",
        "matrix_v2_day_branch_anchor",
        "matrix_v2_hidden_stem_dark_line",
        "matrix_v2_complete_triple_combination",
        "matrix_v2_broken_triple_combination",
        "matrix_v2_clash_breaks_main_path",
        "matrix_v2_output_to_wealth",
        "matrix_v2_output_controls_pressure",
        "matrix_v2_mixed_officer_killing_with_control",
        "matrix_v2_resource_disrupts_output",
        "matrix_v2_wealth_generates_officer",
        "matrix_v2_peer_competes_for_wealth",
        "matrix_v2_mixed_no_obvious_main_path",
        "matrix_v2_luck_changes_main_path",
        "matrix_v2_year_activates_key_node",
    }

    bridge_case = cases_by_id["matrix_v2_bridge_node_dominant"]
    assert bridge_case["active_flows"] == ["flow.output_controls_pressure", "flow.output_to_wealth_potential"]
    assert bridge_case["expected_gaps"] == []
    assert bridge_case["top_nodes"][0]["node"] == "酉:hour_branch"

    complete_combination = cases_by_id["matrix_v2_complete_triple_combination"]
    assert {gap["code"] for gap in complete_combination["expected_gaps"]} == {"path:combination_future_scope"}

    timing_case = cases_by_id["matrix_v2_luck_changes_main_path"]
    assert {gap["code"] for gap in timing_case["expected_gaps"]} == {"path:timing_resource_reroute_candidate"}
    assert timing_case["checks"]["known_gaps_are_reported_not_tuned"] is True
