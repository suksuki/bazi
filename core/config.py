"""
Antigravity Engine V3.0 Core Configuration
==========================================
Role: Single Source of Truth for Numerical Parameters
Version: 3.0 (Pure Logic Support)

此文件承载了从文档和逻辑代码中剥离的所有物理阈值。
Logic Layer (代码) 必须通过 `from core.config import config` 引用这些值，
严禁在业务逻辑中出现任何 Magic Number。
"""

from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class PrecisionScoreWeights:
    """Precision Score 权重配置 (FDS-V3.0)"""
    similarity: float = 0.7   # 余弦相似度权重 (方向/形状匹配)
    distance: float = 0.3     # 高斯衰减权重 (位置/概率匹配)
    
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
    """基础物理场参数 (L2: Energy Conduction)"""
    k_factor: float = 3.0               # 标准物理常数 K (张量动力学)
    time_decay_rate: float = 0.05       # 时间衰减系数
    entropy_baseline: float = 0.5       # 熵基准值
    
    # L2 能量传导参数
    rooting_weights: Dict[str, float] = None  # 通根强度系数
    projection_bonus: float = 1.2       # 透干显化加成
    spatial_decay: float = 0.6          # 空间距离衰减基数 (1/D^k)
    global_entropy: float = 0.05        # 系统全局熵增 (自然损耗)
    
    # FDS-V3.0 Precision Score 参数（增强版算法，完全配置化）
    # 核心思想：方向正确 (Cosine) + 位置精准 (Gaussian) + 能量充足 (Gating)
    precision_weights: PrecisionScoreWeights = None  # 相似度/距离权重
    precision_gaussian_sigma: float = 3.5            # 高斯衰减参数 σ
    precision_energy_gate_k: float = 0.3             # SAI能量门控阈值 (tanh(SAI/k))
    
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

@dataclass
class PatternSpecificParams:
    """格局专属参数 (FDS-V3.0格局特定阈值)"""
    # A-03 羊刃架杀格参数
    a03: Dict[str, Any] = None
    
    # D-01 正财格参数
    d01: Dict[str, Any] = None
    
    # A-01 正官格参数 (保留兼容)
    a01_officer: Dict[str, float] = None
    
    # D-02 偏财格参数 (保留兼容)
    d02_wealth: Dict[str, float] = None

    def __post_init__(self):
        # A-03 羊刃架杀格 (The Reactor)
        self.a03 = {
            # 安全门控阈值
            "alliance_e_min": 0.6,          # 仿星器态最小E值
            "alliance_s_min": 0.5,          # 仿星器态最小S值
            "alliance_r_min": 0.5,          # 仿星器态最小R值
            "standard_e_min": 0.6,          # 标准态最小E值
            "standard_s_min": 0.5,          # 标准态最小S值
            "standard_o_max": 0.35,         # 标准态最大O值
            # 马氏距离阈值
            "mahalanobis_threshold": 2.5,
            # 物理参数
            "integrity_threshold": 0.6
        }
        
        # D-01 正财格 (The Keeper)
        self.d01 = {
            # 安全门控阈值
            "keeper_e_min": 0.45,           # 守财态最小E值
            "keeper_m_min": 0.4,            # 守财态最小M值
            "surrender_r_max": 0.5,         # 弃命态最大R值
            "surrender_e_max": 0.3,         # 弃命态最大E值
            # 物理参数
            "integrity_threshold": 0.5,
            "k_factor": 3.0
        }
        
        # D-02 偏财格 (The Hunter)
        self.d02 = {
            # 安全门控阈值
            "collider_e_min": 0.45,         # 风投态最小E值
            "collider_m_min": 0.6,          # 风投态最小M值
            "collider_s_min": 0.5,          # 风投态最小S值
            "syndicate_e_min": 0.45,        # 财团态最小E值
            "syndicate_m_min": 0.6,         # 财团态最小M值
            "syndicate_r_min": 0.5,         # 财团态最小R值
            "syndicate_r_limit": 0.55,      # 财团态的比劫下限 (FDS文档引用)
            "syndicate_m_limit": 0.60,      # 财团态的财星下限 (FDS文档引用)
            "standard_e_min": 0.45,         # 标准态最小E值
            "standard_m_min": 0.55,         # 标准态最小M值
            # 物理参数
            "integrity_threshold": 0.5,
            "mahalanobis_threshold": 3.0,
            "k_factor": 3.0
        }
        
        # B-01 食神格 (The Artist)
        self.b01 = {
            # 安全门控阈值
            "reversal_s_min": 0.4,          # 逆转态最小S值
            "reversal_e_min": 0.45,         # 逆转态最小E值
            "standard_e_min": 0.32,         # 标准态最小E值（防止泄漏）
            # 物理参数
            "integrity_threshold": 0.5,
            "mahalanobis_threshold": 3.0,
            "k_factor": 2.0
        }
        
        # A-01 正官格 (The Judge)
        self.a01 = {
            # 安全门控阈值
            "standard_e_min": 0.45,         # 标准态最小E值（防假格）
            # 物理参数
            "integrity_threshold": 0.65,
            "mahalanobis_threshold": 3.0,
            "k_factor": 2.0
        }
        
        # B-02 伤官格 (The Innovator)
        self.b02 = {
            # 安全门控阈值
            "authority_e_min": 0.45,        # 权威态最小E值（防神经质）
            "authority_high_e_min": 0.65,   # 权威态高E值要求
            "tycoon_e_min": 0.45,           # 巨贾态最小E值
            "tycoon_m_min": 0.6,            # 巨贾态最小M值
            "standard_e_min": 0.45,         # 标准态最小E值
            # 物理参数
            "integrity_threshold": 0.6,
            "mahalanobis_threshold": 3.0,
            "k_factor": 1.5
        }
        
        # A-01 正官格参数 (保留兼容)
        self.a01_officer = {
            "purity_threshold": 0.55,
            "nobility_factor": 1.2
        }
        
        # D-02 偏财格参数 (保留兼容)
        self.d02_wealth = {
            "risk_tolerance": 0.8,
            "leverage_cap": 2.0
        }

@dataclass
class SystemConfig:
    """系统总配置 (FDS-V3.0 Master Config)"""
    version: str = "3.0.0"
    mode: str = "PRODUCTION"
    
    # L2 场域物理参数
    spacetime: SpacetimeParams = field(default_factory=SpacetimeParams)
    vault: VaultParams = field(default_factory=VaultParams)
    physics: PhysicsParams = field(default_factory=PhysicsParams)
    flow: FlowParams = field(default_factory=FlowParams)
    interactions: InteractionsParams = field(default_factory=InteractionsParams)
    mediation: MediationParams = field(default_factory=MediationParams)
    
    # L3 格局协议参数
    integrity: IntegrityParams = field(default_factory=IntegrityParams)
    gating: GatingParams = field(default_factory=GatingParams)
    singularity: SingularityParams = field(default_factory=SingularityParams)
    clustering: ClusteringParams = field(default_factory=ClusteringParams)
    patterns: PatternSpecificParams = field(default_factory=PatternSpecificParams)
    
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

# Global Singleton instance
config = SystemConfig()
