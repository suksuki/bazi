from __future__ import annotations

from v30.contracts import AnswerContext, CoreRuntimeResult
from v30.expression.contracts import ExpressionFrame, NarrativePlan
from v30.expression.style import resolve_style_profile, resolve_style_profile_from_role_state


EXPRESSION_FRAMEWORK_VERSION = "v30.expression.framework.v1"


def build_runtime_narrative_plan(
    runtime: CoreRuntimeResult,
    *,
    answer_context: AnswerContext | None = None,
    role_key: str = "user",
    client: str = "web",
    role_state: dict[str, object] | None = None,
) -> NarrativePlan:
    style_profile = (
        resolve_style_profile_from_role_state(role_state, locale=runtime.chart_context.locale, client=client)
        if role_state
        else resolve_style_profile(
            role_key=role_key,
            locale=runtime.chart_context.locale,
            client=client,
        )
    )
    frames = [
        ExpressionFrame(
            frame_id=f"{runtime.reading_id}:expression:mainline",
            kind="mainline_summary",
            source_ids=[runtime.mainline_state.mainline_id, runtime.structure_state.structure_id],
            semantic_intent="explain_current_bazi_mainline_without_overstating_final_verdict",
            bazi_terms=["日主", "格局", "结构动态"],
            user_meaning=_mainline_meaning(runtime),
            boundary=runtime.structure_state.boundary,
        )
    ]
    if answer_context is not None:
        anchor = answer_context.selected_question_anchor
        frames.append(
            ExpressionFrame(
                frame_id=f"{runtime.reading_id}:expression:question:{anchor.question_id}",
                kind="question_recommendation",
                source_ids=[anchor.anchor_id, anchor.question_id],
                semantic_intent="turn_selected_anchor_into_bazi_dialogue_question",
                bazi_terms=["原局", "大运", "流年"],
                user_meaning=_question_meaning(anchor.anchor_status, anchor.missing_requirements),
                boundary="question_is_for_context_binding_not_template_generation",
            )
        )
        rbd_meaning = _rbd_answer_meaning(runtime, answer_context)
        if rbd_meaning:
            frames.append(
                ExpressionFrame(
                    frame_id=f"{runtime.reading_id}:expression:rbd:{anchor.question_id}",
                    kind="real_bazi_diagnosis",
                    source_ids=_rbd_answer_source_ids(runtime, answer_context),
                    semantic_intent="answer_selected_question_with_rbd_claims_not_generic_template",
                    bazi_terms=["十神", "结构路径", "画像", "大运流年"],
                    user_meaning=rbd_meaning,
                    boundary="real_bazi_diagnosis_expression_consumes_traceable_claims_not_chart_fact_mutation",
                )
            )
        frames.append(
            ExpressionFrame(
                frame_id=f"{runtime.reading_id}:expression:boundary:{anchor.question_id}",
                kind="answer_boundary",
                source_ids=answer_context.knowledge_boundaries,
                semantic_intent="state_answer_scope_in_consultation_language",
                bazi_terms=["断语", "应期", "证据"],
                user_meaning="当前只顺着已定的盘面、结构和问题来说明，不把未确认的年份或背景线索说成定论。",
                boundary="rule_bound_answer_no_llm_fact_mutation",
            )
        )
    for projection in _macro_portraits(runtime):
        frames.append(
            ExpressionFrame(
                frame_id=f"{runtime.reading_id}:expression:portrait:{projection.get('projection_id', projection.get('domain', 'unknown'))}",
                kind="portrait_projection",
                source_ids=[str(projection.get("source_signal_id", ""))],
                semantic_intent=f"project_{projection.get('domain', 'macro')}_portrait_language",
                bazi_terms=["画像", "气势", "取象"],
                user_meaning=_portrait_meaning(projection),
                boundary=str(projection.get("source_policy") or "portrait_is_projection_not_fact_source"),
            )
        )
    return NarrativePlan(
        plan_id=f"{runtime.reading_id}:expression-plan:{style_profile.role_key}:{style_profile.client}",
        style_profile=style_profile,
        frames=frames,
        output_channel="runtime_surface_text",
    )


def _mainline_meaning(runtime: CoreRuntimeResult) -> str:
    time_status = str(runtime.chart_context.time_layers.get("status", "not_provided"))
    structure_phrase = "格局和支合刑冲的动态关系"
    if "missing" in time_status or runtime.structure_state.boundary:
        boundary_phrase = "但时柱与时间层仍需先定边界"
    else:
        boundary_phrase = "再顺着大运流年的气势看变化"
    return (
        f"此盘以{runtime.chart_context.day_master}日主为中心，先看"
        f"{structure_phrase}，{boundary_phrase}。"
    )


def _question_meaning(anchor_status: str, missing_requirements: list[str]) -> str:
    if anchor_status == "missing_time":
        return "时柱和时间层还未稳，先补齐原局边界，再谈大运流年里的应事轻重。"
    if missing_requirements:
        return "这个问题需要先补足原局和关键背景，才适合进入更细的格局判断。"
    return "这个问题已经能贴着原局、结构和当前主线继续追问。"


def _rbd_answer_meaning(runtime: CoreRuntimeResult, answer_context: AnswerContext) -> str:
    projection = _rbd_public_projection(runtime)
    if not projection:
        return ""
    domain = _rbd_answer_domain(answer_context)
    summaries = projection.get("domain_summaries", {})
    summaries = summaries if isinstance(summaries, dict) else {}
    summary = str(summaries.get(domain) or "")
    if not summary and domain == "structure":
        summary = str(projection.get("diagnosis_overview") or "")
    paths = projection.get("domain_paths", {})
    paths = paths if isinstance(paths, dict) else {}
    path_rows = paths.get(domain, [])
    if not isinstance(path_rows, list) and domain != "structure":
        path_rows = paths.get("structure", [])
    path_statement = ""
    for row in path_rows if isinstance(path_rows, list) else []:
        if isinstance(row, dict) and row.get("diagnosis_statement"):
            path_statement = str(row.get("diagnosis_statement") or "")
            break
    portraits = projection.get("domain_portraits", {})
    portraits = portraits if isinstance(portraits, dict) else {}
    portrait_rows = portraits.get(domain, [])
    portrait_statement = ""
    for row in portrait_rows if isinstance(portrait_rows, list) else []:
        if isinstance(row, dict) and row.get("statement"):
            portrait_statement = str(row.get("statement") or "")
            break
    parts = [part for part in (summary, path_statement, portrait_statement) if part]
    return "".join(parts[:3])


def _rbd_answer_source_ids(runtime: CoreRuntimeResult, answer_context: AnswerContext) -> list[str]:
    projection = _rbd_public_projection(runtime)
    domain = _rbd_answer_domain(answer_context)
    source_ids: list[str] = []
    for key, id_key in (
        ("domain_claims", "claim_id"),
        ("domain_paths", "path_id"),
        ("domain_portraits", "portrait_id"),
    ):
        section = projection.get(key, {}) if isinstance(projection, dict) else {}
        rows = section.get(domain, []) if isinstance(section, dict) else []
        if not isinstance(rows, list) and domain != "structure":
            rows = section.get("structure", []) if isinstance(section, dict) else []
        for row in rows[:3] if isinstance(rows, list) else []:
            if isinstance(row, dict) and row.get(id_key):
                source_ids.append(str(row.get(id_key)))
    return source_ids


def _rbd_public_projection(runtime: CoreRuntimeResult) -> dict[str, object]:
    diagnosis = runtime.question_plan.policy_effect.get("real_bazi_diagnosis", {})
    diagnosis = diagnosis if isinstance(diagnosis, dict) else {}
    projection = diagnosis.get("public_projection", {})
    return projection if isinstance(projection, dict) else {}


def _rbd_answer_domain(answer_context: AnswerContext) -> str:
    anchor = answer_context.selected_question_anchor
    marker = " ".join([anchor.question_id, anchor.intent_id, anchor.why_this_question]).lower()
    if "wealth" in marker or "财" in marker:
        return "wealth"
    if "career" in marker or "事业" in marker:
        return "career"
    if "relationship" in marker or "romance" in marker or "关系" in marker or "感情" in marker:
        return "relationship"
    if "timing" in marker or "大运" in marker or "流年" in marker:
        return "timing"
    if "health" in marker or "健康" in marker:
        return "health"
    if "useful" in marker or "用神" in marker:
        return "useful_god"
    if "hidden" in marker or "隐藏" in marker:
        return "hidden_factor"
    return "structure"


def _portrait_meaning(projection: dict[str, object]) -> str:
    domain = str(projection.get("domain") or "macro")
    label_map = {
        "wealth": "财务取向",
        "career": "事业路径",
        "relationship": "关系模式",
        "romance": "感情节奏",
        "health": "身心状态",
        "hidden_factor": "背景校准线索",
        "foundation": "底层气势",
    }
    label = label_map.get(domain, domain)
    return f"{label}只作为画像投射来观察，用来帮助追问，不直接当成命盘事实。"


def _macro_portraits(runtime: CoreRuntimeResult) -> list[dict[str, object]]:
    value = runtime.question_plan.policy_effect.get("macro_portrait_projections", [])
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]
