# V17.99 Skill Specification
V17_SKILL_MANIFEST = {
    "id": "ten_god_pattern",
    "Layer": "L2",
    "Skill_Type": "Pattern",
    "Domain": "Logic",
    "Description": "在十神分布上给出主轴格局标签，作为叙事与决策的标题锚点。",
    "Rationale": "格局为 L2 结构层总控，它决定了整个测算模型的叙事调性与优先级锚点。"
}

DECLARED_PARAMS = {
    "GUAN_THRESHOLD": 40.0,        # 正官格激活能量阈值
    "SHI_SHANG_THRESHOLD": 35.0,   # 食伤格激活能量阈值
    "CAI_THRESHOLD": 35.0,         # 财星格激活能量阈值
    "PATTERN_PRIORITY": 0.78       # 事实输出优先级
}


def judge_ten_god_pattern(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> str:
    if not deity_scores:
        return "未定格"
    
    gt = float(cfg.get("GUAN_THRESHOLD", DECLARED_PARAMS["GUAN_THRESHOLD"]))
    st = float(cfg.get("SHI_SHANG_THRESHOLD", DECLARED_PARAMS["SHI_SHANG_THRESHOLD"]))
    ct = float(cfg.get("CAI_THRESHOLD", DECLARED_PARAMS["CAI_THRESHOLD"]))

    top = sorted(deity_scores.items(), key=lambda kv: kv[1], reverse=True)
    name, score = top[0]
    if name == "正官" and score >= gt:
        return "正官格势强"
    if name in {"食神", "伤官"} and score >= st:
        return "食伤外放格"
    if name in {"偏财", "正财"} and score >= ct:
        return "财星主导格"
    return f"{name}主轴格"


def _collect_rows(deity_scores: Dict[str, float], cfg: Dict[str, Any] = {}) -> List[dict]:
    prio = float(cfg.get("PATTERN_PRIORITY", DECLARED_PARAMS["PATTERN_PRIORITY"]))
    pattern = judge_ten_god_pattern(deity_scores, cfg)
    if pattern == "未定格":
        return []
    return [
        {
            "plugin": "ten_god_pattern",
            "fact": f"十神格局判定：{pattern}。",
            "label": "围绕主轴格局统一资源优先级，避免多线分散。",
            "priority": prio,
        }
    ]


@dataclass
class TenGodPatternPlugin(V17PluginSpec):
    plugin_id: str = "ten_god_pattern"
    causal_tier: int = 3
    registry_priority: float = 0.55

    def collect_v17_facts(self, physics_tensor: Dict[str, Any]) -> List[V17Fact]:
        from v17_rebirth.backend.logic.configs.manager import get_plugin_config
        cfg = get_plugin_config(self.plugin_id)
        scores = deity_scores_from_tensor(physics_tensor)
        return rows_dict_to_v17_facts(_collect_rows(scores, cfg), causal_tier=self.causal_tier, default_plugin_id=self.plugin_id)


PLUGIN = TenGodPatternPlugin()
