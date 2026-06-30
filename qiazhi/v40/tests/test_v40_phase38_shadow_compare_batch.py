from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from v40.api.app import API_PREFIX, create_app
from v40.contracts.base import ReleaseRecommendation
from v40.evaluation import build_shadow_compare_batch_summary, build_shadow_compare_result
from v40.migration import V30ExportEnvelope, build_runtime_from_v30_export


ROOT = Path(__file__).resolve().parents[1]
EXPORT_PATH = ROOT / "tests" / "fixtures" / "v30_export_minimal.json"


def _export(export_id: str, reading_id: str) -> V30ExportEnvelope:
    payload = json.loads(EXPORT_PATH.read_text(encoding="utf-8"))
    payload["export_id"] = export_id
    payload["reading_id"] = reading_id
    return V30ExportEnvelope.model_validate(payload)


def _compare(export_id: str, reading_id: str):
    envelope = _export(export_id, reading_id)
    runtime = build_runtime_from_v30_export(envelope)
    return build_shadow_compare_result(
        compare_id=f"compare.phase38.{export_id}",
        envelope=envelope,
        runtime_result=runtime,
    )


def test_shadow_compare_batch_summary_promotes_migration_risk_to_batch_level() -> None:
    compares = [
        _compare("export.phase38.001", "reading.phase38.001"),
        _compare("export.phase38.002", "reading.phase38.002"),
    ]

    summary = build_shadow_compare_batch_summary(
        batch_id="shadow.batch.phase38.unit.001",
        compares=compares,
    )

    assert summary.compare_count == 2
    assert summary.passed_count == 2
    assert summary.regression_count == 0
    assert summary.average_import_coverage_rate == 1.0
    assert summary.average_verdict_topic_overlap_rate == 1.0
    assert summary.product_projection_ready_rate == 1.0
    assert summary.recommendation == ReleaseRecommendation.APPROVE
    assert summary.writes_v30_state is False
    assert summary.writes_v40_production is False


def test_shadow_compare_batch_api_uses_plain_v30_exports_without_writes() -> None:
    client = TestClient(create_app())
    exports = [
        _export("export.phase38.api.001", "reading.phase38.api.001"),
        _export("export.phase38.api.002", "reading.phase38.api.002"),
    ]

    response = client.post(
        f"{API_PREFIX}/shadow-compare/batch",
        json={
            "batch_id": "shadow.batch.phase38.api.001",
            "exports": [export.model_dump(mode="json") for export in exports],
            "persist": False,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["summary"]["compare_count"] == 2
    assert body["summary"]["recommendation"] == "approve"
    assert len(body["compares"]) == 2
    assert body["persisted"] is False
    assert body["writes_v30_state"] is False
    assert body["writes_v40_production"] is False


def test_shadow_compare_batch_rejects_regression() -> None:
    regression = _compare("export.phase38.regression.001", "reading.phase38.regression.001")
    regression = regression.model_copy(
        update={
            "regression_detected": True,
            "failed_reasons": ["product_projection_not_ready"],
            "product_projection_ready": False,
        }
    )

    summary = build_shadow_compare_batch_summary(
        batch_id="shadow.batch.phase38.regression.001",
        compares=[regression],
    )

    assert summary.recommendation == ReleaseRecommendation.REJECT
    assert summary.regression_count == 1
    assert summary.failed_reason_counts["product_projection_not_ready"] >= 1


def test_phase38_shadow_compare_batch_contract_and_api_are_v40_only() -> None:
    manifest = Path("qiazhi/v40/v40/contracts/manifest.py").read_text(encoding="utf-8")
    app_source = Path("qiazhi/v40/v40/api/app.py").read_text(encoding="utf-8")
    models = Path("qiazhi/v40/v40/api/models.py").read_text(encoding="utf-8")
    shadow = Path("qiazhi/v40/v40/evaluation/shadow_compare.py").read_text(encoding="utf-8")

    assert "ShadowCompareBatchSummary" in manifest
    assert "/shadow-compare/batch" in app_source
    assert "ShadowCompareBatchRequest" in models
    assert "build_shadow_compare_batch_summary" in shadow
    assert "writes_v30_state" in app_source
    assert "import v30" not in shadow
    assert "v30.runtime" not in shadow
