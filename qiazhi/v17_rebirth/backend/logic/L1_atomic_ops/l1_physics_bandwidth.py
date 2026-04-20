from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from v17_rebirth.backend.adapters.physics_adapter import PhysicsAdapter
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "l1.physics.full_bandwidth",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "PhysicsAdapter 全带宽映射。深度扫描地支冲突烈度（轻/中/猛）。",
    "Rationale": "作为 L1 原子算子，负责将 L0 的隐性物理张力转化为显性的烈度档位，不仅是信息显示，更是后续熵增计算的触发器。"
}

DECLARED_PARAMS = {
    "PRIORITY_NORMAL": 0.62,       # 普通烈度事实优先级
    "PRIORITY_FIERCE": 0.65         # 剧烈爆发事实优先级
}


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[5]


def _seg(label: str, tier: Optional[str]) -> str | None:
    if not tier or tier == "无":
        return None
    return f"{label}{tier}"


@dataclass
class L1PhysicsBandwidthPlugin(V17PluginSpec):
    plugin_id: str = "l1.physics.full_bandwidth"
    causal_tier: int = 4
    registry_priority: float = 0.735

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        pno = float(cfg.get("PRIORITY_NORMAL", DECLARED_PARAMS["PRIORITY_NORMAL"]))
        pfe = float(cfg.get("PRIORITY_FIERCE", DECLARED_PARAMS["PRIORITY_FIERCE"]))

        ad = PhysicsAdapter(root=_repo_root())
        bundle = ad.read_physics_bundle(physics_tensor if isinstance(physics_tensor, dict) else {})
        v2 = bundle.get("interaction_v2") if isinstance(bundle.get("interaction_v2"), dict) else {}
        delta = bundle.get("interaction_delta") if isinstance(bundle.get("interaction_delta"), dict) else {}
        if not v2 and not delta:
            return []
        segs: List[str] = []
        if isinstance(delta, dict) and str(delta.get("version") or "").startswith("l1_delta"):
            for key, lab in (
                ("chong_tier", "六冲"),
                ("sanxing_tier", "三刑"),
                ("hai_tier", "六害"),
                ("po_tier", "六破"),
                ("he_tier", "六合"),
                ("ban_he_tier", "半合"),
                ("stem_fusion_tier", "天干五合"),
            ):
                s = _seg(lab, str(delta.get(key) or "").strip() or None)
                if s:
                    segs.append(s)
        if not segs:
            for k in ("liu_chong", "liu_hai", "liu_po", "liu_he", "ban_he", "sanxing"):
                rows = v2.get(k)
                if isinstance(rows, list) and len(rows) > 0:
                    segs.append(k)
            if isinstance(delta, dict) and int(delta.get("n_stem_fusion_cases") or 0) > 0:
                segs.append("stem_fusion")
        if not segs:
            return []
        fierce = any("猛" in x for x in segs)
        line = "[L1全带宽·烈度: " + "·".join(segs) + "]"
        trip = bool(delta.get("yin_si_shen_complete")) if isinstance(delta, dict) else False
        if trip:
            line += "〔无恩三刑支齐〕"
        return [
            V17Fact(
                plugin_id=self.plugin_id,
                text=line,
                causal_tier=int(self.causal_tier),
                priority=pfe if fierce else pno,
                decision_hint="地支场烈度",
                meta={"is_fierce": fierce},
            )
        ]


PLUGIN = L1PhysicsBandwidthPlugin()
