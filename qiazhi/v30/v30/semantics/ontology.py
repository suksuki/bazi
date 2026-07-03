from __future__ import annotations

BAZI_SEMANTIC_ONTOLOGY_VERSION = "v30.bazi_semantic_ontology.v1"


TEN_GOD_ONTOLOGY: dict[str, dict[str, object]] = {
    "bi_jian": {
        "label": "比肩",
        "macro_domains": {"career": 0.42, "wealth": 0.34, "relationship": 0.28, "family": 0.22},
        "keywords": ["自我", "竞争", "同辈", "独立", "分担"],
        "drivers": ["self_agency", "peer_competition", "resource_split"],
        "relationship_roles": ["同辈", "兄弟姐妹", "同事"],
    },
    "jie_cai": {
        "label": "劫财",
        "macro_domains": {"wealth": 0.54, "career": 0.38, "relationship": 0.32, "family": 0.24},
        "keywords": ["争夺", "合作", "分配", "冲动", "合伙"],
        "drivers": ["resource_competition", "partnership_risk", "impulse_cost"],
        "relationship_roles": ["同辈", "合伙人", "竞争者"],
    },
    "shi_shen": {
        "label": "食神",
        "macro_domains": {"career": 0.46, "wealth": 0.38, "health": 0.34, "children": 0.3},
        "keywords": ["输出", "表达", "稳定产出", "享受", "养分"],
        "drivers": ["sustainable_output", "creative_expression", "wellbeing_rhythm"],
        "relationship_roles": ["子女", "作品", "下属"],
    },
    "shang_guan": {
        "label": "伤官",
        "macro_domains": {"career": 0.52, "relationship": 0.4, "wealth": 0.36, "health": 0.24},
        "keywords": ["表达", "突破", "不服管", "才华", "锋芒"],
        "drivers": ["breakthrough_output", "rule_tension", "visibility"],
        "relationship_roles": ["表达对象", "制度边界", "下属"],
    },
    "zheng_cai": {
        "label": "正财",
        "macro_domains": {"wealth": 0.68, "relationship": 0.42, "family": 0.34, "career": 0.3},
        "keywords": ["稳定收入", "现实责任", "管理", "配偶", "积累"],
        "drivers": ["stable_income", "asset_discipline", "responsibility"],
        "relationship_roles": ["配偶", "父亲线索", "资源对象"],
    },
    "pian_cai": {
        "label": "偏财",
        "macro_domains": {"wealth": 0.72, "career": 0.42, "relationship": 0.34, "family": 0.26},
        "keywords": ["机会", "流动资金", "资源整合", "投资", "外财"],
        "drivers": ["opportunity_capture", "resource_network", "risk_reward"],
        "relationship_roles": ["父亲线索", "资源方", "客户"],
    },
    "zheng_guan": {
        "label": "正官",
        "macro_domains": {"career": 0.68, "relationship": 0.38, "family": 0.32, "health": 0.22},
        "keywords": ["规则", "职位", "责任", "秩序", "名分"],
        "drivers": ["role_responsibility", "institutional_order", "boundary"],
        "relationship_roles": ["上级", "丈夫线索", "制度"],
    },
    "qi_sha": {
        "label": "七杀",
        "macro_domains": {"career": 0.62, "health": 0.36, "relationship": 0.34, "timing": 0.3},
        "keywords": ["压力", "风险", "竞争", "执行", "危机"],
        "drivers": ["pressure_response", "risk_control", "decisive_action"],
        "relationship_roles": ["压力源", "强势对象", "竞争者"],
    },
    "zheng_yin": {
        "label": "正印",
        "macro_domains": {"career": 0.48, "family": 0.44, "health": 0.32, "learning": 0.3},
        "keywords": ["保护", "资质", "学习", "长辈", "承接"],
        "drivers": ["credential_support", "protection", "learning_capacity"],
        "relationship_roles": ["母亲线索", "长辈", "平台"],
    },
    "pian_yin": {
        "label": "偏印",
        "macro_domains": {"career": 0.42, "health": 0.38, "family": 0.34, "hidden_factor": 0.32},
        "keywords": ["偏门知识", "敏感", "孤独", "非标准资源", "转化"],
        "drivers": ["nonstandard_support", "sensitivity", "hidden_pattern"],
        "relationship_roles": ["母亲线索", "特殊资源", "非典型平台"],
    },
}

MACRO_DOMAIN_ONTOLOGY: dict[str, dict[str, object]] = {
    "career": {
        "label": "事业",
        "ten_god_weights": {"zheng_guan": 0.9, "qi_sha": 0.82, "zheng_yin": 0.62, "shang_guan": 0.58, "shi_shen": 0.5},
        "keywords": ["职位", "职责", "平台", "转型", "输出", "权责"],
        "question_slots": ["direction", "pressure", "timing", "platform"],
    },
    "wealth": {
        "label": "财富",
        "ten_god_weights": {"zheng_cai": 0.94, "pian_cai": 0.96, "jie_cai": 0.54, "shi_shen": 0.42, "shang_guan": 0.38},
        "keywords": ["收入", "现金流", "投资", "分配", "风险", "积累"],
        "question_slots": ["earning", "risk", "timing", "allocation"],
    },
    "relationship": {
        "label": "感情",
        "ten_god_weights": {"zheng_cai": 0.5, "pian_cai": 0.42, "zheng_guan": 0.5, "qi_sha": 0.42, "shang_guan": 0.38},
        "keywords": ["相处", "边界", "承诺", "反复", "压力", "沟通"],
        "question_slots": ["pattern", "tension", "boundary", "timing"],
    },
    "family": {
        "label": "亲情",
        "ten_god_weights": {"zheng_yin": 0.62, "pian_yin": 0.54, "zheng_cai": 0.42, "pian_cai": 0.4, "bi_jian": 0.3},
        "keywords": ["父母", "长辈", "家庭责任", "支持", "牵挂"],
        "question_slots": ["support", "pressure", "boundary"],
    },
    "health": {
        "label": "身体健康",
        "ten_god_weights": {"qi_sha": 0.46, "pian_yin": 0.42, "shi_shen": 0.38, "zheng_yin": 0.34},
        "keywords": ["负荷", "节律", "睡眠", "压力", "消耗", "恢复"],
        "question_slots": ["rhythm", "stress", "recovery", "warning"],
    },
    "timing": {
        "label": "时机",
        "ten_god_weights": {"qi_sha": 0.42, "pian_cai": 0.36, "shang_guan": 0.34, "zheng_guan": 0.32},
        "keywords": ["大运", "流年", "触发", "窗口", "阶段"],
        "question_slots": ["year", "trigger", "choice", "pressure"],
    },
    "hidden_factor": {
        "label": "隐藏属性",
        "ten_god_weights": {"pian_yin": 0.58, "jie_cai": 0.38, "qi_sha": 0.36, "shang_guan": 0.34},
        "keywords": ["反复状态", "暗线", "代价", "特殊年份", "触发"],
        "question_slots": ["domain", "recurrence", "year", "trigger", "cost", "outcome"],
    },
}

ELEMENT_HEALTH_KEYWORDS: dict[str, list[str]] = {
    "wood": ["筋骨", "肝胆", "舒展", "情绪郁结"],
    "fire": ["心火", "睡眠", "血压", "兴奋"],
    "earth": ["脾胃", "消化", "湿重", "稳定"],
    "metal": ["呼吸", "皮肤", "收敛", "规则"],
    "water": ["肾水", "泌尿", "寒湿", "恢复"],
}


def get_bazi_semantic_ontology() -> dict[str, object]:
    return {
        "version": BAZI_SEMANTIC_ONTOLOGY_VERSION,
        "ten_gods": TEN_GOD_ONTOLOGY,
        "macro_domains": MACRO_DOMAIN_ONTOLOGY,
        "element_health_keywords": ELEMENT_HEALTH_KEYWORDS,
        "trainable_slots": [
            "ten_god_to_macro_domain_weight",
            "macro_domain_question_slot_weight",
            "semantic_driver_claim_weight",
            "hidden_factor_probe_slot_weight",
        ],
        "blocked_targets": ["chart_facts", "calendar_conversion", "pillar_calculation"],
        "boundary": "semantic_ontology_maps_meaning_for_dialogue_and_training_without_mutating_chart_facts",
    }
