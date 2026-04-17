"""
Decision Inbox 门控遥测：统计哪些插件 / Skill 签名最常伴随「可推送冲突卡片」或「被门控抑制」。
供 PluginRegistry.get_conflict_hotspots 聚合。
"""
from __future__ import annotations

import threading
from collections import defaultdict
from typing import Any, Dict, List, Tuple

_lock = threading.RLock()
# signature -> (eligible_hits, gated_hits)
_counts: Dict[str, Tuple[int, int]] = defaultdict(lambda: (0, 0))


def _normalize_signature(raw: str) -> str:
    s = str(raw or "").strip()
    return s[:512] if len(s) > 512 else s


def record_decision_inbox_signal(*, signature: str, eligible: bool) -> None:
    sig = _normalize_signature(signature)
    if not sig:
        return
    with _lock:
        el, gt = _counts.get(sig, (0, 0))
        if eligible:
            el += 1
        else:
            gt += 1
        _counts[sig] = (el, gt)


def get_conflict_hotspot_rows(*, top_n: int = 24) -> List[Dict[str, Any]]:
    with _lock:
        items = list(_counts.items())
    scored: List[Tuple[float, str, int, int]] = []
    for sig, (el, gt) in items:
        total = el + gt
        if total <= 0:
            continue
        # 优先「常触达门控决策」：eligible 高表示常进 Inbox；gated 高表示常被阈值压住
        score = float(el) * 1.0 + float(gt) * 0.65 + (float(el) / max(1, total))
        scored.append((score, sig, el, gt))
    scored.sort(key=lambda x: -x[0])
    out: List[Dict[str, Any]] = []
    for score, sig, el, gt in scored[: max(1, int(top_n))]:
        out.append(
            {
                "signature": sig,
                "inbox_eligible_hits": el,
                "inbox_gated_hits": gt,
                "total_hits": el + gt,
                "score": round(score, 4),
            }
        )
    return out


def reset_conflict_telemetry() -> None:
    with _lock:
        _counts.clear()
