from __future__ import annotations

from v20.access.projection import project_runtime_for_role
from v20.access.roles import access_role_manifest
from v20.api.runtime import run_runtime_from_pillars
from v20.role_view.projection import apply_role_answer_view, build_role_view_model


def test_v20_access_roles_define_projected_runtime_fields() -> None:
    manifest = access_role_manifest()
    roles = {row["role_key"]: row for row in manifest["roles"]}

    assert {"guest", "user", "analyst", "lab", "admin"} <= set(roles)
    assert "answer_text" in roles["guest"]["allowed_runtime_fields"]
    assert "feature_layer" in roles["guest"]["blocked_runtime_fields"]
    assert "answer_text" in roles["user"]["allowed_runtime_fields"]
    assert "knowledge_refs" in roles["user"]["blocked_runtime_fields"]
    assert "decision_report" in roles["user"]["allowed_runtime_fields"]
    assert "bazi_context_frame" in roles["user"]["allowed_runtime_fields"]
    assert "context_alignment_report" in roles["user"]["allowed_runtime_fields"]
    assert "dynamic_portrait" not in roles["user"]["allowed_runtime_fields"]
    assert "question_intent_model" in roles["user"]["allowed_runtime_fields"]
    assert "next_question_plan" in roles["user"]["allowed_runtime_fields"]
    assert "interaction_session" in roles["user"]["allowed_runtime_fields"]
    assert "structure_dynamics" in roles["user"]["allowed_runtime_fields"]
    assert "mainline_arbitration" in roles["user"]["allowed_runtime_fields"]
    assert "reasoning_orchestrator" in roles["user"]["allowed_runtime_fields"]
    assert "brain_memory_signal" not in roles["user"]["allowed_runtime_fields"]
    assert "orchestrator_policy_pointer" in roles["user"]["allowed_runtime_fields"]
    assert "orchestrator_policy_observability" not in roles["user"]["allowed_runtime_fields"]
    assert "feature_layer" in roles["analyst"]["allowed_runtime_fields"]
    assert "knowledge_semantic_model" in roles["analyst"]["allowed_runtime_fields"]
    assert "decision_report" in roles["analyst"]["allowed_runtime_fields"]
    assert "decision_validation" in roles["analyst"]["allowed_runtime_fields"]
    assert "feature_state_model" in roles["analyst"]["allowed_runtime_fields"]
    assert "structure_dynamics" in roles["analyst"]["allowed_runtime_fields"]
    assert "mainline_arbitration" in roles["analyst"]["allowed_runtime_fields"]
    assert "reasoning_orchestrator" in roles["analyst"]["allowed_runtime_fields"]
    assert "brain_memory_signal" in roles["analyst"]["allowed_runtime_fields"]
    assert "orchestrator_policy_pointer" in roles["analyst"]["allowed_runtime_fields"]
    assert "orchestrator_policy_observability" in roles["analyst"]["allowed_runtime_fields"]
    assert "question_source_ranking_report" in roles["analyst"]["allowed_runtime_fields"]
    assert "next_question_plan" in roles["analyst"]["allowed_runtime_fields"]
    assert "question_intent_model" in roles["analyst"]["allowed_runtime_fields"]
    assert "interaction_session" in roles["analyst"]["allowed_runtime_fields"]
    assert "knowledge_refs" in roles["analyst"]["allowed_runtime_fields"]
    assert "practitioner_session" in roles["analyst"]["allowed_runtime_fields"]
    assert "practitioner_session" not in roles["user"]["allowed_runtime_fields"]
    assert "rule_candidate_support" not in roles["analyst"]["allowed_runtime_fields"]
    assert "decision_report" in roles["admin"]["allowed_runtime_fields"]
    assert "bazi_context_frame" in roles["admin"]["allowed_runtime_fields"]
    assert "context_alignment_report" in roles["admin"]["allowed_runtime_fields"]
    assert "structure_dynamics" in roles["admin"]["allowed_runtime_fields"]
    assert "mainline_arbitration" in roles["admin"]["allowed_runtime_fields"]
    assert "reasoning_orchestrator" in roles["admin"]["allowed_runtime_fields"]
    assert "brain_memory_signal" in roles["admin"]["allowed_runtime_fields"]
    assert "orchestrator_policy_pointer" in roles["admin"]["allowed_runtime_fields"]
    assert "next_question_plan" in roles["admin"]["allowed_runtime_fields"]
    assert "orchestrator_policy_observability" in roles["admin"]["allowed_runtime_fields"]
    assert "question_source_ranking_report" in roles["admin"]["allowed_runtime_fields"]
    assert "portrait_graph_summary" in roles["admin"]["allowed_runtime_fields"]
    assert "latent_signal_report" in roles["admin"]["allowed_runtime_fields"]
    assert "practitioner_session" in roles["admin"]["allowed_runtime_fields"]
    assert "chart_graph" in roles["lab"]["allowed_runtime_fields"]
    assert manifest["runtime_mutation"] is False


def test_v20_user_projection_hides_internal_evidence_and_graphs() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="access.user",
        user_text="我想看流年触发",
        flow_year_pillar="庚子",
    )
    projected = project_runtime_for_role(result, "user")

    assert projected["role"]["role_key"] == "user"
    assert "answer_text" in projected
    assert projected["answer_text"].startswith("用户解读：")
    assert projected["role_answer_profile"]["explanation_style"] == "guided_plain_language"
    assert "feature_layer" not in projected
    assert "knowledge_refs" not in projected
    assert "rule_candidate_support" not in projected
    assert "rule_candidate_validation" not in projected
    assert "chart_graph" not in projected
    assert "decision_report" in projected
    assert "dynamic_portrait" not in projected
    assert "portrait_projection" not in projected["decision_report"]
    assert "defeasible_decision_model" not in projected["decision_report"]
    assert "rule_runtime_report" not in projected["decision_report"]
    assert "decisions" not in projected["decision_report"]
    assert "question_intent_model" in projected
    assert "interaction_session" in projected
    assert "structure_dynamics" in projected
    assert "mainline_arbitration" in projected
    assert "reasoning_orchestrator" in projected
    assert "practitioner_session" not in projected
    assert "orchestrator_policy_observability" not in projected
    assert projected["role_view_model"]["role_key"] == "user"
    assert projected["role_view_model"]["policy_version"] == "v20.role_view_policy.v1"
    assert projected["role_view_model"]["context_binding"]["context_id"] == projected["bazi_context_frame"]["context_id"]
    assert projected["role_view_model"]["portrait_profile"]["context_binding"]["context_id"] == projected["bazi_context_frame"]["context_id"]
    assert projected["role_view_model"]["question_profile"]["context_binding"]["context_id"] == projected["bazi_context_frame"]["context_id"]
    assert projected["role_view_model"]["portrait_profile"]["depth"] == "guided_summary"
    assert projected["role_view_model"]["explanation_profile"]["style"] == "guided_plain_language"
    assert projected["role_view_model"]["answer_governance_profile"]["version"] == "v20.role_answer_governance_profile.v1"
    assert projected["role_answer_profile"]["answer_governance_profile"]["style_policy"]
    assert projected["role_view_model"]["visibility_profile"]["level"] == "public_guided"
    assert all("source_feature_ids" not in row for row in projected["questions"])
    assert all("source_rule_key" not in row for row in projected["questions"])
    assert all("question_strategy" in row for row in projected["questions"])
    assert all(row["display_title"] for row in projected["questions"])
    assert all(row["question_anchor"]["anchor_status"] == "bound" for row in projected["questions"])
    assert all(row["question_anchor"]["day_master"] == projected["bazi_context_frame"]["day_master"] for row in projected["questions"])
    assert all("question_seeds" not in row for row in projected["questions"])
    forbidden_question_fragments = ("先扶身", "先泄秀", "扶身还是", "泄秀还是", "扶身、通关、调候")
    assert all(
        fragment not in row["title"]
        for row in projected["questions"]
        for fragment in forbidden_question_fragments
    )
    assert all(row["question_narrative"]["voice_profile"] == "user_guided_reading" for row in projected["questions"])
    assert all(row["question_narrative"]["why_now"] for row in projected["questions"])
    assert all(row["role_view_level"] == "guided" for row in projected["questions"])
    assert "source_feature_ids" not in projected["selected_question"]
    assert "source_rule_key" not in projected["selected_question"]
    assert projected["selected_question"]["display_title"]
    assert projected["selected_question"]["question_anchor"]["context_id"] == projected["bazi_context_frame"]["context_id"]
    assert projected["selected_question"]["question_narrative"]["voice_profile"] == "user_guided_reading"
    assert all("source_feature_ids" not in row for row in projected["measurement_report"]["topics"])


def test_v20_role_answer_projection_can_label_stream_source() -> None:
    projected = apply_role_answer_view(
        {"answer_text": "事业先看官杀和食伤。"},
        "user",
        {"explanation_profile": {"style": "guided_plain_language"}},
        source_answer="stream_practitioner_answer_text",
    )

    assert projected["answer_text"].startswith("用户解读：")
    assert projected["role_answer_profile"]["source_answer"] == "stream_practitioner_answer_text"


def test_v20_role_answer_projection_consumes_runtime_governance_weight() -> None:
    runtime_pointer = {
        "runtime_answer_governance_applied": True,
        "policy_payload": {
            "answer_governance_style_policy": [
                {
                    "source_role": "user",
                    "style_policy": "preserve_guided_boundary",
                    "style_weight_delta": 0.012,
                    "runtime_allowed": True,
                }
            ]
        },
    }
    result = {
        "llm_assist": {
            "answer_safety_review": {
                "answer_governance_quality": {
                    "quality_score": 1.0,
                    "quality_band": "strong",
                    "dimensions": {
                        "boundary_hint": 1.0,
                        "evidence_language": 1.0,
                        "review_or_counterevidence": 1.0,
                        "next_step_guidance": 1.0,
                    },
                }
            }
        },
        "decision_report": {"portrait_projection": {"axes": []}},
    }
    model = build_role_view_model(result, "user", runtime_pointer=runtime_pointer)
    projected = apply_role_answer_view(
        {"answer_text": "当前命局可见：财星需要结合日主承载复核。边界：只说明结构。"},
        "user",
        model,
    )

    governance = projected["role_answer_profile"]["answer_governance_profile"]
    assert governance["runtime_style_policy_applied"] is True
    assert governance["runtime_style_weight_delta"] == 0.012
    assert projected["answer_text"].startswith("用户解读：")
    assert "训练策略" in projected["answer_text"]


def test_v20_role_measure_view_projects_by_role() -> None:
    result = run_runtime_from_pillars(
        "甲子",
        "戊辰",
        "甲午",
        "辛酉",
        input_id="access.role_view",
        user_text="我想看流年触发",
        flow_year_pillar="庚子",
    )
    user = project_runtime_for_role(result, "user")
    guest = project_runtime_for_role(result, "guest")
    analyst = project_runtime_for_role(result, "analyst")
    admin = project_runtime_for_role(result, "admin")
    roles = access_role_manifest()

    assert guest["role"]["role_key"] == "guest"
    assert guest["role_view_model"]["portrait_profile"]["depth"] == "entry_overview"
    assert guest["role_view_model"]["explanation_profile"]["style"] == "plain_entry"
    assert guest["role_view_model"]["visibility_profile"]["level"] == "public_entry"
    assert len(guest["questions"]) <= 3
    assert guest["questions"][0]["title"] != user["questions"][0]["title"]
    assert guest["role_view_model"]["question_profile"]["voice_profile"] == "guest_soft_entry"
    assert user["role_view_model"]["question_profile"]["voice_profile"] == "user_guided_reading"
    assert analyst["role_view_model"]["question_profile"]["voice_profile"] == "practitioner_evidence_review"
    assert guest["questions"][0]["question_narrative"]["voice_profile"] == "guest_soft_entry"
    assert user["questions"][0]["question_narrative"]["why_now"]
    assert analyst["questions"][0]["question_narrative"]["boundary"]
    assert "source_title" not in guest["questions"][0]
    assert "source_decision_key" not in guest["questions"][0]
    assert "source_title" not in guest["selected_question"]
    assert "source_feature_ids" not in guest["selected_question"]
    assert "feature_layer" not in guest
    assert guest["answer_text"].startswith("游客简读：")
    assert "阅读边界" in guest["answer_text"]
    assert "answer_governance_quality" not in guest["answer_text"]
    assert guest["role_answer_profile"]["explanation_style"] == "plain_entry"
    assert guest["role_answer_profile"]["answer_governance_profile"]["boundary_density"] == "plain_boundary"
    assert user["role"]["role_key"] == "user"
    assert user["role_view_model"]["question_profile"]["style"] == "guided_questions"
    assert user["answer_text"].startswith("用户解读：")
    assert "回答策略" in user["answer_text"]
    assert "feature_layer" not in user
    assert analyst["role"]["role_key"] == "analyst"
    assert analyst["role_view_model"]["question_profile"]["style"] == "review_questions"
    assert analyst["answer_text"].startswith("命理师复核：")
    assert analyst["role_answer_profile"]["explanation_style"] == "technical_review"
    assert analyst["role_answer_profile"]["answer_governance_profile"]["boundary_density"] == "technical_boundary_review"
    assert "治理复核" in analyst["answer_text"]
    assert analyst["questions"][0]["title"].startswith("证据检查：")
    assert "feature_layer" in analyst
    assert "knowledge_semantic_model" in analyst
    assert "decision_validation" in analyst
    assert "feature_state_model" in analyst
    assert "question_intent_model" in analyst
    assert "interaction_session" in analyst
    assert "knowledge_refs" in analyst
    assert "dynamic_portrait" not in analyst
    assert "practitioner_session" in analyst
    assert admin["role"]["role_key"] == "admin"
    assert admin["role_view_model"]["portrait_profile"]["depth"] == "full_observation"
    assert admin["answer_text"].startswith("系统观测：")
    assert "answer_governance_quality" in admin["answer_text"]
    assert "decision_report" in admin
    assert "portrait_graph_summary" in admin
    assert "feature_state_model" in admin
    assert "question_intent_model" in admin
    assert "knowledge_refs" in admin
    assert "practitioner_session" in admin
    assert roles["runtime_mutation"] is False
