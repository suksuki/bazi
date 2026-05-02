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
    if isinstance(sanitized.get("decision_report"), dict):
        report = dict(sanitized["decision_report"])
        report["hits"] = [
            {
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "score": row.get("score", 0),
                "evidence": row.get("evidence", ())[:4],
            }
            for row in report.get("hits", [])
            if isinstance(row, dict)
        ]
        report["decisions"] = [
            {
                "decision_key": row.get("decision_key", ""),
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "status": row.get("status", ""),
                "role": row.get("role", ""),
                "score": row.get("score", 0),
                "support": row.get("support", ())[:4],
                "weakening": row.get("weakening", ())[:3],
                "portrait_tags": row.get("portrait_tags", ())[:4],
                "question_seeds": row.get("question_seeds", ())[:3],
            }
            for row in report.get("decisions", [])
            if isinstance(row, dict)
        ]
        report["practitioner_controls"] = [
            {
                "control_key": row.get("control_key", ""),
                "label": row.get("label", ""),
                "options": row.get("options", ()),
                "default": row.get("default", ""),
                "ui_surface": row.get("ui_surface", ""),
            }
            for row in report.get("practitioner_controls", [])
            if isinstance(row, dict)
        ]
        if isinstance(report.get("portrait_projection"), dict):
            projection = dict(report["portrait_projection"])
            projection["axes"] = [
                {
                    "axis_id": row.get("axis_id", ""),
                    "domain": row.get("domain", ""),
                    "label": row.get("label", ""),
                    "measurement_stage": row.get("measurement_stage", ""),
                    "peak_confidence": row.get("peak_confidence", 0),
                    "calibration_state": row.get("calibration_state", ""),
                    "evidence_boundaries": row.get("evidence_boundaries", ())[:3],
                    "alignment_status": row.get("alignment_status", ""),
                }
                for row in projection.get("axes", [])
                if isinstance(row, dict)
            ]
            sanitized_projection = {
                "version": projection.get("version", ""),
                "status": projection.get("status", ""),
                "role": projection.get("role", ""),
                "axis_count": projection.get("axis_count", 0),
                "axes": projection["axes"],
                "runtime_mutation": False,
            }
            report["portrait_projection"] = sanitized_projection
        sanitized["decision_report"] = report
    if isinstance(sanitized.get("feature_state_model"), dict):
        model = dict(sanitized["feature_state_model"])
        model["states"] = []
        model["priority_features"] = [
            {
                "feature_id": row.get("feature_id", ""),
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "state": row.get("state", ""),
                "priority": row.get("priority", 0),
                "boundary": row.get("boundary", ""),
            }
            for row in model.get("priority_features", [])
            if isinstance(row, dict)
        ]
        sanitized["feature_state_model"] = model
    if isinstance(sanitized.get("question_intent_model"), dict):
        model = dict(sanitized["question_intent_model"])
        model["intents"] = []
        model["question_bindings"] = [
            {
                "question_key": row.get("question_key", ""),
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "primary_intent_type": row.get("primary_intent_type", ""),
                "intent_priority": row.get("intent_priority", 0),
            }
            for row in model.get("question_bindings", [])
            if isinstance(row, dict)
        ]
        sanitized["question_intent_model"] = model
    if isinstance(sanitized.get("interaction_session"), dict):
        session = dict(sanitized["interaction_session"])
        session["signals"] = [
            {
                "signal_type": row.get("signal_type", ""),
                "domain": row.get("domain", ""),
                "strength": row.get("strength", 0),
                "effect": row.get("effect", ""),
                "primary_intent_type": row.get("primary_intent_type", ""),
            }
            for row in session.get("signals", [])
            if isinstance(row, dict)
        ]
        sanitized["interaction_session"] = session
    return sanitized
