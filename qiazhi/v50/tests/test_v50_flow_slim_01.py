from __future__ import annotations

import time

from fastapi.testclient import TestClient

from core.mingli_agent import ChartWorldInstance, MingliAgent
from core.mingli_agent.contracts import (
    AssertionGateReceipt,
    DomainCausalReading,
    WholeChartCognitionDraft,
)
from product.agent_case_store import MemoryAgentCaseStore
from product.agent_job_store import MemoryAgentJobStore
from product.app import create_product_app
from product.product_store import MemoryProductStore
from tests.test_v50_mingli_agent_refoundation import FakeCognitiveModel, _birth_payload


class CountingCognitiveModel(FakeCognitiveModel):
    def __init__(self) -> None:
        self.baseline_calls = 0
        self.domain_calls = 0

    def generate(self, *, prompt, schema, temperature=0.2, thinking=True, max_tokens=3200):
        if schema is WholeChartCognitionDraft:
            self.baseline_calls += 1
        if schema is DomainCausalReading:
            self.domain_calls += 1
        return super().generate(
            prompt=prompt,
            schema=schema,
            temperature=temperature,
            thinking=thinking,
            max_tokens=max_tokens,
        )


def _workspace_client():
    product_store = MemoryProductStore()
    case_store = MemoryAgentCaseStore()
    job_store = MemoryAgentJobStore()
    model = CountingCognitiveModel()
    client = TestClient(create_product_app(
        product_store=product_store,
        mingli_agent=MingliAgent(model),
        agent_case_store=case_store,
        agent_job_store=job_store,
    ))
    registered = client.post(
        "/api/v50/product/auth/register",
        json={
            "display_name": "Flow Slim Member",
            "email": "flow-slim@example.com",
            "password": "secure-pass-123",
            "role": "member",
        },
    )
    assert registered.status_code == 200, registered.text
    profile = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": _birth_payload()},
    )
    assert profile.status_code == 200, profile.text
    return (
        client,
        case_store,
        job_store,
        model,
        profile.json()["profile"]["profile_id"],
    )


def _bootstrap(client: TestClient, profile_id: str) -> dict:
    response = client.post(
        "/api/v50/experience/workspace/bootstrap",
        json={"profile_id": profile_id, "case_id": ""},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _wait_for_job(client: TestClient, job_id: str) -> dict:
    for _ in range(100):
        job = client.get(f"/api/v50/experience/workspace/jobs/{job_id}")
        assert job.status_code == 200, job.text
        payload = job.json()
        if payload["status"] in {"completed", "failed"}:
            return payload
        time.sleep(0.01)
    raise AssertionError("background baseline did not finish")


def test_profile_selection_is_one_deterministic_workspace_bootstrap() -> None:
    client, case_store, _, model, profile_id = _workspace_client()

    first = _bootstrap(client, profile_id)
    second = _bootstrap(client, profile_id)

    assert first["request_budget"] == {
        "api_requests": 1,
        "llm_calls": 0,
        "tts_calls": 0,
        "domain_generations": 0,
    }
    assert first["selected_case_id"] == second["selected_case_id"]
    assert first["envelope"]["mode"] == "chart_facts_only"
    assert len(first["envelope"]["allowed_chart_facts"]) == 4
    assert first["workspace"] is None
    assert first["cognition"]["status"] == "chart_ready"
    assert model.baseline_calls == model.domain_calls == 0
    assert len(case_store.list_for_user(user_id=first["envelope"]["participant_scope"]["participant_ref"])) == 1
    assert client.get("/api/v50/experience/cases").status_code == 404
    assert client.get(
        f"/api/v50/experience/cases/{first['selected_case_id']}/baseline"
    ).status_code == 404


def test_chart_facts_and_abu_manifest_work_before_cognition() -> None:
    client, _, _, model, profile_id = _workspace_client()
    bootstrap = _bootstrap(client, profile_id)

    response = client.get(
        f"/api/v50/narration/cases/{bootstrap['selected_case_id']}/baseline"
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["tts_called"] is False
    assert payload["llm_used"] is False
    assert payload["manifest"]["formal_insight_id"] == "deterministic-chart-facts"
    assert [item["kind"] for item in payload["manifest"]["segments"]] == [
        "thesis",
        "uncertainty",
    ]
    assert model.baseline_calls == model.domain_calls == 0


def test_missing_baseline_runs_once_and_topics_remain_on_demand() -> None:
    client, _, _, model, profile_id = _workspace_client()
    bootstrap = _bootstrap(client, profile_id)
    case_id = bootstrap["selected_case_id"]

    started = client.post(
        f"/api/v50/experience/workspace/cases/{case_id}/baseline"
    )
    assert started.status_code == 200, started.text
    start_payload = started.json()
    assert start_payload["status"] == "baseline_preparing"
    assert start_payload["llm_calls_started"] == 1
    job = _wait_for_job(client, start_payload["job_id"])
    assert job["status"] == "completed"
    assert model.baseline_calls == 1
    assert model.domain_calls == 0

    repeated = client.post(
        f"/api/v50/experience/workspace/cases/{case_id}/baseline"
    )
    assert repeated.json()["status"] == "baseline_cache_reused"
    assert repeated.json()["llm_calls_started"] == 0
    assert model.baseline_calls == 1

    refreshed = _bootstrap(client, profile_id)
    assert refreshed["cognition"]["status"] == "ready"
    assert refreshed["cognition"]["cache_hit"] is True
    assert refreshed["workspace"] is not None
    assert model.domain_calls == 0

    domain = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/career",
        json={"user_question": "我的职业价值如何形成？", "progressive": False},
    )
    assert domain.status_code == 200, domain.text
    assert domain.json()["status"] == "domain_exploration_ready"
    assert model.domain_calls == 1
    cached = client.post(
        f"/api/v50/agent/cases/{case_id}/domains/career",
        json={"user_question": "我的职业价值如何形成？", "progressive": False},
    )
    assert cached.status_code == 200, cached.text
    assert cached.json()["cache_hit"] is True
    assert model.domain_calls == 1


def test_stored_draft_is_reconciled_locally_without_another_model_call() -> None:
    client, case_store, _, model, profile_id = _workspace_client()
    bootstrap = _bootstrap(client, profile_id)
    case_id = bootstrap["selected_case_id"]
    row = case_store.get(case_id=case_id)
    assert row is not None
    source_record = MingliAgent(FakeCognitiveModel()).first_baseline_reading(
        case_id=case_id,
        world=ChartWorldInstance.model_validate(row["world"]),
    )
    stored_record = source_record.model_copy(update={
        "assertion_gate": AssertionGateReceipt(),
    })
    row["record"] = stored_record.model_dump(mode="json")
    row["life_case"] = None
    row["status"] = "blocked"
    row["background_cognition"] = {
        "status": "failed",
        "attempt_count": 1,
        "job_id": "",
    }
    case_store.save(
        case_id=case_id,
        user_id=str(row["user_id"]),
        profile_id=profile_id,
        payload=row,
    )

    response = client.post(
        f"/api/v50/experience/workspace/cases/{case_id}/baseline"
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "baseline_reconciled"
    assert response.json()["llm_calls_started"] == 0
    assert model.baseline_calls == model.domain_calls == 0
    reconciled = case_store.get(case_id=case_id)
    assert reconciled is not None
    assert reconciled["life_case"]["baseline_insight"]["status"] == "committed"
    assert reconciled["record_archive"]


def test_birth_change_supersedes_chart_only_case_and_creates_a_new_version() -> None:
    client, case_store, _, model, profile_id = _workspace_client()
    first = _bootstrap(client, profile_id)
    old_case_id = first["selected_case_id"]
    changed = {
        **_birth_payload(),
        "birth_date": "1987-05-13",
        "year_pillar": "",
        "month_pillar": "",
        "day_pillar": "",
        "hour_pillar": "",
    }

    updated = client.put(
        f"/api/v50/product/profiles/{profile_id}",
        json={"birth_input": changed},
    )
    assert updated.status_code == 200, updated.text
    old_row = case_store.get(case_id=old_case_id)
    assert old_row is not None
    assert old_row["status"] == "superseded"

    replacement = _bootstrap(client, profile_id)
    assert replacement["selected_case_id"] != old_case_id
    assert replacement["cognition"]["status"] == "chart_ready"
    assert model.baseline_calls == model.domain_calls == 0


def test_profile_switch_resolves_each_profile_to_its_current_case() -> None:
    client, _, _, model, first_profile_id = _workspace_client()
    second_birth = {
        **_birth_payload(),
        "name": "Second Profile",
        "birth_date": "1987-05-13",
        "year_pillar": "",
        "month_pillar": "",
        "day_pillar": "",
        "hour_pillar": "",
    }
    created = client.post(
        "/api/v50/product/profiles",
        json={"birth_input": second_birth},
    )
    assert created.status_code == 200, created.text
    second_profile_id = created.json()["profile"]["profile_id"]

    first = _bootstrap(client, first_profile_id)
    second = _bootstrap(client, second_profile_id)

    assert first["selected_profile_id"] == first_profile_id
    assert second["selected_profile_id"] == second_profile_id
    assert first["selected_case_id"] != second["selected_case_id"]
    assert first["envelope"]["allowed_chart_facts"] != second["envelope"]["allowed_chart_facts"]
    assert model.baseline_calls == model.domain_calls == 0


def test_frontend_has_no_legacy_blocking_first_reading_chain() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    shell = root / "apps/product/experience_shell/src"
    api = (shell / "api.ts").read_text(encoding="utf-8")
    data = (shell / "experience_data.ts").read_text(encoding="utf-8")
    main = (shell / "main.ts").read_text(encoding="utf-8")
    interactions = (shell / "experience_interactions.ts").read_text(encoding="utf-8")
    legacy = (root / "apps/product/static/l5/app.js").read_text(encoding="utf-8")

    assert "/api/v50/experience/workspace/bootstrap" in api
    assert "Promise.allSettled" not in data
    assert "/api/v50/experience/cases/${encodeURIComponent(caseId)}/baseline" not in api
    assert "loadReadOnlyCanvas(activeCaseId)" in main
    assert "loadNarration(activeCaseId)" in main
    assert "startMissingBaseline(activeCaseId)" in main
    assert "let openCaseEpoch = 0" in main
    assert "requestEpoch !== openCaseEpoch" in main
    assert "void openCase({ profileId })" in main
    assert "data-profile-select" in (shell / "components.ts").read_text(encoding="utf-8")
    assert 'querySelectorAll<HTMLSelectElement>("[data-profile-select]")' in interactions
    assert 'querySelector<HTMLSelectElement>("[data-profile-select]")' not in interactions
    assert "window.location.assign(`/experience?profile=" in legacy
    assert "window.location.replace(`/experience?profile=" in legacy
    assert "PROFILE_MANAGEMENT_MODE" in legacy
    assert "最终事实与证据检查没有通过" not in legacy
