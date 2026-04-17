"""
V17.20：元数据中心（SSOT）——六柱与 LLM 事实行仅允许从后端 physics_tensor 物化，
禁止依赖 HTTP Body 回传的柱位字符串。
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

_PHYS_DASH = "\u2014"


def _cell_ok(value: Any) -> bool:
    s = str(value or "").strip()
    return bool(s) and s not in (_PHYS_DASH, "-")


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
        total_energy = physics_tensor.get("total_energy_index")
        scores = physics_tensor.get("ten_gods_absolute_intensity") or physics_tensor.get("deity_scores")
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
                rows.append(f"十神绝对强度（非比例）：{' | '.join(top_rows)}")
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
