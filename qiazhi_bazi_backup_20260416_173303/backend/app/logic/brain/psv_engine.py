"""
V12 M2：物理基调符号化（PSV）引擎 — 100% 确定性，禁止 LLM。

参考：docs/V12_BRAIN_FRAMEWORK.md §6.1；实现类 ``PSVEngine`` / ``PSVSymbol``。
全部比例阈值来自 ``PSVRuntimeConfig``，本模块不写死业务常数。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, List, Literal

from pydantic import BaseModel, Field

from app.logic.brain.config import PSVRuntimeConfig, load_psv_runtime_config_for_tri
from app.schemas.tri_layer_v12 import TriLayerMetadata

PolarityV12 = Literal[
    "STRONG_POSITIVE",
    "MILD_POSITIVE",
    "NEUTRAL",
    "MILD_NEGATIVE",
    "STRONG_NEGATIVE",
    "UNKNOWN",
]


class PSVSymbol(BaseModel):
    """单条物理基调符号（监军输入）。"""

    model_config = {"extra": "forbid"}

    axis: str = Field(..., description="如 WEALTH、OFFICER、ELEMENT_BALANCE、LAW_STRUCTURE")
    polarity: PolarityV12 = Field(..., description="与白皮书 M2 枚举一致")
    strength: float = Field(..., ge=0.0, le=1.0, description="0–1 连续强度")
    evidence: List[str] = Field(default_factory=list, description="证据链：逻辑路径与规则 id")
    fingerprint: str = Field(default="", description="本条符号的稳定哈希前缀")


def _fingerprint_payload(payload: Any) -> str:
    try:
        blob = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    except (TypeError, ValueError):
        blob = str(payload).encode("utf-8", errors="replace")
    return hashlib.sha256(blob).hexdigest()[:16]


class PSVEngine:
    """
    输入：``TriLayerMetadata``（通常由 ``MetadataProjectorV12`` 生成）。

    输出：``List[PSVSymbol]``，按 axis 去重后保留极性更「极端」的一条（负向优先于弱负）。

    构造时必须注入 ``PSVRuntimeConfig``；若需与 ``tri.arbiter_bias`` 对齐，可使用
    ``PSVEngine.from_tri(tri)``。
    """

    def __init__(self, config: PSVRuntimeConfig) -> None:
        self._config = config

    @classmethod
    def from_tri(cls, tri: TriLayerMetadata) -> PSVEngine:
        """使用 ``tri.arbiter_bias`` 中的覆盖与环境变量合并后的配置。"""
        return cls(load_psv_runtime_config_for_tri(tri.arbiter_bias))

    def build(self, tri: TriLayerMetadata) -> List[PSVSymbol]:
        raw: List[PSVSymbol] = []
        raw.extend(self._rule_robber_wealth_pierce(tri))
        raw.extend(self._rule_element_spread(tri))
        raw.extend(self._rule_l2_primary_and_intention(tri))
        return self._dedupe_by_axis(raw)

    def _dedupe_by_axis(self, symbols: List[PSVSymbol]) -> List[PSVSymbol]:
        priority = {
            "STRONG_NEGATIVE": 4,
            "MILD_NEGATIVE": 3,
            "NEUTRAL": 2,
            "UNKNOWN": 1,
            "MILD_POSITIVE": 3,
            "STRONG_POSITIVE": 4,
        }

        best: dict[str, PSVSymbol] = {}
        for s in symbols:
            cur = best.get(s.axis)
            if cur is None:
                best[s.axis] = s
                continue
            p_new = priority.get(s.polarity, 0)
            p_old = priority.get(cur.polarity, 0)
            if p_new > p_old or (p_new == p_old and s.strength > cur.strength):
                best[s.axis] = s
        return [best[k] for k in sorted(best.keys())]

    def _rule_robber_wealth_pierce(self, tri: TriLayerMetadata) -> List[PSVSymbol]:
        """比劫 vs 财星穿透比；超过配置阈值则财星轴负向。"""
        cfg = self._config
        ds = tri.static_fact.baseline_tensor.get("deity_scores")
        if not isinstance(ds, dict):
            return []

        rob = float(ds.get("比肩", 0) or 0) + float(ds.get("劫财", 0) or 0)
        wealth = float(ds.get("正财", 0) or 0) + float(ds.get("偏财", 0) or 0)
        eps = float(cfg.robber_wealth_denominator_epsilon)
        if wealth <= eps and rob <= 0:
            return []

        pierce_ratio = rob / (wealth + eps)
        l1 = tri.dynamic_inference.l1_audit
        robber_plugin_hit = isinstance(l1, dict) and bool(l1.get("l1_robber_wealth_v1"))

        if pierce_ratio <= cfg.robber_wealth_pierce_threshold and not robber_plugin_hit:
            return []

        if pierce_ratio >= cfg.robber_wealth_strong_threshold or robber_plugin_hit:
            polarity: PolarityV12 = "STRONG_NEGATIVE"
            base = float(cfg.robber_wealth_base_strong_negative)
        else:
            polarity = "MILD_NEGATIVE"
            base = float(cfg.robber_wealth_base_mild_negative)

        span = max(pierce_ratio - cfg.robber_wealth_pierce_threshold, 0.0)
        div = float(cfg.robber_wealth_span_divisor)
        scale = float(cfg.robber_wealth_span_scale)
        strength = min(1.0, base + min(1.0, span / div) * scale)
        if robber_plugin_hit:
            strength = min(1.0, strength + float(cfg.robber_plugin_evidence_strength_bonus))

        evidence = [
            "static_fact.baseline_tensor.deity_scores",
            "rule:psv.robber_wealth_pierce_ratio",
            f"ratio={pierce_ratio:.4f}",
        ]
        if robber_plugin_hit:
            evidence.append("dynamic_inference.l1_audit.l1_robber_wealth_v1")

        fp_src = {"axis": "WEALTH", "polarity": polarity, "pierce_ratio": round(pierce_ratio, 4)}
        sym = PSVSymbol(
            axis="WEALTH",
            polarity=polarity,
            strength=round(strength, 4),
            evidence=evidence,
            fingerprint=_fingerprint_payload(fp_src),
        )
        return [sym]

    def _rule_element_spread(self, tri: TriLayerMetadata) -> List[PSVSymbol]:
        """五行 normalized 极差过大 → ELEMENT_BALANCE 负向或中性压力。"""
        cfg = self._config
        norm = tri.static_fact.baseline_tensor.get("normalized")
        if not isinstance(norm, dict):
            return []
        vals = []
        for k in ("wood", "fire", "earth", "metal", "water"):
            v = norm.get(k)
            if isinstance(v, (int, float)) and not isinstance(v, bool):
                vals.append(float(v))
        if len(vals) < 3:
            return []
        spread = max(vals) - min(vals)
        if spread <= cfg.element_balance_spread_threshold:
            return []

        brk = float(cfg.element_balance_mild_vs_strong_breakpoint)
        polarity: PolarityV12 = "MILD_NEGATIVE" if spread < brk else "STRONG_NEGATIVE"
        scale_div = float(cfg.element_balance_strength_scale_divisor)
        strength = min(1.0, (spread - cfg.element_balance_spread_threshold) / scale_div)
        evidence = [
            "static_fact.baseline_tensor.normalized",
            "rule:psv.element_normalized_spread",
            f"spread={spread:.4f}",
        ]
        fp_src = {"axis": "ELEMENT_BALANCE", "spread": round(spread, 4)}
        return [
            PSVSymbol(
                axis="ELEMENT_BALANCE",
                polarity=polarity,
                strength=round(strength, 4),
                evidence=evidence,
                fingerprint=_fingerprint_payload(fp_src),
            )
        ]

    def _rule_l2_primary_and_intention(self, tri: TriLayerMetadata) -> List[PSVSymbol]:
        """L2 头名格局 + Arbiter 意志定调（官杀格 × 避险意志 → 官轴正向加强）。"""
        cfg = self._config
        rows = tri.dynamic_inference.l2_pattern_rows
        if not isinstance(rows, list) or not rows:
            return []

        scored: List[tuple[float, dict[str, Any]]] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            aff = r.get("affinity_score", r.get("progress", 0))
            try:
                a = float(aff or 0)
            except (TypeError, ValueError):
                a = 0.0
            scored.append((a, r))
        if not scored:
            return []
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[0][1]
        aff = float(scored[0][0])

        pid = str(top.get("pattern_id") or "").strip()
        excl = bool(top.get("exclusion_hit", False))
        unknown_cut = float(cfg.l2_affinity_unknown_cutoff)
        if excl or aff < unknown_cut:
            sym = PSVSymbol(
                axis="LAW_STRUCTURE",
                polarity="UNKNOWN",
                strength=0.0,
                evidence=[
                    "dynamic_inference.l2_pattern_rows",
                    "rule:psv.l2_primary_excluded_or_weak",
                    f"pattern_id={pid}",
                ],
                fingerprint=_fingerprint_payload({"pid": pid, "excl": excl}),
            )
            return [sym]

        intention = (tri.arbiter_bias.user_intention_id or "").strip()
        will_ctx = tri.dynamic_inference.will_intention_context
        active_will = ""
        if isinstance(will_ctx, dict):
            active_will = str(will_ctx.get("active_intention") or "").strip()

        floor_s = float(cfg.l2_primary_strength_floor)
        strength = min(1.0, max(floor_s, aff))
        polarity: PolarityV12 = "MILD_POSITIVE"
        axis = "LAW_STRUCTURE"

        strong_th = float(cfg.l2_affinity_strong_threshold)
        officer_floor = float(cfg.officer_seek_stability_affinity_floor)
        officer_bonus = float(cfg.intention_officer_bonus)
        wealth_pat_bonus = float(cfg.intention_wealth_pattern_bonus)

        if pid in ("GOV_PATTERN", "KILL_PATTERN") or "官" in str(top.get("name") or ""):
            axis = "OFFICER"
            if aff >= strong_th and not excl:
                polarity = "STRONG_POSITIVE"
            if intention in ("seek_stability", "seek_fame") or active_will in ("seek_stability", "seek_fame"):
                strength = min(1.0, strength + officer_bonus)
                polarity = "STRONG_POSITIVE" if aff >= officer_floor else polarity

        if pid in ("WEALTH_PATTERN", "FOLLOW_WEALTH", "FOLLOW_WEALTH_POWER"):
            axis = "WEALTH"
            polarity = "STRONG_POSITIVE" if aff >= strong_th else "MILD_POSITIVE"
            if intention == "seek_wealth" or active_will == "seek_wealth":
                strength = min(1.0, strength + wealth_pat_bonus)

        evidence = [
            "dynamic_inference.l2_pattern_rows",
            "arbiter_bias.user_intention_id",
            "rule:psv.l2_primary_with_intention",
            f"pattern_id={pid}",
            f"affinity={aff:.4f}",
        ]
        if active_will:
            evidence.append(f"will_intention_context.active_intention={active_will}")

        fp_src = {"axis": axis, "pid": pid, "aff": round(aff, 4), "intention": intention or active_will}
        return [
            PSVSymbol(
                axis=axis,
                polarity=polarity,
                strength=round(strength, 4),
                evidence=evidence,
                fingerprint=_fingerprint_payload(fp_src),
            )
        ]


__all__ = ["PSVEngine", "PSVSymbol", "PolarityV12"]
