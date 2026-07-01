from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

import v40.api.app as api_app
from v40.admin.app import ADMIN_PREFIX, create_admin_app
from v40.api.app import API_PREFIX, create_app
from v40.contracts import EngineContext, RuntimeContext, RuntimeRequest, Topic
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds

from test_v40_rc2_batch_trainer_v1 import _attribution, _base_registry, _label


def test_runtime_records_policy_version_used_from_engine_context() -> None:
    request = RuntimeRequest(
        request_id="request.policy.version",
        reading_id="reading.policy.version",
        runtime_context=RuntimeContext(
            engine_context=EngineContext(engine_policy_version="policy.candidate.v1"),
        ),
    )

    assert request.policy_version_used == "policy.candidate.v1"

    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    runtime = build_native_bazi_runtime(
        request_id="request.policy.runtime",
        reading_id="reading.policy.runtime",
        chart=seed.chart_facts,
        topic=Topic.CAREER,
        user_question=seed.question,
        engine_context=EngineContext(engine_policy_version="policy.runtime.candidate.v1"),
    )

    assert runtime.request.policy_version_used == "policy.runtime.candidate.v1"
    assert runtime.policy_version_used == "policy.runtime.candidate.v1"


def test_batch_trainer_response_can_dry_run_without_applying_active_policy() -> None:
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/training/batch-trainer-v1",
        json={
            "training_run_id": "train.policy.registry.api.v1",
            "base_registry": _base_registry().model_dump(mode="json"),
            "attributions": [_attribution().model_dump(mode="json")],
            "label_events": [_label().model_dump(mode="json")],
            "candidate_policy_version": "policy.registry.candidate.v1",
            "persist_registry": False,
            "persist_impact": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["registry_persisted"] is False
    assert body["writes_v40_production"] is False
    assert body["changes_chart_facts"] is False
    assert body["candidate_registry"]["candidate_policy_version"] == "policy.registry.candidate.v1"


def test_native_runtime_uses_active_policy_registry_when_no_context_is_passed(monkeypatch) -> None:
    class FakeRepository:
        def get_active_trainable_policy_registry(self):
            return {
                "registry_id": "registry.active.fake",
                "active_policy_version": "policy.active.fake.v1",
            }

    monkeypatch.setattr(api_app.V40PostgresRepository, "from_env", classmethod(lambda cls: FakeRepository()))
    seed = load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]
    response = TestClient(create_app()).post(
        f"{API_PREFIX}/runtime/native-bazi",
        json={
            "request_id": "request.policy.active.api",
            "reading_id": "reading.policy.active.api",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "topic": Topic.CAREER.value,
            "user_question": seed.question,
            "persist": False,
        },
    )

    assert response.status_code == 200
    runtime = response.json()["runtime"]
    assert runtime["policy_version_used"] == "policy.active.fake.v1"
    assert runtime["request"]["policy_version_used"] == "policy.active.fake.v1"
    assert runtime["decision_input"]["policy_version"] == "policy.active.fake.v1"


def test_policy_registry_schema_api_admin_and_docs_are_wired() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    api_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    admin_page = TestClient(create_admin_app()).get(ADMIN_PREFIX)
    doc = Path("qiazhi/v40/docs/V40_RC2_POLICY_REGISTRY_PERSISTENCE.md").read_text(encoding="utf-8")
    status = Path("qiazhi/v40/v40/project/trainable_spine.py").read_text(encoding="utf-8")

    assert "v40_trainable_policy_registries" in schema
    assert "save_trainable_policy_registry" in repository
    assert "/training/policy-registries" in api_source
    assert "/training/policy-registries/active" in api_source
    assert "policy_version_used" in Path("qiazhi/v40/v40/contracts/runtime.py").read_text(encoding="utf-8")
    assert admin_page.status_code == 200
    assert "Policy Registry" in admin_page.text
    assert "/admin/v40/api/policy-registries" in admin_page.text
    assert "RuntimeResult.policy_version_used" in doc
    assert "训练后直接生效" in doc
    assert "TrainablePolicyRegistry persistence and Admin read model" in status
