from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import Topic
from v40.decision import build_decision_output
from v40.engines import build_native_bazi_runtime, run_native_bazi_engine
from v40.synthetic import load_synthetic_seeds
from v40.contracts.engine import EngineRunRequest
from v40.contracts.base import EngineKey, EngineMode
from v40.contracts.signal import SignalRegistrySnapshot

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def test_decision_engine_consumes_signal_registry_without_llm_authority() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    engine_result = run_native_bazi_engine(
        engine_request=EngineRunRequest(
            request_id="engine.phase13.001",
            reading_id="reading.phase13.001",
            engine=EngineKey.BAZI,
            mode=EngineMode.SIGNAL_SIDECAR,
            topic=Topic.CAREER,
        ),
        chart=seed.chart_facts,
    )
    registry = SignalRegistrySnapshot(
        registry_id="registry.phase13.001",
        reading_id="reading.phase13.001",
        signals=engine_result.signals,
    )

    output = build_decision_output(
        reading_id="reading.phase13.001",
        registry=registry,
        topic=Topic.CAREER,
        role_key="user",
        user_question=seed.question,
    )

    assert output.input_bundle.llm_input_used is False
    assert output.llm_decision_authority is False
    assert output.central_brain_decision_authority is False
    assert output.branch_candidates
    assert output.verdicts[0].evidence_refs
    assert output.advice_plans[0].source_verdict_ids == [output.verdicts[0].verdict_id]
    assert output.probes[0].ask_now is False


def test_native_runtime_separates_user_report_from_practitioner_calibration() -> None:
    seed = load_synthetic_seeds(SEED_PATH)[0]

    user_runtime = build_native_bazi_runtime(
        request_id="request.phase13.user",
        reading_id="reading.phase13.user",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="user",
    )
    practitioner_runtime = build_native_bazi_runtime(
        request_id="request.phase13.practitioner",
        reading_id="reading.phase13.practitioner",
        chart=seed.chart_facts,
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )

    assert user_runtime.decision_input is not None
    assert user_runtime.branches
    assert user_runtime.product_projection is not None
    assert user_runtime.product_projection.branch_cards == []
    assert user_runtime.surface_bundle is not None
    assert user_runtime.surface_bundle.surfaces["conversation"]["auto_start"] is False

    assert practitioner_runtime.product_projection is not None
    assert practitioner_runtime.product_projection.branch_cards
    assert practitioner_runtime.surface_bundle is not None
    assert practitioner_runtime.surface_bundle.surfaces["calibration"]["available"] is True


def test_practitioner_calibration_endpoint_records_training_label_without_weight_write() -> None:
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/calibration/practitioner-selection",
        json={
            "event_id": "calibration.phase13.001",
            "reading_id": "reading.phase13.api",
            "target_type": "branch",
            "target_ids": ["branch:reading.phase13.api:career:1"],
            "label": "supports",
            "strength": 0.8,
            "confidence": 0.72,
            "reason": "命理师确认事业主分支更贴合用户反馈",
            "created_by_role": "practitioner",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["event"]["source"] == "practitioner_selection"
    assert body["event"]["local_only"] is True
    assert body["writes_v40_weight"] is False
    assert body["writes_v30_state"] is False
