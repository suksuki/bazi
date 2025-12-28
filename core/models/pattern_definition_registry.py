"""
[QGA V25.0] 格局定义注册表
将格局转化为纯粹的物理特性描述字典，移除硬编码判定逻辑
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import json
from pathlib import Path


@dataclass
class PatternDefinition:
    """
    格局定义：纯粹的物理特性描述
    不包含判定逻辑，只包含物理特征和修正规则
    """
    pattern_id: str  # 格局ID（如 "SHANG_GUAN_JIAN_GUAN"）
    pattern_name: str  # 格局名称（如 "伤官见官"）
    pattern_type: str  # 格局类型（"Special" / "Conflict" / "Normal"）
    
    # 物理特性描述
    core_conflict: str  # 核心矛盾点（如 "旧秩序晶格崩塌"）
    force_characteristics: Dict[str, float]  # 受力特征（五行场强分布）
    ideal_field_distribution: Dict[str, float]  # 理想场强分布
    
    # 修正规则
    correction_elements: List[str]  # 修正元素（如 ["土", "木"]）
    correction_strength: float  # 修正强度（0.0-1.0）
    
    # 语义特征
    semantic_keywords: List[str]  # 语义关键词（用于LLM理解）
    priority_rank: int  # 优先级（1=最高）
    base_strength: float  # 基础强度（0.0-1.0）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PatternDefinition':
        """从字典创建"""
        return cls(**data)


class PatternDefinitionRegistry:
    """
    格局定义注册表
    管理所有格局的物理特性描述
    """
    
    def __init__(self, registry_file: Optional[Path] = None):
        """
        初始化注册表
        
        Args:
            registry_file: 注册表JSON文件路径（可选）
        """
        self._definitions: Dict[str, PatternDefinition] = {}
        self.registry_file = registry_file or Path(__file__).parent / "pattern_definition_registry.json"
        
        # 加载默认定义
        self._load_default_definitions()
        
        # 如果存在JSON文件，尝试加载
        if self.registry_file.exists():
            try:
                self.load_from_file(self.registry_file)
            except Exception as e:
                print(f"⚠️ 无法加载注册表文件 {self.registry_file}: {e}，使用默认定义")
    
    def _load_default_definitions(self):
        """加载默认格局定义"""
        # 伤官见官
        self.register(PatternDefinition(
            pattern_id="SHANG_GUAN_JIAN_GUAN",
            pattern_name="伤官见官",
            pattern_type="Conflict",
            core_conflict="旧秩序晶格崩塌，产生高频剪切力，系统稳定性急剧下降",
            force_characteristics={
                "metal": -20.0,  # 官星（金）大幅扣减
                "earth": +10.0,  # 财星（土）救应
                "wood": +10.0    # 印星（木）救应
            },
            ideal_field_distribution={
                "metal": 0.3,  # 官星降低
                "earth": 0.4,  # 财星增强
                "wood": 0.3    # 印星增强
            },
            correction_elements=["土", "木"],
            correction_strength=0.75,
            semantic_keywords=["权威与自由冲突", "规则挑战", "名誉损耗", "秩序崩塌"],
            priority_rank=2,
            base_strength=0.75
        ))
        
        # 化火格
        self.register(PatternDefinition(
            pattern_id="HUA_HUO_GE",
            pattern_name="化火格",
            pattern_type="Special",
            core_conflict="分子级化学相变因环境干预而被迫中断，导致能量淤积",
            force_characteristics={
                "fire": +30.0,   # 火大幅增加（合化成功）
                "earth": -15.0,  # 戊的能量转化为火
                "water": -15.0   # 癸的能量转化为火
            },
            ideal_field_distribution={
                "fire": 0.6,    # 火占主导
                "earth": 0.2,   # 土减少
                "water": 0.2    # 水减少
            },
            correction_elements=["火"],
            correction_strength=0.85,
            semantic_keywords=["化学相变", "能量转化", "性格转化", "人生转折"],
            priority_rank=1,
            base_strength=0.85
        ))
        
        # 枭神夺食
        self.register(PatternDefinition(
            pattern_id="XIAO_SHEN_DUO_SHI",
            pattern_name="枭神夺食",
            pattern_type="Conflict",
            core_conflict="生物能供给截断，偏印（枭）对食神的相位干涉，导致系统输入中断",
            force_characteristics={
                "earth": +12.0,  # 财星通关
                "metal": +8.0,   # 财星通关
                "wood": +5.0,    # 比劫制印
                "fire": -10.0,   # 食神被夺，火能量减少
                "water": -5.0    # 偏印（枭）可能对应水
            },
            ideal_field_distribution={
                "earth": 0.35,  # 财星增强
                "metal": 0.25,  # 财星增强
                "wood": 0.15,   # 比劫制印
                "fire": 0.15,   # 食神降低
                "water": 0.10   # 偏印（需要制衡）
            },
            correction_elements=["土", "金"],
            correction_strength=0.7,
            semantic_keywords=["精神内耗", "资源被夺", "项目停滞", "生机受损"],
            priority_rank=2,
            base_strength=0.7
        ))
        
        # 建禄月劫
        self.register(PatternDefinition(
            pattern_id="JIAN_LU_YUE_JIE",
            pattern_name="建禄月劫",
            pattern_type="Special",
            core_conflict="热力学正反馈爆炸，能量密度过载，缺乏疏导",
            force_characteristics={
                "earth": +15.0,  # 财星疏导（土）
                "metal": +10.0   # 财星疏导（金）
            },
            ideal_field_distribution={
                "earth": 0.5,   # 财星占主导
                "metal": 0.3,   # 财星增强
                "fire": 0.2     # 能量释放
            },
            correction_elements=["土", "金"],
            correction_strength=0.8,
            semantic_keywords=["能量过载", "破财", "能量爆发", "需要疏导"],
            priority_rank=1,
            base_strength=0.8
        ))
        
        # 官印相生
        self.register(PatternDefinition(
            pattern_id="GUAN_YIN_XIANG_SHENG",
            pattern_name="官印相生",
            pattern_type="Normal",
            core_conflict="稳态层流模型，能量流不存在紊流和对撞",
            force_characteristics={
                "metal": +8.0,   # 正官（金）
                "water": +10.0,  # 正印（水）
                "wood": +5.0     # 正印（木，部分情况）
            },
            ideal_field_distribution={
                "metal": 0.3,   # 官星
                "water": 0.4,   # 印星占主导
                "wood": 0.2,    # 印星
                "fire": 0.1     # 平衡
            },
            correction_elements=["金", "水", "木"],
            correction_strength=0.65,
            semantic_keywords=["社会声望", "资源位阶", "无阻力跃迁", "能量平滑传导"],
            priority_rank=3,
            base_strength=0.65
        ))
        
        # 羊刃架杀
        self.register(PatternDefinition(
            pattern_id="YANG_REN_JIA_SHA",
            pattern_name="羊刃架杀",
            pattern_type="Special",
            core_conflict="极端高压下的动态平衡，系统承载能力达到峰值",
            force_characteristics={
                "fire": +10.0,  # 高压状态，能量集中
                "metal": +5.0   # 七杀（金）的力量
            },
            ideal_field_distribution={
                "fire": 0.5,    # 能量集中
                "metal": 0.3,   # 七杀
                "water": 0.2     # 平衡
            },
            correction_elements=["火", "金"],
            correction_strength=0.9,
            semantic_keywords=["极端高压", "动态平衡", "危机扩张", "竞争征服"],
            priority_rank=1,
            base_strength=0.9
        ))
        
        # 从儿格
        self.register(PatternDefinition(
            pattern_id="CONG_ER_GE",
            pattern_name="从儿格",
            pattern_type="Special",
            core_conflict="等离子喷泉模型，才华如等离子喷泉般喷发",
            force_characteristics={
                "fire": +5.0,   # 火土增加
                "earth": +5.0   # 火土增加
            },
            ideal_field_distribution={
                "fire": 0.4,    # 才华能量
                "earth": 0.3,   # 才华能量
                "water": 0.2,   # 平衡
                "wood": 0.1     # 平衡
            },
            correction_elements=["火", "土"],
            correction_strength=0.85,
            semantic_keywords=["才华横溢", "等离子喷泉", "能量喷发", "需要激活"],
            priority_rank=1,
            base_strength=0.85
        ))
    
    def register(self, definition: PatternDefinition):
        """注册格局定义"""
        self._definitions[definition.pattern_id] = definition
    
    def get_by_id(self, pattern_id: str) -> Optional[PatternDefinition]:
        """根据ID获取格局定义"""
        return self._definitions.get(pattern_id)
    
    def get_by_name(self, pattern_name: str) -> Optional[PatternDefinition]:
        """根据名称获取格局定义"""
        for definition in self._definitions.values():
            if definition.pattern_name == pattern_name:
                return definition
        return None
    
    def get_all_definitions(self) -> List[PatternDefinition]:
        """获取所有格局定义"""
        return list(self._definitions.values())
    
    def save_to_file(self, file_path: Optional[Path] = None):
        """保存到JSON文件"""
        file_path = file_path or self.registry_file
        data = {
            pattern_id: definition.to_dict()
            for pattern_id, definition in self._definitions.items()
        }
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, file_path: Optional[Path] = None):
        """从JSON文件加载"""
        file_path = file_path or self.registry_file
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        for pattern_id, definition_data in data.items():
            definition = PatternDefinition.from_dict(definition_data)
            self.register(definition)


# 全局注册表实例
_pattern_definition_registry = PatternDefinitionRegistry()


def get_pattern_definition_registry() -> PatternDefinitionRegistry:
    """获取全局格局定义注册表"""
    return _pattern_definition_registry

