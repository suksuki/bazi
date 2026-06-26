from __future__ import annotations

from dataclasses import replace
from typing import Any

from v20.answer.measurement_policy import domain_label
from v20.interaction.questions import QuestionCandidate


QUESTION_ANCHOR_VERSION = "v20.bazi_question_anchor.v1"

TIME_DOMAINS = {"time"}
STRUCTURE_SENSITIVE_DOMAINS = {
    "branch",
    "career",
    "health",
    "pattern",
    "relationship",
    "strength",
    "structure",
    "ten_god",
    "useful_god",
    "wealth",
}
TECHNICAL_ROLES = {"admin", "lab", "analyst", "practitioner"}


def bind_questions_to_bazi_context(
    questions: tuple[QuestionCandidate, ...],
    *,
    bazi_context_frame: dict[str, object],
    structure_dynamics: dict[str, object],
    mainline_arbitration: dict[str, object],
    role_key: str = "user",
    limit: int | None = None,
) -> tuple[QuestionCandidate, ...]:
    bound: list[QuestionCandidate] = []
    for question in questions:
        anchor = build_question_anchor(
            question,
            bazi_context_frame=bazi_context_frame,
            structure_dynamics=structure_dynamics,
            mainline_arbitration=mainline_arbitration,
            role_key=role_key,
        )
        if _hide_for_role(anchor, role_key):
            continue
        display_title = render_question_display_title(question, anchor, role_key=role_key)
        bound.append(replace(question, display_title=display_title, question_anchor=anchor))
        if limit is not None and len(bound) >= limit:
            break
    if bound:
        return tuple(bound)
    if str(role_key or "user") not in TECHNICAL_ROLES:
        return ()
    fallback = []
    for question in questions:
        anchor = build_question_anchor(
            question,
            bazi_context_frame=bazi_context_frame,
            structure_dynamics=structure_dynamics,
            mainline_arbitration=mainline_arbitration,
            role_key=role_key,
            force_weak=True,
        )
        display_title = render_question_display_title(question, anchor, role_key=role_key)
        fallback.append(replace(question, display_title=display_title, question_anchor=anchor))
        if limit is not None and len(fallback) >= limit:
            break
    return tuple(fallback)


def build_question_anchor(
    question: QuestionCandidate,
    *,
    bazi_context_frame: dict[str, object],
    structure_dynamics: dict[str, object],
    mainline_arbitration: dict[str, object],
    role_key: str = "user",
    force_weak: bool = False,
) -> dict[str, object]:
    time_layers = tuple(row for row in bazi_context_frame.get("time_layers", ()) or () if isinstance(row, dict))
    primary_chain = _primary_chain(structure_dynamics)
    primary_mainline = mainline_arbitration.get("primary_mainline", {})
    if not isinstance(primary_mainline, dict):
        primary_mainline = {}
    chain_label = _chain_label(primary_chain)
    mainline_label = _mainline_label(primary_mainline)
    requires_time = _requires_time(question)
    requires_structure = _requires_structure(question)
    missing: list[str] = []
    if not bazi_context_frame.get("context_id") or not bazi_context_frame.get("day_master"):
        missing.append("current_bazi_context")
    if requires_time and not time_layers:
        missing.append("luck_or_flow_year")
    if requires_structure and not chain_label:
        missing.append("primary_dynamic_chain")
    evidence_refs = _evidence_refs(question, primary_chain, primary_mainline)
    if not evidence_refs:
        missing.append("evidence_refs")
    status = _anchor_status(missing, force_weak=force_weak)
    return {
        "version": QUESTION_ANCHOR_VERSION,
        "context_id": str(bazi_context_frame.get("context_id", "")),
        "question_key": question.question_key,
        "question_id": question.question_id,
        "atom_id": question.next_question_atom_id,
        "role_key": "analyst" if role_key == "practitioner" else str(role_key or "user"),
        "anchor_status": status,
        "natal_pillars": bazi_context_frame.get("natal_pillars", {}),
        "day_master": str(bazi_context_frame.get("day_master", "")),
        "day_master_element": str(bazi_context_frame.get("day_master_element", "")),
        "time_layers": list(time_layers),
        "luck_pillar": _time_pillar(time_layers, "luck"),
        "flow_year_pillar": _time_pillar(time_layers, "flow_year"),
        "primary_dynamic_chain": primary_chain,
        "primary_dynamic_chain_label": chain_label,
        "mainline_domain": str(primary_mainline.get("domain", "") or question.domain),
        "mainline_label": mainline_label,
        "question_domain": question.domain,
        "question_topic": question.next_question_topic or question.measurement_topic or domain_label(question.domain),
        "question_stage": question.next_question_stage or question.measurement_stage,
        "time_binding": "explicit_time_context" if time_layers else "natal_only",
        "evidence_refs": evidence_refs,
        "feature_ids": list(question.source_feature_ids)[:8],
        "why_this_question": _why_this_question(question, chain_label, mainline_label, time_layers),
        "missing_requirements": missing,
        "runtime_mutation": False,
        "guardrails": [
            "QUESTION_MUST_BIND_CURRENT_BAZI_CONTEXT",
            "QUESTION_ANCHOR_DOES_NOT_CREATE_CHART_FACTS",
            "DISPLAY_TITLE_MUST_RENDER_FROM_ANCHOR_NOT_RAW_TEMPLATE",
        ],
    }


def render_question_display_title(question: QuestionCandidate, anchor: dict[str, object], *, role_key: str = "user") -> str:
    role = "analyst" if role_key == "practitioner" else str(role_key or "user")
    day_master = str(anchor.get("day_master", "")).strip()
    chain = str(anchor.get("primary_dynamic_chain_label", "")).strip()
    mainline = str(anchor.get("mainline_label", "")).strip()
    domain = str(question.domain or anchor.get("mainline_domain", "") or "").strip()
    time_text = _time_text(anchor)
    basis = chain or mainline or domain_label(domain)
    topic = _topic_phrase(question)
    if role in {"admin", "lab"}:
        return f"锚定问题：{day_master}日主 / {basis or '当前主线'} / {time_text or '原局'}，观测{topic}。"
    if role in {"analyst", "practitioner"}:
        return _practitioner_title(question, day_master=day_master, basis=basis, time_text=time_text)
    return _user_title(question, day_master=day_master, basis=basis, time_text=time_text)


def _user_title(question: QuestionCandidate, *, day_master: str, basis: str, time_text: str) -> str:
    prefix = f"这盘{day_master}日主" if day_master else "这盘"
    chain = f"，主线先看「{basis}」" if basis else ""
    time_part = f"，又遇到{time_text}" if time_text else ""
    key = question.question_key
    if question.domain == "useful_god":
        if "gap" in key:
            return f"{prefix}{chain}{time_part}，用神判断还缺哪条证据，先补哪一处最影响结论？"
        return f"{prefix}{chain}{time_part}，用神和调节方向是什么，应落在哪条路径上？"
    if question.domain == "time":
        return f"{prefix}{chain}{time_part}，这一步时间层先触发主线、机会，还是压力边界？"
    if question.domain == "career":
        return f"{prefix}{chain}{time_part}，事业判断先看规则压力、个人发挥，还是资源承接？"
    if question.domain == "wealth":
        return f"{prefix}{chain}{time_part}，财运先看机会从哪里来，还是先看日主能不能接住？"
    if question.domain == "relationship":
        return f"{prefix}{chain}{time_part}，关系里更该先看互动方式、现实承接，还是边界压力？"
    if question.domain == "strength":
        return f"{prefix}{chain}{time_part}，日主承接先看根气帮扶，还是泄耗和外部压力？"
    if question.domain == "branch":
        return f"{prefix}{chain}{time_part}，地支互动里哪条冲合刑害最会牵动主线？"
    if question.domain in {"pattern", "structure"}:
        return f"{prefix}{chain}{time_part}，格局和结构主线已经到哪一步，下一步该确认什么？"
    if question.domain == "ten_god":
        return f"{prefix}{chain}{time_part}，十神关系里哪一组最影响当前判断？"
    if question.domain == "element":
        return f"{prefix}{chain}{time_part}，五行分布先提示支持、泄耗，还是失衡压力？"
    if question.domain == "health":
        return f"{prefix}{chain}{time_part}，平衡压力主要落在哪个五行或结构环节？"
    return f"{prefix}{chain}{time_part}，下一步围绕当前主线先确认哪一段最关键？"


def _practitioner_title(question: QuestionCandidate, *, day_master: str, basis: str, time_text: str) -> str:
    prefix = f"当前原局为{day_master}日主" if day_master else "当前原局"
    chain = f"，结构主线指向「{basis}」" if basis else ""
    time_part = f"，{time_text}参与触发" if time_text else ""
    if question.domain == "useful_god":
        return f"{prefix}{chain}{time_part}。用神候选是什么，证据、反证和取舍边界分别在哪里？"
    if question.domain == "time":
        return f"{prefix}{chain}{time_part}。岁运触发应先归入原局主链，还是形成新的阻断边？"
    if question.domain == "career":
        return f"{prefix}{chain}{time_part}。事业复核先看官杀压力、食伤表达，还是印星资源承接？"
    if question.domain == "wealth":
        return f"{prefix}{chain}{time_part}。财运复核先看财星通道、食伤转财，还是日主承载与比劫竞争？"
    return f"{prefix}{chain}{time_part}。下一步复核当前主线的证据、承接点和反向约束？"


def _hide_for_role(anchor: dict[str, object], role_key: str) -> bool:
    role = "analyst" if role_key == "practitioner" else str(role_key or "user")
    status = str(anchor.get("anchor_status", ""))
    if role in TECHNICAL_ROLES:
        return status == "unsupported"
    return status != "bound"


def _anchor_status(missing: list[str], *, force_weak: bool) -> str:
    if force_weak:
        return "weak"
    if "current_bazi_context" in missing:
        return "unsupported"
    if "luck_or_flow_year" in missing:
        return "missing_time"
    if "primary_dynamic_chain" in missing:
        return "missing_structure"
    if "evidence_refs" in missing:
        return "weak"
    return "bound"


def _requires_time(question: QuestionCandidate) -> bool:
    return question.domain in TIME_DOMAINS or question.next_question_stage == "timing" or "time" in question.question_key


def _requires_structure(question: QuestionCandidate) -> bool:
    return question.domain in STRUCTURE_SENSITIVE_DOMAINS or bool(question.next_question_atom_id)


def _primary_chain(structure_dynamics: dict[str, object]) -> dict[str, object]:
    for key in ("primary_dynamic_chain", "dominant_chain", "legacy_dynamic_chain"):
        row = structure_dynamics.get(key)
        if isinstance(row, dict) and row:
            return row
    rows = structure_dynamics.get("activated_structures", ())
    if isinstance(rows, (list, tuple)):
        for row in rows:
            if isinstance(row, dict) and row:
                return row
    return {}


def _chain_label(chain: dict[str, object]) -> str:
    for key in ("label", "structure_label", "name", "mechanism_label", "path_label"):
        value = str(chain.get(key, "")).strip()
        if value:
            return value
    nodes = chain.get("nodes", ())
    if isinstance(nodes, (list, tuple)) and nodes:
        labels = [str(row.get("label", "") if isinstance(row, dict) else row).strip() for row in nodes[:3]]
        labels = [row for row in labels if row]
        if labels:
            return "->".join(labels)
    return ""


def _mainline_label(mainline: dict[str, object]) -> str:
    for key in ("label", "title", "mainline_label", "domain_label"):
        value = str(mainline.get(key, "")).strip()
        if value:
            return value
    return ""


def _time_pillar(time_layers: tuple[dict[str, object], ...], key: str) -> str:
    for row in time_layers:
        layer_key = str(row.get("layer_key", "")).strip()
        if key in layer_key:
            return str(row.get("pillar", "")).strip()
    return ""


def _time_text(anchor: dict[str, object]) -> str:
    luck = str(anchor.get("luck_pillar", "")).strip()
    flow = str(anchor.get("flow_year_pillar", "")).strip()
    if luck and flow:
        return f"{luck}大运、{flow}流年"
    if luck:
        return f"{luck}大运"
    if flow:
        return f"{flow}流年"
    return ""


def _evidence_refs(question: QuestionCandidate, primary_chain: dict[str, object], primary_mainline: dict[str, object]) -> list[dict[str, str]]:
    refs = [{"type": "feature", "id": str(row)} for row in question.source_feature_ids[:8] if str(row)]
    chain_id = str(primary_chain.get("chain_id", "") or primary_chain.get("structure_key", "") or primary_chain.get("key", "")).strip()
    if chain_id:
        refs.append({"type": "structure_dynamic_chain", "id": chain_id})
    mainline_id = str(primary_mainline.get("mainline_id", "") or primary_mainline.get("key", "") or primary_mainline.get("domain", "")).strip()
    if mainline_id:
        refs.append({"type": "mainline", "id": mainline_id})
    return refs


def _why_this_question(
    question: QuestionCandidate,
    chain_label: str,
    mainline_label: str,
    time_layers: tuple[dict[str, object], ...],
) -> str:
    basis = chain_label or mainline_label or domain_label(question.domain)
    if question.domain == "time" and time_layers:
        return f"当前有明确大运/流年时间层，需要判断它先牵动「{basis}」的哪一段。"
    if chain_label:
        return f"当前结构主线指向「{chain_label}」，这个问题用于确认承接、阻断或下一步追问。"
    return f"这个问题来自当前{domain_label(question.domain)}证据，用于继续收束测算主线。"


def _topic_phrase(question: QuestionCandidate) -> str:
    return question.next_question_topic or question.measurement_topic or domain_label(question.domain)
