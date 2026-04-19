"""V17.13：L2 Registry parity — 格局 / 盲派从 meta hydration 读取真实标签（非占位）。"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from v17_rebirth.backend.logic.L1_atomic_ops.v17_op_fact import generate_v17_fact_from_op, strip_score_noise
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

PLUGIN_SUMMARY = "L2 Registry parity：climate / conflict / pattern / blind 四插件。"
PLUGIN_RATIONALE = "pattern_detector / blind_school 与 L1 hydration 输出的 meta 对齐。"


@dataclass
class ClimateAdjusterStub(V17PluginSpec):
    plugin_id: str = "classical.climate_adjuster.v1"
    causal_tier: int = 3
    registry_priority: float = 0.88
    doc_summary: str = "月令场强调候（climate_manifest）占位。"
    doc_rationale: str = "旧 run_climate_adjuster_v1 脱水入口。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        pt = physics_tensor if isinstance(physics_tensor, dict) else {}
        energy_meta = pt.get("energy_meta") if isinstance(pt.get("energy_meta"), dict) else {}
        month_command_god = str(energy_meta.get("month_command_god") or "").strip()
        if not month_command_god:
            return []
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=f"调候提示：当前月令主气落在 {month_command_god}，所有解释应先服从月令气候背景。",
                causal_tier=int(self.causal_tier),
                priority=0.82,
                decision_hint="先调候，再取用",
                meta={"month_command_god": month_command_god, "match_ratio": 0.86},
            )
        ]


@dataclass
class ConflictAuditorStub(V17PluginSpec):
    plugin_id: str = "classical.conflict_auditor.v1"
    causal_tier: int = 3
    registry_priority: float = 0.87
    doc_summary: str = "冲突拓扑审计（CONFLICT_MANIFEST）占位。"
    doc_rationale: str = "旧 run_conflict_auditor_v1 脱水入口。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        pt = physics_tensor if isinstance(physics_tensor, dict) else {}
        meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
        conflicts = [dict(row) for row in (meta.get("plugin_conflicts") or []) if isinstance(row, dict)]
        resolutions = [dict(row) for row in (meta.get("plugin_conflict_resolutions") or []) if isinstance(row, dict)]
        if not conflicts:
            return []
        unresolved = [
            row for row in conflicts
            if str(row.get("resolution_status") or "").strip() not in {"resolved_system", "resolved_llm", "resolved_user"}
        ]
        text = (
            f"插件冲突审计：当前检测到 {len(conflicts)} 组冲突，未闭环 {len(unresolved)} 组，"
            f"已有 {len(resolutions)} 条裁决建议。"
        )
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=text,
                causal_tier=int(self.causal_tier),
                priority=0.86,
                decision_hint="优先处理冲突层",
                meta={
                    "conflict_count": len(conflicts),
                    "unresolved_conflict_count": len(unresolved),
                    "resolution_count": len(resolutions),
                    "match_ratio": min(0.9, max(0.45, len(conflicts) / max(len(conflicts) + 1, 1))),
                },
            )
        ]


@dataclass
class PatternDetectorV2(V17PluginSpec):
    """对齐旧 `run_pattern_detector_v2` headline：使用 hydration 的 `hit_pattern_name`（无数值）。"""

    plugin_id: str = "classical.pattern_detector.v2"
    causal_tier: int = 3
    registry_priority: float = 0.84
    doc_summary: str = "格局阈值引擎（manifest 驱动）。"
    doc_rationale: str = "V17.13：meta.hit_pattern_name 显影为格局标签。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        pt = physics_tensor if isinstance(physics_tensor, dict) else {}
        meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
        name = strip_score_noise(str(meta.get("hit_pattern_name") or "").strip())
        if not name or name == "未定格局":
            return []
        text = generate_v17_fact_from_op(kind="pattern", detail=name)
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=text,
                causal_tier=int(self.causal_tier),
                priority=0.84,
                decision_hint="格局对焦",
                meta={"match_ratio": 0.78},
            )
        ]


@dataclass
class BlindSchoolV1(V17PluginSpec):
    """盲派做功：极简提示（三刑聚势 / 支冲），与备份 encyclopedia 分层解耦。"""

    plugin_id: str = "classical.blind_school.v1"
    causal_tier: int = 3
    registry_priority: float = 0.81
    doc_summary: str = "盲派核心做功引擎（轻量版）。"
    doc_rationale: str = "V17.13：meta.blind_work_hint 显影。"

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        pt = physics_tensor if isinstance(physics_tensor, dict) else {}
        meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
        hint = strip_score_noise(str(meta.get("blind_work_hint") or "").strip())
        if not hint:
            return []
        text = generate_v17_fact_from_op(kind="blind_work", detail=hint)
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=text,
                causal_tier=int(self.causal_tier),
                priority=0.81,
                decision_hint="做功检视",
                meta={"match_ratio": 0.74},
            )
        ]


PLUGINS: List[V17PluginSpec] = [
    ClimateAdjusterStub(),
    ConflictAuditorStub(),
    PatternDetectorV2(),
    BlindSchoolV1(),
]
