from __future__ import annotations

from v20.access.roles import role_policy


def project_runtime_for_role(result: dict[str, object], role_key: str) -> dict[str, object]:
    policy = role_policy(role_key)
    payload = {key: result[key] for key in policy.allowed_runtime_fields if key in result}
    if role_key == "user":
        payload = _sanitize_user_payload(payload)
    payload["version"] = "v20.role_runtime_view.v1"
    payload["role"] = policy.to_dict()
    payload["runtime_mutation"] = False
    payload["guardrails"] = list(payload.get("guardrails", ())) + [
        "ROLE_VIEW_PROJECTED_SERVER_SIDE",
        "BLOCKED_FIELDS_NOT_RENDERED",
    ]
    return payload


def _sanitize_user_payload(payload: dict[str, object]) -> dict[str, object]:
    sanitized = dict(payload)
    sanitized["questions"] = [
        {
            "question_key": row.get("question_key", ""),
            "title": row.get("title", ""),
            "domain": row.get("domain", ""),
            "score": row.get("score", 0),
            "measurement_topic": row.get("measurement_topic", ""),
            "measurement_stage": row.get("measurement_stage", ""),
            "role": row.get("role", ""),
        }
        for row in sanitized.get("questions", [])
        if isinstance(row, dict)
    ]
    if isinstance(sanitized.get("measurement_report"), dict):
        report = dict(sanitized["measurement_report"])
        report["topics"] = [
            {
                "topic_key": row.get("topic_key", ""),
                "label": row.get("label", ""),
                "stage": row.get("stage", ""),
                "status": row.get("status", ""),
                "confidence": row.get("confidence", 0),
                "question_keys": row.get("question_keys", ()),
                "boundary": row.get("boundary", ""),
                "role": row.get("role", ""),
            }
            for row in report.get("topics", [])
            if isinstance(row, dict)
        ]
        sanitized["measurement_report"] = report
    if isinstance(sanitized.get("portrait_projection"), dict):
        portrait = dict(sanitized["portrait_projection"])
        portrait["axes"] = [
            {
                "domain": row.get("domain", ""),
                "label": row.get("label", ""),
                "measurement_stage": row.get("measurement_stage", ""),
                "feature_count": row.get("feature_count", 0),
                "peak_confidence": row.get("peak_confidence", 0),
                "calibration_state": row.get("calibration_state", ""),
                "knowledge_ref_count": row.get("knowledge_ref_count", 0),
                "source_policy": row.get("source_policy", ""),
                "allowed_feedback_signals": row.get("allowed_feedback_signals", ()),
            }
            for row in portrait.get("axes", [])
            if isinstance(row, dict)
        ]
        portrait["items"] = [
            {
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "measurement_topic": row.get("measurement_topic", ""),
                "measurement_stage": row.get("measurement_stage", ""),
                "measurement_focus": row.get("measurement_focus", ""),
                "confidence": row.get("confidence", 0),
                "calibration_state": row.get("calibration_state", ""),
                "knowledge_ref_count": row.get("knowledge_ref_count", 0),
                "source_policy": row.get("source_policy", ""),
            }
            for row in portrait.get("items", [])
            if isinstance(row, dict)
        ]
        sanitized["portrait_projection"] = portrait
    return sanitized
