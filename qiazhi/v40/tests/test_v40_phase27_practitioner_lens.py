from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import SurfaceKey, Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def _ziwei_facts() -> ZiweiChartFacts:
    return ZiweiChartFacts(
        chart_id="ziwei.phase27.001",
        life_palace="命宫在寅",
        body_palace="身宫在申",
        palaces={"官禄": {"stars": ["紫微", "天府"]}, "迁移": {"stars": ["七杀"]}},
        major_stars={"官禄": ["紫微", "天府"], "迁移": ["七杀"]},
        annual_transformations={"禄": "官禄", "忌": "交友"},
        domain_lenses={"career": "事业旁路更关注平台、职责边界和外部机会承接。"},
    )


def test_practitioner_lens_is_hidden_for_ordinary_user() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase27.user.001",
        reading_id="reading.phase27.user.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="user",
    )

    lens = runtime.surface_bundle.surfaces[SurfaceKey.CALIBRATION]["practitioner_lens"]

    assert lens["available"] is False
    assert "普通用户" in lens["reason"]


def test_practitioner_lens_exposes_bazi_ziwei_sidecar_without_verdict_mutation() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase27.practitioner.001",
        reading_id="reading.phase27.practitioner.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
        role_key="practitioner",
    )

    lens = runtime.surface_bundle.surfaces[SurfaceKey.CALIBRATION]["practitioner_lens"]

    assert lens["available"] is True
    assert lens["summary"]["bazi_signal_count"] > 0
    assert lens["summary"]["ziwei_signal_count"] > 0
    assert lens["summary"]["ziwei_probe_trigger_count"] > 0
    assert "事业" in lens["agreement_topics"]
    assert lens["ziwei_signals"][0]["topic"] == "事业"
    assert "职责边界" in lens["probe_triggers"][0]["question"]
    assert any(action["label"] == "需要追问" for action in lens["calibration_actions"])
    assert lens["candidate_board"]["version"] == "v40.mingli_candidate_board.v1"
    assert lens["boundaries"]["changes_verdict"] is False
    assert lens["boundaries"]["ordinary_user_visible"] is False
    assert runtime.decision_input is not None
    assert all(signal.source.value != "ziwei_engine" for signal in runtime.decision_input.signals)


def test_native_report_returns_practitioner_lens_for_practitioner_role() -> None:
    seed = _seed()
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase27.report.001",
            "reading_id": "reading.phase27.report.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "ziwei_chart_facts": _ziwei_facts().model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "practitioner",
            "execution_mode": "local",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    lens = body["runtime"]["surface_bundle"]["surfaces"]["calibration"]["practitioner_lens"]
    assert lens["available"] is True
    assert lens["summary"]["ziwei_signal_count"] > 0
    assert body["accepted"] is True
