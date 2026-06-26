from __future__ import annotations

from v20.api.schemas import FeedbackRequest
from v20.interaction.feedback_analysis import analyze_feedback
from v20.learning.registries import registry_manifest
from v20.server import app


def _endpoint(path: str, method: str = "GET"):
    method = method.upper()
    for route in app.routes:
        if getattr(route, "path", "") == path and method in getattr(route, "methods", set()):
            return route.endpoint
    raise AssertionError(f"route not found: {method} {path}")


def test_v20_registry_manifest_maps_learning_stores_without_connection() -> None:
    manifest = registry_manifest()
    registries = {row["registry_key"]: row for row in manifest["registries"]}

    assert {"DatasetRegistry", "ArtifactRegistry", "RunRegistry", "DecisionRegistry", "FeedbackLedger"} <= set(registries)
    assert registries["FeedbackLedger"]["postgres_table"] == "v20_feedback_ledger"
    assert manifest["runtime_mutation"] is False
    assert "NO_DATABASE_CONNECTION_ATTEMPTED" in manifest["guardrails"]


def test_v20_feedback_analysis_redacts_and_blocks_auto_runtime_override() -> None:
    report = analyze_feedback(
        input_id="feedback.case",
        source_role="user",
        feedback_text="姓名: 张三，我想看财运，电话 010-12345678，email me@example.com",
        feature_ids=("feature.wealth.material_available",),
    )
    text = str(report)

    assert report["runtime_mutation"] is False
    assert report["raw_feedback_retained"] is False
    assert "[email]" in report["redacted_summary"]
    assert "[number]" in report["redacted_summary"]
    assert "张三" not in text
    assert "me@example.com" not in text
    assert report["calibration_signals"][0]["feature_id"] == "feature.wealth.material_available"
    assert report["learning_proposal"]["status"] == "draft"
    assert "NO_AUTOMATIC_PROMOTION" in report["guardrails"]


def test_v20_feedback_and_registry_endpoints_are_read_only() -> None:
    registry = _endpoint("/api/v20/learning/registries")()
    feedback = _endpoint("/api/v20/feedback/analyze", "POST")(
        FeedbackRequest(
            input_id="feedback.endpoint",
            source_role="analyst",
            feedback_text="这个回答的用神边界需要更清楚",
            feature_ids=["feature.useful_god.evidence_gate"],
        )
    )

    assert registry["runtime_mutation"] is False
    assert feedback["runtime_mutation"] is False
    assert feedback["calibration_signals"][0]["source_role"] == "analyst"
    assert feedback["ledger_entry"]["decision_status"] == "recorded_only"
