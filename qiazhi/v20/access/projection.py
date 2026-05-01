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
    if isinstance(sanitized.get("feature_discovery"), dict):
        discovery = dict(sanitized["feature_discovery"])
        discovery["ranked_features"] = [
            {
                "title": row.get("title", ""),
                "domain": row.get("domain", ""),
                "domain_label": row.get("domain_label", ""),
                "measurement_stage": row.get("measurement_stage", ""),
                "discovery_score": row.get("discovery_score", 0),
                "summary": row.get("summary", ""),
                "reason": row.get("reason", ""),
                "boundary": row.get("boundary", ""),
            }
            for row in discovery.get("ranked_features", [])
            if isinstance(row, dict)
        ]
        discovery["domain_hypotheses"] = [
            {
                "domain": row.get("domain", ""),
                "label": row.get("label", ""),
                "measurement_stage": row.get("measurement_stage", ""),
                "discovery_score": row.get("discovery_score", 0),
                "feature_count": row.get("feature_count", 0),
                "related_feature_count": row.get("related_feature_count", 0),
                "knowledge_ref_count": row.get("knowledge_ref_count", 0),
                "interaction_match": row.get("interaction_match", False),
                "status": row.get("status", ""),
            }
            for row in discovery.get("domain_hypotheses", [])
            if isinstance(row, dict)
        ]
        training = discovery.get("training_signal", {})
        if isinstance(training, dict):
            discovery["training_signal"] = {
                "status": training.get("status", ""),
                "run_id": training.get("run_id", ""),
                "case_count": training.get("case_count", 0),
                "artifact_status": training.get("artifact_status", ""),
                "similarity_status": training.get("similarity_status", ""),
                "cluster_count": training.get("cluster_count", 0),
                "training_tracks": training.get("training_tracks", ()),
                "runtime_mutation": False,
            }
        discovery.pop("question_policy", None)
        discovery["guardrails"] = [
            "USER_VIEW_SANITIZED_FEATURE_DISCOVERY",
            "NO_INTERNAL_FEATURE_IDS_OR_POLICY_WEIGHTS",
        ]
        sanitized["feature_discovery"] = discovery
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
    if isinstance(sanitized.get("portrait_intelligence"), dict):
        intelligence = dict(sanitized["portrait_intelligence"])
        intelligence["axis_models"] = [
            {
                "domain": row.get("domain", ""),
                "label": row.get("label", ""),
                "measurement_stage": row.get("measurement_stage", ""),
                "intelligence_score": row.get("intelligence_score", 0),
                "feature_count": row.get("feature_count", 0),
                "knowledge_ref_count": row.get("knowledge_ref_count", 0),
                "sub_axis_candidates": [
                    {
                        "label": candidate.get("label", ""),
                        "domain": candidate.get("domain", ""),
                        "status": candidate.get("status", ""),
                    }
                    for candidate in row.get("sub_axis_candidates", [])
                    if isinstance(candidate, dict)
                ],
                "calibration_prompt": row.get("calibration_prompt", ""),
            }
            for row in intelligence.get("axis_models", [])
            if isinstance(row, dict)
        ]
        intelligence["profile_tags"] = [
            {
                "label": row.get("label", ""),
                "domain": row.get("domain", ""),
                "score": row.get("score", 0),
                "source": row.get("source", ""),
            }
            for row in intelligence.get("profile_tags", [])
            if isinstance(row, dict)
        ]
        intelligence["interaction_prompts"] = [
            {
                "domain": row.get("domain", ""),
                "label": row.get("label", ""),
                "prompt": row.get("prompt", ""),
            }
            for row in intelligence.get("interaction_prompts", [])
            if isinstance(row, dict)
        ]
        intelligence.pop("training_lane", None)
        intelligence["guardrails"] = [
            "USER_VIEW_SANITIZED_PORTRAIT_INTELLIGENCE",
            "NO_INTERNAL_FEATURE_IDS_OR_SOURCE_KNOWLEDGE_IDS",
        ]
        sanitized["portrait_intelligence"] = intelligence
    return sanitized
