from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from v17_rebirth.backend.api import v18_1_predictive as predictive_api
from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def p1_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload(version: str = "v1", effect: float = 0.6):
    return {
        "rule_id": "agent.wealth.rule",
        "theory_family": "agent_wealth",
        "condition": {"wealth_visible": True},
        "effect": {"wealth": effect},
        "priority": 0.8,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": version,
        "owner_plugin": "plugin.agent",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }


def _activate_rule(service: engine.V18PredictiveStore):
    service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=1)
    service.update_rule_status("agent.wealth.rule", "validated", actor_role="manager", actor_user_id=1, version="v1")
    service.activate_rule(rule_id="agent.wealth.rule", target_version="v1", actor_role="manager", actor_user_id=1)
    return service.get_rule("agent.wealth.rule")


def _run_pipeline(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade):
    rule = _activate_rule(service)
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-p1-full",
            "user_query": "今年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "system",
        0,
    )


def _run_sensitive_pipeline(service: engine.V18PredictiveStore, facade: engine.RuleRuntimeFacade):
    rule = _activate_rule(service)
    return facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-public-redaction",
            "user_query": "我是张三，1990-01-01 09:00 出生，住在首尔江南区，未来财运如何？",
            "topic": "wealth",
            "debug": {"admin_note": "internal-only"},
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {
                "matched_facts": ["wealth_visible"],
                "birth_time": "1990-01-01T09:00:00",
                "birth_fields": {"year": "1990", "month": "01", "day": "01", "hour": "09"},
                "four_pillars": {"year": "甲子", "month": "丁丑", "day": "庚寅", "hour": "辛巳"},
                "private_note": "Seoul Gangnam private chart detail",
            },
        },
        "system",
        0,
    )


def _wealth_feature_chart():
    return {
        "matched_facts": ["wealth_visible", "格局候选：食伤生财，输出换财通道显性。", "墓库门态：辰为库，资金结构等待引动。", "合冲刑害带来稳定性波动。"],
        "day_master_stem": "乙",
        "four_pillars": {
            "year": "丁巳",
            "month": "乙巳",
            "day": "乙丑",
            "hour": "乙酉",
        },
        "luck_pillar": "庚子",
        "flow_pillar": "丙午",
        "flow_year": 2026,
        "ten_gods_runtime": {
            "食神": 36.0,
            "伤官": 22.0,
            "正财": 30.0,
            "偏财": 20.0,
            "正官": 16.0,
            "七杀": 8.0,
            "正印": 10.0,
            "偏印": 6.0,
            "比肩": 10.0,
            "劫财": 8.0,
        },
        "facts": [
            {"fact": "格局候选：食伤生财，输出换财通道显性。", "plugin": "classical.pattern.shishen_shengcai.v1"},
            {"fact": "墓库门态：辰为库，资金结构等待引动。", "plugin": "l1.physics.op_branch_muku"},
            {"fact": "合冲刑害带来财富稳定性波动。", "plugin": "l1.physics.relation"},
        ],
        "meta": {
            "god_ring_authority": {
                "use_gods": ["食神", "伤官", "正财"],
                "taboo_gods": ["七杀"],
                "tongguan_gods": ["正官"],
                "confidence": 0.82,
            }
        },
    }


def test_ledger_contract_hash_is_server_owned_stable_and_sensitive(p1_runtime) -> None:
    service, facade = p1_runtime
    result = _run_pipeline(service, facade)
    ledger = service.get_ledger("pred-p1-full")

    assert ledger["ledger_id"] == "led_pred-p1-full"
    assert ledger["contract_hash"].startswith("sha256:")
    assert ledger["user_query"] == "今年财运如何？"
    assert ledger["conclusion_refs"]
    assert ledger["evidence_refs"]
    assert ledger["chart_snapshot_hash"].startswith("sha256:")

    contract = dict(result["contract"])
    stable_hash = engine._contract_hash(contract)
    assert stable_hash == ledger["contract_hash"]
    tampered = dict(contract)
    tampered["user_query"] = "tampered"
    assert engine._contract_hash(tampered) != stable_hash
    tampered["contract_hash"] = "external-forgery"
    assert engine._contract_hash(contract) == stable_hash


def test_feedback_binds_prediction_preserves_contract_and_generates_learning_signal(p1_runtime) -> None:
    service, facade = p1_runtime
    _run_pipeline(service, facade)
    before_contract_hash = service.get_ledger("pred-p1-full")["contract_hash"]
    active_rule_hash = service.get_rule("agent.wealth.rule").content_hash
    conclusion_ref = service.get_ledger("pred-p1-full")["conclusion_refs"][0]

    with pytest.raises(engine.PredictiveServiceError) as missing:
        service.append_prediction_feedback("missing-prediction", {"feedback_type": "miss"})
    assert missing.value.code == "LEDGER_NOT_FOUND"

    result = service.append_prediction_feedback(
        "pred-p1-full",
        {
            "conclusion_ref": conclusion_ref,
            "feedback_type": "miss",
            "user_comment": "没有发生",
            "observed_event": {"revenue": "flat"},
        },
    )
    assert result["feedback"]["feedback_type"] == "miss"
    assert result["learning_signal"]["suggested_action"] in {"review_rule", "create_candidate"}
    assert service.get_ledger("pred-p1-full")["contract_hash"] == before_contract_hash
    assert service.get_rule("agent.wealth.rule").content_hash == active_rule_hash
    assert service.query_feedback(prediction_id="pred-p1-full")["total_matched"] == 1
    assert service.query_learning_signals(prediction_id="pred-p1-full")


def test_agent_session_clarifies_missing_info_and_uses_contract_when_complete(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    session = facade.create_agent_session({"agent_session_id": "agent-p1"}, "user", 42)
    assert session["agent_session_id"] == "agent-p1"

    clarification = facade.append_agent_turn(
        "agent-p1",
        {"user_message": "今年财运如何？", "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}]},
        "user",
        42,
    )
    assert clarification["safe_output"]["type"] == "clarification_question"
    assert clarification["safe_output"]["is_prediction"] is False
    assert not clarification["prediction_id"]

    predicted = facade.append_agent_turn(
        "agent-p1",
        {
            "user_message": "今年财运如何？",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "user",
        42,
    )
    assert predicted["prediction_id"]
    assert predicted["contract_id"]
    assert predicted["minimal_trace"]["conclusion_count"] >= 1
    assert "conclusion_ids" in predicted["safe_output"]
    stored = facade.get_agent_session("agent-p1")
    assert len(stored["agent_turns"]) == 2


def test_wealth_features_enter_contract_and_compose_multiple_evidence(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    result = facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-wealth-features",
            "user_query": "我未来两年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "wealth-feature-test"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": _wealth_feature_chart(),
        },
        "system",
        0,
    )
    contract = result["contract"]
    evidence = contract["rule_evidence"]
    conclusions = contract["conclusions"]

    assert len(evidence) >= 3
    assert all(row["feature_id"] for row in evidence)
    assert {row["feature_type"] for row in evidence} & {"wealth_strength", "wealth_vault", "output_generate_wealth", "constraint_structure", "flow_activation", "stability_risk"}
    assert conclusions
    assert all(row["evidence_ids"] for row in conclusions)
    assert len(conclusions[0]["evidence_ids"]) >= 2
    assert all(ref in {row["evidence_id"] for row in evidence} for conclusion in conclusions for ref in conclusion["evidence_ids"])
    assert 0.0 < contract["confidence"] <= 1.0
    assert "wealth_feature_engine_v1" in contract["data_sources"]
    assert result["minimal_trace"]["evidence_count"] == len(evidence)


def test_no_wealth_feature_does_not_generate_wealth_conclusion(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    result = facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-no-wealth-feature",
            "user_query": "我未来两年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "wealth-feature-test"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["neutral_fact"], "four_pillars": {}},
        },
        "system",
        0,
    )
    contract = result["contract"]

    assert contract["chain_state"] == "insufficient_evidence"
    assert contract["conclusions"] == []
    assert result["safe_output"]["text"] == "证据不足，不足以判断。"


def test_relation_volatility_only_affects_risk_without_standalone_wealth_conclusion(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    result = facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-relation-only",
            "user_query": "我未来两年财运如何？",
            "topic": "wealth",
            "debug": True,
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "wealth-feature-test"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": {"matched_facts": ["合冲刑害明显"], "facts": [{"fact": "合冲刑害明显，稳定性波动。"}]},
        },
        "system",
        0,
    )
    contract = result["contract"]
    evidence = contract["rule_evidence"]

    assert evidence
    assert all(row["feature_type"] == "stability_risk" for row in evidence)
    assert contract["conclusions"] == []
    assert contract["uncertainty"]["score"] >= 0.9


def test_explanation_adapter_cannot_reference_missing_evidence(p1_runtime) -> None:
    service, facade = p1_runtime
    rule = _activate_rule(service)
    facade.run_prediction_contract_pipeline(
        {
            "prediction_id": "pred-explain-scope",
            "user_query": "我未来两年财运如何？",
            "topic": "wealth",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "wealth-feature-test"}],
            "rule_candidates": [{"rule_id": rule.rule_id, "version": rule.version, "activation_score": 1.0}],
            "chart_snapshot": _wealth_feature_chart(),
        },
        "system",
        0,
    )

    with pytest.raises(engine.PredictiveServiceError) as exc:
        service.explain_prediction(
            "pred-explain-scope",
            {
                "contract_id": "contract_pred-explain-scope",
                "candidate_output": {
                    "text": "引用不存在证据的解释。",
                    "is_prediction": True,
                    "sections": {
                        "conclusion": ["bad"],
                        "conclusion_ids": ["conclusion_1", "invented_conclusion"],
                        "evidence": ["missing_evidence"],
                        "causal": [],
                        "risk": [],
                    },
                    "max_confidence": 0.5,
                },
            },
        )
    assert exc.value.code == "EXPLANATION_VERIFIER_FAILED"


def test_agent_capability_boundary_guides_unsupported_scope_without_prediction(p1_runtime) -> None:
    service, facade = p1_runtime
    session = facade.create_agent_session({"agent_session_id": "agent-boundary"}, "user", 42)
    assert session["agent_session_id"] == "agent-boundary"

    turn = facade.append_agent_turn(
        "agent-boundary",
        {
            "user_message": "我想看感情婚姻和健康怎么样",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "birth_payload": {"year": "1990", "month": "01", "day": "01", "hour": "09", "gender": "male"},
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "user",
        42,
    )

    safe_output = turn["safe_output"]
    assert turn["capability_boundary"] is True
    assert safe_output["type"] == "capability_boundary"
    assert safe_output["is_prediction"] is False
    assert safe_output["capability_boundary"] is True
    assert not turn["prediction_id"]
    assert not turn["contract_id"]
    assert safe_output["supported_scopes"] == ["财运趋势", "收入稳定性", "财富机会与风险"]
    assert "感情 / 婚姻" in safe_output["unsupported_scopes"]
    assert safe_output["suggested_queries"]

    with pytest.raises(engine.PredictiveServiceError) as exc:
        service.get_ledger("agent-boundary_turn_1")
    assert exc.value.code == "LEDGER_NOT_FOUND"


def test_agent_capability_boundary_blocks_wealth_when_no_active_rule(p1_runtime) -> None:
    service, facade = p1_runtime
    session = facade.create_agent_session({"agent_session_id": "agent-no-rule"}, "user", 42)
    assert session["agent_session_id"] == "agent-no-rule"

    turn = facade.append_agent_turn(
        "agent-no-rule",
        {
            "user_message": "我未来两年财运如何？",
            "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
            "birth_payload": {"year": "1990", "month": "01", "day": "01", "hour": "09", "gender": "male"},
            "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
        },
        "user",
        42,
    )

    safe_output = turn["safe_output"]
    assert turn["capability_boundary"] is True
    assert safe_output["type"] == "capability_boundary"
    assert safe_output["is_prediction"] is False
    assert safe_output["active_rule_required"] is True
    assert not turn["prediction_id"]
    assert not turn["contract_id"]

    with pytest.raises(engine.PredictiveServiceError) as exc:
        service.get_ledger("agent-no-rule_turn_1")
    assert exc.value.code == "LEDGER_NOT_FOUND"


def test_api_rate_limit_and_dedupe_use_fallback_when_redis_unavailable(monkeypatch: pytest.MonkeyPatch) -> None:
    request = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"), headers={"user-agent": "pytest"})
    predictive_api._RATE_LIMIT_FALLBACK.clear()
    predictive_api._DEDUP_FALLBACK.clear()
    monkeypatch.setattr(predictive_api, "_redis_get_json", lambda key: None)
    monkeypatch.setattr(predictive_api, "_redis_set_json", lambda key, value, ttl_seconds: False)

    predictive_api._rate_limit(request, "unit", limit=1, window_seconds=60, key_extra="demo")
    with pytest.raises(engine.PredictiveServiceError) as limited:
        predictive_api._rate_limit(request, "unit", limit=1, window_seconds=60, key_extra="demo")
    assert limited.value.code == "RATE_LIMITED"

    predictive_api._dedupe_once(request, "feedback", "pred-1:hit:conclusion-1")
    with pytest.raises(engine.PredictiveServiceError) as duplicate:
        predictive_api._dedupe_once(request, "feedback", "pred-1:hit:conclusion-1")
    assert duplicate.value.code == "DUPLICATE_FEEDBACK"


def test_api_fail_response_uses_public_trilingual_message() -> None:
    response = predictive_api._fail(engine.PredictiveServiceError("RULE_SCOPE_VIOLATION", "No rule candidates", 409))
    body = json.loads(response.body.decode("utf-8"))

    assert body["code"] == "RULE_SCOPE_VIOLATION"
    assert body["message"] != "No rule candidates"
    assert "RULE_SCOPE_VIOLATION" not in body["message"]
    assert body["user_message"]["zh"]
    assert body["user_message"]["en"]
    assert body["user_message"]["ko"]


def test_agent_does_not_use_sandbox_candidate_for_formal_prediction(p1_runtime) -> None:
    service, facade = p1_runtime
    sandbox = service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload(version="sandbox-v1")},
        actor_role="practitioner",
        actor_user_id=3,
    )
    session = facade.create_agent_session({"agent_session_id": "agent-sandbox"}, "user", 1)
    assert session["agent_session_id"] == "agent-sandbox"

    with pytest.raises(engine.PredictiveServiceError) as exc:
        facade.append_agent_turn(
            "agent-sandbox",
            {
                "user_message": "今年财运如何？",
                "plugin_claims": [{"plugin_id": "plugin.agent", "claim_id": "c1"}],
                "rule_candidates": [
                    {
                        "rule_id": sandbox["rule_payload"]["rule_id"],
                        "version": sandbox["rule_payload"]["version"],
                        "activation_score": 1.0,
                        "rule_payload": sandbox["rule_payload"],
                    }
                ],
                "chart_snapshot": {"matched_facts": ["wealth_visible"], "four_pillars": {"year": "甲子"}},
                "allow_sandbox": True,
            },
            "user",
            1,
        )
    assert exc.value.code == "RULE_SCOPE_VIOLATION"


def test_replay_returns_contract_feedback_signals_and_rule_drift(p1_runtime) -> None:
    service, facade = p1_runtime
    _run_pipeline(service, facade)
    conclusion_ref = service.get_ledger("pred-p1-full")["conclusion_refs"][0]
    service.append_prediction_feedback("pred-p1-full", {"conclusion_ref": conclusion_ref, "feedback_type": "hit"})

    replay = service.replay_prediction("pred-p1-full")
    assert replay["ledger"]["prediction_id"] == "pred-p1-full"
    assert replay["contract"]["prediction_id"] == "pred-p1-full"
    assert replay["evidence"]
    assert replay["feedback"]
    assert replay["learning_signals"]
    assert replay["rule_drift"] is False

    rule = service.get_rule("agent.wealth.rule", version="v1")
    rule.content_hash = "sha256:changed"
    service._rule_kernels[service._normalize_rule_key(rule.rule_id, rule.version)] = rule
    drifted = service.replay_prediction("pred-p1-full")
    assert drifted["rule_drift"] is True


def test_public_replay_redacts_private_birth_query_hashes_and_debug(p1_runtime) -> None:
    service, facade = p1_runtime
    _run_sensitive_pipeline(service, facade)
    conclusion_ref = service.get_ledger("pred-public-redaction")["conclusion_refs"][0]
    service.append_prediction_feedback("pred-public-redaction", {"conclusion_ref": conclusion_ref, "feedback_type": "hit"})

    private = service.replay_prediction("pred-public-redaction")
    public = service.public_replay_prediction("pred-public-redaction")
    public_text = str(public)

    assert public["public_safe"] is True
    assert public["prediction_id_short"] == "pred-public-redact"
    assert public["conclusion_summary"]
    assert isinstance(public["confidence"], float)
    assert public["verifier_status"]
    assert public["evidence_summary"]
    assert public["feedback_count"] == 1
    assert public["learning_signal_count"] == 1
    assert public["rule_drift"] is False
    assert public["redaction"]["notice"] == "此回放已隐藏个人信息"
    assert public["redaction"]["full_record_notice"] == "完整记录仅本人登录后可见"

    assert "1990-01-01" not in public_text
    assert "09:00" not in public_text
    assert "张三" not in public_text
    assert "首尔江南区" not in public_text
    assert "Seoul Gangnam" not in public_text
    assert "birth_fields" not in public_text
    assert "four_pillars" not in public_text
    assert "chart_snapshot" not in public_text
    assert private["ledger"]["contract_hash"] not in public_text
    if private["contract"].get("contract_hash"):
        assert private["contract"]["contract_hash"] not in public_text
    assert private["evidence"][0]["content_hash"] not in public_text
    assert "sha256:" not in public_text
    assert "internal-only" not in public_text
    assert "admin_note" not in public_text
