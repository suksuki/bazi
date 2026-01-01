"""
Antigravity Engine V3.0 Core Configuration
==========================================
Role: Single Source of Truth for Numerical Parameters
Version: 3.0 (Pure Logic Support) + V3.2 (Cascading Configuration)

此文件承载了从文档和逻辑代码中剥离的所有物理阈值。
Logic Layer (代码) 必须通过 `from core.config import config, get_pattern_param` 引用这些值，
严禁在业务逻辑中出现任何 Magic Number。

[V3.2] 层级化配置系统 (Cascading Configuration):
- L1 (Global Physics): 宇宙基准物理，适用于90%情况的默认值
- L2 (Category Defaults): 族群特征（如财富组、官杀组等）
- L3 (Pattern Specifics): 格局特异性参数，可以重写L1和L2
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

@dataclass
class PrecisionScoreWeights:
    """Precision Score 权重配置 (FDS-V3.1 校准版)"""
    similarity: float = 0.5   # 余弦相似度权重 (方向/形状匹配) - V3.1: 回调至0.5，平衡形状和位置
    distance: float = 0.5     # 高斯衰减权重 (位置/概率匹配) - V3.1: 回调至0.5，恢复距离约束
    
    def __post_init__(self):
        # 验证权重和为1.0
        total = self.similarity + self.distance
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"PrecisionScoreWeights 权重和必须为1.0，当前为{total}")


@dataclass
class SpacetimeParams:
    """时空相对论参数 (L2: Spacetime Relativity)"""
    macro_bonus: float = 0.2           # 国运共振加成 (Era Resonance)
    latitude_coefficients: Dict[str, float] = None  # 纬度修正系数
    invert_seasons: bool = False       # 南北半球季节反转开关
    solar_time_correction: float = 4.0 # 经度每差1度的时间偏移(分钟)
    
    def __post_init__(self):
        if self.latitude_coefficients is None:
            self.latitude_coefficients = {
                "high": 1.2,           # 高纬度 (寒/燥增强)
                "low": 0.8             # 低纬度 (热/湿增强)
            }

@dataclass
class VaultParams:
    """墓库拓扑参数 (L2: Storehouse Topology)"""
    threshold: float = 20.0            # 库与墓的能量分界线
    sealed_damping: float = 0.4        # 闭库状态下的能量利用率 (0.0 - 1.0)
    open_bonus: float = 1.5            # 冲开后的量子隧穿爆发系数 (> 1.0)
    collapse_penalty: float = 0.5      # 破墓后的结构震荡惩罚系数

@dataclass
class FlowParams:
    """流体力学参数 (L2: Energy Conduction)"""
    generation_efficiency: float = 0.3 # 生的传递效率
    control_impact: float = 0.7        # 克/耗的打击力度

@dataclass
class InteractionsParams:
    """交互作用参数 (L2: Energy Conduction)"""
    clash_damping: float = 0.3         # 冲导致的能量折损率

@dataclass
class MediationParams:
    """通关机制参数 (L2: Energy Conduction)"""
    threshold: float = 4.0             # 通关神生效的最低能量阈值

@dataclass
class PhysicsParams:
    """基础物理场参数 (L1: Global Physics - 宇宙基准物理)"""
    k_factor: float = 3.0               # 标准物理常数 K (张量动力学)
    time_decay_rate: float = 0.05       # 时间衰减系数
    entropy_baseline: float = 0.5       # 熵基准值
    
    # L2 能量传导参数
    rooting_weights: Dict[str, float] = None  # 通根强度系数
    projection_bonus: float = 1.2       # 透干显化加成
    spatial_decay: float = 0.6          # 空间距离衰减基数 (1/D^k)
    global_entropy: float = 0.05        # 系统全局熵增 (自然损耗)
    
    # FDS-V3.1 Precision Score 参数（L1全局默认值）
    # 核心思想：方向正确 (Cosine) + 位置精准 (Gaussian) + 能量充足 (Gating)
    precision_weights: PrecisionScoreWeights = None  # 相似度/距离权重 (L1默认: 0.5/0.5)
    precision_gaussian_sigma: float = 2.5            # 高斯衰减参数 σ (L1默认: 2.5)
    precision_energy_gate_k: float = 0.4             # SAI能量门控阈值 (L1默认: 0.4)
    
    def __post_init__(self):
        # 初始化默认权重配置
        if self.precision_weights is None:
            self.precision_weights = PrecisionScoreWeights()
        if self.rooting_weights is None:
            self.rooting_weights = {
                "main": 1.0,           # 本气
                "middle": 0.6,         # 中气
                "residual": 0.3        # 余气
            }
    
@dataclass
class IntegrityParams:
    """完整性阈值参数"""
    threshold: float = 0.6              # 默认完整性阈值

@dataclass
class GatingParams:
    """门控（安全阀）参数 (L3: Pattern Topology)"""
    # E-Gating: 能量门控 (防止身弱假格)
    min_self_energy: float = 0.40      # 通用身弱界限 (L3文档引用)
    weak_self_limit: float = 0.45      # FDS拟合用的身弱死线 (更严)
    
    # R-Gating: 关联门控 (防止杂气混杂)
    max_relation: float = 0.60         # 纯粹格局允许的最大杂气干扰 (L3文档引用)
    max_relation_limit: float = 0.60   # 别名，保持向后兼容
    
    # M-Gating: 物质门控 (成格底线)
    min_wealth_level: float = 0.30

@dataclass
class SingularityParams:
    """奇点与拓扑参数 (FDS-V3.0)"""
    # 距离判定阈值 (Mahalanobis Distance)
    # 超过此距离被视为"偏离标准流形"
    deviation_threshold: float = 1.35
    threshold: float = 2.5             # 判定为奇点的马氏距离下限 (FDS文档引用)
    distance_threshold: float = 2.5    # 别名，保持向后兼容
    
    # 最小成团样本数 (DBSCAN)
    clustering_min_samples: int = 30
    min_samples: int = 30              # 别名，保持向后兼容
    
    # 奇点置信度下限
    confidence_floor: float = 0.75

@dataclass
class ClusteringParams:
    """聚类参数 (FDS-V3.0)"""
    min_samples: int = 30              # 晋升为子格局的最少样本数

# =========================================================================
# [V3.2] Pattern-Specific Configuration Classes (L3: 格局特异性参数)
# 每个格局可以重写L1的全局默认值
# =========================================================================

@dataclass
class PatternA03Config:
    """A-03 羊刃架杀格特异性参数 (L3)"""
    # 重写L1默认值：七杀需要高宽容度（因为本身是动态平衡）
    precision_weights: Optional[PrecisionScoreWeights] = field(default=None)  # 重写：0.5/0.5 (保持平衡)
    precision_gaussian_sigma: float = 2.2      # 重写：比默认(2.5)更严，因为七杀容易泛化
    precision_energy_gate_k: float = 0.35      # 重写：稍微放宽身弱限制（允许动态平衡）
    
    def __post_init__(self):
        # 如果precision_weights为None，使用默认值0.5/0.5
        if self.precision_weights is None:
            self.precision_weights = PrecisionScoreWeights(similarity=0.5, distance=0.5)
    
    # 业务门控阈值（格局特定）
    min_killer_energy: float = 0.6             # 七杀必须具备的最低能量
    standard_e_min: float = 0.6                # 标准态最小E值
    standard_s_min: float = 0.5                # 标准态最小S值
    standard_o_max: float = 0.35               # 标准态最大O值
    alliance_e_min: float = 0.6                # 仿星器态最小E值
    alliance_s_min: float = 0.5                # 仿星器态最小S值
    alliance_r_min: float = 0.5                # 仿星器态最小R值
    mahalanobis_threshold: float = 2.5         # 马氏距离阈值
    integrity_threshold: float = 0.6           # 完整性阈值

@dataclass
class PatternA01Config:
    """A-01 正官格特异性参数 (L3)"""
    # 重写L1默认值：正官要求"纯粹"，形状权重极高
    precision_weights: Optional[PrecisionScoreWeights] = field(default=None)  # 重写：0.8/0.2（形状优先）
    precision_gaussian_sigma: float = 1.8      # 重写：靶心极小，不允许杂质
    precision_energy_gate_k: float = 0.45      # 重写：身弱不能任官，门槛较高
    
    def __post_init__(self):
        # 如果precision_weights为None，使用特异性值0.8/0.2
        if self.precision_weights is None:
            self.precision_weights = PrecisionScoreWeights(similarity=0.8, distance=0.2)
    
    # 业务参数
    standard_e_min: float = 0.45               # 标准态最小E值（防假格）
    integrity_threshold: float = 0.65          # 完整性阈值（更严格）
    mahalanobis_threshold: float = 3.0
    k_factor: float = 2.0

@dataclass
class PatternD02Config:
    """D-02 偏财格特异性参数 (L3)"""
    # 重写L1默认值：偏财看重"势"（形状），位置可以飘忽
    precision_weights: Optional[PrecisionScoreWeights] = field(default=None)  # 重写：0.7/0.3（形状优先）
    precision_gaussian_sigma: float = 3.0      # 重写：允许较大的波动（大鳄通常不走寻常路）
    precision_energy_gate_k: float = 0.3       # 重写：允许身稍弱但财气通门户
    
    def __post_init__(self):
        # 如果precision_weights为None，使用特异性值0.7/0.3
        if self.precision_weights is None:
            self.precision_weights = PrecisionScoreWeights(similarity=0.7, distance=0.3)
    
    # 业务参数
    collider_e_min: float = 0.45               # 风投态最小E值
    collider_m_min: float = 0.6                # 风投态最小M值
    collider_s_min: float = 0.5                # 风投态最小S值
    syndicate_e_min: float = 0.45              # 财团态最小E值
    syndicate_m_min: float = 0.6               # 财团态最小M值
    syndicate_r_min: float = 0.5               # 财团态最小R值
    syndicate_r_limit: float = 0.55            # 财团态的比劫下限 (FDS文档引用)
    syndicate_m_limit: float = 0.60            # 财团态的财星下限 (FDS文档引用)
    standard_e_min: float = 0.45               # 标准态最小E值
    standard_m_min: float = 0.55               # 标准态最小M值
    integrity_threshold: float = 0.5
    mahalanobis_threshold: float = 3.0
    k_factor: float = 3.0

@dataclass
class PatternB02Config:
    """B-02 伤官格特异性参数 (L3)"""
    # 重写L1默认值：伤官容易混杂，需要收紧
    precision_gaussian_sigma: float = 2.0      # 重写：收紧靶心
    precision_energy_gate_k: float = 0.5       # 重写：身弱伤旺必泄气，门槛最高
    
    # 业务参数
    authority_e_min: float = 0.45              # 权威态最小E值（防神经质）
    authority_high_e_min: float = 0.65         # 权威态高E值要求
    tycoon_e_min: float = 0.45                 # 巨贾态最小E值
    tycoon_m_min: float = 0.6                  # 巨贾态最小M值
    standard_e_min: float = 0.45               # 标准态最小E值
    integrity_threshold: float = 0.6
    mahalanobis_threshold: float = 3.0
    k_factor: float = 1.5

@dataclass
class PatternD01Config:
    """D-01 正财格特异性参数 (L3)"""
    keeper_e_min: float = 0.45                 # 守财态最小E值
    keeper_m_min: float = 0.4                  # 守财态最小M值
    surrender_r_max: float = 0.5               # 弃命态最大R值
    surrender_e_max: float = 0.3               # 弃命态最大E值
    integrity_threshold: float = 0.5
    k_factor: float = 3.0

@dataclass
class PatternB01Config:
    """B-01 食神格特异性参数 (L3)"""
    reversal_s_min: float = 0.4                # 逆转态最小S值
    reversal_e_min: float = 0.45               # 逆转态最小E值
    standard_e_min: float = 0.32               # 标准态最小E值（防止泄漏）
    integrity_threshold: float = 0.5
    mahalanobis_threshold: float = 3.0
    k_factor: float = 2.0

@dataclass
class PatternSpecificParams:
    """格局专属参数容器 (保持向后兼容)"""
    # V3.2: 使用新的L3配置类
    a03: PatternA03Config = field(default_factory=PatternA03Config)
    a01: PatternA01Config = field(default_factory=PatternA01Config)
    d02: PatternD02Config = field(default_factory=PatternD02Config)
    b02: PatternB02Config = field(default_factory=PatternB02Config)
    d01: PatternD01Config = field(default_factory=PatternD01Config)
    b01: PatternB01Config = field(default_factory=PatternB01Config)
    
    # 向后兼容：字典形式的访问（旧代码可能还在用）
    def __post_init__(self):
        # 初始化字典形式的访问（用于向后兼容）
        self._dict_cache = {}

    def get_dict(self, pattern_id: str) -> Dict[str, Any]:
        """向后兼容：返回字典形式的参数"""
        if pattern_id in self._dict_cache:
            return self._dict_cache[pattern_id]
        
        pattern_map = {
            'a03': self.a03,
            'a01': self.a01,
            'd02': self.d02,
            'b02': self.b02,
            'd01': self.d01,
            'b01': self.b01
        }
        
        if pattern_id.lower() not in pattern_map:
            return {}
        
        pattern_obj = pattern_map[pattern_id.lower()]
        result = {}
        
        # 提取所有字段
        for key, value in pattern_obj.__dict__.items():
            if not key.startswith('_'):
                if isinstance(value, PrecisionScoreWeights):
                    result[key] = {'similarity': value.similarity, 'distance': value.distance}
                else:
                    result[key] = value
        
        self._dict_cache[pattern_id] = result
        return result

@dataclass
class SystemConfig:
    """系统总配置 (FDS-V3.0 Master Config)"""
    version: str = "3.2.0"
    mode: str = "PRODUCTION"
    
    # L1 & L2 场域物理参数
    spacetime: SpacetimeParams = field(default_factory=SpacetimeParams)
    vault: VaultParams = field(default_factory=VaultParams)
    physics: PhysicsParams = field(default_factory=PhysicsParams)  # L1: Global Physics
    flow: FlowParams = field(default_factory=FlowParams)
    interactions: InteractionsParams = field(default_factory=InteractionsParams)
    mediation: MediationParams = field(default_factory=MediationParams)
    
    # L3 格局协议参数
    integrity: IntegrityParams = field(default_factory=IntegrityParams)
    gating: GatingParams = field(default_factory=GatingParams)
    singularity: SingularityParams = field(default_factory=SingularityParams)
    clustering: ClusteringParams = field(default_factory=ClusteringParams)
    patterns: PatternSpecificParams = field(default_factory=PatternSpecificParams)  # L3: Pattern Specifics
    
    def resolve_config_ref(self, ref_path: str) -> Any:
        """
        解析配置引用路径，如 '@config.gating.weak_self_limit'
        
        Args:
            ref_path: 配置引用路径，格式为 '@config.xxx.yyy.zzz'
            
        Returns:
            配置值
            
        Raises:
            KeyError: 如果路径不存在
        """
        if not ref_path.startswith('@config.'):
            return ref_path
        
        path = ref_path.replace('@config.', '').split('.')
        current = self
        
        for key in path:
            if hasattr(current, key):
                current = getattr(current, key)
            elif isinstance(current, dict):
                current = current.get(key)
                if current is None:
                    raise KeyError(f"Config path not found: {ref_path} (failed at {key})")
            else:
                raise KeyError(f"Config path not found: {ref_path} (failed at {key}, current type: {type(current)})")
        
        return current

# =========================================================================
# [V3.2] 参数获取函数：支持层级继承和重写
# =========================================================================

def get_pattern_param(
    pattern_id: str, 
    param_name: str, 
    default_value: Any = None
) -> Any:
    """
    获取格局特异性参数，支持层级继承和重写机制
    
    优先级顺序：L3 (Pattern Specific) > L1 (Global Physics)
    
    Args:
        pattern_id: 格局ID，如 'A-03', 'D-02', 'A-01' 等（支持大小写）
        param_name: 参数名称，如 'precision_gaussian_sigma', 'precision_energy_gate_k' 等
        default_value: 如果所有层级都没有该参数，返回的默认值
        
    Returns:
        参数值（优先返回L3特异性值，如果没有则返回L1全局默认值）
        
    Examples:
        >>> get_pattern_param('A-03', 'precision_gaussian_sigma')
        2.2  # 返回A-03特异值
        
        >>> get_pattern_param('A-03', 'precision_gaussian_sigma')
        2.5  # 如果A-03没有重写，返回L1默认值
        
        >>> get_pattern_param('UNKNOWN', 'precision_gaussian_sigma')
        2.5  # 未知格局返回L1默认值
    """
    # 标准化格局ID（移除连字符，转小写）
    pattern_key = pattern_id.replace('-', '').replace('_', '').lower()
    
    # 映射格局ID到配置类
    pattern_map = {
        'a03': config.patterns.a03,
        'a01': config.patterns.a01,
        'd02': config.patterns.d02,
        'b02': config.patterns.b02,
        'd01': config.patterns.d01,
        'b01': config.patterns.b01
    }
    
    # 步骤1：尝试从L3 (Pattern Specific) 获取
    pattern_config = pattern_map.get(pattern_key)
    if pattern_config:
        # 检查是否是precision_weights特殊处理
        if param_name == 'precision_weights':
            pattern_weights = getattr(pattern_config, param_name, None)
            if pattern_weights is not None:
                return pattern_weights
        else:
            value = getattr(pattern_config, param_name, None)
            if value is not None:
                return value
    
    # 步骤2：回退到L1 (Global Physics)
    if hasattr(config.physics, param_name):
        value = getattr(config.physics, param_name)
        # 如果是precision_weights，可能需要特殊处理
        if param_name == 'precision_weights' and isinstance(value, PrecisionScoreWeights):
            return value
        return value
    
    # 步骤3：如果还是没有，返回默认值
    if default_value is not None:
        return default_value
    
    # 步骤4：最后尝试从其他命名空间查找（如gating, singularity等）
    for attr_name in ['gating', 'singularity', 'integrity', 'spacetime', 'vault']:
        if hasattr(config, attr_name):
            namespace = getattr(config, attr_name)
            if hasattr(namespace, param_name):
                return getattr(namespace, param_name)
    
    # 如果所有层级都没有，抛出异常
    raise KeyError(
        f"Parameter '{param_name}' not found for pattern '{pattern_id}'. "
        f"Available patterns: {list(pattern_map.keys())}"
    )

def get_pattern_weights(pattern_id: str) -> Dict[str, float]:
    """
    获取格局的Precision Score权重配置
    
    Args:
        pattern_id: 格局ID
        
    Returns:
        权重字典 {'similarity': float, 'distance': float}
    """
    weights = get_pattern_param(pattern_id, 'precision_weights')
    
    if isinstance(weights, PrecisionScoreWeights):
        return {
            'similarity': weights.similarity,
            'distance': weights.distance
        }
    elif isinstance(weights, dict):
        return weights
    else:
        # 默认返回L1全局值
        return {
            'similarity': config.physics.precision_weights.similarity,
            'distance': config.physics.precision_weights.distance
        }

# Global Singleton instance
config = SystemConfig()
