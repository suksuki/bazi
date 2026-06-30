from __future__ import annotations

import json
from pathlib import Path

import pytest

from v40.contracts import AssertionLevel, ReleaseRecommendation, Topic
from v40.evaluation import build_shadow_compare_result
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export


ROOT = Path(__file__).resolve().parents[1]


def _minimal_envelope() -> V30ExportEnvelope:
    payload = json.loads((ROOT / "tests" / "fixtures" / "v30_export_minimal.json").read_text(encoding="utf-8"))
    return V30ExportEnvelope.model_validate(payload)


def test_v30_json_export_imports_into_v40_runtime_contracts() -> None:
    envelope = _minimal_envelope()
    runtime = build_runtime_from_v30_export(envelope, role_key="user")

    assert runtime.reading_id == "v30-reading-career-001:v40-shadow"
    assert runtime.v30_runtime_imported is False
    assert runtime.signal_registry is not None
    assert len(runtime.signal_registry.signals) == 2
    assert runtime.signal_registry.signals[0].reading_id == runtime.reading_id
    assert runtime.verdicts[0].topic == Topic.CAREER
    assert runtime.verdicts[0].assertion_level == AssertionLevel.SUPPORTED
    assert runtime.advice_plans[0].source_verdict_ids == ["verdict.career.path"]
    assert runtime.product_projection is not None
    assert runtime.product_projection.leakage_scan_passed is True
    assert runtime.product_projection.verdict_cards[0].title == "事业适合先稳定承接压力，再逐步寻找突破。"
    assert runtime.product_projection.advice_cards[0].action_points


def test_shadow_compare_reports_import_coverage_without_writes() -> None:
    envelope = _minimal_envelope()
    runtime = build_runtime_from_v30_export(envelope, role_key="user")
    compare = build_shadow_compare_result(
        compare_id="compare-001",
        envelope=envelope,
        runtime_result=runtime,
    )

    assert compare.v30_signal_count == 2
    assert compare.v40_signal_count == 2
    assert compare.v30_verdict_count == 1
    assert compare.v40_verdict_count == 1
    assert compare.import_coverage_rate == 1.0
    assert compare.verdict_topic_overlap_rate == 1.0
    assert compare.product_projection_ready is True
    assert compare.leakage_free is True
    assert compare.regression_detected is False
    assert compare.recommendation == ReleaseRecommendation.NEEDS_REVIEW
    assert compare.writes_v30_state is False
    assert compare.writes_v40_production is False


def test_importer_downgrades_strong_verdict_without_evidence() -> None:
    envelope = V30ExportEnvelope(
        export_id="v30-export-no-evidence",
        reading_id="v30-reading-no-evidence",
        verdict_rows=[
            {
                "verdict_id": "verdict.no.evidence",
                "domain": "wealth",
                "headline": "财运一定会大涨",
                "assertion_level": "confirmed",
                "confidence": 0.9
            }
        ],
    )
    runtime = build_runtime_from_v30_export(envelope)

    assert runtime.verdicts[0].assertion_level == AssertionLevel.WEAK_CANDIDATE


def test_migration_envelope_rejects_raw_prior_runtime_references() -> None:
    with pytest.raises(ValueError, match="raw V30 runtime paths"):
        V30ExportEnvelope(
            export_id="bad-export",
            reading_id="bad-reading",
            raw_database_ref="postgresql://v30",
        )
