from __future__ import annotations

import json
from pathlib import Path


def test_p69_mainline_p1_wraps_all_r3_r4_archive_sources_without_activation() -> None:
    from v19.rule_graph_orchestrator import orchestrate_rule_graph_paths
    from v19.synthetic_validation import build_p65_mainline_completion_audit, build_p69_mainline_p1_safe_wrappers, run_p69_mainline_p1_regression
    from v19.synthetic_validation.guided_cases import P11_GUIDED_SYNTHETIC_CASES
    from v19.synthetic_validation.guided_runner import _agent_data_for_case

    root = Path(__file__).resolve().parents[2]
    manifest = json.loads((root / "docs/bazi_knowledge/catalog/knowledge_base_v2_manifest.json").read_text(encoding="utf-8"))
    server = (root / "v19/server.py").read_text(encoding="utf-8")

    registry = build_p69_mainline_p1_safe_wrappers()
    regression = run_p69_mainline_p1_regression()
    audit = build_p65_mainline_completion_audit()

    assert registry["status"] == "mainline_p1_safe_wrappers_ready_no_activation"
    assert registry["summary"]["source_blocked_count"] == 88
    assert registry["summary"]["existing_p61_wrapped_count"] == 6
    assert registry["summary"]["candidate_count"] == 82
    assert registry["summary"]["total_safe_wrapper_coverage_count"] == 88
    assert registry["summary"]["unwrapped_source_count"] == 0
    assert registry["summary"]["by_wrapper_mode"] == {
        "boundary_only_safe_wrapper": 44,
        "evidence_only_label": 23,
        "route_only_safe_wrapper": 15,
    }
    assert all(row["risk_level"] == "R2" for row in registry["candidates"])
    assert all(row["source_risk_level"] in {"R3", "R4"} for row in registry["candidates"])
    assert all(row["engine_enabled"] is False and row["activation_allowed"] is False for row in registry["candidates"])

    assert regression["status"] == "pass"
    assert regression["summary"]["coverage_row_count"] == 4
    assert regression["summary"]["coverage_failed"] == 0
    assert regression["summary"]["failure_count"] == 0
    assert regression["summary"]["runtime_mutation"] is False
    assert {row["coverage_id"] for row in regression["coverage"]["rows"]} == {
        "pattern_boundary",
        "blind_lifa_boundary",
        "auxiliary_evidence",
        "advanced_branch_time",
    }
    assert all(row["matching_wrapper_count"] >= 1 for row in regression["coverage"]["rows"])

    data = _agent_data_for_case(P11_GUIDED_SYNTHETIC_CASES[0])
    pattern = orchestrate_rule_graph_paths(data, message="格局成格破格应该只看哪些结构边界？", answer_kind="pattern_structure", limit=8)
    blind = orchestrate_rule_graph_paths(data, message="盲派做功效率只能作为什么结构线索？", answer_kind="blind_lifa_boundary", limit=8)
    auxiliary = orchestrate_rule_graph_paths(data, message="神煞纳音命宫身宫只是什么证据标签？", answer_kind="auxiliary_evidence", limit=8)

    assert pattern["summary"]["candidate_count"] == 436
    assert any(row["domain"] == "pattern" and row["conversion_mode"] == "boundary_only_safe_wrapper" for row in pattern["selected_paths"])
    assert any(row["domain"] == "blind" and row["conversion_mode"] == "boundary_only_safe_wrapper" for row in blind["selected_paths"])
    assert any(row["topic_lane"] == "auxiliary_evidence" and row["conversion_mode"] == "evidence_only_label" for row in auxiliary["selected_paths"])

    assert audit["summary"]["p69_safe_wrapper_count"] == 82
    assert audit["summary"]["r3_r4_unwrapped_count"] == 0
    assert audit["summary"]["p1_action_count"] == 1
    assert {row["action_id"] for row in audit["priority_actions"] if row["priority"] == "P1"} == {"p65.p1.rule_graph_selection_coverage"}

    assert "/api/lab/mainline-p1-safe-wrappers" in server
    assert "/api/lab/mainline-p1-safe-wrappers/run" in server
    assert "docs/v19/V19_P69_MAINLINE_P1_SAFE_WRAPPERS.md" in manifest["created_from"]
    assert manifest["p69_mainline_p1_safe_wrappers"]["candidate_count"] == 82
    assert manifest["p69_mainline_p1_safe_wrappers"]["coverage_failed"] == 0
    assert manifest["p69_mainline_p1_safe_wrappers"]["runtime_mutation"] is False
    assert "P69_MAINLINE_P1_SAFE_WRAPPERS" in manifest["guardrails"]
