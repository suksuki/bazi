from __future__ import annotations

from v20.knowledge.completeness_audit import build_knowledge_completeness_audit
from v20.tests.support_paths import read_v20_text


def test_v20_knowledge_completeness_audit_reports_directory_gaps() -> None:
    audit = build_knowledge_completeness_audit()

    assert audit["version"] == "v20.knowledge_completeness_audit.v1"
    assert audit["status"] in {"needs_work", "complete"}
    assert audit["node_count"] == 13
    assert audit["p0_node_count"] >= 10
    assert audit["rule_count"] >= 483
    assert audit["runtime_allowed_count"] == audit["rule_count"]
    assert audit["external_topic_count"] >= 12
    assert 0 <= audit["external_completeness_percent"] <= 100
    assert audit["runtime_mutation"] is False
    assert "KNOWLEDGE_COMPLETENESS_AUDIT_READ_ONLY" in audit["guardrails"]

    by_node = {row["node_key"]: row for row in audit["node_audits"]}
    assert {"L0", "L1", "L6", "L7", "L8", "L9", "L10", "L11", "L12"} <= set(by_node)
    assert by_node["L0"]["external_topics"]
    assert by_node["L0"]["rule_count"] >= 1
    assert by_node["L0"]["answer_guidance_count"] >= 1
    assert by_node["L0"]["synthetic_case_count"] >= 1
    assert "missing_synthetic_case_for_p0_external_topics" not in by_node["L0"]["gap_tags"]
    assert "needs_p0_atomized_knowledge_units" not in by_node["L0"]["gap_tags"]
    assert by_node["L1"]["rule_count"] >= 1
    assert by_node["L1"]["answer_guidance_count"] >= 1
    assert by_node["L1"]["synthetic_case_count"] >= 1
    assert "needs_p0_atomized_knowledge_units" not in by_node["L1"]["gap_tags"]
    assert by_node["L6"]["rule_count"] >= 1
    assert by_node["L6"]["answer_guidance_count"] >= 1
    assert by_node["L6"]["synthetic_case_count"] >= 1
    assert "needs_p0_atomized_knowledge_units" not in by_node["L6"]["gap_tags"]
    assert by_node["L7"]["rule_count"] >= 1
    assert by_node["L7"]["answer_guidance_count"] >= 1
    assert by_node["L7"]["counterexample_count"] >= 1
    assert by_node["L7"]["synthetic_case_count"] >= 3
    assert by_node["L7"]["missing_external_topics"] == ()
    assert "missing_synthetic_case_for_p0_external_topics" not in by_node["L7"]["gap_tags"]
    assert "needs_p0_atomized_knowledge_units" not in by_node["L7"]["gap_tags"]
    assert by_node["L8"]["rule_count"] >= 1
    assert by_node["L8"]["answer_guidance_count"] >= 1
    assert by_node["L8"]["counterexample_count"] >= 1
    assert by_node["L8"]["synthetic_case_count"] >= 3
    assert by_node["L8"]["missing_external_topics"] == ()
    assert "missing_synthetic_case_for_p0_external_topics" not in by_node["L8"]["gap_tags"]
    assert "needs_p0_atomized_knowledge_units" not in by_node["L8"]["gap_tags"]
    assert by_node["L9"]["rule_count"] >= 1
    assert by_node["L9"]["answer_guidance_count"] >= 1
    assert by_node["L9"]["synthetic_case_count"] >= 1
    assert "needs_p0_atomized_knowledge_units" not in by_node["L9"]["gap_tags"]
    assert by_node["L11"]["rule_count"] >= 1
    assert by_node["L11"]["answer_guidance_count"] >= 1
    assert by_node["L11"]["synthetic_case_count"] >= 1
    assert "missing_synthetic_case_for_p0_external_topics" not in by_node["L11"]["gap_tags"]
    assert "needs_p0_atomized_knowledge_units" not in by_node["L11"]["gap_tags"]
    assert by_node["L10"]["rule_count"] >= 1
    assert by_node["L10"]["answer_guidance_count"] >= 1
    assert by_node["L10"]["counterexample_count"] >= 7
    assert by_node["L10"]["synthetic_case_count"] >= 1
    assert by_node["L10"]["missing_external_topics"] == ()
    assert "needs_application_topic_expansion" not in by_node["L10"]["gap_tags"]
    assert by_node["L12"]["rule_count"] >= 1
    assert by_node["L12"]["answer_guidance_count"] >= 1
    assert by_node["L12"]["counterexample_count"] >= 1
    assert by_node["L12"]["synthetic_case_count"] >= 3
    assert by_node["L12"]["missing_external_topics"] == ()
    assert isinstance(audit["p0_gaps"], list)
    assert isinstance(audit["next_actions"], list)


def test_v20_knowledge_completeness_audit_endpoints_are_declared() -> None:
    server_text = read_v20_text("server.py")

    assert "/api/v20/knowledge/completeness-audit" in server_text
    assert "/api/v20/admin/knowledge-completeness-audit" in server_text
    assert "build_knowledge_completeness_audit" in server_text
