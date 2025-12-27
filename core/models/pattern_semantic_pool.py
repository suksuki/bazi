"""
格局语义池 (Pattern Semantic Pool)
为每个核心格局编写高度浓缩的物理逻辑判词
用于LLM推理流程
"""

from typing import Dict, List, Optional

PATTERN_SEMANTIC_POOL = {
    # === 冲突格局 ===
    "伤官见官": {
        "physical_logic": "旧有秩序的引力场与新生离心力的正面碰撞，导致系统稳态崩塌，产生剧烈应力，表现为规则挑战与名誉损耗。",
        "energy_flow": "伤官（离心力）与正官（向心力）形成相位冲突，能量在对抗中耗散，系统稳定性急剧下降。",
        "destiny_traits": "权威与自由的撕裂，易有官非、职场冲突、名誉受损，但同时也可能带来突破性创新。"
    },
    
    "伤官伤尽": {
        "physical_logic": "离心力完全占据主导，系统处于超稳态结构，能量极度聚焦于表达和创造，无约束状态下的纯粹动能释放。",
        "energy_flow": "伤官能量高度聚焦，形成单向能量流，系统处于临界稳定状态，一旦有官星介入即发生相变。",
        "destiny_traits": "才华横溢，不受约束，适合自由职业或艺术创作，名誉极高但易招小人嫉妒。"
    },
    
    "枭神夺食": {
        "physical_logic": "印星（资源）与食神（输出）形成能量争夺，导致输出通道被阻塞，系统内部能量无法有效释放。",
        "energy_flow": "印星吸收食神能量，形成能量内耗，表现为才华被压抑、表达受阻、创造力受限。",
        "destiny_traits": "内在矛盾，才华难以施展，易有精神压力，需要通过财星通关或比劫制印来化解。"
    },
    
    # === 化气格局 ===
    "化火格": {
        "physical_logic": "系统发生化学变质，能量结构从原始状态转化为火元素主导，形成单一能量场。",
        "energy_flow": "天干五合成功，原始能量完全转化为火，系统能量流向单一，形成高度聚焦的能量场。",
        "destiny_traits": "性格和命运发生转化，具有火的特性：热情、急躁、执行力强，但易冲动。"
    },
    
    "化金格": {
        "physical_logic": "系统能量转化为金元素主导，形成刚硬、锐利的能量场，具有强烈的切割和约束力。",
        "energy_flow": "能量完全转化为金，形成单向能量流，系统处于刚强状态，但缺乏柔韧性。",
        "destiny_traits": "性格刚毅果断，具有强烈的原则性和执行力，但可能过于刚硬，需要水来调候。"
    },
    
    # === 从格 ===
    "从财格": {
        "physical_logic": "系统完全服从财星，能量流向单一，日主极弱，形成完全依赖外部能量的结构。",
        "energy_flow": "财星能量占据绝对主导，日主能量被完全压制，系统能量完全流向财富积累。",
        "destiny_traits": "以财为用，善于经营和积累，财富是人生核心追求，但需要注意平衡物质与精神。"
    },
    
    "从官格": {
        "physical_logic": "系统完全服从官星，能量流向权威和秩序，日主极弱，形成完全依赖规则的结构。",
        "energy_flow": "官星能量占据绝对主导，日主能量被完全压制，系统能量完全流向权力和地位。",
        "destiny_traits": "以官为用，具有强烈的责任感和秩序感，适合体制内工作，但可能过于拘谨。"
    },
    
    # === 空间奇点 ===
    "拱合财局": {
        "physical_logic": "地支空隙产生的虚拟质量吸积，形成暗能量引力场，表现为非对称竞争优势与隐形资源获取。",
        "energy_flow": "通过空间奇点汇聚能量，形成局部高能区，财富能量突然出现，但可能伴随突变。",
        "destiny_traits": "财富或机遇突然出现，具有非对称优势，但需要注意突变带来的风险。"
    },
    
    "三会局": {
        "physical_logic": "三个地支形成方向性汇聚，产生强大的能量场，形成局部能量爆发。",
        "energy_flow": "三个地支能量汇聚，形成高能区，能量流动加速，系统处于活跃状态。",
        "destiny_traits": "能量爆发，机遇突然出现，各方面发展加速，但可能伴随不稳定因素。"
    },
    
    "三合局": {
        "physical_logic": "三个地支形成三角形稳定结构，产生持续的能量场，形成稳定的能量循环。",
        "energy_flow": "三个地支形成能量循环，系统处于稳定状态，能量持续流动，形成良性循环。",
        "destiny_traits": "稳定的能量循环，各方面发展平稳，具有持续的优势，但可能缺乏突破性。"
    },
    
    # === 特殊格局 ===
    "羊刃驾杀": {
        "physical_logic": "能量极度刚强，系统处于临界状态，羊刃与七杀形成动态平衡，具有极强的爆发力。",
        "energy_flow": "羊刃（极强能量）与七杀（约束力）形成平衡，系统处于临界状态，能量随时可能爆发。",
        "destiny_traits": "刚强果断，有领导力，但易冲动，需要印星或食神来制衡，否则易有冲突。"
    },
    
    "超导体格局": {
        "physical_logic": "系统能量高度聚焦，结构极度稳定，形成超导状态，能量流动无损耗，表现为纯粹与秩序。",
        "energy_flow": "能量高度聚焦，形成超导通道，能量流动无阻力，系统处于完美状态，但易受杂质干扰。",
        "destiny_traits": "纯粹与秩序，追求完美，具有超常的专注力，适合科研、精密制造等需要极致专注的领域。"
    },
    
    "墓库格局": {
        "physical_logic": "能量被存储在地支库中，形成潜在能量场，一旦冲开即爆发，表现为财富或机遇的突然出现。",
        "energy_flow": "能量被锁定在库中，形成潜在能量，一旦触发即爆发，系统能量突然释放。",
        "destiny_traits": "财富或机遇被锁定，需要等待时机冲开，一旦触发即爆发，但可能伴随突变。"
    },
    
    # === 冲突子格局 ===
    "化火受阻": {
        "physical_logic": "结构性动荡，原本顺遂的能量流突然发生相位偏移，化火过程被水元素阻断。",
        "energy_flow": "化火能量流被水元素阻断，系统发生相变，能量流动受阻，系统稳定性下降。",
        "destiny_traits": "原本顺利的转化过程受阻，易有挫折和反复，需要耐心等待或寻找通关路径。"
    },
    
    "伤官伤尽见官": {
        "physical_logic": "超稳态结构被打破，能量发生冲突，伤官伤尽的纯粹状态被官星破坏。",
        "energy_flow": "超稳态结构被打破，能量发生冲突，系统从稳定状态退化为冲突状态。",
        "destiny_traits": "原本的自由状态受到约束，易有官非或职场冲突，需要调整策略。"
    }
}


def get_pattern_semantic(pattern_name: str) -> Optional[Dict[str, str]]:
    """
    获取格局的语义判词
    
    Args:
        pattern_name: 格局名称
        
    Returns:
        格局语义字典，包含physical_logic, energy_flow, destiny_traits
    """
    # 模糊匹配
    for key, value in PATTERN_SEMANTIC_POOL.items():
        if key in pattern_name or pattern_name in key:
            return value
    
    # 如果找不到，返回通用语义
    return {
        "physical_logic": "系统能量分布相对均衡，无明显特殊结构。",
        "energy_flow": "能量流动平稳，系统处于稳定状态。",
        "destiny_traits": "运势平稳，无明显波动，需要根据具体情况调整。"
    }


def get_multiple_pattern_semantics(pattern_names: List[str]) -> List[Dict[str, str]]:
    """
    获取多个格局的语义判词
    
    Args:
        pattern_names: 格局名称列表
        
    Returns:
        格局语义列表
    """
    semantics = []
    for pattern_name in pattern_names:
        semantic = get_pattern_semantic(pattern_name)
        if semantic:
            semantic['pattern_name'] = pattern_name
            semantics.append(semantic)
    return semantics

