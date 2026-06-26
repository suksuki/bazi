from __future__ import annotations

from v30.presentation.client_model import _customer_answer_panel
from v30.presentation import build_presentation_model
from v30.presentation import build_role_locale_client_projection_matrix
from v30.runtime import create_smoke_runtime


def test_presentation_localizes_runtime_controlled_labels() -> None:
    runtime = create_smoke_runtime("i18n-reading")
    en = build_presentation_model(runtime, locale="en", client="web").model_dump(mode="json")
    ko = build_presentation_model(runtime, locale="ko", client="web").model_dump(mode="json")
    zh = build_presentation_model(runtime, locale="zh", client="web").model_dump(mode="json")

    assert en["header"]["title"] == "Qiazhi V30"
    assert ko["header"]["title"] == "치지 V30"
    assert zh["header"]["title"] == "启智 V30"
    en_career = next(question for question in en["questions"] if question["question_id"] == "q_v30_user_career_direction")
    ko_career = next(question for question in ko["questions"] if question["question_id"] == "q_v30_user_career_direction")
    zh_career = next(question for question in zh["questions"] if question["question_id"] == "q_v30_user_career_direction")
    assert en_career["topic_label"] == "Career"
    assert en["questions"][0]["interaction_type"] == "user_question"
    assert en["questions"][0]["label_source"] == "expression_rendered_question_label"
    assert en["questions"][0]["label"] != runtime.question_anchors[0].why_this_question
    assert ko_career["topic_label"] == "커리어"
    assert zh_career["topic_label"] == "事业"
    assert zh["layout"]["rendered_question_label_summary"]["fallback_count"] == 0


def test_mobile_projection_is_compact_and_action_light() -> None:
    runtime = create_smoke_runtime("mobile-reading")
    payload = build_presentation_model(runtime, locale="zh", client="mobile").model_dump(mode="json")
    assert payload["layout"]["density"] == "compact"
    assert payload["layout"]["portrait_projection_view_summary"]["clients"] == ["mobile"]
    assert len(payload["questions"]) == 3
    assert payload["questions"][0]["answer_mode"] == "direct_answer"
    assert payload["questions"][0]["interaction_type"] == "user_question"
    assert len(payload["questions"][0]["label"]) <= 44
    assert payload["questions"][0]["label_boundary"] == "question_label_is_presentation_text_not_chart_fact"
    assert payload["questions"][0]["reasons"] == []
    assert [action["type"] for action in payload["actions"]] == ["submit_answer"]
    assert payload["diagnostics"] == {}


def test_customer_reading_surface_hides_internal_bazi_context() -> None:
    runtime = create_smoke_runtime("customer-surface-reading")
    payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")

    assert payload["reading_surface"]["surface_type"] == "customer_reading_loop"
    assert payload["reading_surface"]["next_question"]["expected_information_gain"]["primary_gain"]
    assert payload["reading_surface"]["next_question"]["options"]
    assert payload["reading_surface"]["options"] == payload["reading_surface"]["next_question"]["options"][:4]
    assert payload["reading_surface"]["interaction_goal"] == "ask_high_value_question_then_refresh_context"
    assert payload["reading_surface"]["internal_context_visible"] is False
    assert payload["projection_contract"]["version"] == "v30.api_projection_contract.v1"
    assert payload["projection_contract"]["customer_surface_order"][:2] == ["core_bazi_reading", "domain_cards"]
    assert payload["projection_contract"]["core_first_projection"]["version"] == "v30.core_first_projection.v1"
    assert payload["projection_contract"]["core_first_projection"]["calculation_before_questions"] is True
    assert payload["projection_contract"]["core_first_projection"]["required_surface_prefix"] == [
        "core_bazi_reading",
        "domain_cards",
    ]
    assert payload["projection_contract"]["customer_surface_contract"]["version"] == "v30.customer_surface_contract.v1"
    assert payload["projection_contract"]["customer_surface_contract"]["surface_prefix_ready"] is True
    assert {"reading_surface", "core_bazi_reading", "domain_cards", "questions", "answer_panel", "diagnostics"} <= set(
        payload["projection_contract"]["additive_api_policy"]["must_preserve"]
    )
    assert {"internal_next_question_id", "actor_context", "llm_runtime_status"} <= set(
        payload["projection_contract"]["additive_api_policy"]["must_preserve"]
    )
    assert {"raw_score", "raw_weight", "training_signal", "policy_effect"} <= set(
        payload["projection_contract"]["customer_forbidden_fields"]["fields"]
    )
    assert payload["projection_contract"]["role_visibility_matrix"]["user"]["diagnostics_visible"] is False
    assert payload["projection_contract"]["role_visibility_matrix"]["admin"]["diagnostics_visible"] is True
    assert payload["projection_contract"]["leak_scan"]["passed"] is True
    assert payload["projection_contract"]["leak_scan"]["diagnostics_hidden"] is True
    assert payload["projection_contract"]["leak_scan"]["forbidden_token_hits"] == []
    assert payload["reading_surface"]["reading_summary"]["primary_message"]
    assert payload["reading_surface"]["core_bazi_reading"]["version"] == "v30.core_bazi_reading.v1"
    assert payload["reading_surface"]["core_bazi_reading"]["surface_type"] == "core_bazi_calculation"


    assert payload["reading_surface"]["core_bazi_reading"]["fact_integrity"]["deterministic"] is True
    assert payload["reading_surface"]["core_bazi_reading"]["fact_integrity"]["llm_generated"] is False
    assert payload["reading_surface"]["core_bazi_reading"]["fact_integrity"]["training_generated"] is False
    assert payload["reading_surface"]["core_bazi_reading"]["base_fact_summary"]["version"] == "v30.base_bazi_fact_summary.v1"
    assert len(payload["reading_surface"]["basic_assertions"]) >= 5
    assert payload["reading_surface"]["basic_assertions"] == payload["reading_surface"]["core_bazi_reading"]["basic_assertions"]
    assertion_kinds = {row["kind"] for row in payload["reading_surface"]["basic_assertions"]}
    assert {
        "day_master_assertion",
        "strength_assertion",
        "structure_assertion",
        "useful_god_direction",
        "current_luck_flow_assertion",
        "risk_boundary",
    } <= assertion_kinds
    assert all(row["assertion"] and row["evidence"] for row in payload["reading_surface"]["basic_assertions"])
    assert all(row["boundary"] for row in payload["reading_surface"]["basic_assertions"])
    assert len(payload["reading_surface"]["bazi_features"]) >= 5
    assert len(payload["reading_surface"]["bazi_portraits"]) >= 5
    assert all(row["statement"] and row["evidence_labels"] for row in payload["reading_surface"]["bazi_features"])
    assert all(row["statement"] and row["evidence_labels"] for row in payload["reading_surface"]["bazi_portraits"])
    assert "feature_id" not in str(payload["reading_surface"]["bazi_features"])
    assert "portrait_id" not in str(payload["reading_surface"]["bazi_portraits"])
    assert "v30.krp." not in str(payload["reading_surface"]["bazi_features"])
    assert "v30.krp." not in str(payload["reading_surface"]["bazi_portraits"])
    assert "season=" not in str(payload["reading_surface"]["bazi_features"])
    assert "strongest=" not in str(payload["reading_surface"]["bazi_features"])
    assert len(payload["reading_surface"]["bazi_paths"]) >= 3
    assert all(row["path_label"] and row["meaning"] for row in payload["reading_surface"]["bazi_paths"])
    assert all(row["domain_impact"] and row["uncertainty_boundary"] for row in payload["reading_surface"]["bazi_paths"])
    assert all(row["boundary"] == "dynamic_path_is_context_for_structure_review_not_final_verdict" for row in payload["reading_surface"]["bazi_paths"])
    assert "score" not in str(payload["reading_surface"]["bazi_paths"])
    completion = payload["reading_surface"]["core_bazi_reading"]["m1_m2_completion_summary"]
    assert completion["version"] == "v30.m1_m2_completion_summary.v1"
    assert completion["status"] == "ready"
    assert completion["required_key_coverage"] == 1.0
    assert completion["explanation_coverage"] == 1.0
    assert completion["downstream_consumption_ready"] is True
    assert completion["m5_uses_root_fact_summary_count"] >= 3
    assert completion["m6_uses_m1_m2_fact_count"] >= 5
    assert completion["chart_fact_mutation_allowed"] is False
    explanations = payload["reading_surface"]["core_bazi_reading"]["base_fact_explanations"]
    assert explanations["version"] == "v30.base_bazi_fact_explanations.v1"
    assert explanations["day_master"]["value"] == runtime.chart_context.day_master
    assert explanations["ten_gods"]["visible_count"] > 0
    assert explanations["five_elements"]["strongest_elements"]
    assert explanations["relations"]["relation_count"] >= 0
    assert explanations["roots_and_vaults"]["same_element_root_count"] >= explanations["roots_and_vaults"]["day_master_root_count"]
    assert explanations["boundary"] == "base_fact_explanations_are_deterministic_context_not_ranked_decisions"
    assert len(payload["reading_surface"]["core_bazi_reading"]["four_pillars"]) == 4
    assert all(row["pillar"] for row in payload["reading_surface"]["core_bazi_reading"]["four_pillars"])
    assert payload["reading_surface"]["core_bazi_reading"]["day_master"] == runtime.chart_context.day_master
    assert payload["reading_surface"]["core_bazi_reading"]["visible_ten_gods"][0]["ten_god"]
    assert payload["reading_surface"]["core_bazi_reading"]["five_elements"]
    assert set(payload["reading_surface"]["core_bazi_reading"]["ranked_decisions"]) >= {
        "strength",
        "structure_pattern",
        "useful_god",
    }
    assert payload["reading_surface"]["domain_cards"]
    assert payload["reading_surface"]["domain_cards"][0]["customer_takeaway"]
    assert payload["reading_surface"]["domain_cards"][0]["path_summary"]
    assert payload["reading_surface"]["domain_cards"][0]["path_assertions"]
    assert payload["reading_surface"]["domain_cards"][0]["boundary"] == "domain_card_is_customer_projection_not_internal_bazi_context"
    structure_dynamics = payload["reading_surface"]["structure_dynamics"]
    assert structure_dynamics["version"] == "v30.structure_dynamics_surface.v1"
    assert structure_dynamics["dynamic_path_count"] >= 0
    assert structure_dynamics["visible_detail_level"] == "customer_summary"
    assert structure_dynamics["boundary"] == "structure_dynamics_projects_m3_dynamic_paths_as_reading_context_not_fixed_geju_or_event_verdict"
    assert "path_scores" not in str(structure_dynamics)
    assert "raw_score" not in str(structure_dynamics)
    assert payload["structure_card"]["state"] == "internal_context"
    assert payload["structure_card"]["confidence"] is None
    assert payload["mainline_card"]["why_selected"] == ""
    assert payload["chart_summary"]["six_pillar_context"] == {}
    assert payload["diagnostics"] == {}
    rendered = str(payload["reading_surface"])
    assert "ten_god_energy_model" not in rendered
    assert "feature_evidence_count" not in rendered
    assert "feature_evidence" not in rendered
    assert "path_scores" not in rendered
    assert "raw_weight" not in rendered
    assert "raw_score" not in rendered


def test_customer_answer_panel_filters_internal_diagnostic_text() -> None:
    payload = _customer_answer_panel(
        {
            "question_id": "q_v30_user_career_direction",
            "text": "\n".join(
                [
                    "诊断复核：事业主线看官印相生，压力要转成资质、规则或平台承接。",
                    "基础判断：强弱取相对平衡为主。",
                    "路径复核：官杀 → 印星(事业,关系,用神)。",
                    "特征画像：特征=五行分布特征。",
                    "边界：证据数=25；不改四柱、大运、流年事实。",
                    "llm_bazi_answer_draft · LLM accepted",
                ]
            ),
            "evidence_ids": ["a", "b"],
            "llm_metadata": {"status": "accepted"},
        },
        {"basic_assertions": []},
    )

    assert payload["text"] == "事业主线看官印相生，压力要转成资质、规则或平台承接。"
    assert "诊断复核：" not in payload["text"]
    assert "基础判断：" not in payload["text"]
    assert "路径复核：" not in payload["text"]
    assert "特征画像：" not in payload["text"]
    assert "证据数=" not in payload["text"]
    assert "llm_bazi_answer_draft" not in payload["text"]
    assert payload["evidence_count"] == 2


def test_practitioner_projection_can_inspect_bazi_context_without_admin_actions() -> None:
    runtime = create_smoke_runtime("practitioner-surface-reading")
    payload = build_presentation_model(runtime, role_key="practitioner", locale="zh", client="web").model_dump(mode="json")

    assert payload["layout"]["role_profile"]["surface"] == "practitioner_review"
    assert payload["layout"]["role_profile"]["diagnostics_visible"] is True
    assert payload["diagnostics"]["bazi_context"]["version"] == "v30.internal_bazi_context.v1"
    assert payload["reading_surface"]["internal_context_visible"] is True
    assert payload["reading_surface"]["role_contract"]["density"] == "evidence_chain"
    assert payload["projection_contract"]["diagnostics_visible"] is True
    assert payload["projection_contract"]["leak_scan"]["applies_to_customer_surface"] is False
    assert payload["structure_card"]["confidence"] is not None
    assert payload["reading_surface"]["bazi_features"][0]["feature_id"]
    assert payload["reading_surface"]["bazi_features"][0]["evidence_ids"]
    assert payload["reading_surface"]["bazi_portraits"][0]["portrait_id"]
    assert payload["reading_surface"]["bazi_portraits"][0]["evidence_ids"] or payload["reading_surface"]["bazi_portraits"][0]["path_ids"]
    assert payload["reading_surface"]["bazi_paths"][0]["score"] >= 0
    assert payload["reading_surface"]["bazi_paths"][0]["blocked_overclaim"]
    user_payload = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    assert payload["answer_panel"]["text"] != user_payload["answer_panel"]["text"]
    assert payload["answer_panel"]["text"].startswith("命理师复核口径：")
    assert payload["answer_panel"]["original_text"] == user_payload["answer_panel"]["text"]
    assert payload["answer_panel"]["role_adaptation"]["role_key"] == "practitioner"
    assert payload["answer_panel"]["role_adaptation"]["diagnostic_lines"]
    assert payload["answer_panel"]["role_adaptation"]["uses_bazi_paths"] is True
    assert "基础判断：" not in payload["answer_panel"]["text"]
    assert "路径复核：" not in payload["answer_panel"]["text"]
    assert "特征画像：" not in payload["answer_panel"]["text"]
    assert "证据数=" not in payload["answer_panel"]["text"]
    assert payload["reading_surface"]["structure_dynamics"]["visible_detail_level"] == "diagnostic"
    assert payload["mainline_card"]["why_selected"]
    assert [action["type"] for action in payload["actions"]] == ["submit_answer"]


def test_admin_projection_exposes_diagnostics_and_training_actions() -> None:
    runtime = create_smoke_runtime("admin-reading")
    payload = build_presentation_model(runtime, role_key="admin", locale="en", client="admin").model_dump(mode="json")
    assert payload["layout"]["density"] == "diagnostic"
    assert payload["layout"]["role_profile"]["surface"] == "operations"
    assert "run_training" in [action["type"] for action in payload["actions"]]
    assert "open_trace" in [action["type"] for action in payload["actions"]]
    assert "Run training" in [action["label"] for action in payload["actions"]]
    assert payload["diagnostics"]["trace_id"] == runtime.trace_id
    assert payload["projection_contract"]["diagnostics_visible"] is True
    assert payload["projection_contract"]["internal_visibility_policy"]["guest_user_diagnostics"] == "hidden"
    assert payload["diagnostics"]["active_policy_versions"]
    assert payload["diagnostics"]["ten_god_energy_model"]["status"] == "ready"
    assert payload["diagnostics"]["ten_god_energy_summary"]["top_energy"]
    assert payload["diagnostics"]["llm_runtime_status"]["version"] == "v30.llm_runtime_status.v1"
    assert payload["diagnostics"]["llm_runtime_status"]["call_status"] in {"accepted", "fallback", "deferred", "not_called"}
    assert payload["diagnostics"]["hidden_factor_probe_count"] == 1
    assert payload["diagnostics"]["knowledge_rule_portrait_signal_count"] >= 3
    assert payload["diagnostics"]["macro_portrait_view_summary"]["roles"] == ["admin"]
    assert payload["diagnostics"]["rendered_question_label_summary"]["roles"] == ["admin"]
    assert payload["diagnostics"]["rendered_question_label_summary"]["fallback_count"] == 0
    assert payload["diagnostics"]["rendered_question_label_summary"]["forbidden_token_hits"] == []
    assert payload["diagnostics"]["rendered_question_labels"]
    forbidden = {"policy_effect", "question_policy", "dynamic_graph", "evidence-bound", "Current chart", "Quality gate"}
    assert not any(
        token in question["label"]
        for question in payload["questions"]
        for token in forbidden
    )
    assert payload["diagnostics"]["macro_portrait_view_summary"]["hidden_factor_view_count"] >= 1
    assert all(
        row["visibility"] == "diagnostic"
        for row in payload["diagnostics"]["macro_portrait_projection_views"]
    )


def test_role_locale_client_projection_matrix_is_contract_shaped() -> None:
    runtime = create_smoke_runtime("projection-matrix-reading")
    matrix = build_role_locale_client_projection_matrix(runtime)

    assert matrix["version"] == "v30.role_locale_client_projection_matrix.v1"
    assert set(matrix["roles"]) >= {"guest", "user", "practitioner", "analyst", "admin", "lab"}
    assert set(matrix["locales"]) == {"zh", "en", "ko"}
    assert set(matrix["clients"]) >= {"web", "mobile", "admin", "lab"}
    assert matrix["combination_count"] >= 72
    assert set(matrix["sampled_roles"]) >= {"guest", "user", "admin", "lab"}
    assert set(matrix["sampled_locales"]) == {"zh", "en", "ko"}
    assert set(matrix["sampled_clients"]) >= {"web", "mobile", "admin", "lab"}
    assert "admin" in matrix["diagnostic_roles"]
    assert "mobile" in matrix["compact_clients"]
    assert matrix["boundary"] == "role_locale_client_projection_changes_visibility_language_density_not_chart_fact"
