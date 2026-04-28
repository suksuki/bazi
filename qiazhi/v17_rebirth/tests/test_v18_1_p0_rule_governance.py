from __future__ import annotations

from pathlib import Path

import pytest

from v17_rebirth.backend.services import v18_1_predictive_engine as engine


@pytest.fixture()
def p0_runtime(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(engine, "RUNTIME_DIR", tmp_path)
    service = engine.V18PredictiveStore()
    facade = engine.RuleRuntimeFacade(service)
    return service, facade


def _rule_payload(**overrides):
    payload = {
        "rule_id": "p0.rule",
        "theory_family": "p0_family",
        "condition": {"x": 1},
        "effect": {"wealth": 0.5},
        "priority": 0.9,
        "evidence_strength": 0.8,
        "conflict_policy": "merge",
        "version": "v1",
        "owner_plugin": "plugin.alpha",
        "status": "experimental",
        "effect_scope": ["wealth"],
        "allowed_topics": ["wealth"],
        "content_hash": "spoofed",
    }
    payload.update(overrides)
    return payload


def _resolver_payload():
    return {
        "prediction_id": "pred-p0",
        "topic": "wealth",
        "plugin_claims": [{"plugin_id": "plugin.alpha", "claim_id": "c1"}],
        "rule_candidates": [{"rule_id": "p0.rule", "activation_score": 1.0}],
        "runtime_context": {"time_weight": {"natal": 0.5, "decade": 0.3, "year": 0.2}},
    }


def _activate_rule(service: engine.V18PredictiveStore) -> dict:
    created = service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=7)
    service.update_rule_status("p0.rule", "validated", actor_role="manager", actor_user_id=7, version="v1")
    service.activate_rule(rule_id="p0.rule", target_version="v1", actor_role="manager", actor_user_id=7)
    return created


def test_active_rule_is_immutable_and_content_hash_is_server_owned(p0_runtime) -> None:
    service, _ = p0_runtime
    created = _activate_rule(service)

    assert created["content_hash"] != "spoofed"

    with pytest.raises(engine.PredictiveServiceError) as duplicate:
        service.register_rule(_rule_payload(), actor_role="manager", actor_user_id=7)
    assert duplicate.value.code == "RULE_VERSION_CONFLICT"

    with pytest.raises(engine.PredictiveServiceError) as active_update:
        service.update_rule_status("p0.rule", "deprecated", actor_role="manager", actor_user_id=7, version="v1")
    assert active_update.value.code == "RULE_IMMUTABLE"


def test_runtime_facade_is_required_for_resolver_and_tests(p0_runtime) -> None:
    service, facade = p0_runtime
    _activate_rule(service)
    direct_token = service.issue_lifecycle_token(actor_role="system", purpose="runtime")

    with pytest.raises(engine.PredictiveServiceError) as direct_resolve:
        service.resolve_rules(
            {
                **_resolver_payload(),
                "lifecycle_token": direct_token,
                "execution_mode": "runtime",
            }
        )
    assert direct_resolve.value.code == engine.LIFECYCLE_BYPASS_CODE

    resolved = facade.run_resolver(_resolver_payload(), "system", 0)
    assert resolved["status"] == "resolved"
    assert resolved["resolver_snapshot"]["resolver_lifecycle"]["gatekeeper_protocol"] == engine.RULE_GATEKEEPER_PROTOCOL
    assert resolved["resolver_snapshot"]["resolver_lifecycle"]["execution_mode"] == "runtime"

    sandbox_override = {
        **_resolver_payload(),
        "prediction_id": "pred-p0-override",
        "execution_mode": "debug",
        "allow_sandbox": True,
        "rule_candidates": [
            {
                "rule_id": "non.persisted",
                "activation_score": 1.0,
                "rule_payload": _rule_payload(rule_id="non.persisted", version="v1"),
            }
        ],
    }
    with pytest.raises(engine.PredictiveServiceError) as override_attempt:
        facade.run_resolver(sandbox_override, "system", 0)
    assert override_attempt.value.code == "RULE_SCOPE_VIOLATION"

    with pytest.raises(engine.PredictiveServiceError) as direct_test:
        service.run_rule_test_v0(
            {
                "rule_id": "p0.rule",
                "test_cases": [{"case_id": "1", "expected_active": True, "observed_active": True}],
                "lifecycle_token": direct_token,
            }
        )
    assert direct_test.value.code == engine.LIFECYCLE_BYPASS_CODE

    test_run = facade.run_rule_test(
        {
            "rule_id": "p0.rule",
            "version": "v1",
            "test_cases": [
                {"case_id": str(i), "expected_active": True, "observed_active": True}
                for i in range(5)
            ],
        },
        "manager",
        7,
    )
    assert test_run["execution_mode"] == "test"
    assert test_run["quality_gate"] == "pass"


def test_gatekeeper_fail_close_and_ledger_requires_resolver_lifecycle(p0_runtime) -> None:
    service, facade = p0_runtime
    _activate_rule(service)

    with pytest.raises(engine.PredictiveServiceError) as wrong_claim:
        facade.run_resolver(
            {
                **_resolver_payload(),
                "plugin_claims": [{"plugin_id": "plugin.beta", "claim_id": "c2"}],
            },
            "system",
            0,
        )
    assert wrong_claim.value.code == "GATEKEEPER_DENIED"

    resolved = facade.run_resolver(_resolver_payload(), "system", 0)
    contract_payload = {
        "prediction_id": "pred-p0",
        "topic": "wealth",
        "chain_id": "chain-p0",
        "causal_path": ["a"],
        "rule_ids": resolved["active_rules"],
        "chain_state": "partial",
        "confidence": 0.7,
        "period": {"start_at": "2026-01-01", "end_at": "2026-12-31"},
        "evidence_ids": ["ev1"],
        "verifiable_indicators": {"outcome": ["x"]},
        "risk_modes": ["r1"],
        "data_sources": ["ds1"],
        "model_version": "v18.1",
        "schema_version": "v18.1",
        "display_policy": {},
        "resolver_snapshot": resolved["resolver_snapshot"],
    }
    contract = service.build_contract(contract_payload, resolved_rules=resolved)
    record = service.write_ledger_record({"prediction_id": "pred-p0"}, contract.to_dict())
    assert record.prediction_hash.startswith("sha256:")

    with pytest.raises(engine.PredictiveServiceError) as ledger_bypass:
        service.write_ledger_record(
            {"prediction_id": "pred-bad"},
            {
                **contract_payload,
                "prediction_id": "pred-bad",
                "resolver_snapshot": {"resolver_version": "fake"},
            },
        )
    assert ledger_bypass.value.code == engine.LIFECYCLE_BYPASS_CODE


def test_bypass_audit_is_persisted_and_wealth_pilot_requires_explicit_candidates(p0_runtime) -> None:
    service, facade = p0_runtime
    _activate_rule(service)

    direct_token = service.issue_lifecycle_token(actor_role="system", purpose="runtime")
    with pytest.raises(engine.PredictiveServiceError):
        service.resolve_rules(
            {
                **_resolver_payload(),
                "lifecycle_token": direct_token,
                "execution_mode": "runtime",
            }
        )
    persisted = engine.V18PredictiveStore()
    bypass_events = persisted.query_rule_audit_events(event_type=engine.LIFECYCLE_BYPASS_CODE)["items"]
    assert bypass_events
    assert bypass_events[0]["event_type"] == engine.LIFECYCLE_BYPASS_CODE

    with pytest.raises(engine.PredictiveServiceError) as missing_candidates:
        facade.run_wealth_pilot(
            {
                "prediction_id": "wealth-pilot-no-candidates",
                "plugin_claims": [{"plugin_id": "plugin.alpha", "claim_id": "c1"}],
            },
            "system",
            0,
        )
    assert missing_candidates.value.code == "RULE_CANDIDATES_REQUIRED"


def test_rule_candidate_to_knowledge_pr_to_sandbox_rule_version(p0_runtime) -> None:
    service, _ = p0_runtime
    card = service.register_knowledge_card(
        {
            "card_id": "kc.wealth.output",
            "knowledge_domain": "wealth",
            "title": "Output to Wealth",
            "summary": "Output can become wealth when conversion evidence is present.",
            "status": "draft",
            "version": "v1",
            "source_refs": ["internal:test"],
            "tags": ["wealth"],
            "content": {"principle": "output_to_wealth"},
        },
        actor_role="manager",
        actor_user_id=7,
    )
    assert card["version"] == "v1"

    candidate = service.build_sandbox_rule_candidate(
        {
            "knowledge_card_id": "kc.wealth.output",
            "rule_candidate": _rule_payload(
                rule_id="p1.rule",
                version="v1",
                knowledge_card_id="kc.wealth.output",
                status="active",
            ),
        },
        actor_role="practitioner",
        actor_user_id=3,
    )
    assert candidate["candidate_state"] == "sandbox"
    assert candidate["rule_payload"]["status"] == "experimental"

    pr = service.append_knowledge_pr(
        {
            "prediction_id": "pred-p1",
            "requested_by": "practitioner",
            "knowledge_card_id": "kc.wealth.output",
            "target_status": "validated",
            "rule_candidate": candidate["rule_payload"],
        }
    )
    assert pr["review_state"] == "pending_manual_review"
    assert pr["candidate_state"] == "sandbox"
    test_case = service.register_rule_test_case(
        {
            "case_id": "kc-output-case",
            "source": "synthetic",
            "chart_snapshot": {"matched_facts": ["x"]},
            "query_intent": {"topic": "wealth"},
            "expected_evidence_patterns": ["wealth"],
            "expected_conclusions": ["wealth"],
            "tags": ["wealth"],
        },
        actor_role="manager",
        actor_user_id=7,
    )
    facade = engine.RuleRuntimeFacade(service)
    test_run = facade.run_rule_test_v02(
        {
            "rule_candidate_id": pr["rule_candidate_id"],
            "test_case_ids": [test_case["case_id"]],
        },
        "manager",
        7,
    )
    assert test_run["overall_status"] == "pass"

    reviewed = service.review_knowledge_pr(
        {"pr_id": pr["pr_id"], "decision": "approve", "actor_user_id": 7},
        actor_role="manager",
    )
    assert reviewed["review_state"] == "approved"
    assert reviewed["materialized_rule"]["rule_id"] == "p1.rule"
    materialized = service.get_rule("p1.rule", version="v1", allow_inactive=True)
    assert materialized.status == "validated"
    assert materialized.knowledge_card_id == "kc.wealth.output"
    assert service.get_rule("p1.rule", version="v1", allow_inactive=True).status != "active"
