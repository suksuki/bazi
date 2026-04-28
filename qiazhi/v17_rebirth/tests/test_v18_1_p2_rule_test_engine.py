from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def p2_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload(**overrides):
    payload = {
        "rule_id": "p2.rule",
        "theory_family": "p2_family",
        "condition": {"wealth_visible": True},
        "effect": {"wealth": 0.72},
        "priority": 0.8,
        "evidence_strength": 0.9,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": "plugin.p2",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
    }
    payload.update(overrides)
    return payload


def _candidate(service: engine.V18PredictiveStore):
    return service.build_sandbox_rule_candidate(
        {"rule_candidate": _rule_payload()},
        actor_role="practitioner",
        actor_user_id=3,
    )


def _passing_case(service: engine.V18PredictiveStore):
    return service.register_rule_test_case(
        {
            "case_id": "p2.synthetic.pass",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["wealth_visible"]},
            "query_intent": {"topic": "wealth"},
            "expected_conclusions": ["wealth"],
            "expected_evidence_patterns": ["wealth_visible", "wealth"],
            "forbidden_conclusions": ["破产"],
            "tags": ["wealth", "synthetic"],
        },
        actor_role="manager",
        actor_user_id=7,
    )


def test_create_synthetic_rule_test_case(p2_runtime) -> None:
    service, _ = p2_runtime
    case = _passing_case(service)

    assert case["case_id"] == "p2.synthetic.pass"
    assert case["source"] == "synthetic"
    listed = service.query_rule_test_cases(source="synthetic", tag="wealth")
    assert listed["total_matched"] == 1


def test_sandbox_candidate_can_run_rule_test_run(p2_runtime) -> None:
    service, facade = p2_runtime
    candidate = _candidate(service)
    case = _passing_case(service)

    run = facade.run_rule_test_v02(
        {
            "rule_candidate_id": candidate["candidate_id"],
            "test_case_ids": [case["case_id"]],
        },
        "manager",
        7,
    )

    assert run["rule_candidate_id"] == candidate["candidate_id"]
    assert run["overall_status"] == "pass"
    assert run["pass_count"] == 1
    assert service.get_rule_test_run(run["run_id"])["run_id"] == run["run_id"]


def test_forbidden_conclusion_causes_rule_test_failure(p2_runtime) -> None:
    service, facade = p2_runtime
    candidate = _candidate(service)
    case = service.register_rule_test_case(
        {
            "case_id": "p2.synthetic.forbidden",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["wealth_visible"]},
            "query_intent": {"topic": "wealth"},
            "expected_evidence_patterns": ["wealth_visible"],
            "forbidden_conclusions": ["wealth"],
            "tags": ["wealth"],
        },
        actor_role="manager",
        actor_user_id=7,
    )

    run = facade.run_rule_test_v02(
        {"rule_candidate_id": candidate["candidate_id"], "test_case_ids": [case["case_id"]]},
        "manager",
        7,
    )

    assert run["overall_status"] == "fail"
    assert run["fail_count"] == 1
    assert "FORBIDDEN_CONCLUSION_PRODUCED" in run["results"][0]["failures"][0]


def test_contract_verifier_failure_causes_rule_test_failure(p2_runtime) -> None:
    service, facade = p2_runtime
    candidate = _candidate(service)
    case = service.register_rule_test_case(
        {
            "case_id": "p2.synthetic.verifier",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["wealth_visible"]},
            "query_intent": {"topic": "wealth"},
            "expected_evidence_patterns": ["wealth_visible"],
            "force_verifier_failure": True,
        },
        actor_role="manager",
        actor_user_id=7,
    )

    run = facade.run_rule_test_v02(
        {"rule_candidate_id": candidate["candidate_id"], "test_case_ids": [case["case_id"]]},
        "manager",
        7,
    )

    assert run["overall_status"] == "fail"
    assert any("CONTRACT_VERIFIER_FAILED" in item for item in run["results"][0]["failures"])


def test_knowledge_pr_requires_passing_rule_test_before_approve(p2_runtime) -> None:
    service, facade = p2_runtime
    card = service.register_knowledge_card(
        {
            "card_id": "kc.p2",
            "knowledge_domain": "wealth",
            "title": "P2 Rule",
            "summary": "Candidate rules must pass the rule test engine before review approval.",
            "status": "draft",
            "version": "v1",
            "source_refs": ["internal:p2"],
            "tags": ["wealth"],
            "content": {"principle": "test_gate"},
        },
        actor_role="manager",
        actor_user_id=7,
    )
    assert card["card_id"] == "kc.p2"
    candidate = service.build_sandbox_rule_candidate(
        {
            "knowledge_card_id": "kc.p2",
            "rule_candidate": _rule_payload(rule_id="p2.gated.rule", knowledge_card_id="kc.p2"),
        },
        actor_role="practitioner",
        actor_user_id=3,
    )
    pr = service.append_knowledge_pr(
        {
            "prediction_id": "pred-p2-pr",
            "requested_by": "practitioner",
            "knowledge_card_id": "kc.p2",
            "target_status": "validated",
            "rule_candidate_id": candidate["candidate_id"],
        }
    )

    with pytest.raises(engine.PredictiveServiceError) as blocked:
        service.review_knowledge_pr({"pr_id": pr["pr_id"], "decision": "approve"}, actor_role="manager")
    assert blocked.value.code == "RULE_TEST_REQUIRED"

    case = _passing_case(service)
    run = facade.run_rule_test_v02(
        {"rule_candidate_id": candidate["candidate_id"], "test_case_ids": [case["case_id"]]},
        "manager",
        7,
    )
    assert run["overall_status"] == "pass"

    reviewed = service.review_knowledge_pr({"pr_id": pr["pr_id"], "decision": "approve"}, actor_role="manager")
    assert reviewed["review_state"] == "approved"
    assert reviewed["materialized_rule"]["rule_id"] == "p2.gated.rule"
    assert service.get_rule("p2.gated.rule", version="v1", allow_inactive=True).status == "validated"
