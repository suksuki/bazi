from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping

from v30.contracts import BirthInput
from v30.core.chart_context import build_chart_context_from_birth_input
from v30.presentation import build_presentation_model
from v30.runtime import create_runtime_from_context


UI_CORE_READING_PRODUCT_ACCEPTANCE_VERSION = "v30.ui_core_reading_product_acceptance.v1"

FORBIDDEN_GENERIC_TOKENS = (
    "Current chart",
    "supports strength and pattern candidate review",
    "可以进入具体问题",
    "仍按候选路径表达",
    "不做确定断语",
    "当前只作为候选路径",
    "系统会结合",
    "请补充",
    "fallback",
)

WEALTH_TOKENS = ("财", "财运", "财务", "收入", "赚钱", "风险", "现金流", "投资", "分账")
CAREER_TOKENS = ("事业", "岗位", "职责", "上级", "同事", "合作方", "升迁", "转型")

QUESTION_DOMAIN_BY_ID = {
    "q_v30_user_wealth_tendency": "wealth",
    "q_v30_user_career_focus": "career",
    "q_v30_user_relationship_pattern": "relationship",
    "q_v30_user_health_rhythm": "health",
    "q_v30_user_timing_window": "timing",
}


def run_ui_core_reading_product_acceptance(
    *,
    reading_id: str = "ui-review-20260613-001",
) -> dict[str, Any]:
    """Run the UI-R1.1 product-reading audit against a deterministic BirthInput case."""
    birth_input = BirthInput.model_validate(
        {
            "input_id": "ui-r1-canonical-solar-female",
            "calendar_type": "solar",
            "birth_date": "1990-02-04",
            "birth_time": "23:30",
            "timezone": "Asia/Shanghai",
            "birth_place": "Beijing",
            "gender": "female",
            "use_true_solar_time": False,
            "unknown_hour": False,
            "source": "ui_r1_acceptance",
        }
    )
    build = build_chart_context_from_birth_input(
        reading_id=reading_id,
        birth_input=birth_input,
        locale="zh",
        created_at=datetime(2026, 6, 13, tzinfo=timezone.utc),
    )
    if build.chart_context is None:
        return build_ui_core_reading_product_acceptance(
            runtime_payload={"reading_id": reading_id, "chart_build_status": build.status},
            user_view={},
            practitioner_view={},
            admin_view={"chart_build": build.model_dump(mode="json")},
        )
    runtime = create_runtime_from_context(build.chart_context, trace_suffix="ui-r1-product")
    user_view = build_presentation_model(runtime, role_key="user", locale="zh", client="web").model_dump(mode="json")
    practitioner_view = build_presentation_model(
        runtime,
        role_key="practitioner",
        locale="zh",
        client="web",
    ).model_dump(mode="json")
    admin_view = build_presentation_model(runtime, role_key="admin", locale="zh", client="admin").model_dump(mode="json")
    return build_ui_core_reading_product_acceptance(
        runtime_payload=runtime.model_dump(mode="json"),
        user_view=user_view,
        practitioner_view=practitioner_view,
        admin_view=admin_view,
    )


def build_ui_core_reading_product_acceptance(
    *,
    runtime_payload: Mapping[str, Any],
    user_view: Mapping[str, Any],
    practitioner_view: Mapping[str, Any],
    admin_view: Mapping[str, Any],
) -> dict[str, Any]:
    user_surface = _mapping(user_view.get("reading_surface"))
    practitioner_surface = _mapping(practitioner_view.get("reading_surface"))
    admin_diagnostics = _mapping(admin_view.get("diagnostics"))
    user_answer = _mapping(user_view.get("answer_panel"))
    practitioner_answer = _mapping(practitioner_view.get("answer_panel"))
    checks = _checks(
        runtime_payload=runtime_payload,
        user_surface=user_surface,
        practitioner_surface=practitioner_surface,
        admin_diagnostics=admin_diagnostics,
        user_answer=user_answer,
        practitioner_answer=practitioner_answer,
    )
    decision = _decision(checks)
    return {
        "version": UI_CORE_READING_PRODUCT_ACCEPTANCE_VERSION,
        "executed_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed",
        "task": {
            "task_id": "UI-R1.1",
            "title": "Product Reading Acceptance Audit",
            "scope": "normal UI reading must show calculation-backed Bazi assertions, features, portraits, paths, and role-aware answers",
        },
        "runtime_summary": {
            "reading_id": str(runtime_payload.get("reading_id") or ""),
            "trace_id": str(runtime_payload.get("trace_id") or ""),
            "answer_question_id": str(user_answer.get("question_id") or ""),
            "surface_type": str(user_surface.get("surface_type") or ""),
            "selected_domain": _selected_domain(user_surface, user_answer),
        },
        "checks": checks,
        "decision": decision,
        "policy_boundary": {
            "full_pytest_required": False,
            "synthetic_all_required": False,
            "full_518k_required": False,
            "llm_live_smoke_required": False,
            "chart_fact_mutation_allowed": False,
            "boundary": "ui_r1_acceptance_is_read_only_product_audit_not_pointer_promotion",
        },
        "next_mainline_selection": _next_selection(decision),
        "boundary": "ui_r1_product_audit_records_current_product_reading_blockers_without_changing_chart_facts",
    }


def _checks(
    *,
    runtime_payload: Mapping[str, Any],
    user_surface: Mapping[str, Any],
    practitioner_surface: Mapping[str, Any],
    admin_diagnostics: Mapping[str, Any],
    user_answer: Mapping[str, Any],
    practitioner_answer: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _core_chart_calculation_ready(runtime_payload, user_surface),
        _basic_assertions_present(user_surface),
        _domain_cards_are_not_generic(user_surface),
        _domain_cards_have_core_claim_quality(user_surface),
        _features_and_portraits_projected(user_surface, admin_diagnostics),
        _bazi_paths_projected_as_reading(user_surface),
        _answer_domain_matches_selected_question(user_surface, user_answer),
        _role_outputs_are_differentiated(user_surface, practitioner_surface, user_answer, practitioner_answer),
        _llm_context_pack_has_product_layers(user_answer),
        {
            "check_id": "heavy_gates_remain_explicit",
            "passed": True,
            "observed": {
                "full_pytest_required": False,
                "synthetic_all_required": False,
                "full_518k_required": False,
            },
        },
    ]


def _core_chart_calculation_ready(runtime_payload: Mapping[str, Any], surface: Mapping[str, Any]) -> dict[str, Any]:
    core = _mapping(surface.get("core_bazi_reading"))
    chart = _mapping(core.get("chart"))
    runtime_context = _mapping(runtime_payload.get("chart_context"))
    natal = _mapping(chart.get("natal_pillars") or runtime_context.get("natal_pillars"))
    time_context = _mapping(core.get("time_context"))
    runtime_time_context = _mapping(runtime_context.get("time_layers"))
    pillars = [_pillar_label(natal, key) for key in ("year", "month", "day", "hour")]
    current_luck = (
        time_context.get("current_luck_pillar")
        or time_context.get("luck_pillar")
        or _time_layer_pillar(time_context, "luck")
        or _time_layer_pillar(runtime_time_context, "luck")
    )
    flow_year = (
        time_context.get("flow_year_pillar")
        or _time_layer_pillar(time_context, "flow_year")
        or _time_layer_pillar(runtime_time_context, "flow_year")
    )
    passed = (
        len([pillar for pillar in pillars if pillar]) == 4
        and bool(chart.get("day_master") or runtime_context.get("day_master"))
        and bool(current_luck)
        and bool(flow_year)
    )
    return {
        "check_id": "core_chart_calculation_ready",
        "passed": passed,
        "observed": {
            "pillars": pillars,
            "day_master": chart.get("day_master") or runtime_context.get("day_master"),
            "current_luck_pillar": current_luck,
            "flow_year_pillar": flow_year,
        },
    }


def _basic_assertions_present(surface: Mapping[str, Any]) -> dict[str, Any]:
    assertions = _list(surface.get("basic_assertions"))
    core_assertions = _list(_mapping(surface.get("core_bazi_reading")).get("basic_assertions"))
    rows = assertions or core_assertions
    concrete = [
        row for row in rows
        if isinstance(row, Mapping)
        and str(row.get("assertion") or row.get("statement") or "")
        and str(row.get("evidence") or row.get("evidence_id") or "")
    ]
    return {
        "check_id": "basic_assertions_present",
        "passed": len(concrete) >= 3,
        "observed": {
            "surface_assertion_count": len(assertions),
            "core_assertion_count": len(core_assertions),
            "concrete_assertion_count": len(concrete),
        },
    }


def _domain_cards_are_not_generic(surface: Mapping[str, Any]) -> dict[str, Any]:
    cards = _list(surface.get("domain_cards"))
    text_by_domain: dict[str, str] = {}
    generic_hits: dict[str, list[str]] = {}
    for card in cards:
        if not isinstance(card, Mapping):
            continue
        domain = str(card.get("domain") or "")
        text = " ".join(
            str(card.get(key) or "")
            for key in ("summary", "diagnosis_summary", "title", "description")
        )
        text_by_domain[domain] = text
        hits = [token for token in FORBIDDEN_GENERIC_TOKENS if token in text]
        if hits:
            generic_hits[domain] = hits
    required_domains = {"career", "wealth", "relationship", "health", "timing"}
    ready_domains = {domain for domain, text in text_by_domain.items() if domain in required_domains and text}
    return {
        "check_id": "domain_cards_are_not_generic",
        "passed": required_domains.issubset(ready_domains) and not generic_hits,
        "observed": {
            "ready_domains": sorted(ready_domains),
            "missing_domains": sorted(required_domains - ready_domains),
            "generic_hits": generic_hits,
        },
    }


def _domain_cards_have_core_claim_quality(surface: Mapping[str, Any]) -> dict[str, Any]:
    cards = _list(surface.get("domain_cards"))
    required_domains = {"career", "wealth", "relationship", "health", "timing"}
    ready_domains: set[str] = set()
    failed_domains: dict[str, dict[str, Any]] = {}
    for card in cards:
        if not isinstance(card, Mapping):
            continue
        domain = str(card.get("domain") or "")
        if domain not in required_domains:
            continue
        quality = _mapping(card.get("core_claim_quality"))
        ready = (
            quality.get("version") == "v30.core_bazi_claim_quality.v1"
            and quality.get("quality_ready") is True
            and quality.get("uses_traceable_claims") is True
            and quality.get("chart_fact_mutation_allowed") is False
            and quality.get("fixed_event_prediction_allowed") is False
            and not _list(quality.get("generic_language_hits"))
        )
        if ready:
            ready_domains.add(domain)
        else:
            failed_domains[domain] = {
                "version": quality.get("version"),
                "quality_ready": quality.get("quality_ready"),
                "uses_traceable_claims": quality.get("uses_traceable_claims"),
                "generic_language_hits": _list(quality.get("generic_language_hits")),
            }
    return {
        "check_id": "domain_cards_have_core_claim_quality",
        "passed": required_domains.issubset(ready_domains) and not failed_domains,
        "observed": {
            "ready_domains": sorted(ready_domains),
            "missing_domains": sorted(required_domains - ready_domains),
            "failed_domains": failed_domains,
        },
    }


def _features_and_portraits_projected(surface: Mapping[str, Any], admin_diagnostics: Mapping[str, Any]) -> dict[str, Any]:
    feature_rows = _list(surface.get("bazi_features"))
    portrait_rows = _list(surface.get("bazi_portraits"))
    diagnosis = _mapping(admin_diagnostics.get("real_bazi_diagnosis"))
    admin_claims = _list(diagnosis.get("claims"))
    admin_portraits = _list(diagnosis.get("portraits"))
    passed = len(feature_rows) >= 4 and len(portrait_rows) >= 4
    return {
        "check_id": "bazi_features_and_portraits_projected",
        "passed": passed,
        "observed": {
            "surface_feature_count": len(feature_rows),
            "surface_portrait_count": len(portrait_rows),
            "admin_claim_count": len(admin_claims),
            "admin_portrait_count": len(admin_portraits),
        },
    }


def _bazi_paths_projected_as_reading(surface: Mapping[str, Any]) -> dict[str, Any]:
    path_rows = _list(surface.get("bazi_paths"))
    structure_paths = _list(_mapping(surface.get("structure_dynamics")).get("top_paths"))
    rows = path_rows or structure_paths
    concrete = [
        row for row in rows
        if isinstance(row, Mapping)
        and any(str(row.get(key) or "") for key in ("meaning", "domain_impact", "diagnosis_statement", "summary"))
        and not any(token in str(row) for token in FORBIDDEN_GENERIC_TOKENS)
    ]
    return {
        "check_id": "bazi_paths_projected_as_reading",
        "passed": len(concrete) >= 3 and bool(path_rows),
        "observed": {
            "surface_path_count": len(path_rows),
            "structure_path_count": len(structure_paths),
            "concrete_path_count": len(concrete),
        },
    }


def _answer_domain_matches_selected_question(surface: Mapping[str, Any], answer_panel: Mapping[str, Any]) -> dict[str, Any]:
    text = str(answer_panel.get("text") or "")
    selected_domain = _selected_domain(surface, answer_panel)
    expected_tokens = WEALTH_TOKENS if selected_domain == "wealth" else CAREER_TOKENS if selected_domain == "career" else ()
    competing_tokens = CAREER_TOKENS if selected_domain == "wealth" else WEALTH_TOKENS if selected_domain == "career" else ()
    expected_hits = _token_hits(text, expected_tokens)
    competing_hits = _token_hits(text, competing_tokens)
    starts_with_competing = selected_domain == "wealth" and text[:80].count("事业") > 0
    passed = bool(text) and bool(selected_domain) and bool(expected_hits) and len(competing_hits) <= len(expected_hits) and not starts_with_competing
    return {
        "check_id": "answer_domain_matches_selected_question",
        "passed": passed,
        "observed": {
            "question_id": answer_panel.get("question_id"),
            "selected_domain": selected_domain,
            "expected_hits": expected_hits,
            "competing_hits": competing_hits,
            "answer_excerpt": text[:180],
        },
    }


def _role_outputs_are_differentiated(
    user_surface: Mapping[str, Any],
    practitioner_surface: Mapping[str, Any],
    user_answer: Mapping[str, Any],
    practitioner_answer: Mapping[str, Any],
) -> dict[str, Any]:
    user_text = str(user_answer.get("text") or user_surface.get("reading_summary") or "")
    practitioner_text = str(practitioner_answer.get("text") or practitioner_surface.get("reading_summary") or "")
    role_contract = _mapping(practitioner_surface.get("role_contract"))
    role_adaptation = _mapping(practitioner_answer.get("role_adaptation"))
    diagnostic_lines = _list(role_adaptation.get("diagnostic_lines"))
    passed = (
        bool(user_text)
        and bool(practitioner_text)
        and bool(role_contract or practitioner_surface)
        and bool(diagnostic_lines)
        and "基础判断：" not in practitioner_text
        and "路径复核：" not in practitioner_text
        and "证据数=" not in practitioner_text
    )
    return {
        "check_id": "role_outputs_are_differentiated",
        "passed": passed,
        "observed": {
            "user_excerpt": user_text[:120],
            "practitioner_excerpt": practitioner_text[:120],
            "same_answer_text": user_text == practitioner_text,
            "practitioner_role_contract_present": bool(role_contract),
            "diagnostic_lines_present": bool(diagnostic_lines),
            "diagnostics_separated_from_answer_text": "基础判断：" not in practitioner_text and "路径复核：" not in practitioner_text,
        },
    }


def _llm_context_pack_has_product_layers(answer_panel: Mapping[str, Any]) -> dict[str, Any]:
    metadata = _mapping(answer_panel.get("llm_metadata"))
    context_pack = _mapping(metadata.get("context_pack_summary") or metadata.get("bazi_context_pack"))
    layers = _list(context_pack.get("layers"))
    required = {
        "basic_assertions",
        "domain_card",
        "bazi_features",
        "bazi_portraits",
        "bazi_paths",
        "time_context",
        "role_contract",
    }
    observed = {str(row) for row in layers}
    return {
        "check_id": "llm_context_pack_has_product_layers",
        "passed": required.issubset(observed),
        "observed": {
            "layers": sorted(observed),
            "missing_layers": sorted(required - observed),
            "metadata_keys": sorted(str(key) for key in metadata.keys()),
        },
    }


def _selected_domain(surface: Mapping[str, Any], answer_panel: Mapping[str, Any]) -> str:
    question_id = str(answer_panel.get("question_id") or "")
    if question_id in QUESTION_DOMAIN_BY_ID:
        return QUESTION_DOMAIN_BY_ID[question_id]
    next_question = _mapping(surface.get("next_question"))
    topic = str(next_question.get("topic") or "")
    if topic in {"wealth", "career", "relationship", "health", "timing"}:
        return topic
    for token, domain in (("wealth", "wealth"), ("career", "career"), ("relationship", "relationship")):
        if token in question_id:
            return domain
    return ""


def _decision(checks: list[Mapping[str, Any]]) -> dict[str, Any]:
    failed = [str(row.get("check_id") or "") for row in checks if row.get("passed") is not True]
    product_ready = not failed
    blocking_failures = [check_id for check_id in failed if check_id != "heavy_gates_remain_explicit"]
    audit_ready = len(checks) >= 8 and "heavy_gates_remain_explicit" not in failed
    next_task_id = _next_task_id(blocking_failures, product_ready=product_ready)
    return {
        "audit_ready": audit_ready,
        "product_reading_ready": product_ready,
        "decision_status": (
            "ui_r1_product_reading_accepted"
            if product_ready
            else "ui_r1_product_acceptance_baseline_recorded"
        ),
        "check_count": len(checks),
        "passed_check_count": len(checks) - len(failed),
        "failed_check_ids": failed,
        "blocking_failures": blocking_failures,
        "next_task_id": next_task_id,
        "rationale": (
            "Core UI reading is product-ready."
            if product_ready
            else "Audit completed and recorded product-reading blockers for the next UI-R1 implementation task."
        ),
    }


def _next_selection(decision: Mapping[str, Any]) -> dict[str, Any]:
    if decision.get("product_reading_ready") is True:
        return {
            "task_id": "UI-R1.10",
            "title": "Product-Level Synthetic Validation",
            "selected_track": "ui_core_reading_productization",
            "scope": [
                "add product-level synthetic cases for typical Bazi reading outputs",
                "keep lightweight UI-R1 acceptance in the default UI regression set",
            ],
        }
    task_id = str(decision.get("next_task_id") or "UI-R1.2")
    if task_id == "UI-R1.3":
        return {
            "task_id": "UI-R1.3",
            "title": "Bazi Feature And Portrait Projection",
            "selected_track": "ui_core_reading_productization",
            "scope": [
                "project M3/RBD features and portraits into customer-safe reading_surface rows",
                "keep practitioner evidence labels while hiding raw internal IDs from customer roles",
                "preserve chart-fact no-mutation and candidate-bound reading language",
            ],
        }
    if task_id == "UI-R1.4":
        return {
            "task_id": "UI-R1.4",
            "title": "Bazi Path Reading Projection",
            "selected_track": "ui_core_reading_productization",
            "scope": [
                "convert structure and diagnosis paths into practical reading rows",
                "link path rows to domains and uncertainty boundaries",
            ],
        }
    if task_id == "UI-R1.8":
        return {
            "task_id": "UI-R1.8",
            "title": "Multi-Role Reading Surfaces",
            "selected_track": "ui_core_reading_productization",
            "scope": ["differentiate user and practitioner wording without changing chart facts"],
        }
    if task_id == "UI-R1.7":
        return {
            "task_id": "UI-R1.7",
            "title": "LLM Context And Prompt Upgrade",
            "selected_track": "ui_core_reading_productization",
            "scope": ["align LLM prompt context with product reading layers"],
        }
    return {
        "task_id": "UI-R1.2",
        "title": "Basic Assertion Projection",
        "selected_track": "ui_core_reading_productization",
        "scope": [
            "project calculation-backed basic assertions into reading_surface",
            "make the first-screen Bazi reading concrete before expanding UI chrome",
            "keep LLM as synthesis over module context instead of chart-fact generation",
        ],
    }


def _next_task_id(blocking_failures: list[str], *, product_ready: bool) -> str:
    if product_ready:
        return "UI-R1.10"
    if "basic_assertions_present" in blocking_failures:
        return "UI-R1.2"
    if "bazi_features_and_portraits_projected" in blocking_failures:
        return "UI-R1.3"
    if "bazi_paths_projected_as_reading" in blocking_failures:
        return "UI-R1.4"
    if "role_outputs_are_differentiated" in blocking_failures:
        return "UI-R1.8"
    if "llm_context_pack_has_product_layers" in blocking_failures:
        return "UI-R1.7"
    return "UI-R1.2"


def _token_hits(text: str, tokens: tuple[str, ...]) -> list[str]:
    return [token for token in tokens if token in text]


def _pillar_label(natal: Mapping[str, Any], key: str) -> str:
    if natal.get(key):
        return str(natal.get(key) or "")
    pillars = _mapping(natal.get("pillars"))
    pillar = _mapping(pillars.get(key))
    stem = str(pillar.get("stem") or "")
    branch = str(pillar.get("branch") or "")
    return f"{stem}{branch}" if stem or branch else ""


def _time_layer_pillar(time_context: Mapping[str, Any], layer_key: str) -> str:
    for row in _list(time_context.get("layers")):
        if not isinstance(row, Mapping) or row.get("layer_key") != layer_key:
            continue
        pillar = _mapping(row.get("pillar"))
        stem = str(pillar.get("stem") or "")
        branch = str(pillar.get("branch") or "")
        return f"{stem}{branch}" if stem or branch else ""
    return ""


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[Any]:
    return value if isinstance(value, list) else []
