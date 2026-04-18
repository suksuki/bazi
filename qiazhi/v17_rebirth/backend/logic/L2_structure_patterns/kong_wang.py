# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "kong_wang",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Risk",
    "Description": "刻画承诺与执行之间的落空风险（空亡吸纳）。",
    "Rationale": "空亡是信息态的耗散，直接影响到 L2 级叙事中的执行力度与反馈闭环。"
}

DECLARED_PARAMS = {
    "VOID_THRESHOLD": 0.75,        # 触发空亡判定的比值阈值
    "EFFICIENCY": 0.3,             # 能量传输效率修正值
    "PRIORITY": 0.82                # 事实输出优先级
}


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    threshold = float(cfg.get("VOID_THRESHOLD", DECLARED_PARAMS["VOID_THRESHOLD"]))
    eff = float(cfg.get("EFFICIENCY", DECLARED_PARAMS["EFFICIENCY"]))
    prio = float(cfg.get("PRIORITY", DECLARED_PARAMS["PRIORITY"]))

    peer = float(deity_scores.get("比肩", 0.0))
    rob = float(deity_scores.get("劫财", 0.0))
    officer = float(deity_scores.get("正官", 0.0))
    void_ratio = round((peer + rob + 1.0) / (officer + 6.0), 3)
    if void_ratio < threshold:
        return []
    return [
        {
            "plugin": "kong_wang",
            "fact": f"空亡吸纳：能量传输效率 (η) 强制修正为 {eff}。",
            "label": "高风险动作加一层回执确认，避免信息落空。",
            "priority": prio,
            "meta": {
                "transmission_efficiency": eff,
                "logic_gate": "VOID_ABSORPTION"
            }
        }
    ]


@dataclass
class KongWangPlugin(V17PluginSpec):
    plugin_id: str = "kong_wang"
    causal_tier: int = 3
    registry_priority: float = 0.58

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores, cfg), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = KongWangPlugin()
