from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import SurfaceKey, Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.engines import build_native_bazi_runtime
from v40.training import build_practitioner_lens_action
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def _ziwei_facts() -> ZiweiChartFacts:
    return ZiweiChartFacts(
        chart_id="ziwei.phase28.001",
        life_palace="命宫在寅",
        body_palace="身宫在申",
        palaces={"官禄": {"stars": ["紫微", "天府"]}, "迁移": {"stars": ["七杀"]}},
        major_stars={"官禄": ["紫微", "天府"], "迁移": ["七杀"]},
        annual_transformations={"禄": "官禄", "忌": "交友"},
        domain_lenses={"career": "事业旁路更关注平台、职责边界和外部机会承接。"},
    )


def _practitioner_runtime():
    seed = _seed()
    return build_native_bazi_runtime(
        request_id="request.phase28.practitioner.001",
        reading_id="reading.phase28.practitioner.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )


def test_practitioner_lens_action_builds_training_label_and_local_overlay() -> None:
    runtime = _practitioner_runtime()
    lens = runtime.surface_bundle.surfaces[SurfaceKey.CALIBRATION]["practitioner_lens"]
    target_id = lens["ziwei_signals"][0]["signal_id"]

    event, overlay = build_practitioner_lens_action(
        action_id="phase28.local.001",
        runtime=runtime,
        action_key="ask_to_confirm",
        target_type="signal",
        target_ids=[target_id],
        note="先转追问，不直接进结论。",
        created_by_role="practitioner",
    )

    assert event.event_id == "label:practitioner_lens:phase28.local.001"
    assert event.source.value == "practitioner_selection"
    assert event.label.value == "needs_probe"
    assert event.local_only is True
    assert event.chart_fact_mutation_allowed is False
    assert target_id in event.target_ids
    assert "命理师备注" in event.reason
    assert overlay.overlay_id == "overlay:practitioner_lens:phase28.local.001"
    assert overlay.label_event_ids == [event.event_id]
    assert overlay.affected_target_ids == [target_id]
    assert overlay.global_update_allowed is False
    assert overlay.expires_after_reading is True


def test_practitioner_lens_action_api_rejects_user_runtime_and_accepts_practitioner_runtime() -> None:
    seed = _seed()
    user_runtime = build_native_bazi_runtime(
        request_id="request.phase28.user.001",
        reading_id="reading.phase28.user.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="user",
    )
    practitioner_runtime = _practitioner_runtime()
    lens = practitioner_runtime.surface_bundle.surfaces[SurfaceKey.CALIBRATION]["practitioner_lens"]
    target_id = lens["ziwei_signals"][0]["signal_id"]
    client = TestClient(create_app())

    rejected = client.post(
        f"{API_PREFIX}/calibration/practitioner-lens-action",
        json={
            "action_id": "phase28.rejected.001",
            "runtime": user_runtime.model_dump(mode="json"),
            "action_key": "more_like_this",
            "target_type": "signal",
            "target_ids": [target_id],
            "persist": False,
            "persist_overlay": False,
        },
    )
    assert rejected.status_code == 422

    accepted = client.post(
        f"{API_PREFIX}/calibration/practitioner-lens-action",
        json={
            "action_id": "phase28.accepted.001",
            "runtime": practitioner_runtime.model_dump(mode="json"),
            "action_key": "more_like_this",
            "target_type": "signal",
            "target_ids": [target_id],
            "persist": False,
            "persist_overlay": False,
        },
    )
    assert accepted.status_code == 200
    body = accepted.json()
    assert body["event"]["label"] == "supports"
    assert body["overlay"]["affected_target_ids"] == [target_id]
    assert body["event_persisted"] is False
    assert body["overlay_persisted"] is False
    assert body["writes_v40_weight"] is False
    assert body["changes_verdict"] is False
    assert body["changes_chart_facts"] is False


def test_phase28_local_overlay_schema_and_repository_are_v40_only() -> None:
    schema = Path("qiazhi/v40/deploy/postgres_v40_schema.sql").read_text(encoding="utf-8")
    repository = Path("qiazhi/v40/v40/storage/postgres.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")

    assert "v40_local_overlays" in schema
    assert "idx_v40_local_overlays_reading" in schema
    assert "save_local_overlay" in repository
    assert "list_local_overlays" in repository
    assert "INSERT INTO v40_local_overlays" in repository
    assert "/calibration/practitioner-lens-action" in app_source
    assert "/calibration/local-overlays" in app_source
    assert "v30_local_overlay" not in schema
    assert "v30_local_overlay" not in repository
