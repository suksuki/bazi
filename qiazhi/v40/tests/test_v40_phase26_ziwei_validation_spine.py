from __future__ import annotations

from v40.contracts.base import Topic
from v40.contracts.chart import BirthInputCanonical, ZiweiChartFacts
from v40.contracts.evaluation import EvaluationCaseSpec, ExpectedVerdict, ForbiddenAssertion
from v40.contracts.signal import SignalSource
from v40.engines import build_native_bazi_runtime
from v40.evaluation import build_metric_summary
from v40.synthetic import load_synthetic_seeds


def _seed():
    return load_synthetic_seeds("qiazhi/v40/data/synthetic/native_bazi_seeds.json")[0]


def _ziwei_facts() -> ZiweiChartFacts:
    return ZiweiChartFacts(
        chart_id="ziwei.phase26.001",
        life_palace="命宫在寅",
        body_palace="身宫在申",
        palaces={
            "官禄": {"stars": ["紫微", "天府"], "note": "平台与职责边界较明显"},
            "迁移": {"stars": ["七杀"], "note": "外部机会与变化并见"},
        },
        major_stars={"命宫": ["紫微"], "官禄": ["天府"], "迁移": ["七杀"]},
        annual_transformations={"禄": "官禄", "忌": "交友"},
        decade_luck="甲辰",
        flow_year="丙午",
        palace_notes={"迁移": "外部平台与职责压力较明显"},
        domain_lenses={"career": "事业旁路更关注平台、职责边界和外部机会承接。"},
    )


def test_birth_input_canonical_declares_ziwei_readiness() -> None:
    complete = BirthInputCanonical(
        input_id="birth.phase26.complete",
        birth_date="1990-02-03",
        birth_time="辰时",
        gender="乾",
        timezone="Asia/Shanghai",
    )
    partial = BirthInputCanonical(input_id="birth.phase26.partial", birth_date="1990-02-03")
    unavailable = BirthInputCanonical(input_id="birth.phase26.unavailable")

    assert complete.can_run_ziwei is True
    assert complete.ziwei_input_quality == "complete"
    assert partial.can_run_ziwei is False
    assert partial.ziwei_input_quality == "partial"
    assert unavailable.ziwei_input_quality == "unavailable"


def test_ziwei_domain_lens_emits_domain_probe_triggers() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase26.ziwei.001",
        reading_id="reading.phase26.ziwei.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
    )

    assert runtime.engine_result is not None
    ziwei_result = [result for result in runtime.engine_result.results if result.engine.value == "ziwei"][0]
    assert ziwei_result.probe_candidates
    assert ziwei_result.probe_candidates[0]["topic"] == "career"
    assert "职责边界" in ziwei_result.probe_candidates[0]["question"]
    assert any(feature["feature_id"] == "ziwei.domain_palace_map" for feature in ziwei_result.features)
    ziwei_signal = [signal for signal in runtime.signal_registry.signals if signal.source == SignalSource.ZIWEI_ENGINE][0]
    assert "ziwei.palace.官禄" in ziwei_signal.evidence_refs
    assert "ziwei.palace.迁移" in ziwei_signal.evidence_refs


def test_ziwei_sidecar_metrics_observe_without_release_gate_authority() -> None:
    seed = _seed()
    runtime = build_native_bazi_runtime(
        request_id="request.phase26.metrics.001",
        reading_id="reading.phase26.metrics.001",
        chart=seed.chart_facts,
        ziwei_chart=_ziwei_facts(),
        user_question=seed.question,
        topic=Topic.CAREER,
    )
    case = EvaluationCaseSpec(
        case_id="case.phase26.ziwei.metrics",
        user_question=seed.question,
        topic=Topic.CAREER,
        expected_verdicts=[ExpectedVerdict(topic=Topic.CAREER, expected_keywords=["事业"])],
        forbidden_assertions=[ForbiddenAssertion(text="一定发财", reason="overclaim guard")],
    )

    metrics = build_metric_summary(case_spec=case, runtime=runtime)

    assert metrics.ziwei_sidecar_signal_rate == 1.0
    assert metrics.cross_engine_topic_agreement_rate == 1.0
    assert "ziwei" not in metrics.failed_reasons
