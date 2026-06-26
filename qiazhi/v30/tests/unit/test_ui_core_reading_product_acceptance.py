from __future__ import annotations

from v30.validation.ui_core_reading_product_acceptance import (
    UI_CORE_READING_PRODUCT_ACCEPTANCE_VERSION,
    build_ui_core_reading_product_acceptance,
    run_ui_core_reading_product_acceptance,
)


def test_ui_r1_acceptance_records_current_product_blockers() -> None:
    result = run_ui_core_reading_product_acceptance(reading_id="ui-r1-current-product-blockers")

    assert result["version"] == UI_CORE_READING_PRODUCT_ACCEPTANCE_VERSION
    assert result["status"] == "completed"
    assert result["decision"]["audit_ready"] is True
    assert result["decision"]["product_reading_ready"] is True

    failed = set(result["decision"]["failed_check_ids"])
    assert "basic_assertions_present" not in failed
    assert "bazi_features_and_portraits_projected" not in failed
    assert "bazi_paths_projected_as_reading" not in failed
    assert "role_outputs_are_differentiated" not in failed
    assert "llm_context_pack_has_product_layers" not in failed


def test_ui_r1_acceptance_passes_with_product_ready_payload() -> None:
    user_view = _product_ready_view(role="user", answer_text="财务问题以财星、收入节奏和现金流风险为核心，先看财来财去再看投资边界。")
    practitioner_view = _product_ready_view(
        role="practitioner",
        answer_text="命理师复核：财富追问应落在财星通关、收入结构、现金流风险与分账边界，先核证据再给建议。",
    )
    result = build_ui_core_reading_product_acceptance(
        runtime_payload={
            "reading_id": "ui-r1-product-ready",
            "trace_id": "trace-ui-r1-product-ready",
            "chart_context": {"day_master": "庚", "natal_pillars": {"year": "庚午", "month": "戊寅", "day": "庚子", "hour": "戊子"}},
        },
        user_view=user_view,
        practitioner_view=practitioner_view,
        admin_view={
            "diagnostics": {
                "real_bazi_diagnosis": {
                    "claims": [{"id": "c1"}] * 8,
                    "portraits": [{"id": "p1"}] * 8,
                }
            }
        },
    )

    assert result["status"] == "completed"
    assert result["decision"]["product_reading_ready"] is True
    assert result["decision"]["failed_check_ids"] == []
    assert result["next_mainline_selection"]["task_id"] == "UI-R1.10"


def _product_ready_view(*, role: str, answer_text: str) -> dict[str, object]:
    return {
        "reading_surface": {
            "surface_type": f"{role}_reading",
            "reading_summary": "庚金日主坐子，月令寅木透戊，财官印关系需要按时序展开。",
            "core_bazi_reading": {
                "chart": {
                    "natal_pillars": {"year": "庚午", "month": "戊寅", "day": "庚子", "hour": "戊子"},
                    "day_master": "庚",
                },
                "time_context": {"current_luck_pillar": "甲戌", "flow_year_pillar": "丙午"},
                "basic_assertions": [
                    {"assertion": "日主庚金坐子，表达和变动线明显。", "evidence": "day_pillar"},
                    {"assertion": "月令寅木带出财星议题。", "evidence": "month_pillar"},
                    {"assertion": "丙午流年触发官杀压力。", "evidence": "flow_year"},
                ],
            },
            "basic_assertions": [
                {"assertion": "日主庚金坐子，表达和变动线明显。", "evidence": "day_pillar"},
                {"assertion": "月令寅木带出财星议题。", "evidence": "month_pillar"},
                {"assertion": "丙午流年触发官杀压力。", "evidence": "flow_year"},
            ],
            "domain_cards": [
                {"domain": "career", "diagnosis_summary": "事业看官杀压力与印星承接，适合职责清晰的路径。", "core_claim_quality": _quality()},
                {"domain": "wealth", "diagnosis_summary": "财富看财星被日主承接的能力，重收入结构和现金流节奏。", "core_claim_quality": _quality()},
                {"domain": "relationship", "diagnosis_summary": "关系看表达、边界和责任压力的同步变化。", "core_claim_quality": _quality()},
                {"domain": "health", "diagnosis_summary": "健康看火土压力下的作息和消耗管理。", "core_claim_quality": _quality()},
                {"domain": "timing", "diagnosis_summary": "时间看甲戌大运与丙午流年的触发顺序。", "core_claim_quality": _quality()},
            ],
            "bazi_features": [{"name": "财星显现"}, {"name": "官杀触发"}, {"name": "印星承接"}, {"name": "子午冲"}],
            "bazi_portraits": [{"name": "决策谨慎"}, {"name": "抗压强"}, {"name": "重边界"}, {"name": "现金流敏感"}],
            "bazi_paths": [
                {"meaning": "财星路径先看收入结构。", "domain_impact": "wealth"},
                {"meaning": "官杀路径先看职责压力。", "domain_impact": "career"},
                {"meaning": "印星路径先看资源承接。", "domain_impact": "support"},
            ],
            "next_question": {"question_id": "q_v30_user_wealth_tendency", "topic": "wealth"},
            "role_contract": {"role": role},
        },
        "answer_panel": {
            "question_id": "q_v30_user_wealth_tendency",
            "text": answer_text,
            "role_adaptation": {
                "role_key": role,
                "diagnostic_lines": ["基础判断：财星显现，官杀触发，印星承接。"] if role == "practitioner" else [],
            },
            "llm_metadata": {
                "context_pack_summary": {
                    "layers": [
                        "basic_assertions",
                        "domain_card",
                        "bazi_features",
                        "bazi_portraits",
                        "bazi_paths",
                        "time_context",
                        "role_contract",
                    ]
                }
            },
        },
    }


def _quality() -> dict[str, object]:
    return {
        "version": "v30.core_bazi_claim_quality.v1",
        "quality_ready": True,
        "uses_traceable_claims": True,
        "chart_fact_mutation_allowed": False,
        "fixed_event_prediction_allowed": False,
        "generic_language_hits": [],
    }
