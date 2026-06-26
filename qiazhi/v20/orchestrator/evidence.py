from __future__ import annotations

from typing import Any

from v20.orchestrator.schema import EvidenceItem


EVIDENCE_COMPILER_VERSION = "v20.orchestrator_evidence_compiler.v1"


def compile_orchestrator_evidence(
    *,
    decision_report: dict[str, Any],
    feature_state_model: dict[str, Any],
    structure_dynamics: dict[str, Any],
    question_intent_model: dict[str, Any],
    time_context: dict[str, Any],
) -> dict[str, Any]:
    items: list[EvidenceItem] = []
    items.extend(_decision_evidence(decision_report))
    items.extend(_knowledge_evidence(decision_report))
    items.extend(_portrait_evidence(decision_report))
    items.extend(_feature_state_evidence(feature_state_model))
    items.extend(_structure_evidence(structure_dynamics))
    items.extend(_question_intent_evidence(question_intent_model))
    items.extend(_time_evidence(time_context))
    deduped = _dedupe(items)
    return {
        "version": EVIDENCE_COMPILER_VERSION,
        "status": "ready" if deduped else "empty",
        "evidence_count": len(deduped),
        "items": [row.to_dict() for row in deduped],
        "runtime_mutation": False,
        "guardrails": [
            "EVIDENCE_ITEMS_NORMALIZE_EXISTING_RUNTIME_SIGNALS",
            "NO_NEW_FACTS_CREATED_BY_ORCHESTRATOR",
            "ROLE_VISIBILITY_IS_DECLARED_PER_ITEM",
        ],
    }


def _decision_evidence(decision_report: dict[str, Any]) -> list[EvidenceItem]:
    rows: list[EvidenceItem] = []
    for index, row in enumerate(decision_report.get("decisions", ())):
        if not isinstance(row, dict):
            continue
        key = str(row.get("decision_key") or row.get("rule_key") or f"decision.{index}")
        domain = str(row.get("domain") or "general")
        score = _score(row.get("score", 0.0))
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.decision.{_safe(key)}",
                source_type="decision",
                source_key=key,
                domain=domain,
                label=str(row.get("label") or key),
                summary=_first_text(row.get("support", ())) or str(row.get("status") or ""),
                confidence=score,
                weight=score + 0.24,
                supports=(key,),
                weakens=tuple(str(x) for x in row.get("weakening", ())[:3]) if isinstance(row.get("weakening", ()), (list, tuple)) else (),
                boundary="规则裁决证据，只能支持结构主线，不能单独形成吉凶断语。",
                role_visibility=("analyst", "admin"),
            )
        )
    for index, row in enumerate(decision_report.get("mainlines", ())):
        if not isinstance(row, dict):
            continue
        key = str(row.get("mainline_key") or f"mainline.{index}")
        domain = str(row.get("domain") or "general")
        score = _score(row.get("score", 0.0))
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.mainline.{_safe(key)}",
                source_type="decision_mainline",
                source_key=key,
                domain=domain,
                label=str(row.get("title") or key),
                summary=_first_text(row.get("support", ())) or str(row.get("status") or ""),
                confidence=score,
                weight=score + 0.32,
                supports=(key,),
                boundary="规则主线候选证据，需与问题意图、画像和结构动态共同仲裁。",
                role_visibility=("user", "analyst", "admin"),
            )
        )
    return rows


def _knowledge_evidence(decision_report: dict[str, Any]) -> list[EvidenceItem]:
    rows: list[EvidenceItem] = []
    seen: set[str] = set()
    for index, decision in enumerate(decision_report.get("decisions", ())):
        if not isinstance(decision, dict):
            continue
        decision_key = str(decision.get("decision_key") or decision.get("rule_key") or f"decision.{index}")
        domain = str(decision.get("domain") or "general")
        base_score = _score(decision.get("score", 0.0))
        for ref_index, ref in enumerate(decision.get("knowledge_rule_refs", ())[:3]):
            if not isinstance(ref, dict) or ref.get("runtime_allowed") is not True:
                continue
            source_id = str(ref.get("source_knowledge_id") or f"knowledge.{index}.{ref_index}")
            evidence_id = f"evidence.knowledge.{_safe(decision_key)}.{_safe(source_id)}"
            if evidence_id in seen:
                continue
            seen.add(evidence_id)
            labels = [str(row) for row in ref.get("portrait_labels", ())[:2] if str(row)]
            questions = [str(row.get("title", "")) for row in ref.get("question_outputs", ())[:2] if isinstance(row, dict) and row.get("title")]
            summary = "、".join(dict.fromkeys((*labels, *questions))) or str(ref.get("title") or "知识依据")
            confidence = _score(base_score + float(ref.get("policy_source_trust_delta", 0.0) or 0.0))
            weight = min(1.0, confidence + 0.18 + float(ref.get("policy_mapping_weight_delta", 0.0) or 0.0))
            rows.append(
                EvidenceItem(
                    evidence_id=evidence_id,
                    source_type="knowledge_basis",
                    source_key=source_id,
                    domain=domain,
                    label=_public_knowledge_label(ref),
                    summary=summary,
                    confidence=confidence,
                    weight=round(weight, 3),
                    supports=(decision_key,),
                    boundary="知识依据用于校对判断范围和表达边界，不能单独替代命局结构。",
                    answer_guidance=_public_answer_guidance(ref),
                    role_visibility=("user", "analyst", "admin"),
                )
            )
    return rows


def _portrait_evidence(decision_report: dict[str, Any]) -> list[EvidenceItem]:
    portrait = decision_report.get("portrait_projection", {})
    axes = portrait.get("axes", ()) if isinstance(portrait, dict) else ()
    rows: list[EvidenceItem] = []
    for index, row in enumerate(axes):
        if not isinstance(row, dict):
            continue
        key = str(row.get("axis_id") or f"portrait.axis.{index}")
        domain = str(row.get("domain") or "general")
        score = _score(row.get("peak_confidence", row.get("score", 0.0)))
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.portrait.{_safe(key)}",
                source_type="portrait_axis",
                source_key=key,
                domain=domain,
                label=str(row.get("label") or key),
                summary=str(row.get("profile_summary") or row.get("summary") or ""),
                confidence=score,
                weight=score + 0.12,
                supports=(key,),
                boundary="画像轴只能作为主题投射和主线加权，不替代八字事实。",
                role_visibility=("user", "analyst", "admin"),
            )
        )
    return rows


def _public_knowledge_label(ref: dict[str, object]) -> str:
    title = str(ref.get("title") or "").strip()
    if not title or title.startswith("Extracted rule") or _ascii_ratio(title) > 0.55:
        return "知识依据"
    return title


def _ascii_ratio(value: str) -> float:
    if not value:
        return 0.0
    ascii_count = sum(1 for ch in value if ord(ch) < 128 and not ch.isspace())
    return ascii_count / max(1, len(value))


def _feature_state_evidence(feature_state_model: dict[str, Any]) -> list[EvidenceItem]:
    rows: list[EvidenceItem] = []
    for index, row in enumerate(feature_state_model.get("priority_features", ())):
        if not isinstance(row, dict):
            continue
        key = str(row.get("feature_id") or f"feature_state.{index}")
        domain = str(row.get("domain") or "general")
        score = _score(row.get("priority", 0.0))
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.feature_state.{_safe(key)}",
                source_type="feature_state",
                source_key=key,
                domain=domain,
                label=str(row.get("title") or key),
                summary=str(row.get("boundary") or row.get("state") or ""),
                confidence=score,
                weight=score + 0.08,
                supports=(key,),
                boundary="特征状态用于排序和聚焦，不单独下结论。",
                role_visibility=("analyst", "admin"),
            )
        )
    return rows


def _structure_evidence(structure_dynamics: dict[str, Any]) -> list[EvidenceItem]:
    chain = structure_dynamics.get("primary_dynamic_chain", {})
    if not isinstance(chain, dict) or not chain.get("nodes"):
        chain = structure_dynamics.get("dominant_chain_v2", {})
    if not isinstance(chain, dict) or not chain.get("nodes"):
        chain = structure_dynamics.get("legacy_dynamic_chain", {})
    if not isinstance(chain, dict):
        return []
    rows: list[EvidenceItem] = []
    key = str(chain.get("chain_key") or "structure.primary_dynamic_chain")
    score = _score(chain.get("confidence", structure_dynamics.get("volatility_score", 0.0)))
    node_labels = [str(row) for row in chain.get("node_labels", ()) if str(row)]
    summary = " → ".join(node_labels) if node_labels else " → ".join(str(x) for x in chain.get("nodes", ()) if str(x))
    rows.append(
        EvidenceItem(
            evidence_id=f"evidence.structure.{_safe(key)}",
            source_type="structure_dynamics",
            source_key=key,
            domain="structure",
            label=str(chain.get("pattern_label") or chain.get("label") or "结构动态主链"),
            summary=summary,
            confidence=score,
            weight=score + 0.18,
            supports=(key,),
            boundary="结构动态反映引动和链条状态，需要规则与问题意图共同确认。",
            role_visibility=("user", "analyst", "admin"),
        )
    )
    chain_v2 = structure_dynamics.get("dominant_chain_v2", {})
    if isinstance(chain_v2, dict) and chain_v2.get("nodes"):
        v2_key = str(chain_v2.get("chain_key") or "structure.dynamic_work_path")
        path_score = _score(chain_v2.get("confidence", chain_v2.get("path_score", score)))
        node_labels = [str(row) for row in chain_v2.get("node_labels", ()) if str(row)]
        edge_labels = [str(row) for row in chain_v2.get("edge_labels", ()) if str(row)]
        summary = " → ".join(node_labels) if node_labels else " → ".join(str(x) for x in chain_v2.get("nodes", ()) if str(x))
        if edge_labels:
            summary = f"{summary}；作用：{'、'.join(edge_labels)}"
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.structure_v2.{_safe(v2_key)}",
                source_type="structure_dynamics_v2",
                source_key=v2_key,
                domain="structure",
                label=str(chain_v2.get("pattern_label") or "核心做功链"),
                summary=summary,
                confidence=path_score,
                weight=path_score + 0.22,
                supports=(v2_key,),
                boundary="结构动态 v2 只说明当前八字和岁运里的做功通路，不单独下结论。",
                role_visibility=("user", "analyst", "admin"),
            )
        )
    return rows


def _question_intent_evidence(question_intent_model: dict[str, Any]) -> list[EvidenceItem]:
    selected = question_intent_model.get("selected_question_intent", {})
    if not isinstance(selected, dict) or not selected:
        return []
    key = str(selected.get("question_key") or "question.selected")
    domain = str(selected.get("domain") or "general")
    score = _score(selected.get("intent_priority", 0.0))
    return [
        EvidenceItem(
            evidence_id=f"evidence.question_intent.{_safe(key)}",
            source_type="question_intent",
            source_key=key,
            domain=domain,
            label=str(selected.get("title") or key),
            summary=str(selected.get("primary_intent_type") or ""),
            confidence=score,
            weight=score + 0.16,
            supports=(key,),
            boundary="用户问题意图只影响主线优先级，不创造事实。",
            role_visibility=("user", "analyst", "admin"),
        )
    ]


def _time_evidence(time_context: dict[str, Any]) -> list[EvidenceItem]:
    status = str(time_context.get("status") or "")
    if status != "ready":
        return []
    rows: list[EvidenceItem] = []
    for index, layer in enumerate(time_context.get("layers", ())):
        if not isinstance(layer, dict):
            continue
        key = str(layer.get("layer_key") or f"time.{index}")
        rows.append(
            EvidenceItem(
                evidence_id=f"evidence.time.{_safe(key)}",
                source_type="time_context",
                source_key=key,
                domain="time",
                label=str(layer.get("label") or key),
                summary=str(layer.get("pillar") or ""),
                confidence=0.72,
                weight=0.78,
                supports=(key,),
                boundary="岁运层只作为触发背景，不能单独作事件断语。",
                role_visibility=("user", "analyst", "admin"),
            )
        )
    return rows


def _dedupe(items: list[EvidenceItem]) -> tuple[EvidenceItem, ...]:
    result: dict[str, EvidenceItem] = {}
    for item in items:
        result[item.evidence_id] = item
    return tuple(result.values())


def _score(value: object) -> float:
    try:
        return round(max(0.0, min(1.0, float(value or 0.0))), 3)
    except (TypeError, ValueError):
        return 0.0


def _first_text(values: object) -> str:
    if isinstance(values, (list, tuple)):
        for value in values:
            text = str(value or "").strip()
            if text:
                return text
    return ""


def _public_answer_guidance(rows: object) -> tuple[dict[str, object], ...]:
    if isinstance(rows, dict) and not rows.get("answer_guidance"):
        domain = str(rows.get("domain", ""))
        boundary = str(rows.get("boundary", ""))
        if not boundary and not rows.get("answer_guidance_keys"):
            return ()
        return (
            {
                "domain": domain,
                "reading_focus": "围绕知识边界组织表达，不把结构线索写成确定事件。",
                "allowed_phrases": ["结构", "证据", "边界", "复核"],
                "forbidden_phrases": ["必然", "一定", "保证", "注定"],
                "boundary": boundary or "知识依据只能校对表达范围，不能单独替代命局结构。",
            },
        )
    if isinstance(rows, dict):
        rows = rows.get("answer_guidance", ())
    result: list[dict[str, object]] = []
    if not isinstance(rows, (list, tuple)):
        return ()
    for row in rows:
        if not isinstance(row, dict):
            continue
        result.append(
            {
                "domain": str(row.get("domain", "")),
                "reading_focus": str(row.get("reading_focus", "")),
                "allowed_phrases": _public_phrase_list(row.get("allowed_phrases", ())),
                "forbidden_phrases": _public_phrase_list(row.get("forbidden_phrases", ())),
                "boundary": str(row.get("boundary", "")),
            }
        )
        if len(result) >= 2:
            break
    return tuple(result)


def _public_phrase_list(value: object) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    result: list[str] = []
    for row in value:
        text = str(row).strip()
        if text and not text.startswith("answer.") and "." not in text[:16]:
            result.append(text)
        if len(result) >= 4:
            break
    return result


def _safe(value: str) -> str:
    return "".join(ch if ch.isalnum() else "." for ch in str(value or "").strip()).strip(".")[:120] or "item"
