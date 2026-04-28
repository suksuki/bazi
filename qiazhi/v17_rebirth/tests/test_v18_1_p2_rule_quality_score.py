from __future__ import annotations

from pathlib import Path

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


def _rule_payload(rule_id: str, owner_plugin: str, effect: float = 0.7):
    return {
        "rule_id": rule_id,
        "theory_family": "quality_family",
        "condition": {"quality_visible": True, "rule": rule_id},
        "effect": {"wealth": effect},
        "priority": 0.86,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": owner_plugin,
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _runtime(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _activate(service: engine.V18PredictiveStore, rule_id: str, owner_plugin: str, effect: float = 0.7):
    service.register_rule(_rule_payload(rule_id, owner_plugin, effect), actor_role="manager", actor_user_id=1)
    service.update_rule_status(rule_id, "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id=rule_id, target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule(rule_id)


def _prediction(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade, rule, prediction_id: str):
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": prediction_id,
            "user_query": "质量评分样例",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": rule.owner_plugin, "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["quality_visible"], "four_pillars": {"year": "甲子"}},
        },
        "system",
        0,
    )


def _feedback(service: engine.V18PredictiveStore, prediction_id: str, feedback_type: str):
    conclusion_ref = service.get_ledger(prediction_id)["conclusion_refs"][0]
    return service.append_prediction_feedback(
        prediction_id,
        {"conclusion_ref": conclusion_ref, "feedback_type": feedback_type, "observed_event": {"type": feedback_type}},
    )


def _score(service: engine.V18PredictiveStore, rule_id: str):
    return service.get_rule_quality_score(rule_id, version="v1")


def test_hit_heavy_rule_quality_score_is_higher_than_miss_heavy_rule(tmp_path: Path, monkeypatch) -> None:
    service, facade = _runtime(tmp_path, monkeypatch)
    hit_rule = _activate(service, "quality.hit.rule", "plugin.quality.hit")
    miss_rule = _activate(service, "quality.miss.rule", "plugin.quality.miss")
    for idx in range(3):
        _prediction(service, facade, hit_rule, f"pred-hit-{idx}")
        _feedback(service, f"pred-hit-{idx}", "hit")
        _prediction(service, facade, miss_rule, f"pred-miss-{idx}")
        _feedback(service, f"pred-miss-{idx}", "miss")

    hit_score = _score(service, "quality.hit.rule")
    miss_score = _score(service, "quality.miss.rule")

    assert hit_score["quality_score"] > miss_score["quality_score"]
    assert hit_score["recommended_action"] == "keep"


def test_miss_heavy_rule_has_higher_risk_score(tmp_path: Path, monkeypatch) -> None:
    service, facade = _runtime(tmp_path, monkeypatch)
    rule = _activate(service, "quality.risk.rule", "plugin.quality.risk")
    for idx in range(3):
        _prediction(service, facade, rule, f"pred-risk-{idx}")
        _feedback(service, f"pred-risk-{idx}", "miss")

    score = _score(service, "quality.risk.rule")

    assert score["risk_score"] >= 0.5
    assert score["confidence_calibration"] == "overconfident"
    assert score["recommended_action"] in {"review", "reduce_confidence"}


def test_verifier_failure_strongly_lowers_quality_score(tmp_path: Path, monkeypatch) -> None:
    service, facade = _runtime(tmp_path, monkeypatch)
    rule = _activate(service, "quality.verifier.rule", "plugin.quality.verifier")
    result = _prediction(service, facade, rule, "pred-verifier-fail")
    service.run_verifier(
        {
            "prediction_id": "pred-verifier-fail",
            "contract": result["contract"],
            "llm_output": {
                "text": "新增越界判断",
                "sections": {
                    "conclusion": ["新增越界判断"],
                    "conclusion_ids": ["outside_contract"],
                    "evidence": result["contract"]["evidence_ids"],
                    "causal": result["contract"]["causal_path"],
                    "risk": result["contract"]["risk_modes"],
                    "suggestion": [],
                },
                "sources": result["contract"]["data_sources"],
            },
        }
    )

    score = _score(service, "quality.verifier.rule")

    assert score["verifier_failure_count"] == 1
    assert score["quality_score"] < 0.3
    assert score["recommended_action"] == "review"


def test_low_sample_marks_insufficient_data_and_does_not_modify_active_rule(tmp_path: Path, monkeypatch) -> None:
    service, facade = _runtime(tmp_path, monkeypatch)
    rule = _activate(service, "quality.low.sample.rule", "plugin.quality.low")
    before_hash = rule.content_hash
    _prediction(service, facade, rule, "pred-low-sample")
    _feedback(service, "pred-low-sample", "hit")

    score = _score(service, "quality.low.sample.rule")

    assert score["sample_count"] == 1
    assert score["confidence_calibration"] == "insufficient_data"
    assert service.get_rule("quality.low.sample.rule").content_hash == before_hash
    assert service.get_rule("quality.low.sample.rule").status == "active"


def test_pr_queue_returns_review_priority_from_quality_score(tmp_path: Path, monkeypatch) -> None:
    service, facade = _runtime(tmp_path, monkeypatch)
    high_risk_candidate = service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload("quality.candidate.risky", "plugin.quality.candidate")},
        actor_role="practitioner",
        actor_user_id=3,
    )
    low_risk_candidate = service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload("quality.candidate.ready", "plugin.quality.ready")},
        actor_role="practitioner",
        actor_user_id=3,
    )
    fail_case = service.register_rule_test_case(
        {
            "case_id": "quality.fail.case",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["quality_visible"]},
            "query_intent": {"topic": "wealth"},
            "expected_evidence_patterns": ["quality_visible"],
            "forbidden_conclusions": ["wealth"],
        },
        actor_role="manager",
        actor_user_id=7,
    )
    pass_case = service.register_rule_test_case(
        {
            "case_id": "quality.pass.case",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["quality_visible"]},
            "query_intent": {"topic": "wealth"},
            "expected_evidence_patterns": ["quality_visible", "wealth"],
            "expected_conclusions": ["wealth"],
        },
        actor_role="manager",
        actor_user_id=7,
    )
    facade.run_rule_test_v02({"rule_candidate_id": high_risk_candidate["candidate_id"], "test_case_ids": [fail_case["case_id"]]}, "manager", 7)
    facade.run_rule_test_v02({"rule_candidate_id": low_risk_candidate["candidate_id"], "test_case_ids": [pass_case["case_id"]]}, "manager", 7)
    service.append_knowledge_pr({"prediction_id": "pred-pr-risk", "rule_candidate_id": high_risk_candidate["candidate_id"], "target_status": "validated"})
    service.append_knowledge_pr({"prediction_id": "pred-pr-ready", "rule_candidate_id": low_risk_candidate["candidate_id"], "target_status": "validated"})

    queue = service.query_knowledge_pr_queue()

    assert queue["items"][0]["rule_id"] == "quality.candidate.risky"
    assert queue["items"][0]["review_priority"] == "high"
    assert "quality_score" in queue["items"][0]
    assert "risk_score" in queue["items"][0]
    assert queue["items"][1]["review_priority"] in {"medium", "low"}
