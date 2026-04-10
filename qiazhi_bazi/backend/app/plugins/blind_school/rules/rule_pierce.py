"""六穿（害）：与子平害同序；detail 含「穿」以便 L1 harm → pierce 与盲派 η_pierce。"""
from __future__ import annotations

from typing import Any, Dict, List

from app.schemas.bazi_metadata import ConflictPoint, FourPillars

_SIX_HARM_LABELS: Dict[frozenset[str], str] = {
    frozenset(("子", "未")): "子未穿（害）",
    frozenset(("丑", "午")): "丑午穿（害）",
    frozenset(("寅", "巳")): "寅巳穿（害）",
    frozenset(("卯", "辰")): "卯辰穿（害）",
    frozenset(("申", "亥")): "申亥穿（害）",
    frozenset(("酉", "戌")): "酉戌穿（害）",
}


def _compute_pierce_semantic_intensity(vector: Dict[str, Any]) -> float:
    """
    语义强度 0..1：由 Abs 相对损耗（体节点 delta/source）、反噬/解锁比、以及 η 抬升的折损感共同驱动。
    """
    src = max(float(vector.get("source_abs") or 0.0), 1e-9)
    bd = vector.get("body_damage_estimation") if isinstance(vector.get("body_damage_estimation"), dict) else {}
    delta = float((bd or {}).get("delta_abs") or 0.0)
    loss_ratio = min(1.0, delta / src)
    risk = float(vector.get("backfire_risk") or 0.0)
    gain = max(float(vector.get("unlock_gain") or 0.0), 1e-9)
    risk_ratio = min(1.0, risk / gain)
    eta = float(vector.get("eta") or 0.8)
    eta_lift = min(1.0, max(0.0, (eta - 0.65) / 0.34))
    raw = 0.5 * loss_ratio + 0.35 * risk_ratio + 0.15 * eta_lift
    return round(max(0.0, min(1.0, raw)), 4)


def attach_pierce_semantic_intensity(work_vectors: List[Dict[str, Any]]) -> None:
    """就地写入每条穿局 work_vector 的 semantic_intensity。"""
    for v in work_vectors:
        if str(v.get("type") or "") != "穿":
            continue
        v["semantic_intensity"] = _compute_pierce_semantic_intensity(v)


def collect_pierce_semantics(work_vectors: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """结构化摘要，随 meta.mangpai_pierce_semantics 下发前端。"""
    out: List[Dict[str, Any]] = []
    for v in work_vectors:
        if str(v.get("type") or "") != "穿":
            continue
        detail = str(v.get("detail") or "").strip() or "未命名穿局"
        out.append(
            {
                "skill_id": "mp_pierce_01",
                "detail": detail,
                "semantic_intensity": float(v.get("semantic_intensity") or _compute_pierce_semantic_intensity(v)),
            }
        )
    return out


def _pierce_semantic_prefix(semantic_intensity: float) -> str:
    """按 semantic_intensity 分级前缀，供 LLM 对齐语气与物理损耗严重度。"""
    si = float(semantic_intensity)
    if si > 0.8:
        return "[CRITICAL_PIERCE] 剧烈穿倒"
    if si > 0.4:
        return "[STABLE_PIERCE] 稳态穿破"
    return "[TRACE_PIERCE] 微弱穿扰"


def resolve_pierce_eta(settings: Dict[str, float]) -> float:
    """穿局物理损耗下限 η_pierce（与 blind_work_evaluator 穿支升格一致）。"""
    return float(settings.get("MANGPAI_ETA_PIERCE", settings.get("MANGPAI_SIX_HARM_ETA", 0.99)))


def scan_six_harm_points(pillars: FourPillars) -> List[ConflictPoint]:
    """扫描四柱地支两两出现的六穿（害），生成 L1 kind=harm（走 pierce 原子算子）。"""
    branches = {
        "year": pillars.year.branch,
        "month": pillars.month.branch,
        "day": pillars.day.branch,
        "hour": pillars.hour.branch,
    }
    keys = list(branches.keys())
    out: List[ConflictPoint] = []
    seen: set[frozenset[str]] = set()
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            p1, p2 = keys[i], keys[j]
            b1, b2 = branches[p1], branches[p2]
            fk = frozenset((b1, b2))
            if fk not in _SIX_HARM_LABELS:
                continue
            if fk in seen:
                continue
            seen.add(fk)
            out.append(
                ConflictPoint(
                    kind="harm",
                    positions=[f"{p1}_branch", f"{p2}_branch"],
                    detail=_SIX_HARM_LABELS[fk],
                )
            )
    return out


def pierce_chip_logs_from_work_vectors(work_vectors: List[Dict[str, Any]]) -> List[str]:
    """穿局 chip 文案（供 merge_mangpai_chip_logs 聚合）；携带 semantic_intensity。"""
    logs: List[str] = []
    for v in work_vectors:
        if str(v.get("type") or "") != "穿":
            continue
        detail = str(v.get("detail") or "").strip() or "未命名穿局"
        si = float(v.get("semantic_intensity") or _compute_pierce_semantic_intensity(v))
        tier = _pierce_semantic_prefix(si)
        logs.append(
            f"{tier} [MANGPAI_CHIP] 发现穿局：{detail}，semantic_intensity={si:.4f}（mp_pierce_01），能量发生物理折损。"
        )
    return logs
