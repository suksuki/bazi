from __future__ import annotations

from typing import Any


BRAIN_STATE_VERSION = "v20.orchestrator_brain_state.v1"
NODE_LABELS = {
    "output": "食伤",
    "wealth": "财星",
    "authority": "官杀",
    "resource": "印星",
    "self": "日主",
    "peer": "比劫",
}
DOMAIN_LABELS = {
    "strength": "日主承载",
    "wealth": "财运结构",
    "career": "事业结构",
    "useful_god": "用神候选",
    "pattern": "格局结构",
    "relationship": "关系结构",
    "time": "岁运时间",
    "branch": "地支互动",
    "element": "五行分布",
    "ten_god": "十神结构",
}


def build_orchestrator_brain_state(
    *,
    mainline_arbitration: dict[str, Any],
    orchestrator_evidence: dict[str, Any],
    question_mainline_focus: dict[str, Any],
    structure_dynamics: dict[str, Any],
    selected_question: object,
    time_context: dict[str, Any],
) -> dict[str, object]:
    primary = _dict(mainline_arbitration.get("primary_mainline", {}))
    quality_gate = _dict(mainline_arbitration.get("quality_gate", {}))
    dynamic_state = _dict(structure_dynamics.get("dynamic_state", {}))
    support = [_public_evidence(row) for row in _list(mainline_arbitration.get("evidence_items")) if _is_user_visible(row)]
    if not support:
        support = _primary_public_support(primary)
    knowledge_basis = _knowledge_basis(orchestrator_evidence.get("items", ()))
    answer_guidance = _answer_guidance_from_knowledge_basis(knowledge_basis)
    selected_key = str(getattr(selected_question, "question_key", "") or _dict(selected_question).get("question_key", ""))
    selected_title = str(getattr(selected_question, "title", "") or _dict(selected_question).get("title", ""))
    selected_domain = str(getattr(selected_question, "domain", "") or _dict(selected_question).get("domain", ""))
    review_flags = _review_flags(primary, quality_gate, question_mainline_focus, dynamic_state)
    runtime_policy_coordination = _runtime_policy_coordination(
        mainline_arbitration=mainline_arbitration,
        question_focus=question_mainline_focus,
    )
    coordination = _coordination_summary(
        primary=primary,
        quality_gate=quality_gate,
        question_focus=question_mainline_focus,
        structure_dynamics=structure_dynamics,
        selected_domain=selected_domain,
        time_context=time_context,
    )
    status = "requires_review" if review_flags else "ready"
    if str(mainline_arbitration.get("status", "")) != "ready":
        status = "not_ready"
    return {
        "version": BRAIN_STATE_VERSION,
        "status": status,
        "mode": "deterministic_orchestrator_summary",
        "public_summary": {
            "headline": _headline(primary),
            "primary_domain": _domain_label(primary.get("domain", "")),
            "primary_title": _public_title(primary.get("title", "") or primary.get("domain", "")),
            "primary_nodes": _node_labels(primary.get("nodes", ())),
            "selection_reasons": _selection_reasons(mainline_arbitration),
            "selected_question_key": selected_key,
            "selected_question_title": selected_title,
            "selected_question_domain": selected_domain,
            "question_focus_status": question_mainline_focus.get("status", ""),
            "coordination_status": coordination["status_label"],
            "coordination_note": coordination["public_note"],
            "dynamic_chain": _dynamic_chain_label(
                structure_dynamics.get(
                    "primary_dynamic_chain",
                    structure_dynamics.get("dominant_chain_v2", structure_dynamics.get("legacy_dynamic_chain", "")),
                )
            ),
            "dynamic_work_path": _dynamic_work_path_summary(structure_dynamics),
            "chain_state": structure_dynamics.get("chain_state", ""),
            "energy_state": _shift_label(structure_dynamics.get("energy_shift", "")),
            "stability_state": _shift_label(structure_dynamics.get("stability_shift", "")),
            "time_layer_status": str(time_context.get("status", "")),
            "runtime_policy_coordination": runtime_policy_coordination,
            "knowledge_basis": knowledge_basis,
            "answer_guidance": answer_guidance,
            "supporting_evidence": support[:5],
            "next_action": _next_action(review_flags, selected_domain),
        },
        "review_summary": {
            "requires_review": bool(review_flags),
            "review_flags": review_flags,
            "quality_gate_status": quality_gate.get("status", ""),
            "quality_gate_reason": quality_gate.get("reason", ""),
            "candidate_count": mainline_arbitration.get("candidate_count", 0),
            "evidence_count": orchestrator_evidence.get("evidence_count", 0),
            "knowledge_evidence_count": len(knowledge_basis),
            "supporting_mainline_count": len(_list(mainline_arbitration.get("supporting_mainlines"))),
            "rejected_mainline_count": len(_list(mainline_arbitration.get("rejected_mainlines"))),
            "question_focus_reordered": question_mainline_focus.get("reordered", False),
            "explicit_question_preserved": question_mainline_focus.get("explicit_question_requested", False),
            "volatility_score": dynamic_state.get("volatility_score", 0),
            "coordination_flags": coordination["flags"],
            "runtime_policy_coordination_status": runtime_policy_coordination["status"],
        },
        "runtime_mutation": False,
        "guardrails": [
            "BRAIN_STATE_SUMMARIZES_EXISTING_RUNTIME_OUTPUTS",
            "BRAIN_STATE_DOES_NOT_CREATE_FACTS",
            "BRAIN_STATE_CARRIES_PUBLIC_KNOWLEDGE_BASIS",
            "PUBLIC_SUMMARY_EXCLUDES_INTERNAL_SOURCE_KEYS",
            "LLM_CAN_EXPLAIN_BRAIN_STATE_NOT_OVERRIDE_IT",
        ],
}


def _runtime_policy_coordination(
    *,
    mainline_arbitration: dict[str, Any],
    question_focus: dict[str, Any],
) -> dict[str, object]:
    mainline_effect = _dict(mainline_arbitration.get("runtime_policy_effect", {}))
    question_effect = _dict(question_focus.get("runtime_policy_effect", {}))
    active_version = str(mainline_effect.get("active_policy_version", "") or question_effect.get("active_policy_version", ""))
    mainline_status = str(mainline_effect.get("status", ""))
    question_status = str(question_effect.get("status", ""))
    mainline_count = int(mainline_effect.get("applied_adjustment_count", 0) or 0)
    question_delta = float(question_effect.get("applied_boost", 0) or 0)
    applied = mainline_status == "applied" or mainline_count > 0 or question_delta > 0
    if applied:
        status = "applied"
        note = "训练生成的运行时策略已经参与本轮主线排序或问题聚焦。"
    elif active_version and active_version.endswith("baseline.v1"):
        status = "baseline"
        note = "本轮使用基础策略，训练 pointer 暂未改变中枢排序。"
    elif active_version:
        status = "active_no_match"
        note = "训练 pointer 已启用，但本轮没有命中需要调整的主线或问题。"
    else:
        status = "not_applied"
        note = "本轮没有可用的运行时训练策略。"
    return {
        "version": "v20.brain_runtime_policy_coordination.v1",
        "status": status,
        "active_policy_version": active_version,
        "mainline_effect_status": mainline_status,
        "mainline_adjustment_count": mainline_count,
        "question_effect_status": question_status,
        "question_applied_boost": round(question_delta, 4),
        "public_note": note,
        "runtime_mutation": False,
    }


def _coordination_summary(
    *,
    primary: dict[str, Any],
    quality_gate: dict[str, Any],
    question_focus: dict[str, Any],
    structure_dynamics: dict[str, Any],
    selected_domain: str,
    time_context: dict[str, Any],
) -> dict[str, object]:
    flags: list[str] = []
    notes: list[str] = []
    primary_domain = str(primary.get("domain", "") or "")
    if not primary.get("nodes"):
        flags.append("primary_mainline_missing")
        notes.append("第一主线尚未形成，回答只能先保留结构观察。")
    if primary_domain and selected_domain and primary_domain != selected_domain:
        flags.append("question_domain_differs_from_primary")
        notes.append(f"当前问题落在「{_domain_label(selected_domain)}」，第一主线落在「{_domain_label(primary_domain)}」，需要跨域合参。")
    if question_focus.get("status") in {"no_domain_match", "no_primary_domain"}:
        flags.append(str(question_focus.get("status")))
        notes.append("智能问题暂未完全贴合第一主线，需要继续追问或切换问题入口。")
    dynamic_nodes = set(_dynamic_nodes(structure_dynamics.get("primary_dynamic_chain", structure_dynamics.get("dominant_chain_v2", ""))))
    primary_nodes = set(_list(primary.get("nodes")))
    if dynamic_nodes and primary_nodes and not dynamic_nodes.intersection(primary_nodes):
        flags.append("dynamic_chain_off_primary")
        notes.append("结构动态主链与第一主线重合度低，需要把动态结构作为复核线索。")
    if quality_gate.get("requires_review"):
        flags.append("mainline_quality_review")
        targets = [_public_text(row) for row in _list(quality_gate.get("review_targets")) if _public_text(row)]
        notes.append(targets[0] if targets else "第一主线证据覆盖仍需复核。")
    if str(time_context.get("status", "")) != "ready":
        flags.append("time_layer_not_ready")
        notes.append("岁运层暂未就绪，本轮先按原局、规则、画像和结构动态统筹。")
    flags = list(dict.fromkeys(flags))
    notes = list(dict.fromkeys(row for row in notes if row))
    if not flags:
        return {
            "status": "aligned",
            "status_label": "已对齐",
            "public_note": "主线、问题、结构动态和时间层已进入同一轮中枢统筹。",
            "flags": [],
        }
    if "primary_mainline_missing" in flags:
        status = "not_ready"
        label = "未就绪"
    else:
        status = "reviewing"
        label = "需复核"
    return {
        "status": status,
        "status_label": label,
        "public_note": notes[0],
        "flags": flags,
    }


def _dynamic_nodes(value: object) -> list[str]:
    if isinstance(value, dict):
        return [str(row) for row in _list(value.get("nodes")) if str(row)]
    if isinstance(value, (list, tuple)):
        return [str(row) for row in value if str(row)]
    return []


def _headline(primary: dict[str, Any]) -> str:
    title = _public_title(primary.get("title", ""))
    domain = _domain_label(primary.get("domain", ""))
    if title:
        return f"本轮中枢先取「{title}」作为测算主线。"
    if domain:
        return f"本轮中枢先围绕 {domain} 领域组织测算。"
    return "本轮中枢尚未形成清晰主线。"


def _public_evidence(row: object) -> dict[str, object]:
    item = _dict(row)
    return {
        "domain": _domain_label(item.get("domain", "")),
        "label": _public_title(item.get("label", "")),
        "summary": _public_text(item.get("summary", "")),
        "confidence": item.get("confidence", 0),
        "boundary": _public_text(item.get("boundary", "")),
    }


def _knowledge_basis(rows: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in _list(rows):
        item = _dict(row)
        if str(item.get("source_type", "")) != "knowledge_basis" or not _is_user_visible(item):
            continue
        key = (_domain_label(item.get("domain", "")), _public_title(item.get("label", "")))
        if key in seen:
            continue
        seen.add(key)
        result.append(
            {
                "domain": key[0],
                "title": key[1] or "知识依据",
                "summary": _public_text(item.get("summary", "")),
                "confidence": item.get("confidence", 0),
                "boundary": _public_text(item.get("boundary", "")),
                "answer_guidance": _public_answer_guidance(item.get("answer_guidance", ())),
            }
        )
        if len(result) >= 3:
            break
    return result


def _answer_guidance_from_knowledge_basis(rows: list[dict[str, object]]) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for row in rows:
        for guidance in _list(row.get("answer_guidance", ())):
            item = _dict(guidance)
            focus = _public_text(item.get("reading_focus", ""))
            boundary = _public_text(item.get("boundary", ""))
            allowed = _public_phrase_list(item.get("allowed_phrases", ()))
            forbidden = _public_phrase_list(item.get("forbidden_phrases", ()))
            key = (focus, boundary)
            if key in seen or not (focus or boundary or allowed or forbidden):
                continue
            seen.add(key)
            result.append(
                {
                    "domain": _domain_label(item.get("domain", "")),
                    "reading_focus": focus,
                    "allowed_phrases": allowed,
                    "forbidden_phrases": forbidden,
                    "boundary": boundary,
                }
            )
            if len(result) >= 3:
                return result
    return result


def _public_answer_guidance(rows: object) -> list[dict[str, object]]:
    result: list[dict[str, object]] = []
    for row in _list(rows):
        item = _dict(row)
        allowed = _public_phrase_list(item.get("allowed_phrases", ()))
        forbidden = _public_phrase_list(item.get("forbidden_phrases", ()))
        focus = _public_text(item.get("reading_focus", ""))
        boundary = _public_text(item.get("boundary", ""))
        if not (allowed or forbidden or focus or boundary):
            continue
        result.append(
            {
                "domain": str(item.get("domain", "")),
                "reading_focus": focus,
                "allowed_phrases": allowed,
                "forbidden_phrases": forbidden,
                "boundary": boundary,
            }
        )
        if len(result) >= 2:
            break
    return result


def _public_phrase_list(value: object) -> list[str]:
    result: list[str] = []
    for row in _list(value):
        text = _public_text(row).strip(" ，；。")
        if text and not text.startswith("answer.") and "." not in text[:16]:
            result.append(text)
        if len(result) >= 4:
            break
    return result


def _selection_reasons(arbitration: dict[str, Any]) -> list[str]:
    rows = []
    for raw in _list(arbitration.get("why_selected")):
        text = _public_reason_text(raw)
        if text:
            rows.append(text)
        if len(rows) >= 4:
            break
    return rows


def _public_reason_text(value: object) -> str:
    text = _public_text(value)
    if not text:
        return ""
    if "evidence." in text or "source_key" in text or "RuleSpec" in text:
        return ""
    text = text.replace("规则候选", "结构候选")
    text = text.replace("置信分", "参考强度")
    text = text.replace("综合权重", "综合依据")
    text = text.replace("来源：", "依据来源：")
    return text.strip("。； ")


def _is_user_visible(row: object) -> bool:
    item = _dict(row)
    return "user" in _list(item.get("role_visibility"))


def _review_flags(
    primary: dict[str, Any],
    quality_gate: dict[str, Any],
    question_focus: dict[str, Any],
    dynamic_state: dict[str, Any],
) -> list[str]:
    flags = [str(row) for row in _list(quality_gate.get("risk_flags")) if str(row)]
    if primary.get("requires_review"):
        flags.append("primary_mainline_requires_review")
    if question_focus.get("status") in {"no_domain_match", "no_primary_domain"}:
        flags.append(str(question_focus.get("status")))
    volatility = float(dynamic_state.get("volatility_score", 0) or 0)
    if volatility >= 0.72:
        flags.append("high_structure_volatility")
    return list(dict.fromkeys(flags))


def _next_action(review_flags: list[str], selected_domain: str) -> str:
    if review_flags:
        return "先保留复核边界，围绕主线证据和反向约束继续追问。"
    if selected_domain:
        return f"可以继续围绕{selected_domain}问题展开细读。"
    return "可以继续选择一个关心方向，让中枢重新聚焦。"


def _primary_public_support(primary: dict[str, Any]) -> list[dict[str, object]]:
    domain = _domain_label(primary.get("domain", ""))
    title = _public_title(primary.get("title", "") or primary.get("domain", ""))
    rows: list[dict[str, object]] = []
    raw_evidence = [str(row) for row in _list(primary.get("evidence")) if str(row)]
    if raw_evidence:
        rows.append(
            {
                "domain": domain,
                "label": "主线条件",
                "summary": f"{title}相关条件已形成，仍需结合扶身材料和压力材料复核。" if title else "当前主线条件已形成，仍需结合支撑和压力复核。",
                "confidence": primary.get("score", 0),
                "boundary": "这里只说明结构依据，不作固定吉凶断语。",
            }
        )
    for raw in raw_evidence:
        if _is_internal_evidence(raw):
            continue
        item = _support_row_from_text(raw, domain=domain, confidence=primary.get("score", 0))
        if item:
            rows.append(item)
        if len(rows) >= 4:
            break
    return rows


def _support_row_from_text(value: str, *, domain: str, confidence: object) -> dict[str, object] | None:
    text = _public_text(value)
    if not text:
        return None
    if "：" in text:
        label, summary = text.split("：", 1)
    elif "分" in text:
        label, summary = "力量参考", text
    else:
        label, summary = "结构依据", text
    label = _public_title(label)
    summary = _public_text(summary)
    if not label or not summary:
        return None
    return {
        "domain": domain,
        "label": label,
        "summary": summary,
        "confidence": confidence,
        "boundary": "这里只说明结构依据，不作固定吉凶断语。",
    }


def _is_internal_evidence(value: str) -> bool:
    text = str(value or "")
    return "evidence." in text or text.startswith("证据 ") or "条件成立" in text


def _dynamic_chain_label(value: object) -> str:
    if isinstance(value, dict):
        nodes = value.get("nodes", ())
        if isinstance(nodes, (list, tuple)):
            node_text = " → ".join(_node_label(row) for row in nodes if str(row))
            if node_text:
                return node_text
        return str(value.get("chain_key", "") or value.get("state", "") or "")
    if isinstance(value, (list, tuple)):
        return " → ".join(_node_label(row) for row in value if str(row))
    return str(value or "")


def _dynamic_work_path_summary(structure_dynamics: dict[str, Any]) -> dict[str, object]:
    chain = _dict(structure_dynamics.get("dominant_chain_v2", {}))
    if not chain:
        return {
            "label": "",
            "path": "",
            "action": "",
            "state": "",
            "confidence": 0,
        }
    node_labels = [str(row) for row in _list(chain.get("node_labels")) if str(row)]
    edge_labels = [str(row) for row in _list(chain.get("edge_labels")) if str(row)]
    path = " → ".join(node_labels) if node_labels else _dynamic_chain_label(chain)
    return {
        "label": _public_title(chain.get("pattern_label", "")) or "核心做功链",
        "path": _public_text(path),
        "action": _public_text("、".join(edge_labels)),
        "state": _public_text(chain.get("state", "")),
        "confidence": chain.get("confidence", chain.get("path_score", 0)),
    }


def _node_labels(value: object) -> list[str]:
    return [_node_label(row) for row in value] if isinstance(value, (list, tuple)) else []


def _node_label(value: object) -> str:
    text = str(value or "")
    return NODE_LABELS.get(text, text)


def _domain_label(value: object) -> str:
    text = str(value or "").strip()
    return DOMAIN_LABELS.get(text, text)


def _public_title(value: object) -> str:
    text = _public_text(value)
    if not text:
        return ""
    text = text.replace("：明确成立", "")
    text = text.replace("：弱候选", "（弱候选）")
    text = text.replace("：需复核", "（需复核）")
    text = text.replace("：成而不纯", "（成而不纯）")
    text = text.replace("规则", "")
    return _domain_label(text).strip("。； ")


def _public_text(value: object) -> str:
    text = str(value or "").strip()
    if not text:
        return ""
    text = text.replace("RuleSpec", "")
    text = text.replace("规则裁决证据", "结构依据")
    text = text.replace("规则主线候选证据", "主线候选依据")
    text = text.replace("规则", "")
    text = text.replace("：明确成立", "")
    text = text.replace("：弱候选", "（弱候选）")
    text = text.replace("：需复核", "（需复核）")
    text = text.replace("：成而不纯", "（成而不纯）")
    text = text.replace("3/3 条件成立", "条件已形成")
    text = text.replace("2/2 条件成立", "条件已形成")
    return " ".join(text.split()).strip(" ，；。")


def _shift_label(value: object) -> str:
    labels = {
        "amplified": "放大",
        "reduced": "减弱",
        "stable": "稳定",
        "destabilized": "失稳",
        "volatile": "波动",
    }
    return labels.get(str(value), str(value or ""))


def _dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _list(value: object) -> list:
    return list(value) if isinstance(value, (list, tuple)) else []
