"""V12 M3：Active Probing 协调器（逻辑断点 + 挂起协议）。"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field

InterruptState = Literal["pending", "acknowledged", "resolved", "resumed", "expired"]

# persistence_layer 中视为已提供「婚姻/情感宫位」偏置的键（任一存在即不视为缺失）
_MARRIAGE_BIAS_KEYS = frozenset(
    {
        "marriage_palace_bias",
        "emotional_axis_ack",
        "marriage_axis_profile",
    }
)


def _pillar_branches(metadata: Dict[str, Any] | None) -> Dict[str, str]:
    out: Dict[str, str] = {}
    if not isinstance(metadata, dict):
        return out
    pillars = metadata.get("pillars")
    if not isinstance(pillars, dict):
        return out
    for k in ("year", "month", "day", "hour"):
        col = pillars.get(k)
        if isinstance(col, dict):
            b = str(col.get("branch") or "").strip()
            if b:
                out[k] = b
    return out


def _marriage_bias_missing(persistence: Dict[str, Any] | None) -> bool:
    if not persistence:
        return True
    return not any(k in persistence for k in _MARRIAGE_BIAS_KEYS)


def _zi_wu_clash_on_spouse_palace(branches: Dict[str, str]) -> bool:
    """
    情感宫位（MVP：日支配偶宫）与子午冲同现：四柱同时见「子」「午」且日支为子或午，
    即日支与另一柱形成子午对冲张力。
    """
    vals = [branches.get(k, "") for k in ("year", "month", "day", "hour")]
    if "子" not in vals or "午" not in vals:
        return False
    day_b = branches.get("day", "")
    if day_b not in ("子", "午"):
        return False
    if day_b == "子":
        return any(branches.get(k) == "午" for k in ("year", "month", "hour"))
    if day_b == "午":
        return any(branches.get(k) == "子" for k in ("year", "month", "hour"))
    return False


class InterruptRequest(BaseModel):
    model_config = {"extra": "forbid"}

    interrupt_id: str
    source: str = "active_probing"
    reason_code: str
    severity: Literal["blocking", "advisory"] = "blocking"
    state: InterruptState = "pending"
    created_at: str
    required_actions: List[str] = Field(default_factory=list)
    evidence_refs: List[str] = Field(default_factory=list)


class ActiveProbingDecision(BaseModel):
    model_config = {"extra": "forbid"}

    should_probe: bool = False
    block_mode: bool = False
    reason_code: str = "NONE"
    probe_plan: List[str] = Field(default_factory=list)
    interrupt: InterruptRequest | None = None


def evaluate_active_probing(
    *,
    physics_tensor: Dict[str, Any],
    plugin_outputs: Dict[str, Any],
    metadata: Dict[str, Any] | None = None,
) -> ActiveProbingDecision:
    """
    依据 Decision Inbox + 插件冲突信号生成 M3 决策。

    当前策略（MVP）：
    - 若 persistence 缺失婚姻/情感偏置且日支子午冲张力成立，触发 blocking（情感宫位能量波动追问）；
    - 若存在高分插件冲突（match_score>=0.85）且并发插件数>=2，触发 blocking pending；
    - 否则 advisory 或不触发。

    ``metadata`` 可选；未传时尝试从 ``physics_tensor.meta.bundle_metadata`` 读取四柱供冲合判断。
    """
    md = metadata if isinstance(metadata, dict) else {}
    if not md and isinstance(physics_tensor.get("meta"), dict):
        bm = (physics_tensor["meta"] or {}).get("bundle_metadata")
        if isinstance(bm, dict):
            md = bm

    persistence = md.get("persistence_layer") if isinstance(md.get("persistence_layer"), dict) else {}
    branches = _pillar_branches(md)
    meta = physics_tensor.get("meta") if isinstance(physics_tensor.get("meta"), dict) else {}
    l1_flags = meta.get("l1_junction_flags") if isinstance(meta.get("l1_junction_flags"), dict) else {}
    dsn = meta.get("decision_signal_to_noise") if isinstance(meta.get("decision_signal_to_noise"), dict) else {}
    severe_logic_conflict = (
        str(l1_flags.get("sgjg_severity") or "").strip().upper() == "CRITICAL"
        or bool(l1_flags.get("l1_inbox_signal_bypass"))
        or bool(dsn.get("has_critical_marker"))
    )
    if severe_logic_conflict:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        interrupt = InterruptRequest(
            interrupt_id=f"ap-logic-conflict-{now}",
            reason_code="M3_L1_LOGIC_CONFLICT_PENDING",
            severity="blocking",
            state="pending",
            created_at=now,
            required_actions=["confirm_conflict_branch", "choose_conflict_resolution_mode"],
            evidence_refs=[
                f"l1_junction_flags.sgjg_severity={str(l1_flags.get('sgjg_severity') or '')}",
                f"decision_signal_to_noise.has_critical_marker={bool(dsn.get('has_critical_marker'))}",
            ],
        )
        return ActiveProbingDecision(
            should_probe=True,
            block_mode=True,
            reason_code="M3_L1_LOGIC_CONFLICT_PENDING",
            probe_plan=[
                "检测到 L1 级逻辑冲突临界态：请先确认冲突分支，再决定是否继续终判。",
                "未完成冲突确认前，禁止直接跳过追问并产出终审结论。",
            ],
            interrupt=interrupt,
        )

    if _marriage_bias_missing(persistence) and _zi_wu_clash_on_spouse_palace(branches):
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        interrupt = InterruptRequest(
            interrupt_id=f"ap-ziwu-{now}",
            reason_code="M3_ZI_WU_MARRIAGE_PALACE_PROBE",
            severity="blocking",
            state="pending",
            created_at=now,
            required_actions=["confirm_marriage_axis_bias", "ack_emotional_volatility"],
            evidence_refs=[
                "pillars.day_branch=" + str(branches.get("day", "")),
                "topology:zi_wu_clash_on_spouse_palace",
                "persistence:marriage_bias_missing",
            ],
        )
        return ActiveProbingDecision(
            should_probe=True,
            block_mode=True,
            reason_code="M3_ZI_WU_MARRIAGE_PALACE_PROBE",
            probe_plan=[
                "子午冲牵动日支情感宫位：请先确认当前婚恋/亲密关系取向是否作为本轮推演主轴。",
                "若更关注事业名位，请显式切换意志偏好以便局部重算。",
            ],
            interrupt=interrupt,
        )

    inbox = meta.get("decision_inbox_v1") if isinstance(meta.get("decision_inbox_v1"), dict) else {}
    match_scores = inbox.get("match_scores") if isinstance(inbox.get("match_scores"), list) else []
    hot = [x for x in match_scores if isinstance(x, dict) and float(x.get("score") or 0.0) >= 0.85]
    plugin_count = len([k for k in (plugin_outputs or {}).keys() if str(k).strip()])

    if len(hot) >= 1 and plugin_count >= 2:
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        top = hot[0]
        pid = str(top.get("plugin_id") or "unknown")
        interrupt = InterruptRequest(
            interrupt_id=f"ap-{now}-{pid}",
            reason_code="M3_HIGH_TENSION_PENDING",
            severity="blocking",
            state="pending",
            created_at=now,
            required_actions=["confirm_cards", "choose_strategy"],
            evidence_refs=[f"decision_inbox.match_score.{pid}={float(top.get('score') or 0.0):.2f}"],
        )
        return ActiveProbingDecision(
            should_probe=True,
            block_mode=True,
            reason_code="M3_HIGH_TENSION_PENDING",
            probe_plan=[
                "请确认当前最关键冲突卡片。",
                "请在保守/进取策略中二选一。",
            ],
            interrupt=interrupt,
        )

    if plugin_count >= 2:
        return ActiveProbingDecision(
            should_probe=True,
            block_mode=False,
            reason_code="M3_ADVISORY_PROBE",
            probe_plan=["建议补充意志偏好，以减少多插件结论歧义。"],
        )

    return ActiveProbingDecision()


__all__ = ["InterruptRequest", "ActiveProbingDecision", "evaluate_active_probing"]
