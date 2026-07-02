from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts import AnswerSignal, HiddenAttributeUpdate, ProbeAnswerResult
from v40.contracts.base import Topic
from v40.project import build_project_status
from v40.probes import build_probe_answer_result
from v40.synthetic import load_synthetic_seeds


ROOT = Path(__file__).resolve().parents[1]
SEED_PATH = ROOT / "data" / "synthetic" / "native_bazi_seeds.json"


def _runtime_payload(reading_id: str = "reading.phase47.probe.001") -> dict[str, object]:
    seed = load_synthetic_seeds(SEED_PATH)[0]
    return {
        "request_id": f"request.{reading_id}",
        "reading_id": reading_id,
        "chart_facts": seed.chart_facts.model_dump(mode="json"),
        "user_question": seed.question,
        "topic": Topic.CAREER.value,
        "role_key": "user",
        "execution_mode": "local",
        "persist": False,
    }


def _runtime() -> dict[str, object]:
    client = TestClient(create_app())
    response = client.post(f"{API_PREFIX}/readings/native-report", json=_runtime_payload())
    assert response.status_code == 200
    body = response.json()
    assert body["runtime"]["probes"]
    return body["runtime"]


def test_probe_answer_builder_creates_signal_hidden_attribute_overlay_and_refined_advice() -> None:
    runtime_body = _runtime()
    from v40.contracts.runtime import RuntimeResult

    runtime = RuntimeResult.model_validate(runtime_body)
    probe = runtime.probes[0]

    result = build_probe_answer_result(
        answer_id="phase47-builder-001",
        runtime=runtime,
        probe_id=probe.probe_id,
        selected_option="平台资源",
        created_by_role="user",
    )

    assert isinstance(result, ProbeAnswerResult)
    assert isinstance(result.answer_signal, AnswerSignal)
    assert isinstance(result.hidden_attribute_update, HiddenAttributeUpdate)
    assert result.answer_signal.probe_id == probe.probe_id
    assert result.hidden_attribute_update.value == "平台资源"
    assert result.training_label.source.value == "probe_answer"
    assert result.training_label.target_type.value == "probe"
    assert result.local_overlay.affected_target_ids
    assert result.refined_advice_points
    assert result.changes_verdict is False
    assert result.changes_chart_facts is False
    assert result.writes_v40_production is False


def test_probe_answer_api_returns_current_reading_calibration_without_rerun_or_weight_write() -> None:
    client = TestClient(create_app())
    runtime = _runtime()
    probe = runtime["probes"][0]

    response = client.post(
        f"{API_PREFIX}/probes/answer",
        json={
            "answer_id": "phase47-api-001",
            "runtime": runtime,
            "probe_id": probe["probe_id"],
            "selected_option": "平台资源",
            "created_by_role": "user",
            "persist": False,
            "persist_overlay": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "v40.probe_answer_response.v1"
    assert body["answer_signal"]["version"] == "v40.answer_signal.v1"
    assert body["hidden_attribute_update"]["version"] == "v40.hidden_attribute_update.v1"
    assert body["training_label"]["source"] == "probe_answer"
    assert body["local_overlay"]["global_update_allowed"] is False
    assert body["refined_advice_points"]
    assert "平台资源" in body["user_message"]
    assert body["event_persisted"] is False
    assert body["overlay_persisted"] is False
    assert body["reruns_reading"] is False
    assert body["changes_verdict"] is False
    assert body["changes_chart_facts"] is False
    assert body["writes_v40_production"] is False
    assert body["writes_v30_state"] is False


def test_probe_answer_api_accepts_recovery_mismatch_without_existing_probe() -> None:
    client = TestClient(create_app())
    runtime = _runtime()

    response = client.post(
        f"{API_PREFIX}/probes/answer",
        json={
            "answer_id": "phase47-api-recovery-001",
            "runtime": runtime,
            "selected_option": "项目客户",
            "mismatch_area": "财富来源",
            "created_by_role": "user",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["hidden_attribute_update"]["attribute_key"] == "wealth.money_mode"
    assert body["training_label"]["target_type"] == "hidden_attribute"
    assert body["training_label"]["weakens"]
    assert "财富" in body["user_message"]


def test_user_ui_uses_probe_answer_endpoint_for_probe_card() -> None:
    html = TestClient(create_app()).get("/v40/ui").text

    assert "/api/v40/probes/answer" in html
    assert "submitProbeAnswer" in html
    assert "/api/v40/training/labels" in html
    assert "TrainingLabelEvent" not in html


def test_phase47_docs_manifest_and_project_status_track_probe_answer_runtime() -> None:
    doc = Path("qiazhi/v40/docs/V40_PHASE47_PROBE_ANSWER_RUNTIME.md").read_text(encoding="utf-8")
    spec = Path("qiazhi/v40/docs/V40_SPEC.md").read_text(encoding="utf-8")
    readme = Path("qiazhi/v40/README.md").read_text(encoding="utf-8")
    status = build_project_status()
    manifest = TestClient(create_app()).get(f"{API_PREFIX}/contracts").json()

    assert "Probe Answer Runtime" in doc
    assert "AnswerSignal" in doc
    assert "HiddenAttributeUpdate" in doc
    assert "POST /api/v40/probes/answer" in doc
    assert "2026-07-01 Phase 47" in spec
    assert "docs/V40_PHASE47_PROBE_ANSWER_RUNTIME.md" in readme
    assert manifest["probe"] == ["AnswerSignal", "HiddenAttributeUpdate", "ProbeAnswerResult"]
    assert status["current_phase"] == 56
    assert status["current_phase_name"] == "Built-In Admin And V30 Profile Sync"
    assert any(row["range"] == "47" and row["status"] == "complete" for row in status["phase_groups"])
