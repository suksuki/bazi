from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from product.agent_case_store import MemoryAgentCaseStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from core.life_domains import LifeDomain
from core.mingli_agent import MingliAgent, MingliCognitiveRecord
from core.mingli_agent.reliability import domain_request_fingerprint
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload


def _authenticated_case() -> tuple[TestClient, MemoryAgentCaseStore, str, str]:
    case_store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=case_store,
        )
    )
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Life Case Reviewer",
            "email": "life-case-convergence@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200, registered.text
    profile = client.post("/api/v50/product/profiles", json={"birth_input": _birth_payload()})
    assert profile.status_code == 200, profile.text
    profile_id = profile.json()["profile"]["profile_id"]
    started = client.post(
        "/api/v50/agent/cases",
        json={"profile_id": profile_id, "active_mode": "member"},
    )
    assert started.status_code == 200, started.text
    return client, case_store, profile_id, started.json()["case_id"]


def _member_case() -> tuple[TestClient, MemoryAgentCaseStore, dict]:
    case_store = MemoryAgentCaseStore()
    client = TestClient(
        create_product_app(
            product_store=MemoryProductStore(),
            mingli_agent=MingliAgent(FakeCognitiveModel()),
            agent_case_store=case_store,
        )
    )
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Convergence Member",
            "email": "convergence-member@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200, registered.text
    started = client.post(
        "/api/v50/agent/cases",
        json={"birth_input": _birth_payload(), "active_mode": "member"},
    )
    assert started.status_code == 200, started.text
    return client, case_store, started.json()


def test_chart_change_hides_old_case_and_keeps_an_explicit_read_only_history() -> None:
    client, _, profile_id, case_id = _authenticated_case()
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

    current = client.get("/api/v50/agent/cases")
    assert current.status_code == 200, current.text
    assert current.json()["cases"] == []
    assert current.json()["historical_cases_hidden"] == 1

    history = client.get("/api/v50/agent/cases", params={"include_history": True})
    assert history.json()["historical_cases"][0]["case_id"] == case_id
    assert history.json()["historical_cases"][0]["read_only"] is True

    assert client.get(f"/api/v50/agent/cases/{case_id}").status_code == 409
    historical = client.get(
        f"/api/v50/agent/cases/{case_id}",
        params={"historical": True, "active_mode": "member"},
    )
    assert historical.status_code == 200, historical.text
    assert historical.json()["read_only"] is True
    assert historical.json()["reading"]["probe_plan"] is None
    assert client.post(
        f"/api/v50/agent/cases/{case_id}/temporal/select",
        json={"period_key": "2026-06", "active_mode": "member"},
    ).status_code == 409

    replacement = client.post(
        "/api/v50/agent/cases",
        json={"profile_id": profile_id, "active_mode": "member"},
    )
    assert replacement.status_code == 200, replacement.text
    active = client.get("/api/v50/agent/cases").json()["cases"]
    assert [item["case_id"] for item in active] == [replacement.json()["case_id"]]


def test_reality_evidence_month_selection_and_monthly_review_form_one_versioned_loop() -> None:
    client, case_store, started = _member_case()
    case_id = started["case_id"]
    baseline = case_store.get(case_id=case_id)["life_case"]["baseline_insight"]
    selected = client.post(
        f"/api/v50/agent/cases/{case_id}/temporal/select",
        json={"period_key": "2026-06", "active_mode": "member"},
    )
    assert selected.status_code == 200, selected.text
    assert selected.json()["workspace_state"]["selected_period"] == "2026-06"
    assert selected.json()["reading"]["temporal_state"]["selected_period"] == "2026-06"

    payload = {
        "idempotency_key": "event:2026-06:medication-reaction",
        "source": "page",
        "summary": "六月出现一次药物过敏反应。",
        "period_key": "2026-06",
        "domain": "health_vitality",
        "kind": "health_event",
        "severity": "medium",
        "active_mode": "member",
    }
    first = client.post(f"/api/v50/agent/cases/{case_id}/reality-evidence", json=payload)
    assert first.status_code == 200, first.text
    evidence_id = first.json()["evidence"]["evidence_id"]
    replay = client.post(
        f"/api/v50/agent/cases/{case_id}/reality-evidence",
        json={**payload, "source": "abu"},
    )
    assert replay.status_code == 200, replay.text
    assert replay.json()["created"] is False
    listed = client.get(
        f"/api/v50/agent/cases/{case_id}/reality-evidence",
        params={"period_key": "2026-06"},
    ).json()["evidence"]
    assert [item["evidence_id"] for item in listed] == [evidence_id]

    review = client.post(
        f"/api/v50/agent/cases/{case_id}/monthly-review",
        json={
            "period_key": "2026-06",
            "temporal_snapshot_id": first.json()["temporal_snapshot"]["snapshot_id"],
            "evidence_refs": [evidence_id],
            "verdict": "partially_supported",
            "user_note": "有明显变化，但不能把它等同于某个必然事件。",
        },
    )
    assert review.status_code == 200, review.text
    assert review.json()["auto_committed"] is False
    candidate_id = review.json()["candidate"]["candidate_id"]
    replayed_review = client.post(
        f"/api/v50/agent/cases/{case_id}/monthly-review",
        json={
            "period_key": "2026-06",
            "temporal_snapshot_id": first.json()["temporal_snapshot"]["snapshot_id"],
            "evidence_refs": [evidence_id],
            "verdict": "partially_supported",
            "user_note": "有明显变化，但不能把它等同于某个必然事件。",
        },
    )
    assert replayed_review.json()["candidate"]["candidate_id"] == candidate_id
    assert len(case_store.get(case_id=case_id)["life_case"]["monthly_reviews"]) == 1
    before_commit = case_store.get(case_id=case_id)["life_case"]
    assert before_commit["case_version"] == "v1"
    assert before_commit["baseline_insight"]["claim"] == baseline["claim"]

    committed = client.post(
        f"/api/v50/agent/cases/{case_id}/case-revisions/commit",
        json={"candidate_id": candidate_id},
    )
    assert committed.status_code == 200, committed.text
    assert committed.json()["case_version"] == "v2"
    stored = case_store.get(case_id=case_id)["life_case"]
    assert stored["baseline_insight"]["insight_id"] == baseline["insight_id"]
    assert stored["version_history"][0]["case_version"] == "v1"
    assert stored["case_revisions"][-1]["type"] == "case_revision"
    restored = client.get(f"/api/v50/agent/cases/{case_id}", params={"active_mode": "member"})
    assert restored.json()["reading"]["life_case"]["latest_case_revision"]["case_version"] == "v2"


def test_formal_projection_and_canonical_evidence_remain_the_only_restore_authorities() -> None:
    client, case_store, started = _member_case()
    case_id = started["case_id"]
    original_thesis = started["reading"]["whole_chart_thesis"]
    probe = started["reading"]["probe_plan"]
    response = client.post(
        f"/api/v50/agent/cases/{case_id}/probe-respond",
        json={
            "plan_id": probe["plan_id"],
            "option_id": probe["options"][0]["option_id"],
            "active_mode": "member",
            "scenario": probe["scenario"],
            "domain": probe["domain"],
        },
    )
    assert response.status_code == 200, response.text

    internal = case_store._cases[case_id]
    assert "workspace" not in internal
    assert "case_belief_state" in internal
    compatible = case_store.get(case_id=case_id)
    assert len(compatible["workspace"]["probe_history"]) == 1
    assert len(compatible["life_case"]["reality_evidence"]) == 1

    tampered = dict(compatible)
    record = MingliCognitiveRecord.model_validate(tampered["record"])
    tampered["record"] = record.model_copy(update={
        "cognition": record.cognition.model_copy(update={"whole_chart_thesis": "运行记录里的伪造结论"}),
    }).model_dump(mode="json")
    case_store.save(
        case_id=case_id,
        user_id=internal.get("user_id"),
        profile_id=None,
        payload=tampered,
    )
    restored = client.get(f"/api/v50/agent/cases/{case_id}", params={"active_mode": "member"})
    assert restored.status_code == 200, restored.text
    assert restored.json()["reading"]["whole_chart_thesis"] == original_thesis
    assert restored.json()["reading"]["whole_chart_thesis"] != "运行记录里的伪造结论"


def test_domain_workspace_sync_and_cache_key_cover_all_implementation_authorities() -> None:
    client, case_store, started = _member_case()
    case_id = started["case_id"]
    wealth = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/wealth",
        json={"active_mode": "member", "user_question": "资源如何形成并保留？"},
    )
    assert wealth.status_code == 200, wealth.text
    assert wealth.json()["reading"]["workspace_state"]["active_domain"] == "wealth"
    assert case_store.get(case_id=case_id)["workspace_state"]["active_domain"] == "wealth"

    row = case_store.get(case_id=case_id)
    record = MingliCognitiveRecord.model_validate(row["record"])
    common = {
        "record": record,
        "world_id": row["world"]["world_id"],
        "domain": LifeDomain.WEALTH,
        "user_question": "资源如何形成并保留？",
        "case_version": "v1",
        "chart_version_id": row["life_case"]["chart_version"]["version_id"],
        "temporal_scope": "current",
        "input_context_hash": "context-a",
    }
    first = domain_request_fingerprint(
        **common,
        implementation_versions={"reasoner": "r1", "prompt": "p1", "model": "m1", "knowledge": "k1"},
    )
    assert first != domain_request_fingerprint(
        **common,
        implementation_versions={"reasoner": "r1", "prompt": "p2", "model": "m1", "knowledge": "k1"},
    )
    assert first != domain_request_fingerprint(
        **{**common, "case_version": "v2"},
        implementation_versions={"reasoner": "r1", "prompt": "p1", "model": "m1", "knowledge": "k1"},
    )
    assert first != domain_request_fingerprint(
        **{**common, "temporal_scope": datetime.now(timezone.utc).strftime("%Y-%m")},
        implementation_versions={"reasoner": "r1", "prompt": "p1", "model": "m1", "knowledge": "k1"},
    )


def test_legacy_l5_bundle_is_retired_while_case_history_remains_in_storage_contracts() -> None:
    root = Path(__file__).resolve().parents[1]
    surface = (root / "apps/product/product_surface.py").read_text(encoding="utf-8")
    case_store = (root / "apps/product/agent_case_store_contracts.py").read_text(encoding="utf-8")

    assert 'FileResponse(MEDIA_DIR / "app.js"' not in surface
    assert "list_for_user" in case_store
