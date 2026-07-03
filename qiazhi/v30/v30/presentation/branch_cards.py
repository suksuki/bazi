from __future__ import annotations

from v30.presentation.product_contracts import BranchCard, PractitionerAction


DOMAIN_LABELS = {
    "overview": "整体",
    "structure": "结构",
    "career": "事业",
    "wealth": "财运",
    "relationship": "关系",
    "health": "健康",
    "family": "亲情",
    "timing": "时运",
    "decision": "决策",
    "hidden_factor": "隐藏线索",
    "personality": "性情",
    "useful_god": "用神",
}

CONFLICT_TYPE_LABELS = {
    "close_branch_probability": "两条判断接近",
    "requires_calibration": "需要补一个背景",
    "counter_evidence_present": "有反向证据",
}


def branch_cards_from_conflict_audit(audits: list[dict[str, object]], *, role_key: str) -> list[dict[str, object]]:
    diagnostic = role_key in {"practitioner", "admin", "analyst", "lab"}
    rows: list[dict[str, object]] = []
    seen: set[str] = set()
    for audit in audits:
        if not isinstance(audit, dict):
            continue
        conflict_count = _int_count(audit.get("conflict_count"))
        if conflict_count <= 0:
            continue
        domain = str(audit.get("domain") or "overview")
        question = str(audit.get("needed_question") or "").strip()
        key = f"{domain}:{question or audit.get('top_claim_id') or audit.get('top_candidate_id') or len(rows)}"
        if key in seen:
            continue
        seen.add(key)
        top = _bounded_float(audit.get("top_confidence"))
        runner_up = _bounded_float(audit.get("runner_up_confidence"))
        gap = _bounded_float(audit.get("confidence_gap"))
        labels = _conflict_type_labels(audit.get("conflict_types"))
        title = _branch_title(domain, labels)
        user_summary = _user_summary(domain, labels, question=question, gap=gap)
        practitioner_summary = _practitioner_summary(domain, labels, gap=gap)
        source_ids = []
        if diagnostic:
            source_ids = [
                str(row)
                for row in [
                    audit.get("top_candidate_id"),
                    audit.get("runner_up_candidate_id"),
                ]
                if str(row or "")
            ]
        card = BranchCard(
            branch_card_id=f"branch-card:{domain}:{len(rows) + 1}",
            source_conflict_id=str(audit.get("top_claim_id") or audit.get("top_candidate_id") or "") if diagnostic else "",
            domain=domain,
            domain_label=domain_label(domain),
            topic=domain_label(domain),
            title=title,
            user_summary=user_summary,
            practitioner_summary=practitioner_summary if diagnostic else "",
            key_question=question,
            status="needs_calibration",
            top_confidence=top,
            runner_up_confidence=runner_up,
            confidence_gap=gap,
            confidence_label=_confidence_label(top, runner_up, gap),
            signal_bound_candidate_count=_int_count(audit.get("signal_bound_candidate_count")) if diagnostic else 0,
            candidate_signal_count=_int_count(audit.get("candidate_signal_count")) if diagnostic else 0,
            source_candidate_ids=source_ids,
            conflict_types=labels,
            practitioner_actions=_practitioner_actions(domain, question) if diagnostic else [],
            role_visibility=(
                ["practitioner", "admin", "analyst", "lab"]
                if diagnostic
                else ["guest", "user"]
            ),
            allowed_user_text=[title, user_summary, question] if question else [title, user_summary],
            forbidden_user_text=["internal policy keys", "training/debug fields", "raw runtime status"],
        )
        rows.append(card.model_dump(mode="json"))
    return rows[:8 if diagnostic else 4]


def conflict_cards_for_legacy_surface(branch_cards: list[dict[str, object]], *, diagnostic: bool) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for card in branch_cards:
        if not isinstance(card, dict):
            continue
        rows.append(
            {
                "domain": str(card.get("domain") or ""),
                "domain_label": str(card.get("domain_label") or ""),
                "conflict_count": len(_as_list(card.get("conflict_types"))) or 1,
                "conflict_types": _as_list(card.get("conflict_types"))[:3],
                "top_candidate_id": (
                    _as_list(card.get("source_candidate_ids"))[0]
                    if diagnostic and _as_list(card.get("source_candidate_ids"))
                    else ""
                ),
                "top_confidence": _bounded_float(card.get("top_confidence")),
                "runner_up_confidence": _bounded_float(card.get("runner_up_confidence")),
                "confidence_gap": _bounded_float(card.get("confidence_gap")),
                "needed_question": str(card.get("key_question") or ""),
                "resolution_policy": str(card.get("user_summary") or "先保留分支，等待更多证据。"),
                "signal_bound_candidate_count": _int_count(card.get("signal_bound_candidate_count")) if diagnostic else 0,
                "candidate_signal_count": _int_count(card.get("candidate_signal_count")) if diagnostic else 0,
                "branch_card_id": str(card.get("branch_card_id") or ""),
                "boundary": "legacy_conflict_card_uses_product_branch_card_without_raw_policy_keys",
            }
        )
    return rows


def domain_label(domain: str) -> str:
    return DOMAIN_LABELS.get(domain, domain or "整体")


def _conflict_type_labels(value: object) -> list[str]:
    rows = [str(row) for row in _as_list(value) if str(row)]
    labels = [CONFLICT_TYPE_LABELS.get(row, row) for row in rows]
    return labels or ["分支待校准"]


def _branch_title(domain: str, labels: list[str]) -> str:
    if "需要补一个背景" in labels:
        return f"{domain_label(domain)}判断需要补一条关键线索"
    if "有反向证据" in labels:
        return f"{domain_label(domain)}判断存在反向证据"
    return f"{domain_label(domain)}出现两条接近判断"


def _user_summary(domain: str, labels: list[str], *, question: str, gap: float) -> str:
    if question:
        return f"{domain_label(domain)}这里不宜急着定死；补充这个问题后，结论会更贴近实际：{question}"
    if gap <= 0.08:
        return f"{domain_label(domain)}有两条判断很接近，先把主分支和备选都保留。"
    if "有反向证据" in labels:
        return f"{domain_label(domain)}主判断有证据支持，但也有反向线索，结论需要留边界。"
    return f"{domain_label(domain)}主判断暂时占优，但仍需要后续证据确认。"


def _practitioner_summary(domain: str, labels: list[str], *, gap: float) -> str:
    reason = "、".join(labels)
    if gap <= 0.08:
        return f"{domain_label(domain)}主备分支差距很小，适合由命理师结合实际反馈做校准。"
    return f"{domain_label(domain)}分支校准原因：{reason}；选择只反馈权重和训练信号，不改命盘事实。"


def _confidence_label(top: float, runner_up: float, gap: float) -> str:
    if top <= 0:
        return "待证据"
    if gap <= 0.05:
        return "两支非常接近"
    if gap <= 0.12:
        return "主支略占优"
    if runner_up > 0:
        return "主支较清楚"
    return "单支判断"


def _practitioner_actions(domain: str, question: str) -> list[PractitionerAction]:
    label = domain_label(domain)
    return [
        PractitionerAction(
            action_id="accept_primary",
            label="更像这个表现",
            meaning=f"命理师确认{label}主分支更贴近当前案例。",
            effect="raise_primary_branch_weight",
        ),
        PractitionerAction(
            action_id="keep_as_secondary",
            label="作为辅助参考",
            meaning=f"保留{label}备选分支，用作边界和反证。",
            effect="keep_secondary_branch_context",
        ),
        PractitionerAction(
            action_id="reject_for_now",
            label="暂不采用",
            meaning=f"当前证据不足，{label}这条分支先不进入主结论。",
            effect="reduce_branch_surface_priority",
        ),
        PractitionerAction(
            action_id="ask_probe",
            label="需要追问确认",
            meaning=question or f"需要补一条{label}相关背景。",
            effect="convert_branch_to_probe_question",
        ),
    ]


def _bounded_float(value: object, default: float = 0.0) -> float:
    try:
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return default


def _int_count(value: object, default: int = 0) -> int:
    try:
        return max(0, int(value))
    except (TypeError, ValueError):
        return default


def _as_list(value: object) -> list[object]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return []
