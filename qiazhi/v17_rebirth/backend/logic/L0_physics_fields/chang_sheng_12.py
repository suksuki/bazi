# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "l1.physics.op_status",
    "Layer": "L1",
    "Skill_Type": "Atomic",
    "Domain": "Physics",
    "Description": "十二长生状态机节律与抗性修正。",
    "Rationale": "将日主十神能量映射至气数阶段，给出节律型事实锚点。"
}

DECLARED_PARAMS = {
    "RESISTANCE_HIGH": 1.2,        # 帝旺/长生等高状态抗性
    "RESISTANCE_LOW": 0.7,         # 死/绝等低状态抗性
    "STAGE_PRIORITY": 0.85          # 事实输出优先级
}


from dataclasses import dataclass
from typing import Any, Dict, List
from v17_rebirth.backend.logic.plugin_discovery import rows_dict_to_v17_facts
from v17_rebirth.backend.plugins.spec import V17Fact, V17PluginSpec

_STAGES = ["长生", "沐浴", "冠带", "临官", "帝旺", "衰", "病", "死", "墓", "绝", "胎", "养"]

# 十二长生标准查对表 (日主五行 -> 地支序列)
# 顺序：长生, 沐浴, 冠带, 临官, 帝旺, 衰, 病, 死, 墓, 绝, 胎, 养
_12_TABLE = {
    "木": ["亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌"],
    "火": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"],
    "土": ["寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑"], # 土随火行
    "金": ["巳", "午", "未", "申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰"],
    "水": ["申", "酉", "戌", "亥", "子", "丑", "寅", "卯", "辰", "巳", "午", "未"],
}


def _collect_rows(physics_tensor: Dict[str, Any], cfg: Dict[str, Any] = {}) -> List[dict]:
    high = float(cfg.get("RESISTANCE_HIGH", DECLARED_PARAMS["RESISTANCE_HIGH"]))
    low = float(cfg.get("RESISTANCE_LOW", DECLARED_PARAMS["RESISTANCE_LOW"]))
    prio = float(cfg.get("STAGE_PRIORITY", DECLARED_PARAMS["STAGE_PRIORITY"]))

    # 动态映射抗性
    res_map = {
        "长生": high, "冠带": high, "临官": high, "帝旺": high,
        "死": low, "绝": low, "病": low
    }

    meta = physics_tensor.get("meta", {})
    fp = physics_tensor.get("four_pillars", {})
    day_gz = str(fp.get("day", "")).strip()
    if len(day_gz) < 2: return []
    
    dm_stem = day_gz[0]
    from v17_rebirth.backend.logic.L0_physics_fields.ten_gods_engine import STEM_ELEMENT
    dm_el = STEM_ELEMENT.get(dm_stem, "木")
    
    # 获取月令支
    month_gz = str(fp.get("month", "")).strip()
    target_branch = month_gz[1] if len(month_gz) >= 2 else "子"
    
    table = _12_TABLE.get(dm_el, _12_TABLE["木"])
    try:
        stage_idx = table.index(target_branch)
    except ValueError:
        stage_idx = 0
        
    stage = _STAGES[stage_idx]
    resistance = res_map.get(stage, 1.0)
    
    # 注入元数据供结算层使用
    meta["qi_status_coeffs"] = {"stage": stage, "resistance": resistance}
    
    return [
        {
            "plugin": "chang_sheng_12",
            "fact": f"日主 {dm_stem} 位处「{stage}」位，抗性系数 {resistance:.1f}。",
            "label": "状态机节律",
            "priority": prio,
        }
    ]


@dataclass
class ChangSheng12Plugin(V17PluginSpec):
    plugin_id: str = "l1.physics.op_status"
    causal_tier: int = 5
    registry_priority: float = 0.72

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        local_cfg = get_plugin_config("l1.physics.op_status")
        return rows_dict_to_v17_facts(_collect_rows(physics_tensor, local_cfg), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = ChangSheng12Plugin()
