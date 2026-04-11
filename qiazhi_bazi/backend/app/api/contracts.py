"""Shared API request/response contracts."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from app.schemas.bazi_metadata import BaziMetadata, FourPillars


class BlindSchoolFeatureFlags(BaseModel):
    """盲派子开关：可由前端 Plugin 面板传入。"""

    enable_pierce_harm: bool = True
    enable_tomb_vault: bool = True
    enable_host_guest_bonus: bool = True
    enable_standard_overlap: bool = True


class PhysicsConfig(BaseModel):
    WEIGHT_LUCK: Optional[float] = None
    WEIGHT_YEAR: Optional[float] = None
    BASE_BACKFIRE_RISK: Optional[float] = None
    HIGH_IMBALANCE_RISK: Optional[float] = None
    TOMB_LOCK_RATE: Optional[float] = None
    CLIMATE_INTENSITY: Optional[float] = None
    STEM_RESONANCE_BOOST: Optional[float] = None
    TRANSFER_DISTANCE_DECAY: Optional[float] = None
    WORK_MIN_THRESHOLD: Optional[float] = None
    SHOW_WEAK_WORK_PATHS: Optional[float] = None
    L1_OP_PROD_ETA: Optional[float] = Field(default=None, description="相生效率 η（L1_OP_PROD）")
    L1_OP_DEST_ETA: Optional[float] = Field(default=None, description="相克损耗 η（L1_OP_DEST）")
    L1_OP_CONN_ETA: Optional[float] = Field(default=None, description="合化能量系数 η（L1_OP_CONN）")
    INTERDIMENSIONAL_CONDUCTIVITY: Optional[float] = Field(
        default=None,
        description="跨柱干支传导灵敏度（0..2 映射至 blend 权重，默认 0）",
    )
    INTERDIMENSIONAL_BARRIER_STRENGTH: Optional[float] = None
    CONDUCTIVITY_DECAY_RATE: Optional[float] = None
    GHOST_ENERGY_DAMPING: Optional[float] = None
    MANGPAI_ETA_DIMENSIONAL_CRUSH: Optional[float] = None
    MANGPAI_ROOT_RESONANCE: Optional[float] = None
    INTERDIMENSIONAL_SHIELD_ENABLE: Optional[float] = Field(default=None, description="1=启用维度屏蔽，0=关闭")
    STEM_BRANCH_ROOT_RESONANCE_ENABLE: Optional[float] = Field(default=None, description="1=启用通根谐振")
    STEM_BRANCH_VERTICAL_CRUSH_ENABLE: Optional[float] = Field(default=None, description="1=启用盖头截脚损耗")
    user_target_direction: Optional[str] = Field(
        default=None,
        description="用户环境方位：东/南/西/北/中；空或未知则不应用地理算子",
    )
    WS_PIVOT_SELF_WEAK_THRESHOLD: Optional[float] = Field(
        default=None,
        description="旺衰枢纽：self_abs 低于该阈值时用神池偏向印比（physics_settings）",
    )
    PATTERN_CONG_DOMINANCE: Optional[float] = Field(
        default=None,
        description="从格能量集中度阈值（physics_settings）",
    )
    FLOW_AUDITOR_ABS_THRESHOLD: Optional[float] = Field(
        default=None,
        description="五行流通审计相邻段 Abs 阈值（physics_settings）",
    )
    L1_SUB_BRANCH_OP_ENABLE: Optional[float] = None
    SUB_BRANCH_BANHE_PHI: Optional[float] = None
    SUB_BRANCH_BANHE_ABS_BOOST: Optional[float] = None
    SUB_BRANCH_BANHE_VECTOR_BOOST: Optional[float] = None
    SUB_BRANCH_SANHE_ABS_BOOST: Optional[float] = None
    SUB_BRANCH_LIUHE_ABS_BOOST: Optional[float] = None
    SUB_BRANCH_SANXING_ABS_DAMP: Optional[float] = None
    SUB_BRANCH_LIUCHONG_ABS_DAMP: Optional[float] = None
    SUB_BRANCH_LIUHAI_ABS_DAMP: Optional[float] = None
    SUB_BRANCH_LIUPO_ABS_DAMP: Optional[float] = None
    SUB_BRANCH_LIUHAI_ENABLE: Optional[float] = None
    SUB_BRANCH_LIUPO_ENABLE: Optional[float] = None
    L1_STEM_FUSION_ENABLE: Optional[float] = None
    STEM_FUSION_VECTOR_LEAK_RATIO: Optional[float] = None
    STEM_FUSION_BRANCH_SUPPORT_RATIO: Optional[float] = None
    L0_HIDDEN_ENERGY_SCALE: Optional[float] = Field(default=None, description="L0 藏干支能量总标度")
    L0_ROOT_BOOST_FACTOR: Optional[float] = Field(default=None, description="L0 通根反哺乘子")
    L0_YM_DH_WEIGHT_RATIO: Optional[float] = Field(default=None, description="L0 年月相对日时柱位权重比")


class ConsultationCreate(BaseModel):
    subject_ref: Optional[str] = None
    input_meta: Dict[str, Any] = Field(default_factory=dict)


class DecisionStepCreate(BaseModel):
    consultation_id: int
    step_type: str
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    human_choice: Optional[Dict[str, Any]] = None


class DecisionRollbackRequest(BaseModel):
    target_step_id: int
    reason: Optional[str] = None


class ConfirmStructureRequest(BaseModel):
    consultation_id: int
    structure_name: str
    confidence: Optional[float] = None
    evidence: Optional[str] = None


class ChatRequest(BaseModel):
    messages: List[Dict[str, str]]
    temperature: float = 0.4
    max_tokens: int = 2048
    lang: str = "ZH"


class AnalyzeClashRequest(BaseModel):
    pillars: FourPillars
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"
    session_id: Optional[int] = None
    dayun: Optional[str] = None
    liunian: Optional[str] = None
    physics_config: Optional[PhysicsConfig] = None
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None
    temporal_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Chronos V2：流年/大运干支上下文（引动审计）",
    )


class AnalyzeSeedRequest(BaseModel):
    date: str
    time: str = "12:00"
    calendar: str = "solar"
    gender: Literal["male", "female"]
    """用于大运/流年：公历参考年；不传则用服务器当前年。"""
    reference_year: Optional[int] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"
    session_id: Optional[int] = None
    physics_config: Optional[PhysicsConfig] = None
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None
    external_overrides: Optional[Dict[str, Any]] = Field(
        default=None,
        description="模拟时空：干支字符串键 liunian_ganzhi/dayun_ganzhi（如丙午），写入 temporal_context",
    )


class AuditPhysicsWithLlmRequest(BaseModel):
    metadata: BaziMetadata
    physics_tensor: Optional[Dict[str, Any]] = None
    solar_term: Optional[str] = None
    lang: str = "ZH"
    consensus_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[int] = None


class AuditLlmStructuredResponse(BaseModel):
    diagnosis: str = ""
    alignment_score: float = 0.0
    top_anomaly: str = ""
    causal_reasoning: str = ""
    tuning_suggestions: List[str] = Field(default_factory=list)
    sql_patch: str = ""
    refresh_hint: str = ""
    logic_proposal: Dict[str, Any] = Field(default_factory=dict)


class TranslateRequest(BaseModel):
    texts: List[str]
    target_lang: str = "ZH"


class FinalVerdictRequest(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    physics_tensor: Dict[str, Any] = Field(default_factory=dict)
    selected_cards: List[Dict[str, Any]] = Field(default_factory=list)
    consensus_history: List[Dict[str, Any]] = Field(default_factory=list)
    previous_verdict: str = ""
    previous_logical_evidence: List[str] = Field(default_factory=list)
    consultation_id: Optional[int] = None
    lang: str = "ZH"
    clear_previous_verdict: bool = False
    force_clear_cache: bool = False
    enabled_plugins: List[str] = Field(default_factory=list)
    plugin_weights: Dict[str, float] = Field(default_factory=dict)


class ResolveConflictRequest(BaseModel):
    """裁决人意志指纹：冲突处理选择写入 decision_audit_logs（进化训练集）。"""

    consultation_id: Optional[int] = None
    skill_id: str = Field(..., min_length=1)
    abs_delta: float = 0.0
    processing_preference: str = Field(default="", max_length=120)
    extra: Dict[str, Any] = Field(default_factory=dict)


class EvolutionAdmissionRequest(BaseModel):
    admit_evolved_to_mainnet: bool


class EvolutionBatchRunRequest(BaseModel):
    """静默批次：随机种子数（服务端上限防阻塞）。"""

    n_seeds: int = Field(default=20, ge=1, le=120)


class SkillFeedbackRequest(BaseModel):
    """裁决人对单条断言的语义反馈，关联 Skill ID 供进化适应度使用。"""

    skill_id: str = Field(..., min_length=1, description="盲派 / L1 skill_manifest 中的 id")
    line_index: int = Field(ge=0, description="断言在 verdict 文本中的行下标")
    rating: Literal["precise", "drift"] = Field(..., description="精准 / 偏移")
    line_preview: str = Field(default="", max_length=400, description="断言片段摘要")
    session_hint: str = Field(default="", max_length=200, description="可选：咨询 id / 前端会话标识")


class StressTestRequest(BaseModel):
    metadata: Dict[str, Any] = Field(default_factory=dict)
    gender: Literal["male", "female"]
    physics_config: Optional[PhysicsConfig] = None
    baseline_structure_final_decision: Dict[str, Any] = Field(default_factory=dict)
    luck_pillar: Optional[str] = None
    year_pillar: Optional[str] = None
    lang: str = "ZH"
    enabled_plugins: List[str] = Field(default_factory=list)


class LlmTestRequest(BaseModel):
    system_prompt: str = Field(default="你是严谨的命理分析助手。")
    user_prompt: str = Field(default="请用中文简要说明‘寅申冲’的核心矛盾。")
    language: str = Field(default="ZH", description="ZH/EN/KO")
    temperature: float = 0.3
    max_tokens: int = 256
    base_url: Optional[str] = Field(default=None, description="可覆盖 LLM 地址，如 http://192.168.0.10:8000/v1")
    api_key: Optional[str] = Field(default=None, description="可覆盖 API Key")
    model: Optional[str] = Field(default=None, description="可覆盖模型名")


class DbStatusRequest(BaseModel):
    db_url: Optional[str] = Field(default=None, description="可覆盖数据库连接串")


class LlmModelsRequest(BaseModel):
    base_url: str = Field(..., description="LLM OpenAI 兼容地址")
    api_key: Optional[str] = Field(default=None, description="可选 API Key")


class RuntimeConfigRequest(BaseModel):
    llm: Dict[str, Any] = Field(default_factory=dict)
    causal_routing: Optional[Dict[str, Any]] = Field(default=None, description="因果路由：策略、主权、权比等")


class ApplyPhysicsSqlRequest(BaseModel):
    sql_patch: str = Field(..., description="仅允许更新 physics_interaction_params 的单条 UPDATE")
    auto_refresh: bool = Field(default=True, description="执行后是否自动 refresh physics cache")


class PhysicsSettingPersistItem(BaseModel):
    key: str = Field(..., min_length=1, max_length=128)
    value: float


class PhysicsSettingsPersistRequest(BaseModel):
    """写入 `physics_settings_registry`，作为全局 DB 基准（单次请求 API 覆盖仍优先）。"""

    items: List[PhysicsSettingPersistItem] = Field(default_factory=list)
