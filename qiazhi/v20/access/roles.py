from __future__ import annotations

from v20.access.schema import AccessRolePolicy


ROLE_POLICIES = {
    "user": AccessRolePolicy(
        role_key="user",
        label="游客",
        purpose="Receives bounded Bazi measurement answers and safe topic/question context.",
        allowed_runtime_fields=(
            "version",
            "input_id",
            "locale",
            "selected_question",
            "measurement_report",
            "questions",
            "decision_report",
            "dynamic_portrait",
            "answer_text",
            "prediction_policy",
            "runtime_mutation",
            "guardrails",
        ),
        blocked_runtime_fields=(
            "chart_graph",
            "rule_paths",
            "knowledge_refs",
            "llm_capabilities",
            "storage_contract",
            "redis_contract",
        ),
    ),
    "analyst": AccessRolePolicy(
        role_key="analyst",
        label="命理师",
        purpose="Reviews current-chart decisions, dynamic portrait tags, knowledge alignment, LLM assist, and answer boundaries.",
        allowed_runtime_fields=(
            "version",
            "input_id",
            "locale",
            "chart_facts",
            "time_context",
            "core_inference",
            "feature_layer",
            "knowledge_report",
            "knowledge_alignment",
            "knowledge_semantic_model",
            "knowledge_semantic_validation",
            "decision_report",
            "decision_validation",
            "dynamic_portrait",
            "questions",
            "selected_question",
            "practitioner_session",
            "measurement_report",
            "answer_plan",
            "answer_text",
            "prediction_policy",
            "llm_assist",
            "runtime_mutation",
            "guardrails",
        ),
        blocked_runtime_fields=("llm_capabilities", "raw_private_feedback", "secret_config"),
    ),
    "lab": AccessRolePolicy(
        role_key="lab",
        label="实验室",
        purpose="Runs dry-run corpus, validation, and learning experiments without production promotion.",
        allowed_runtime_fields=(
            "version",
            "input_id",
            "locale",
            "chart_facts",
            "time_context",
            "core_inference",
            "chart_graph",
            "rule_paths",
            "feature_layer",
            "knowledge_report",
            "knowledge_alignment",
            "knowledge_semantic_model",
            "knowledge_semantic_validation",
            "decision_report",
            "decision_validation",
            "dynamic_portrait",
            "questions",
            "selected_question",
            "practitioner_session",
            "measurement_report",
            "answer_plan",
            "prediction_policy",
            "llm_capabilities",
            "llm_assist",
            "runtime_mutation",
            "guardrails",
        ),
        blocked_runtime_fields=("secret_config", "production_promotion_write"),
    ),
    "admin": AccessRolePolicy(
        role_key="admin",
        label="管理员",
        purpose="Views operational scope contracts and promotion guardrails; secrets remain hidden.",
        allowed_runtime_fields=(
            "version",
            "input_id",
            "locale",
            "selected_question",
            "measurement_report",
            "prediction_policy",
            "runtime_mutation",
            "guardrails",
        ),
        blocked_runtime_fields=("secret_config", "raw_private_feedback", "redis_ephemeral_values"),
    ),
}


def role_policy(role_key: str) -> AccessRolePolicy:
    try:
        return ROLE_POLICIES[role_key]
    except KeyError as exc:
        raise ValueError(f"Unknown V20 access role: {role_key}") from exc


def access_role_manifest() -> dict[str, object]:
    return {
        "version": "v20.access_role_manifest.v1",
        "roles": [policy.to_dict() for policy in ROLE_POLICIES.values()],
        "runtime_mutation": False,
        "guardrails": [
            "ACCESS_CONTRACT_ONLY",
            "AUTHENTICATION_LAYER_CAN_WRAP_THIS_POLICY",
            "NO_SECRET_VALUES_RENDERED",
        ],
    }
