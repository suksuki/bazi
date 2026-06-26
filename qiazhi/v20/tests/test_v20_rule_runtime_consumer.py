from __future__ import annotations

from v20.features.schema import FeatureLayer
from v20.rules.engine import build_rule_runtime_report


def test_v20_rule_runtime_report_consumes_active_rule_policy_pointer() -> None:
    feature_layer = FeatureLayer(
        version="test",
        features=(),
        discovery_trace={
            "evidence_atoms": (
                {
                    "atom_id": "atom.wealth.visible",
                    "domain": "wealth",
                    "evidence_type": "wealth_star",
                    "title": "正财透出",
                    "layer": "core_symbol",
                },
            )
        },
    )
    catalog = {
        "rules": (
            {
                "rule_id": "rule.test.wealth_capacity",
                "title": "财富结构测试规则",
                "directory_node": "L3",
                "domain": "wealth",
                "layer": "core_symbol",
                "runtime_status": "active",
                "decision_state": "candidate",
                "conditions": (
                    {
                        "condition_id": "condition.wealth.visible",
                        "evidence_type": "wealth_star",
                    },
                ),
                "runtime_allowed": True,
            },
        ),
        "guardrails": (),
    }
    pointer = {
        "version": "v20.rule_runtime_pointer.v1",
        "status": "candidate_active",
        "active_policy_version": "v20.rule_policy.candidate.test",
        "candidate_policy_version": "v20.rule_policy.candidate.test",
        "runtime_applied": True,
        "runtime_allowed": True,
        "policy_payload": {
            "rule_weight_policy": (
                {
                    "rule_key": "rule.test.wealth_capacity",
                    "domain": "wealth",
                    "weight_delta": 0.04,
                    "source": "test",
                },
            )
        },
        "blocking_gate": "",
        "runtime_mutation": False,
    }

    report = build_rule_runtime_report(feature_layer, catalog=catalog, runtime_policy_pointer=pointer)
    rule = report["rules"][0]
    effect = report["policy_effect"]["rule_policy"]

    assert rule["base_match_score"] == 1.0
    assert rule["match_score"] == 1.0
    assert rule["policy_weight_delta"] == 0.04
    assert rule["policy_applied"] is True
    assert effect["status"] == "applied"
    assert effect["active_policy_version"] == "v20.rule_policy.candidate.test"
    assert effect["policy_count"] == 1
    assert effect["applied_rule_count"] == 1
    assert report["runtime_policy_effect"] == effect
    assert "RULE_RUNTIME_CONSUMES_ACTIVE_RULE_POINTER" in report["guardrails"]
