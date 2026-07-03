from __future__ import annotations

from v30.api.app import _thinking_summary_required_unavailable_call
from v30.llm.acceptance import validate_thinking_step_summary_text
from v30.llm.client import (
    _central_brain_review_thinking_derivation,
    _normalize_thinking_derivation_text,
    _thinking_derivation_from_payload,
    _thinking_acceptance_hard_failures,
)


def test_central_brain_cleans_and_adopts_nonempty_llm_derivation() -> None:
    step = {
        "step_id": "rule_matching",
        "analysis_result": {
            "conclusion": "结论：规则命中集中在官印相生与食伤生财，主线是压力先转资质，再通过输出带动财务。",
            "next_focus": "建议：先确认职责边界和输出成果，不宜同时追求多条赚钱路径。",
            "user_summary": "规则页已定位官印相生、食伤生财和财星透出的组合。",
            "public_trace": [
                {"label": "匹配规则", "text": "官印相生、食伤生财、财星透出"},
                {"label": "测算作用", "text": "把规则命中转成事业与财务的取舍依据。"},
            ],
        },
        "summary_policy": {
            "signals": {
                "focus_scope": "stage_local",
                "prompt_profile": {"profile_id": "rule_matching.detail"},
            }
        },
    }
    derivation = {
        "text": "综合来看，当前阶段需要进一步分析。",
        "derived_conclusion": "",
        "derived_advice": "",
        "public_thinking_lines": [],
        "used_evidence": [],
        "uncertainty": [],
    }

    review = _central_brain_review_thinking_derivation(derivation, step)

    assert review["status"] == "accepted"
    assert review["adoption_mode"] == "central_brain_cleaned_llm_derivation"
    assert review["quality_gate"]["brain_judge_is_blocking"] is False
    assert review["failures"] == []
    assert "官印相生" in review["cleaned_stage_text"]
    assert "结论：" not in review["cleaned_stage_text"]
    assert "建议：" not in review["cleaned_stage_text"]
    assert not review["final_conclusion"].startswith("结论")
    assert not review["final_advice"].startswith("建议")
    assert review["stage_point_set"]["version"] == "v30.stage_point_set.v1"
    assert review["stage_points"]
    assert {row["kind"] for row in review["stage_points"]} >= {"verdict", "advice"}
    assert all("结论：" not in row["text"] and "建议：" not in row["text"] for row in review["stage_points"])
    assert "missing_derived_conclusion" in review["quality_notes"]


def test_central_brain_adopts_candidate_stage_points_from_llm_payload() -> None:
    step = {
        "step_id": "path_reasoning",
        "analysis_result": {
            "conclusion": "做功路径主线锁定为官杀转印，优先落点是事业。",
            "next_focus": "重点看压力能否被资质、平台和交付成果承接。",
            "public_trace": [
                {"label": "路径结论", "text": "官杀 -> 印星"},
                {"label": "测算作用", "text": "解释压力如何转成资质和平台。"},
            ],
        },
        "summary_policy": {
            "signals": {
                "focus_scope": "stage_local",
                "prompt_profile": {"profile_id": "path_reasoning.detail"},
            }
        },
    }
    derivation = _thinking_derivation_from_payload(
        {
            "public_derivation": [
                "官杀压力先进入印星，说明压力不是直接压身，而是要转成资质或平台。",
                "这条路径落到事业时，重点看职责是否能被可交付成果承接。",
            ],
            "candidate_points": [
                {
                    "kind": "verdict",
                    "text": "官杀转印是本页主路径，压力要先变成资质、规则或平台，才有稳定落点。",
                    "short_label": "官杀转印：压力转资质",
                    "bazi_terms": ["官杀", "印星", "做功路径"],
                    "macro_domains": ["career"],
                    "evidence_refs": ["路径结论：官杀 -> 印星"],
                },
                {
                    "kind": "advice",
                    "text": "事业判断先看职责能否沉淀成资质和交付成果，不宜只看岗位变化本身。",
                    "short_label": "先看职责承接",
                    "bazi_terms": ["官杀", "印星"],
                    "macro_domains": ["career"],
                    "evidence_refs": ["测算作用：解释压力如何转成资质和平台。"],
                },
            ],
            "used_evidence": ["路径结论：官杀 -> 印星"],
            "uncertainty": [],
        }
    )

    review = _central_brain_review_thinking_derivation(derivation, step)

    assert review["status"] == "accepted"
    assert review["candidate_failures"] == []
    assert review["stage_point_set"]["selected_count"] >= 2
    assert review["stage_points"][0]["kind"] == "verdict"
    assert review["stage_points"][0]["short_label"] == "官杀转印：压力转资质"
    assert review["stage_points"][0]["sidebar_visible"] is True


def test_central_brain_preserves_evidence_bound_branch_candidates() -> None:
    step = {
        "step_id": "useful_god_arbitration",
        "analysis_result": {
            "conclusion": "用神取向优先看土来承接官杀压力，火只作为调候辅助。",
            "next_focus": "先确认土能否承接财官，再看火是否过旺导致燥性上升。",
            "public_trace": [
                {"label": "用神取向", "text": "土承接为主，火调候为辅"},
                {"label": "忌避风险", "text": "火过旺会加重燥性"},
            ],
        },
        "summary_policy": {
            "signals": {
                "focus_scope": "stage_local",
                "prompt_profile": {"profile_id": "useful_god.detail"},
            }
        },
    }
    derivation = _thinking_derivation_from_payload(
        {
            "public_derivation": [
                "官杀压力需要先被土的承接路径稳定下来。",
                "火分支仍然保留，因为调候能改善寒暖，但火过旺会触发反证。",
            ],
            "candidate_points": [
                {
                    "kind": "branch",
                    "text": "用神取向有两条分支：土负责承接，火负责温煦；当前土的概率更高，因为路径证据更能承接官杀压力。",
                    "short_label": "土主火辅",
                    "bazi_terms": ["用神", "官杀", "土", "火"],
                    "macro_domains": ["career"],
                    "evidence_refs": ["用神取向：土承接为主，火调候为辅"],
                    "counter_refs": ["忌避风险：火过旺会加重燥性"],
                    "probability": 0.72,
                    "resolution_conditions": ["财官能被土承接则土升权", "火势过旺则火分支降权"],
                    "option_hints": [
                        {"label": "土为主", "value": "earth_primary"},
                        {"label": "火为辅", "value": "fire_secondary"},
                    ],
                },
                {
                    "kind": "advice",
                    "text": "命理师复核时先选土能否承接，再判断火是否只是辅助调候。",
                    "short_label": "先看土承接",
                    "bazi_terms": ["用神", "土", "火"],
                    "evidence_refs": ["用神取向：土承接为主，火调候为辅"],
                },
            ],
            "used_evidence": ["用神取向：土承接为主，火调候为辅"],
            "uncertainty": ["火分支需要看寒暖和燥性反证"],
        }
    )

    review = _central_brain_review_thinking_derivation(derivation, step)

    assert review["status"] == "accepted"
    assert "土" in review["final_conclusion"]
    branch = next(row for row in review["stage_point_set"]["points"] if row["kind"] == "branch")
    assert "两条分支" in branch["text"]
    assert branch["kind_label"] == "枝"
    assert branch["branch_probability"] == 0.72
    assert branch["resolution_conditions"]
    assert branch["option_hints"]
    assert "branch_probability_calibration" in branch["training_tags"]


def test_thinking_acceptance_allows_evidence_bound_uncertainty() -> None:
    prompt_request = {
        "prompt_contract": {},
        "context_pack": {
            "context_pack": "ThinkingStageContext",
            "role_contract": {"diagnostics_visible": False},
            "output_policy": {"max_chars": 560, "forbidden_tokens": []},
            "fact_boundary": {"chart_fact_mutation_allowed": False},
            "stage": {"step_id": "useful_god_arbitration"},
        },
        "raw_runtime_payload_included": False,
    }
    accepted = validate_thinking_step_summary_text(
        "用神候选有土火两条分支，土的置信更高，因为官杀压力需要承接；若火势过旺，火分支要降权。",
        prompt_request=prompt_request,
    )
    rejected = validate_thinking_step_summary_text(
        "可能还不好说，后续再看，仅供参考。",
        prompt_request=prompt_request,
    )

    assert accepted["accepted"] is True
    assert accepted["failures"] == []
    assert rejected["accepted"] is False
    assert "unbound_uncertainty_language" in rejected["failures"] or "generic_or_process_filler_language" in rejected["failures"]


def test_thinking_summary_hard_boundary_and_unavailable_are_separate() -> None:
    hard_failures = _thinking_acceptance_hard_failures(
        {
            "failures": [
                "generic_or_process_filler_language",
                "template_like_opening",
                "internal_identifier:v30.",
                "high_risk_fixed_verdict",
            ]
        }
    )
    assert hard_failures == ["internal_identifier:v30.", "high_risk_fixed_verdict"]

    policy = {"llm_enhancement": "auto"}
    hard_boundary_call = {
        "status": "fallback",
        "fallback_reason": "thinking_summary_hard_boundary_failed",
        "executed": True,
    }
    unavailable_call = {
        "status": "fallback",
        "fallback_reason": "provider_not_ready",
        "executed": False,
    }

    assert _thinking_summary_required_unavailable_call(hard_boundary_call, policy)["status"] == "fallback"
    converted = _thinking_summary_required_unavailable_call(unavailable_call, policy)
    assert converted["status"] == "unavailable"
    assert converted["user_message"].startswith("本页需要大模型推演")


def test_thinking_derivation_normalization_removes_orphan_leading_particle() -> None:
    assert _normalize_thinking_derivation_text("当前的命理判断必须以结构主线为纲") == "命理判断必须以结构主线为纲"
