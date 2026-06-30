from __future__ import annotations

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import EngineKey, Topic
from v40.contracts.chart import ZiweiChartFacts
from v40.contracts.signal import SignalSource
from v40.engines import build_native_bazi_runtime
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def _ziwei_facts() -> ZiweiChartFacts:
    return ZiweiChartFacts(
        chart_id="ziwei.phase25.001",
        life_palace="命宫在寅",
        body_palace="身宫在申",
        major_stars={"命宫": ["紫微", "天府"], "迁移": ["七杀"]},
        palace_notes={"迁移": "外部平台与职责压力较明显"},
        domain_lenses={"career": "事业旁路更关注平台、职责边界和外部机会承接。"},
    )


def test_ziwei_domain_lens_enters_runtime_without_decision_weight() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase25.ziwei.001",
        reading_id="reading.phase25.ziwei.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
    )

    assert runtime.engine_result is not None
    engines = [result.engine for result in runtime.engine_result.results]
    assert EngineKey.BAZI in engines
    assert EngineKey.ZIWEI in engines
    ziwei_plan = [item for item in runtime.engine_result.plan.items if item.engine == EngineKey.ZIWEI][0]
    assert ziwei_plan.decision_weight == 0.0
    ziwei_result = [result for result in runtime.engine_result.results if result.engine == EngineKey.ZIWEI][0]
    assert ziwei_result.decision_weight == 0.0
    assert ziwei_result.signals
    assert runtime.signal_registry is not None
    assert any(signal.source == SignalSource.ZIWEI_ENGINE for signal in runtime.signal_registry.signals)
    assert runtime.decision_input is not None
    assert all(signal.source != SignalSource.ZIWEI_ENGINE for signal in runtime.decision_input.signals)


def test_native_report_accepts_optional_ziwei_facts_as_sidecar() -> None:
    seed = _seed()
    client = TestClient(create_app())

    response = client.post(
        f"{API_PREFIX}/readings/native-report",
        json={
            "request_id": "request.phase25.report.001",
            "reading_id": "reading.phase25.report.001",
            "chart_facts": seed.chart_facts.model_dump(mode="json"),
            "ziwei_chart_facts": _ziwei_facts().model_dump(mode="json"),
            "user_question": seed.question,
            "topic": Topic.CAREER.value,
            "role_key": "user",
            "execution_mode": "local",
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["accepted"] is True
    results = body["runtime"]["engine_result"]["results"]
    assert any(result["engine"] == "ziwei" for result in results)
    ziwei_signals = [
        signal
        for signal in body["runtime"]["signal_registry"]["signals"]
        if signal["source"] == "ziwei_engine"
    ]
    assert ziwei_signals
    decision_signals = body["runtime"]["decision_input"]["signals"]
    assert all(signal["source"] != "ziwei_engine" for signal in decision_signals)
