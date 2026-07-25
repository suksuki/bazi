from __future__ import annotations

from product.reading_projection import project_living_reading


def _payload() -> dict:
    return {
        "version": "deepbazi.living_reading.v1",
        "experience_mode": "research",
        "pillars": ["甲子", "乙丑", "丙寅", "丁卯"],
        "first_look": "第一眼",
        "whole_chart_thesis": "整盘主线",
        "lenses_available": {"bazi": True, "ziwei": True, "integrated": True},
        "confidence": "medium",
        "salient_phenomena": [{"observation": "重心", "evidence_refs": ["F1"]}],
        "hypotheses": [{"hypothesis_id": "h1", "name": "主假设", "thesis": "解释"}],
        "selected_hypothesis_id": "h1",
        "system_selected_hypothesis_id": "h1",
        "work_path": {"path_statement": "路径", "evidence_refs": ["F1"]},
        "useful_god_reasoning": [{"candidate": "火", "evidence_refs": ["F1"]}],
        "portrait": [{"assertion_id": "a1", "domain": "portrait", "claim": "画像", "rationale": "内部理由", "epistemic_status": "supported", "conditions": ["条件"], "falsifiers": ["反证"], "evidence_refs": ["F1"]}],
        "prior_predictions": [{"prediction_id": "p1", "claim": "预测", "why_predicted": "理由", "disconfirming_answer": "反证", "evidence_refs": ["F1"]}],
        "probe_plan": {"question": "问题"},
        "latest_revision": {"revision_id": "r1", "summary": "判断已更新", "affected_hidden_attributes": ["timing_response_pattern"], "chart_facts_modified": False},
        "dual_lens": {"identity_axis": "舞台", "palace_observations": [{"observation_id": "z1", "domain": "identity", "claim": "宫位", "why_it_matters": "意义", "evidence_refs": ["Z1"]}]},
        "ziwei_profile": {"status": "ready", "reasoning_ready": True, "life_palace": "命宫", "palaces": {"命宫": {"stars": ["紫微"]}}, "horoscope": {"raw": True}},
        "life_domains": [],
        "domain_explorations": {},
        "temporal_state": {"analysis_year": 2026, "annual_pillar": "丙午", "luck_pillar": "己丑"},
        "life_case": {"life_case_id": "life-case-1", "baseline": {"claim": "整盘基线", "uncertainty": {"reasons": ["待确认"]}}},
        "workspace": {"active_hypothesis_id": "h1", "hypothesis_beliefs": [{"hypothesis_id": "h1"}], "assertion_beliefs": [{"assertion_id": "a1"}], "hidden_attribute_beliefs": [{"attribute_id": "timing_response_pattern"}], "probe_response_count": 0, "revision_count": 0, "chart_facts_locked": True, "global_update_allowed": False},
        "review": {"passed": True, "issues": [], "fact_traceability_rate": 1.0},
        "cognitive_run": {"stage_count": 4},
        "unresolved_questions": ["未知"],
        "deliberation": {"stages": []},
        "latest_deliberation_revision": None,
        "revision_count": 0,
    }


def test_guest_projection_does_not_leak_professional_or_runtime_surfaces() -> None:
    projected = project_living_reading(_payload(), mode="guest")
    assert projected["projection_contract"]["name"] == "GuestReadingProjection"
    assert projected["projection_contract"]["new_mingli_claims_created"] is False
    assert "hypotheses" not in projected
    assert "work_path" not in projected
    assert projected["public_work_path"] == {"path_statement": "路径"}
    assert "evidence_refs" not in projected["public_work_path"]
    assert "useful_god_reasoning" not in projected
    assert "review" not in projected
    assert "cognitive_run" not in projected
    assert "palaces" not in projected["ziwei_profile"]
    assert "rationale" not in projected["portrait"][0]
    assert "evidence_refs" not in projected["portrait"][0]
    assert "hypothesis_beliefs" not in projected["workspace"]
    assert "hidden_attribute_beliefs" not in projected["workspace"]
    assert "affected_hidden_attributes" not in projected["latest_revision"]
    assert projected["life_case"]["baseline"]["claim"] == "整盘基线"
    assert projected["temporal_state"]["annual_pillar"] == "丙午"
    assert projected["public_evidence"]["observations"] == [{"observation": "重心"}]
    assert projected["public_evidence"]["primary_explanation"]["thesis"] == "解释"
    assert "evidence_refs" not in str(projected["public_evidence"])


def test_member_projection_keeps_conditions_without_internal_evidence() -> None:
    projected = project_living_reading(_payload(), mode="member")
    assert projected["projection_contract"]["name"] == "MemberReadingProjection"
    assert projected["portrait"][0]["conditions"] == ["条件"]
    assert projected["prior_predictions"][0]["why_predicted"] == "理由"
    assert "evidence_refs" not in projected["prior_predictions"][0]
    assert projected["public_evidence"]["uncertainties"] == ["未知"]


def test_practitioner_projection_keeps_cognition_but_not_research_runtime() -> None:
    projected = project_living_reading(_payload(), mode="practitioner")
    assert projected["projection_contract"]["name"] == "PractitionerCognitiveProjection"
    assert projected["hypotheses"][0]["hypothesis_id"] == "h1"
    assert projected["work_path"]["path_statement"] == "路径"
    assert "review" not in projected
    assert "cognitive_run" not in projected
    assert "horoscope" not in projected["ziwei_profile"]


def test_research_projection_keeps_full_audit_payload() -> None:
    projected = project_living_reading(_payload(), mode="research")
    assert projected["projection_contract"]["name"] == "ResearchAuditProjection"
    assert projected["review"]["fact_traceability_rate"] == 1.0
    assert projected["cognitive_run"]["stage_count"] == 4
    assert projected["ziwei_profile"]["palaces"]
