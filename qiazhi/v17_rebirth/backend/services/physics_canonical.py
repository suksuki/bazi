"""
V17.20：元数据中心（SSOT）——六柱与 LLM 事实行仅允许从后端 physics_tensor 物化，
禁止依赖 HTTP Body 回传的柱位字符串。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.logic.runtime_field_protocol import runtime_field_prompt_lines
from v17_rebirth.backend.services.physics_layers import read_runtime_scores

_PHYS_DASH = "\u2014"


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _cell_ok(value: Any) -> bool:
    s = str(value or "").strip()
    return bool(s) and s not in (_PHYS_DASH, "-")


def _meta_rows(pt: Dict[str, Any]) -> Dict[str, Any]:
    meta = pt.get("meta")
    return meta if isinstance(meta, dict) else {}


def _energy_meta_rows(pt: Dict[str, Any]) -> Dict[str, Any]:
    raw = pt.get("energy_meta")
    return raw if isinstance(raw, dict) else {}


def _relation_summary_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    energy_meta = _energy_meta_rows(pt)
    meta = _meta_rows(pt)
    raw = (
        energy_meta.get("relation_formation_summary")
        if isinstance(energy_meta.get("relation_formation_summary"), list)
        else meta.get("relation_formation_summary")
    )
    if not isinstance(raw, list) or not raw:
        return []
    rows = [
        "合化解释合同：以下百分比表示成局度/效率，不是十神能量百分比；需与家族基准倍数、源气保留比例和十神绝对强度合读。"
    ]
    ranked = sorted(
        (
            row for row in raw
            if isinstance(row, dict) and str(row.get("formation_label") or "").strip()
        ),
        key=lambda row: float(row.get("formation_percent") or 0.0),
        reverse=True,
    )
    for row in ranked[:3]:
        label = str(row.get("formation_label") or "").strip()
        percent = _safe_float(row.get("formation_percent"), 0.0)
        factor = _safe_float(row.get("family_factor"), 0.0)
        status = str(row.get("status") or "").strip()
        conflict_damping = _safe_float(row.get("conflict_damping"), 1.0)
        projection_preview = row.get("projection_preview") if isinstance(row.get("projection_preview"), list) else []
        fragments = [f"{label} {percent:.1f}%"]
        if factor > 0.0:
            fragments.append(f"基准x{factor:.2f}")
        source_retention_ratio = _safe_float(row.get("source_retention_ratio"), 1.0)
        if source_retention_ratio < 0.995:
            fragments.append(f"源气保留{round(source_retention_ratio * 100):.0f}%")
        if status:
            fragments.append(status)
        if conflict_damping < 0.995:
            fragments.append(f"受扰保留{round(conflict_damping * 100):.0f}%")
        if projection_preview:
            projection_text = " / ".join(
                str(item).strip() for item in projection_preview[:2] if str(item).strip()
            )
            if projection_text:
                fragments.append(f"主投影 {projection_text}")
        rows.append("合化摘要：" + "，".join(fragments[:5]))
    return rows


def _relation_dynamics_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    energy_meta = _energy_meta_rows(pt)
    meta = _meta_rows(pt)
    raw = (
        energy_meta.get("relation_dynamics_summary")
        if isinstance(energy_meta.get("relation_dynamics_summary"), list)
        else meta.get("relation_dynamics_summary")
    )
    if not isinstance(raw, list) or not raw:
        return []
    rows = [
        "关系动力学合同：刑冲克害破与合必须分开读能量与稳定性；冲偏激发，刑偏内耗，克偏压制转移，害偏暗损，破偏解构，合偏绑定/组织化。"
    ]
    ranked = sorted(
        (row for row in raw if isinstance(row, dict) and str(row.get("label") or "").strip()),
        key=lambda row: abs(_safe_float(row.get("stability_delta_ratio"), 0.0)) + _safe_float(row.get("energy_effect_ratio"), 0.0),
        reverse=True,
    )
    for row in ranked[:4]:
        label = str(row.get("label") or "").strip()
        energy_axis = str(row.get("energy_axis") or "").strip()
        energy_ratio = _safe_float(row.get("energy_effect_ratio"), 0.0)
        stability_delta = _safe_float(row.get("stability_delta_ratio"), 0.0)
        lock_ratio = _safe_float(row.get("free_energy_lock_ratio"), 0.0)
        note = str(row.get("note") or "").strip()
        fragments = [f"{label} {energy_axis}{round(energy_ratio * 100):.0f}%"]
        if abs(stability_delta) > 1e-6:
            sign = "+" if stability_delta > 0 else ""
            fragments.append(f"稳定{sign}{round(stability_delta * 100):.0f}%")
        if lock_ratio > 0.0:
            fragments.append(f"自由能锁定{round(lock_ratio * 100):.0f}%")
        if note:
            fragments.append(note)
        rows.append("关系动力学：" + "，".join(fragments[:4]))
    return rows


def _runtime_field_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    return runtime_field_prompt_lines()


def _pattern_summary_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = _meta_rows(pt)
    claims = meta.get("plugin_claims") if isinstance(meta.get("plugin_claims"), list) else []
    if not claims:
        return []
    candidates: Dict[str, Dict[str, Any]] = {}
    for row in claims:
        if not isinstance(row, dict):
            continue
        name = str(row.get("pattern_candidate") or row.get("pattern_name") or "").strip()
        if not name:
            continue
        confidence_raw = row.get("pattern_confidence_percent")
        if confidence_raw is None:
            confidence_raw = row.get("pattern_confidence")
        if confidence_raw is None:
            confidence_raw = row.get("match_ratio")
        confidence = _safe_float(confidence_raw, 0.0)
        if confidence <= 1.0:
            confidence *= 100.0
        confidence = max(0.0, min(100.0, confidence))
        target = str(row.get("target_god") or "").strip()
        scope = str(row.get("pattern_scope_label") or row.get("pattern_scope") or "").strip()
        key = f"{name}::{target or 'na'}"
        current = candidates.get(key)
        candidate = {
            "name": name,
            "confidence": round(confidence, 1),
            "target": target,
            "scope": scope,
        }
        if current is None or float(candidate["confidence"]) > float(current.get("confidence") or 0.0):
            candidates[key] = candidate
    ranked = sorted(candidates.values(), key=lambda row: float(row.get("confidence") or 0.0), reverse=True)
    if not ranked:
        return []
    rows = ["格局解释合同：以下百分比表示格局拟合度/置信度，不直接改写十神能量；应与原局、运流和做功链条合读。"]
    fragments: List[str] = []
    for row in ranked[:3]:
        name = str(row.get("name") or "").strip()
        if not name:
            continue
        confidence = _safe_float(row.get("confidence"), 0.0)
        target = str(row.get("target") or "").strip()
        scope = str(row.get("scope") or "").strip()
        bits = [f"{name} {confidence:.1f}%"]
        if target:
            bits.append(f"主落点 {target}")
        if scope:
            bits.append(scope)
        fragments.append("，".join(bits[:3]))
    if fragments:
        rows.append("格局摘要：" + "；".join(fragments))
    return rows


def _ten_gods_prompt_contract_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    return [
        "十神解释合同：`ten_gods_base_l0/ten_gods_runtime` 为绝对物理强度，不是百分比。",
        "十神解释合同：单个十神总分应理解为显化、根气、势能、潜藏残值的合成结果，不能当作单一来源。",
        "十神解释合同：显化内部还包含柱位贴身权重；原局天干通常按月干 > 时干 > 年干，且这不属于根气。",
        "十神解释合同：根气与势能不是同一概念；根气回答“是否扎根”，势能回答“是否得势”。",
        "十神解释合同：通根只定义为“天干 <- 地支藏干”；透干只定义为“地支藏干 -> 天干显影”。",
        "十神解释合同：地支之间不谈根气，天干之间不谈透干；二者可互相增强，但必须基于冻结盘面单次结算，禁止递归放大。",
        "十神解释合同：天干五合与地支成局分开解读；五合只回看地支根气与争合/支扰，倍率明显轻于地支三合三会。",
        "十神解释合同：关系成局的大倍率主要由动态透干/显神触发；月干透出最强，日干在动态做功中有效，但不回流为静态比劫显化。",
        "十神解释合同：同五行可通根，但阴阳不纯配时应折损；本根强于异阴阳根。",
        "十神解释合同：日干是十神参照轴，不直接计入比肩/劫财等显化分。",
        "十神解释合同：只有藏干未透时通常仅作弱支撑或潜藏残值，不宜直接判为强轴。",
        "十神解释合同：例如丙见巳偏根强，丙见午偏势强；解释时必须区分“根深”与“势猛”。",
    ]


def _ten_gods_decomposition_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    raw = pt.get("ten_gods_decomposition_l0")
    if not isinstance(raw, dict) or not raw:
        return []
    ranked = sorted(
        (
            (str(god).strip(), row)
            for god, row in raw.items()
            if str(god).strip() and isinstance(row, dict)
        ),
        key=lambda item: float(item[1].get("total") or 0.0),
        reverse=True,
    )
    lines: List[str] = []
    for god, row in ranked[:3]:
        lines.append(
            "十神分解："
            f"{god} 总{float(row.get('total') or 0.0):.2f}"
            f"＝显化{float(row.get('manifest') or 0.0):.2f}"
            f"+根气{float(row.get('root') or 0.0):.2f}"
            f"+势能{float(row.get('momentum') or 0.0):.2f}"
            f"+潜藏{float(row.get('hidden') or 0.0):.2f}"
        )
        momentum_parts = [
            ("月令势", float(row.get("momentum_month_order") or 0.0)),
            ("阶段势", float(row.get("momentum_stage") or 0.0)),
            ("禄势", float(row.get("momentum_stage_lu") or 0.0)),
            ("刃势", float(row.get("momentum_stage_blade") or 0.0)),
            ("长生势", float(row.get("momentum_stage_general") or 0.0)),
            ("结构势", float(row.get("momentum_structure") or 0.0)),
            ("辅助势", float(row.get("momentum_auxiliary") or 0.0)),
            ("其他势", float(row.get("momentum_other") or 0.0)),
        ]
        visible_parts = [f"{label}{value:.2f}" for label, value in momentum_parts if value > 0.0]
        if visible_parts:
            lines.append(f"十神势能细项：{god}＝{' + '.join(visible_parts)}")
    return lines


def _core_flux_prompt_lines(pt: Dict[str, Any]) -> List[str]:
    if not isinstance(pt, dict):
        return []
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    authority = meta.get("god_ring_authority") if isinstance(meta.get("god_ring_authority"), dict) else {}
    flux_meta = authority.get("core_flux_meta") if isinstance(authority.get("core_flux_meta"), dict) else {}
    if not flux_meta:
        return []

    rows: List[str] = [
        "做功解释合同：方向矩阵中的 source->target 表示对目标十神/结构的净推动或净压制；回路张力区分同向放大与对冲拉扯。"
    ]

    interaction_rows = flux_meta.get("interaction_matrix") if isinstance(flux_meta.get("interaction_matrix"), list) else []
    if interaction_rows:
        positive_rows = []
        negative_rows = []
        for item in interaction_rows:
            if not isinstance(item, dict):
                continue
            source = str(item.get("source") or "").strip()
            target = str(item.get("target") or "").strip()
            if not source or not target:
                continue
            net = _safe_float(item.get("net"), 0.0)
            support_ratio = _safe_float(item.get("support_ratio"), 0.0)
            resist_ratio = _safe_float(item.get("resist_ratio"), 0.0)
            row = (
                f"{source}->{target} 净{net:+.3f}"
                f"（合{round(support_ratio * 100):.0f}%/抗{round(resist_ratio * 100):.0f}%）"
            )
            if net >= 0.0:
                positive_rows.append((abs(net), row))
            else:
                negative_rows.append((abs(net), row))
        top_fragments: List[str] = []
        if positive_rows:
            top_fragments.append(max(positive_rows, key=lambda item: item[0])[1])
        if negative_rows:
            top_fragments.append(max(negative_rows, key=lambda item: item[0])[1])
        if not top_fragments:
            raw_sorted = sorted(
                (
                    (
                        abs(_safe_float(item.get("net"), 0.0)),
                        f"{str(item.get('source') or '').strip()}->{str(item.get('target') or '').strip()} "
                        f"净{_safe_float(item.get('net'), 0.0):+.3f}"
                    )
                    for item in interaction_rows
                    if isinstance(item, dict)
                    and str(item.get("source") or "").strip()
                    and str(item.get("target") or "").strip()
                ),
                key=lambda item: item[0],
                reverse=True,
            )
            top_fragments = [label for _score, label in raw_sorted[:2]]
        if top_fragments:
            rows.append("做功方向矩阵：" + "；".join(top_fragments[:2]))

    tension_rows = flux_meta.get("tension_pairs") if isinstance(flux_meta.get("tension_pairs"), list) else []
    if tension_rows:
        top_pairs: List[str] = []
        for item in tension_rows[:2]:
            if not isinstance(item, dict):
                continue
            left = str(item.get("left") or "").strip()
            right = str(item.get("right") or "").strip()
            if not left or not right:
                continue
            mode = str(item.get("mode") or "").strip()
            score = _safe_float(item.get("score"), 0.0)
            label = "同向放大" if mode == "reinforce" else "对冲拉扯"
            top_pairs.append(f"{left}<->{right} {label}{score:.3f}")
        if top_pairs:
            rows.append("做功回路：" + "；".join(top_pairs))

    return rows


def six_pillars_tensor_complete(pt: Dict[str, Any]) -> bool:
    """与 VerdictOrchestrator 物理门控一致：四柱 + 大运 + 流年。"""
    fp = pt.get("four_pillars")
    if not isinstance(fp, dict):
        return False
    for key in ("year", "month", "day", "hour"):
        if not _cell_ok(fp.get(key)):
            return False
    if not _cell_ok(pt.get("luck_pillar")):
        return False
    if not _cell_ok(pt.get("flow_pillar")):
        return False
    return True


@dataclass(frozen=True)
class SixPillarsModel:
    """只读物化模型：字段一律从 physics_tensor 读取，不从请求体独立解析。"""

    year: str
    month: str
    day: str
    hour: str
    luck_pillar: str
    flow_pillar: str
    flow_year: Optional[int]

    @classmethod
    def from_physics_tensor(cls, pt: Dict[str, Any]) -> SixPillarsModel:
        fp = pt.get("four_pillars") if isinstance(pt.get("four_pillars"), dict) else {}
        fy = pt.get("flow_year")
        try:
            fy_int = int(fy) if fy is not None else None
        except (TypeError, ValueError):
            fy_int = None
        return cls(
            year=str(fp.get("year") or "").strip(),
            month=str(fp.get("month") or "").strip(),
            day=str(fp.get("day") or "").strip(),
            hour=str(fp.get("hour") or "").strip(),
            luck_pillar=str(pt.get("luck_pillar") or "").strip(),
            flow_pillar=str(pt.get("flow_pillar") or "").strip(),
            flow_year=fy_int,
        )

    def materialize_prompt_lines(self) -> List[str]:
        """元数据中心出口：写入 LLM user 侧的硬事实行（与 Body/facts 解耦）。"""
        fy = self.flow_year if self.flow_year is not None else "?"
        return [
            f"四柱落位（元数据中心）：年{self.year} 月{self.month} 日{self.day} 时{self.hour}",
            f"大运（{fy}）：{self.luck_pillar}；流年：{self.flow_pillar}",
        ]


class PhysicsCanonicalService:
    """物理层单一事实源：供 pipeline / llm_micro_client 在装配 prompt 时调用。"""

    @staticmethod
    def sixpillars_from_tensor(pt: Dict[str, Any]) -> SixPillarsModel:
        return SixPillarsModel.from_physics_tensor(pt)

    @staticmethod
    def materialize_prompt_lines(physics_tensor: Dict[str, Any]) -> List[str]:
        rows = SixPillarsModel.from_physics_tensor(physics_tensor).materialize_prompt_lines()
        if not isinstance(physics_tensor, dict):
            return rows
        rows.extend(_core_flux_prompt_lines(physics_tensor))
        rows.extend(_relation_summary_prompt_lines(physics_tensor))
        rows.extend(_relation_dynamics_prompt_lines(physics_tensor))
        rows.extend(_pattern_summary_prompt_lines(physics_tensor))
        rows.extend(_runtime_field_prompt_lines(physics_tensor))
        rows.extend(_ten_gods_prompt_contract_lines(physics_tensor))
        rows.extend(_ten_gods_decomposition_lines(physics_tensor))
        total_energy = physics_tensor.get("total_energy_index")
        scores = read_runtime_scores(physics_tensor)
        if isinstance(scores, dict) and scores:
            ranked = sorted(
                (
                    (str(k).strip(), float(v))
                    for k, v in scores.items()
                    if str(k).strip()
                ),
                key=lambda kv: kv[1],
                reverse=True,
            )
            top_rows = [f"{name}:{value:.2f}" for name, value in ranked[:6]]
            if top_rows:
                rows.append(f"十神绝对强度（非比例）：{'，'.join(top_rows)}")
        try:
            total_value = float(total_energy)
        except (TypeError, ValueError):
            total_value = None
        if total_value is not None:
            rows.append(f"全盘总能量指标：{total_value:.2f}")
        return rows


def strip_client_pillar_echoes(rows: List[str]) -> List[str]:
    """剔除可能由前端回灌的柱位描述行，避免与元数据中心重复或冲突。"""
    out: List[str] = []
    for r in rows:
        t = str(r).strip()
        if not t:
            continue
        if t.startswith("四柱落位"):
            continue
        if "大运（" in t and ("流年" in t or "流年：" in t):
            continue
        out.append(t)
    return out


@dataclass
class V17PhysicsMetadata:
    """叙事协程启动前的因果对齐：await metadata.is_stable()。"""

    physics: Dict[str, Any]

    async def is_stable(self) -> bool:
        await asyncio.sleep(0)
        pt = self.physics if isinstance(self.physics, dict) else {}
        if not six_pillars_tensor_complete(pt):
            return False
        meta = pt.get("meta")
        if not isinstance(meta, dict):
            return False
        return bool(meta.get("v17_physics_stable"))
