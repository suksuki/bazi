"""
多插件因果路由：优先级、极性冲突检测、合并策略与 LLM 主权排序信号。
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Mapping, Optional

from app.core.runtime_config import get_runtime_config

_BLIND_ID = "classical.blind_school.v1"
_WS_ID = "classical.wangshuai.v1"
_SELF_PARTY = frozenset({"比肩", "劫财", "正印", "偏印"})

_DEFAULT_ROUTING: Dict[str, Any] = {
    "conflict_strategy": "conservative",
    "school_sovereignty": False,
    "priority_base_physics": 100,
    "priority_blind_school": 80,
    "layer_L1": 100,
    "layer_L2": 80,
}


def load_routing_config() -> Dict[str, Any]:
    raw = get_runtime_config().get("causal_routing")
    if not isinstance(raw, dict):
        return dict(_DEFAULT_ROUTING)
    out = dict(_DEFAULT_ROUTING)
    out.update(raw)
    return out


def _layer_weight(plugin_id: str, cfg: Mapping[str, Any]) -> float:
    pid = str(plugin_id)
    if pid.startswith("base."):
        return float(cfg.get("layer_L1", 100))
    return float(cfg.get("layer_L2", 80))


def _plugin_weight(plugin_id: str, cfg: Mapping[str, Any]) -> float:
    pid = str(plugin_id)
    if _BLIND_ID in pid or "blind_school" in pid:
        return float(cfg.get("priority_blind_school", 80))
    if _WS_ID in pid or "wangshuai" in pid:
        return float(cfg.get("priority_blind_school", 80)) * 0.98
    if pid.startswith("base."):
        return float(cfg.get("priority_base_physics", 100))
    return float(cfg.get("layer_L2", 80))


def _extract_blind_deity_signed(payload: Dict[str, Any]) -> Dict[str, float]:
    out: Dict[str, float] = {}
    for wv in payload.get("work_vectors") or []:
        if not isinstance(wv, dict):
            continue
        sd = str(wv.get("source_deity") or "").strip()
        if not sd:
            continue
        ew = float(wv.get("expected_work", 0.0) or 0.0)
        out[sd] = out.get(sd, 0.0) + ew
    return out


def _extract_wangshuai_party_signed(payload: Dict[str, Any]) -> Dict[str, float]:
    verdict = str(payload.get("verdict") or "")
    self_abs = float(payload.get("self_abs", 0.0) or 0.0)
    if "过载" in verdict or "泄耗" in verdict:
        sign = -1.0
    elif "身弱" in verdict or "扶助" in verdict:
        sign = 1.0
    else:
        sign = 0.0
    if sign == 0.0:
        return {}
    mag = min(2.5, max(0.15, self_abs / 4.0))
    v = sign * mag
    n = max(1, len(_SELF_PARTY))
    return {d: v / n for d in _SELF_PARTY}


def _extract_plugin_vector(plugin_id: str, out: Dict[str, Any]) -> Dict[str, float]:
    payload = (out.get("payload") if isinstance(out.get("payload"), dict) else None) or {}
    pid = str(plugin_id)
    if _BLIND_ID == pid or "blind_school" in pid:
        return _extract_blind_deity_signed(payload)
    if _WS_ID == pid or "wangshuai" in pid:
        return _extract_wangshuai_party_signed(payload)
    return {}


@dataclass
class CausalConflictEvent:
    deity: str
    plugin_a: str
    delta_a: float
    plugin_b: str
    delta_b: float
    note: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "Causal_Conflict_Event",
            "deity": self.deity,
            "plugin_a": self.plugin_a,
            "delta_a": round(self.delta_a, 4),
            "plugin_b": self.plugin_b,
            "delta_b": round(self.delta_b, 4),
            "note": self.note,
        }


@dataclass
class CausalRouter:
    routing_config: Dict[str, Any] = field(default_factory=load_routing_config)

    def negotiate_impact(
        self,
        plugin_outputs: Dict[str, Dict[str, Any]],
        *,
        physics_tensor: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        cfg = dict(self.routing_config or load_routing_config())
        strategy = str(cfg.get("conflict_strategy") or "conservative").strip()
        school_sov = bool(cfg.get("school_sovereignty"))
        per_plugin: Dict[str, Dict[str, float]] = {}
        for pid, row in (plugin_outputs or {}).items():
            if not isinstance(row, dict):
                continue
            vec = _extract_plugin_vector(pid, row)
            if vec:
                per_plugin[str(pid)] = vec

        events: List[CausalConflictEvent] = []
        all_deities = set()
        for v in per_plugin.values():
            all_deities.update(v.keys())
        for d in sorted(all_deities):
            contributors = [(pid, vec[d]) for pid, vec in per_plugin.items() if d in vec and abs(vec[d]) > 1e-6]
            if len(contributors) < 2:
                continue
            for i in range(len(contributors)):
                for j in range(i + 1, len(contributors)):
                    pa, da = contributors[i]
                    pb, db = contributors[j]
                    if da * db < 0:
                        events.append(
                            CausalConflictEvent(
                                deity=d,
                                plugin_a=pa,
                                delta_a=da,
                                plugin_b=pb,
                                delta_b=db,
                                note="Polarity_Flip",
                            )
                        )

        merged: Dict[str, float] = {}
        if strategy == "manual_arbitration":
            routing_decision = (
                "冲突解决策略为「人工仲裁」：未自动合并十神影响量，"
                f"检测到 {len(events)} 个极性冲突事件，请裁决人裁定后再写入共识。"
            )
            skill_rank = self._skill_sovereignty_rank(per_plugin, cfg, events, merged)
            return {
                "strategy_applied": "manual_arbitration",
                "conflict_events": [e.to_dict() for e in events],
                "merged_impact": merged,
                "routing_decision": routing_decision,
                "skill_sovereignty_rank": skill_rank,
                "per_plugin_vectors": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in per_plugin.items()},
            }

        if strategy == "school_priority" or school_sov:
            # L2 盲派优先覆盖与印比阵营重叠的轴
            blind_vec = per_plugin.get(_BLIND_ID) or next((v for p, v in per_plugin.items() if "blind" in p), {})
            ws_vec = per_plugin.get(_WS_ID) or next((v for p, v in per_plugin.items() if "wangshuai" in p), {})
            keys = set(blind_vec) | set(ws_vec) | set().union(*(v.keys() for v in per_plugin.values()))
            for d in keys:
                if d in blind_vec and (school_sov or strategy == "school_priority"):
                    merged[d] = float(blind_vec[d])
                elif d in ws_vec:
                    merged[d] = float(ws_vec[d])
                else:
                    vals = [v.get(d, 0.0) for v in per_plugin.values() if d in v]
                    merged[d] = float(sum(vals) / max(1, len(vals))) if vals else 0.0
            routing_decision = (
                f"因 L1/L2 对十神轴存在分歧，路由执行「{'流派主权' if school_sov else '流派优先'}」策略："
                f"盲派向量优先于旺衰向量；共 {len(events)} 个极性事件被压制到单一来源。"
            )
        else:
            # Weighted_Sum（保守默认）
            acc: Dict[str, float] = {}
            wsum: Dict[str, float] = {}
            for pid, vec in per_plugin.items():
                lw = _layer_weight(pid, cfg) * _plugin_weight(pid, cfg)
                for d, val in vec.items():
                    acc[d] = acc.get(d, 0.0) + val * lw
                    wsum[d] = wsum.get(d, 0.0) + abs(lw)
            for d, s in acc.items():
                denom = max(1e-6, wsum.get(d, 1.0))
                merged[d] = round(s / denom, 4)
            routing_decision = (
                f"路由采用加权求和（保守模式）：层级权重 L1≈{cfg.get('layer_L1')}、L2≈{cfg.get('layer_L2')}，"
                f"插件权比 base≈{cfg.get('priority_base_physics')} / blind≈{cfg.get('priority_blind_school')}；"
                f"检出 {len(events)} 个 Causal_Conflict_Event，已按权重融合。"
            )

        skill_rank = self._skill_sovereignty_rank(per_plugin, cfg, events, merged)
        return {
            "strategy_applied": "school_priority" if (strategy == "school_priority" or school_sov) else "weighted_sum",
            "conflict_events": [e.to_dict() for e in events],
            "merged_impact": merged,
            "routing_decision": routing_decision,
            "skill_sovereignty_rank": skill_rank,
            "per_plugin_vectors": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in per_plugin.items()},
        }

    def _skill_sovereignty_rank(
        self,
        per_plugin: Dict[str, Dict[str, float]],
        cfg: Mapping[str, Any],
        events: List[CausalConflictEvent],
        merged: Mapping[str, float],
    ) -> List[Dict[str, Any]]:
        """盲派 Skill 模板排序：流派优先/主权时抬高 mp_*。"""
        blind_vec = per_plugin.get(_BLIND_ID) or {}
        conflict_deities = {e.deity for e in events}
        base_boost = 1.0 + 0.15 * len(conflict_deities)
        school_mode = bool(cfg.get("school_sovereignty")) or str(cfg.get("conflict_strategy")) == "school_priority"
        skills = [
            ("mp_pierce_01", "穿破", {"比肩", "劫财", "七杀", "正官"}),
            ("mp_tomb_01", "墓库", {"正印", "偏印", "偏财", "正财"}),
            ("mp_host_guest_01", "宾主", set(blind_vec.keys()) or {"正财", "偏财", "正官", "七杀"}),
        ]
        rank: List[Dict[str, Any]] = []
        for sid, label, deities in skills:
            touch = sum(1 for d in deities if d in blind_vec or d in merged)
            sov = 0.55 + 0.08 * touch
            if school_mode:
                sov += 0.22
            if any(d in conflict_deities for d in deities):
                sov += 0.12
            sov = round(min(1.0, sov * base_boost), 4)
            rank.append({"skill_id": sid, "label": label, "sovereignty": sov, "high_sovereignty": sov >= 0.75})
        rank.sort(key=lambda x: -float(x["sovereignty"]))
        return rank
