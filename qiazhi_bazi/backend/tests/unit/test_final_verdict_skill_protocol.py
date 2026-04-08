from __future__ import annotations

from app.skills.final_verdict import FinalVerdictSkill


def test_final_verdict_skill_protocol_adapter():
    skill = FinalVerdictSkill.instance()
    consumed = skill.consume(
        {
            "metadata": {"pillars": {}},
            "physics_tensor": {"audit_log": {"param_version_id": "p-1"}},
            "selected_cards": [{"id": "c1"}],
            "consensus_history": [{"decision_key": "k1", "confirmed_value": 1.0}],
            "previous_verdict": "prev",
            "lang": "ZH",
        }
    )
    produced = skill.produce(consumed)
    audit = skill.audit(consumed, produced)

    assert "logical_evidence" in produced
    assert audit.skill_id == "final_verdict_skill"
    assert audit.rule_version == "final_verdict_rules.v1"
    assert audit.param_version_id == "p-1"
