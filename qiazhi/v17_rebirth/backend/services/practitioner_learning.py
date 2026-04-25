from __future__ import annotations

from typing import Any, Iterable

from v17_rebirth.backend.services.plugin_governance import classify_plugin_governance


PRACTITIONER_LEARNING_CANDIDATES_VERSION = "v17.practitioner.learning_candidates.v1"


_FAMILY_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("pattern_specialization.yangren_gate", ("yangren", "阳刃", "羊刃", "劫财", "blade", "ren_jiasha")),
    ("pattern_specialization.follow_gate", ("false_follow", "follow", "从格", "从势", "从旺", "从弱", "假从")),
    ("pattern_specialization.zaqi_gate", ("zaqi", "杂气", "墓库", "透藏")),
    ("pattern_specialization.transformation_gate", ("huaqi", "化气", "合化")),
    ("climate_field.calibration", ("climate", "调候", "寒暖", "燥湿")),
    ("risk_matrix.calibration", ("risk", "风险", "伤官见官", "枭印夺食", "七杀风险")),
    ("relation_gate.sanhe", ("sanhe", "三合")),
    ("relation_gate.sanhui", ("sanhui", "三会")),
    ("relation_gate.liuhe", ("liuhe", "六合")),
    ("relation_gate.liuchong", ("liuchong", "六冲", "冲")),
    ("relation_gate.muku", ("muku", "墓库")),
    ("relation_dynamics.runtime_origin", ("runtime", "流年", "大运", "运流", "触发")),
    ("ten_gods.calibration", ("ten_god", "十神", "比劫", "印星", "食伤", "财星", "官杀")),
    ("authority.leader_axis", ("use_god", "target_god", "用神", "忌神", "通关", "体用", "主轴")),
    ("narrative.prompt_contract", ("narrative", "prompt", "llm", "断语", "文案", "表达")),
)

_GOVERNANCE_FAMILY_MAP = {
    "pattern_specialization": "pattern_specialization.general",
    "ziping_authority": "authority.leader_axis",
    "climate_field": "climate_field.calibration",
    "blind_theme": "narrative.blind_theme",
    "xiangfa_theme": "narrative.xiangfa_theme",
    "risk_matrix": "risk_matrix.calibration",
    "narrative": "narrative.prompt_contract",
}


def build_practitioner_learning_candidates(
    *,
    feedback_rows: Iterable[dict[str, Any]],
    case_rows: Iterable[dict[str, Any]],
    scope: str = "own",
) -> dict[str, Any]:
    feedback = [dict(row) for row in feedback_rows if isinstance(row, dict)]
    cases = [dict(row) for row in case_rows if isinstance(row, dict)]
    buckets: dict[str, dict[str, Any]] = {}

    for row in feedback:
        family = infer_parameter_family_from_feedback(row)
        bucket = buckets.setdefault(family, _empty_bucket(family))
        status = _norm(row.get("status"))
        score = _feedback_score(row)
        bucket["signal_score"] += score
        bucket["feedback_count"] += 1
        bucket["weighted_feedback_score"] += score
        if status == "reject":
            bucket["reject_count"] += 1
        elif status == "confirm":
            bucket["confirm_count"] += 1
        elif status in {"review", "watch"}:
            bucket["watch_count"] += 1
        _append_unique(bucket["source_plugins"], _text(row.get("plugin_id")), limit=8)
        _append_unique(bucket["source_evidence_ids"], _text(row.get("evidence_id")), limit=8)
        _append_unique(bucket["chart_fingerprints"], _text(row.get("chart_fingerprint")), limit=6)
        _append_unique(bucket["failure_modes"], _text(row.get("payload", {}).get("failure_mode") if isinstance(row.get("payload"), dict) else ""), limit=8)
        _append_unique(bucket["review_notes"], _text(row.get("reason") or row.get("source_summary")), limit=4, max_chars=180)

    for row in cases:
        family = infer_parameter_family_from_case(row)
        bucket = buckets.setdefault(family, _empty_bucket(family))
        status = _norm(row.get("status"))
        score = _case_score(row)
        bucket["signal_score"] += score
        bucket["case_count"] += 1
        bucket["weighted_case_score"] += score
        if status == "benchmark_candidate":
            bucket["benchmark_candidate_count"] += 1
        _append_unique(bucket["source_cases"], _text(row.get("case_key") or row.get("case_title")), limit=8)
        _append_unique(bucket["chart_fingerprints"], _text(row.get("chart_fingerprint")), limit=6)
        for key in ("failure_modes", "boundary_flags", "tags", "expected_patterns", "expected_risks"):
            value = row.get(key)
            if isinstance(value, list):
                for item in value:
                    target = "failure_modes" if key == "failure_modes" else "audit_tags"
                    _append_unique(bucket[target], _text(item), limit=10)
        for feedback_id in row.get("source_feedback_ids") or []:
            _append_unique(bucket["source_feedback_ids"], _text(feedback_id), limit=8)
        _append_unique(bucket["review_notes"], _text(row.get("expected_notes") or row.get("description")), limit=4, max_chars=180)

    candidates = [_finalize_bucket(bucket) for bucket in buckets.values()]
    candidates.sort(
        key=lambda row: (
            -float(row.get("signal_score") or 0.0),
            str(row.get("parameter_family") or ""),
        )
    )
    candidates = candidates[:12]
    manual_review_count = sum(1 for row in candidates if row.get("safety_gate") == "manual_review_required")
    top_family = str(candidates[0].get("parameter_family") or "") if candidates else ""
    return {
        "ok": True,
        "protocol": PRACTITIONER_LEARNING_CANDIDATES_VERSION,
        "scope": str(scope or "own").strip() or "own",
        "summary": {
            "feedback_count": len(feedback),
            "case_count": len(cases),
            "candidate_count": len(candidates),
            "manual_review_required_count": manual_review_count,
            "top_family": top_family,
            "learning_loop_state": "review_candidates_ready" if candidates else "collect_more_practitioner_signals",
        },
        "candidates": candidates,
        "guardrails": [
            "candidate plans are review-only",
            "no runtime parameter is changed by this report",
            "synthetic and practitioner benchmark checks are required before promotion",
        ],
    }


def infer_parameter_family_from_feedback(row: dict[str, Any]) -> str:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    haystack = " ".join(
        [
            _text(row.get("plugin_id")),
            _text(row.get("evidence_id")),
            _text(row.get("claim_id")),
            _text(row.get("evidence_type")),
            _text(row.get("target_god")),
            _text(row.get("source_title")),
            _text(row.get("source_summary")),
            _text(row.get("reason")),
            " ".join(_flatten_text_values(payload)),
        ]
    )
    return _infer_family(haystack, plugin_id=_text(row.get("plugin_id")))


def infer_parameter_family_from_case(row: dict[str, Any]) -> str:
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    haystack = " ".join(
        [
            _text(row.get("case_key")),
            _text(row.get("case_title")),
            _text(row.get("description")),
            _text(row.get("expected_notes")),
            _text(row.get("luck_pillar")),
            _text(row.get("flow_pillar")),
            " ".join(_flatten_text_values(payload)),
            " ".join(_list_text(row.get("tags"))),
            " ".join(_list_text(row.get("expected_patterns"))),
            " ".join(_list_text(row.get("expected_use_gods"))),
            " ".join(_list_text(row.get("expected_risks"))),
            " ".join(_list_text(row.get("boundary_flags"))),
            " ".join(_list_text(row.get("failure_modes"))),
        ]
    )
    return _infer_family(haystack, plugin_id="")


def _infer_family(haystack: str, *, plugin_id: str) -> str:
    text = haystack.lower()
    for family, tokens in _FAMILY_KEYWORDS:
        for token in tokens:
            if token and token.lower() in text:
                return family
    if plugin_id:
        profile = classify_plugin_governance(plugin_id=plugin_id)
        learning_family = _text(profile.get("learning_family"))
        if learning_family.startswith("relation."):
            return f"relation_gate.{learning_family.split('.', 1)[1]}"
        if learning_family in _GOVERNANCE_FAMILY_MAP:
            return _GOVERNANCE_FAMILY_MAP[learning_family]
    return "unclassified.practitioner_signal"


def _empty_bucket(family: str) -> dict[str, Any]:
    return {
        "candidate_id": f"candidate::practitioner::{family}",
        "parameter_family": family,
        "signal_score": 0.0,
        "feedback_count": 0,
        "case_count": 0,
        "reject_count": 0,
        "watch_count": 0,
        "confirm_count": 0,
        "benchmark_candidate_count": 0,
        "weighted_feedback_score": 0.0,
        "weighted_case_score": 0.0,
        "source_plugins": [],
        "source_evidence_ids": [],
        "source_feedback_ids": [],
        "source_cases": [],
        "chart_fingerprints": [],
        "failure_modes": [],
        "audit_tags": [],
        "review_notes": [],
    }


def _finalize_bucket(bucket: dict[str, Any]) -> dict[str, Any]:
    score = round(float(bucket.get("signal_score") or 0.0), 3)
    reject_count = int(bucket.get("reject_count") or 0)
    watch_count = int(bucket.get("watch_count") or 0)
    benchmark_count = int(bucket.get("benchmark_candidate_count") or 0)
    issue_count = reject_count + watch_count + benchmark_count
    priority = "high" if score >= 5.5 or reject_count >= 2 or benchmark_count >= 2 else "medium" if score >= 2.4 or issue_count else "low"
    return {
        **bucket,
        "signal_score": score,
        "weighted_feedback_score": round(float(bucket.get("weighted_feedback_score") or 0.0), 3),
        "weighted_case_score": round(float(bucket.get("weighted_case_score") or 0.0), 3),
        "issue_count": issue_count,
        "priority": priority,
        "recommended_action": _recommended_action(str(bucket.get("parameter_family") or ""), issue_count=issue_count),
        "safety_gate": "manual_review_required",
        "review_hints": _review_hints(bucket, issue_count=issue_count),
    }


def _recommended_action(family: str, *, issue_count: int) -> str:
    if not issue_count:
        return "expand_benchmark_coverage"
    if family.startswith("narrative."):
        return "review_prompt_contract"
    if family.startswith("relation_") or family.startswith("relation."):
        return "review_relation_gate_and_runtime_origin"
    if family.startswith("pattern_specialization."):
        return "review_classical_pattern_gate"
    if family.startswith("authority."):
        return "review_authority_weighting"
    if family.startswith("ten_gods."):
        return "review_static_ten_gods_calibration"
    return "manual_protocol_review"


def _review_hints(bucket: dict[str, Any], *, issue_count: int) -> list[str]:
    family = str(bucket.get("parameter_family") or "")
    hints: list[str] = []
    if issue_count:
        hints.append("先复核命理师标注与原始证据，再决定是否进入 synthetic shadow run。")
    else:
        hints.append("当前以确认型反馈为主，可优先扩充基准样本而非调参。")
    if "yangren" in family:
        hints.append("重点检查羊刃/劫财根气门槛、刃杀同见条件和误报保护。")
    elif "follow" in family:
        hints.append("重点检查从格根气、帮身残根和假从边界。")
    elif "zaqi" in family:
        hints.append("重点检查墓库透藏、月令司令和杂气成格条件。")
    elif family.startswith("relation"):
        hints.append("重点检查原局/大运/流年来源，不让运行触发冒充原局结构。")
    elif family.startswith("narrative"):
        hints.append("重点检查 LLM 断语是否把候选说成定论。")
    elif family.startswith("authority") or family.startswith("ten_gods"):
        hints.append("重点检查体用主轴、通关神和静态十神能量权重。")
    notes = bucket.get("review_notes") if isinstance(bucket.get("review_notes"), list) else []
    for note in notes[:2]:
        text = _text(note)
        if text:
            hints.append(text)
    return hints[:4]


def _feedback_score(row: dict[str, Any]) -> float:
    status = _norm(row.get("status"))
    base = {"reject": 1.4, "review": 1.0, "watch": 0.8, "confirm": 0.32}.get(status, 0.5)
    return base * _row_weight(row, "reviewer_weight")


def _case_score(row: dict[str, Any]) -> float:
    status = _norm(row.get("status"))
    base = 1.45 if status == "benchmark_candidate" else 0.8 if status in {"accepted", "submitted"} else 0.35
    failure_bonus = min(0.9, 0.18 * len(_list_text(row.get("failure_modes"))))
    boundary_bonus = min(0.5, 0.1 * len(_list_text(row.get("boundary_flags"))))
    return (base + failure_bonus + boundary_bonus) * _row_weight(row, "owner_weight")


def _row_weight(row: dict[str, Any], key: str) -> float:
    try:
        weight = float(row.get(key) or 1.0)
    except Exception:
        weight = 1.0
    try:
        confidence = float(row.get("confidence") or 0.0)
    except Exception:
        confidence = 0.0
    confidence_factor = 1.0 if confidence <= 0 else 0.7 + min(1.0, max(0.0, confidence)) * 0.6
    return max(0.4, min(3.0, weight)) * confidence_factor


def _flatten_text_values(value: Any) -> list[str]:
    out: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            out.append(_text(key))
            out.extend(_flatten_text_values(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(_flatten_text_values(item))
    else:
        text = _text(value)
        if text:
            out.append(text)
    return out[:80]


def _list_text(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _append_unique(target: list[str], value: str, *, limit: int, max_chars: int = 120) -> None:
    text = value.strip()[:max_chars]
    if not text or text in target:
        return
    if len(target) >= limit:
        return
    target.append(text)


def _text(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return _text(value).lower()
