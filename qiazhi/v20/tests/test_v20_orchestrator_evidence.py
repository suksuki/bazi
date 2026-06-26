from __future__ import annotations

from v20.api.runtime import run_runtime_from_pillars
from v20.access.projection import project_runtime_for_role


def test_v20_orchestrator_compiles_unified_evidence_and_candidates() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.evidence",
        user_text="我想看事业和财运",
    )

    evidence = result["orchestrator_evidence"]
    arbitration = result["mainline_arbitration"]
    primary = arbitration["primary_mainline"]

    assert evidence["version"] == "v20.orchestrator_evidence_compiler.v1"
    assert evidence["status"] == "ready"
    assert evidence["evidence_count"] >= 3
    assert all("evidence_id" in row for row in evidence["items"])
    assert all("role_visibility" in row for row in evidence["items"])
    assert primary["candidate_id"] == primary["candidate_key"]
    assert primary["evidence_ids"]
    assert primary["source_types"]
    assert "question_relevance" in primary
    assert "time_relevance" in primary
    assert "conflict_risk" in primary
    assert arbitration["evidence_count"] == evidence["evidence_count"]
    assert "MAINLINE_CANDIDATES_REFERENCE_UNIFIED_EVIDENCE" in arbitration["guardrails"]


def test_v20_orchestrator_evidence_is_role_projected() -> None:
    result = run_runtime_from_pillars(
        "庚午",
        "辛巳",
        "乙亥",
        "壬午",
        input_id="orchestrator.role_projection",
        user_text="我想看事业和财运",
    )

    user = project_runtime_for_role(result, "user")
    analyst = project_runtime_for_role(result, "analyst")
    admin = project_runtime_for_role(result, "admin")

    assert "orchestrator_evidence" not in user
    assert "orchestrator_evidence" in analyst
    assert "orchestrator_evidence" in admin
    assert all("source_key" not in row for row in user["mainline_arbitration"]["evidence_items"])
    assert analyst["orchestrator_evidence"]["evidence_count"] >= len(user["mainline_arbitration"]["evidence_items"])
