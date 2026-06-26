from __future__ import annotations

from v20.decision.knowledge_bridge import attach_knowledge_rule_bridge


def test_v20_knowledge_bridge_consumes_active_knowledge_policy_pointer(monkeypatch) -> None:
    monkeypatch.setattr(
        "v20.decision.knowledge_bridge.build_knowledge_rule_library",
        lambda: {
            "version": "test.knowledge_rule_library",
            "definition_count": 2,
            "definitions": (
                {
                    "rule_key": "rule.strength.capacity",
                    "title": "日主承载边界",
                    "domain": "strength",
                    "source_knowledge_id": "v20.core.strength_boundary",
                    "source_authority": "test",
                    "condition_atoms": (),
                    "portrait_outputs": (),
                    "question_outputs": (
                        {
                            "question_key": "q_strength_assessment",
                            "title": "日主承载如何判断？",
                            "domain": "strength",
                        },
                    ),
                    "answer_guidance": ({"guidance_key": "strength.boundary"},),
                    "boundary": "只说明强弱承载边界",
                    "validation_state": "active_ready",
                    "activation_status": "active_ready",
                },
                {
                    "rule_key": "rule.strength.capacity",
                    "title": "日主月令根气",
                    "domain": "strength",
                    "source_knowledge_id": "v20.core.strength_root_month_command",
                    "source_authority": "test",
                    "condition_atoms": (),
                    "portrait_outputs": (),
                    "question_outputs": (),
                    "answer_guidance": (),
                    "boundary": "只说明月令根气",
                    "validation_state": "active_ready",
                    "activation_status": "active_ready",
                },
            ),
        },
    )
    pointer = {
        "version": "v20.knowledge_runtime_pointer.v1",
        "status": "candidate_active",
        "active_policy_version": "v20.knowledge_policy.candidate.test",
        "candidate_policy_version": "v20.knowledge_policy.candidate.test",
        "runtime_applied": True,
        "runtime_allowed": True,
        "policy_payload": {
            "knowledge_rule_mapping_policy": (
                {
                    "rule_key": "rule.strength.capacity",
                    "source_knowledge_id": "v20.core.strength_boundary",
                    "domain": "strength",
                    "mapping_weight_delta": 0.05,
                    "answer_guidance_delta": 0.012,
                    "source_trust_delta": 0.02,
                    "source": "test",
                },
            )
        },
        "blocking_gate": "",
        "runtime_mutation": False,
    }
    decision_report = {
        "version": "test.decision_report",
        "decisions": (
            {
                "decision_key": "decision.strength.capacity",
                "rule_key": "rule.strength.capacity",
                "domain": "strength",
                "question_seeds": ("日主承载如何判断？",),
            },
        ),
    }

    enriched = attach_knowledge_rule_bridge(decision_report, runtime_policy_pointer=pointer)
    ref = enriched["decisions"][0]["knowledge_rule_refs"][0]
    effect = enriched["knowledge_rule_bridge"]["policy_effect"]["knowledge_policy"]

    assert ref["source_knowledge_id"] == "v20.core.strength_boundary"
    assert ref["policy_applied"] is True
    assert ref["policy_mapping_weight_delta"] == 0.05
    assert ref["policy_answer_guidance_delta"] == 0.012
    assert ref["policy_source_trust_delta"] == 0.02
    assert effect["status"] == "applied"
    assert effect["active_policy_version"] == "v20.knowledge_policy.candidate.test"
    assert effect["policy_count"] == 1
    assert effect["applied_ref_count"] == 1
    assert "KNOWLEDGE_BRIDGE_CONSUMES_ACTIVE_KNOWLEDGE_POINTER" in enriched["knowledge_rule_bridge"]["guardrails"]
