from __future__ import annotations

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from core.mingli_agent import MingliAgent
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload


def test_product_core_journey_survives_legacy_full_reading_cut(monkeypatch) -> None:
    """The public product must not depend on the retired all-at-once reading path."""

    agent = MingliAgent(FakeCognitiveModel())

    def legacy_full_reading_forbidden(*_args, **_kwargs):
        raise AssertionError("legacy_full_reading_path_called")

    monkeypatch.setattr(agent, "first_reading", legacy_full_reading_forbidden)

    case_store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=agent,
            agent_case_store=case_store,
        )
    )

    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Legacy Cut Reviewer",
            "email": "legacy-cut@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200, registered.text

    profile_response = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": _birth_payload()},
    )
    assert profile_response.status_code == 200, profile_response.text
    profile_id = profile_response.json()["profile"]["profile_id"]

    started = client.post(
        "/api/v50/agent/cases",
        json={"profile_id": profile_id, "active_mode": "member"},
    )
    assert started.status_code == 200, started.text
    start_body = started.json()
    case_id = start_body["case_id"]
    stored = case_store.get(case_id=case_id)
    assert stored is not None
    assert stored["first_run"]["protocol"] == "single_call_baseline_v1"
    assert stored["life_case"]["baseline_insight"]["status"] == "committed"

    abu_plan = client.post(
        "/api/v50/agent/abu/resolve",
        json={
            "message": "继续看财富",
            "has_case": True,
            "has_profile": True,
            "active_mode": "member",
            "active_domain": "whole_chart",
        },
    )
    assert abu_plan.status_code == 200, abu_plan.text
    assert abu_plan.json()["plan"]["action_type"] == "OPEN_DOMAIN"
    assert abu_plan.json()["plan"]["slots"] == {"domain": "wealth"}

    wealth = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/wealth",
        json={"active_mode": "member", "user_question": "资源如何形成并保留？"},
    )
    assert wealth.status_code == 200, wealth.text
    assert wealth.json()["formal_insight"]["status"] == "committed"

    restored = client.get(
        f"/api/v50/agent/cases/{case_id}",
        params={"active_mode": "member"},
    )
    assert restored.status_code == 200, restored.text
    assert "wealth" in restored.json()["reading"]["domain_explorations"]

    probe = start_body["reading"]["probe_plan"]
    feedback = client.post(
        f"/api/v50/agent/cases/{case_id}/probe-respond",
        json={
            "plan_id": probe["plan_id"],
            "option_id": probe["options"][0]["option_id"],
            "active_mode": "member",
            "scenario": probe["scenario"],
            "domain": probe["domain"],
        },
    )
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["receipt"]["chart_facts_modified"] is False
    assert case_store.get(case_id=case_id)["life_case"]["reality_evidence"]

    changed_birth = {
        **_birth_payload(),
        "birth_date": "1987-05-13",
        "year_pillar": "",
        "month_pillar": "",
        "day_pillar": "",
        "hour_pillar": "",
    }
    updated = client.put(
        f"/api/v50/product/profiles/{profile_id}",
        json={"birth_input": changed_birth},
    )
    assert updated.status_code == 200, updated.text
    assert updated.json()["superseded_life_case_count"] == 1
    superseded = case_store.get(case_id=case_id)["life_case"]
    assert superseded["status"] == "superseded"
    assert superseded["chart_version"]["active"] is False
