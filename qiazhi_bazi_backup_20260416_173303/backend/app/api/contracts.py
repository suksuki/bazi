"""Shared API request/response contracts."""
from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional

UserIntentionId = Literal["seek_stability", "seek_wealth", "seek_fame"]

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
    SUB_BRANCH_SANHE_REQ_WANG_ZHI: Optional[float] = Field(
        default=None,
        description="≥0.5 时三合中神须落月或日支（见 sub_branch_condition_eval）",
    )
    SANHE_ALPHA_LEAKAGE: Optional[float] = Field(default=None, description="三合 Abs 增益泄漏比例 0..1")
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
    user_intention: Optional[UserIntentionId] = Field(
        default=None,
        description="V10 WILL_PROXY：用户意志锚点（稳健避险 / 激进求财 / 中道求名），驱动物理参数字典与 L2 亲和度乘子",
    )


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
    request_id: Optional[str] = Field(default=None, description="链路追踪 request_id")


class HotReloadPhysicsRequest(BaseModel):
    """V14：analyze-seed 后热重载物理栈（等价于携带新 physics_config 重跑 analyze_clash），并合并会话态 metadata。"""

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
    temporal_context: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = Field(default=None, description="链路追踪 request_id")
    metadata_carryover: Dict[str, Any] = Field(
        default_factory=dict,
        description="合并进响应 metadata：如 incremental_context_v14 / iterative_verdict_v14 / persistence_layer 等",
    )


class StructuralPreviewHint(BaseModel):
    """影子预览：不修改 physics_param、仅表达结构/插件/逻辑意志的预判语义（SSE 注入）。"""

    kind: str = Field(
        ...,
        description="L1_STRUCTURE | PLUGIN_ENABLE | LOGIC_OVERRIDE | SEMANTIC_VERDICT | PATTERN_SOVEREIGNTY",
    )
    card_id: str = Field(default="", description="来源 Inbox 卡片 id")
    label: str = Field(default="", description="人可读标签，如 巳酉丑金局 · AGGREGATED")
    plugin_id: str = Field(default="", description="PLUGIN_ENABLE 时的插件 id")
    override_key: str = Field(default="", description="LOGIC_OVERRIDE 时的参数键")
    baseline_pattern_kind: str = Field(
        default="",
        description="悬停前客户端快照的 pattern_kind，用于检测「已知格→混乱态」退化",
    )
    baseline_pattern_name_zh: str = Field(
        default="",
        description="悬停前客户端快照的 pattern_name_zh",
    )


class OrchestratorInternalLoopRequest(BaseModel):
    """无 LLM：仅跑 OrchestratorService.run_internal_loop（物理 + 插件 + VF + verdict_skeleton）。"""

    metadata: BaziMetadata
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None
    physics_config: Optional[PhysicsConfig] = None
    session_id: Optional[int] = None
    dayun: Optional[str] = None
    liunian: Optional[str] = None
    is_preview: bool = Field(
        default=False,
        description="影子预览：不落库、不写学习批注、不触发叙事终审；physics_update 带 is_preview 标识",
    )
    structural_preview: Optional[StructuralPreviewHint] = Field(
        default=None,
        description="结构预览：在 vf_discovered 中前置注入预判行，并在 complete 中附带 preview_pattern_alert",
    )


class AuditDiagnoseRequest(BaseModel):
    """逻辑检察院：跑 L1 原子流 + 插件，对照终判文本（可选）。"""

    pillars: FourPillars
    session_id: Optional[int] = None
    dayun: Optional[str] = None
    liunian: Optional[str] = None
    physics_config: Optional[PhysicsConfig] = None
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None
    temporal_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="与 analyze_clash 一致：流年/大运等干支上下文",
    )
    final_verdict_markdown: str = Field(
        default="",
        description="最近一次 Final Verdict 正文（markdown），用于叙事层缺失检测",
    )
    user_question: str = Field(default="", description="逻辑对质：简短追问，原型返回规则草稿")
    generate_report: bool = Field(default=False, description="为 True 时附带 audit_report_markdown")
    return_physics_tensor: bool = Field(default=False, description="为 True 时返回完整 physics_tensor（体积大）")


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
    request_id: Optional[str] = Field(default=None, description="链路追踪 request_id")


class StandardSeedRequest(AnalyzeSeedRequest):
    flow_state: Optional[str] = Field(
        default=None,
        description="V12.92：请求前端声明的流程状态；idle/synthesis 将被后端拒绝为 409",
    )
    seed_short: Optional[str] = Field(
        default=None,
        description="V12.92：标准种子短码（high_lock/marriage_clash/system_stress）",
    )
    user_feedback: Optional[str] = Field(
        default=None,
        description="V12.92：可选用户反馈，后端按 300 字节上限收敛",
    )


class AuditPhysicsWithLlmRequest(BaseModel):
    metadata: BaziMetadata
    physics_tensor: Optional[Dict[str, Any]] = None
    solar_term: Optional[str] = None
    lang: str = "ZH"
    consensus_history: List[Dict[str, Any]] = Field(default_factory=list)
    session_id: Optional[int] = None
    audit_prompt_tier: Optional[Literal["standard", "compact"]] = Field(
        default=None,
        description="审计提示词档位：compact 适合弱模型；省略则使用 runtime_config.llm.audit_prompt_tier",
    )
    will_conflict_duel_context: Optional[str] = Field(
        default=None,
        description="意志对垒：当前意志与系统基准张力（如 verdict_skeleton 风险段），供审计 LLM 专评",
    )


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


class RegenerationContext(BaseModel):
    """终判再生原因（写入 metadata.history_context.regeneration_events）。"""

    reason: str = Field(default="", max_length=480, description="人可读原因，如 η 微调后静默重算触发重写")
    trigger: str = Field(default="", max_length=64, description="manual_regenerate | physics_recalc | inbox_execute 等")
    previous_version_id: str = Field(default="", max_length=64, description="上一版终判 version_id")


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
    regeneration_context: Optional[RegenerationContext] = None
    mandatory_final_synthesis: bool = Field(
        default=False,
        description="为 True 时在 user 提示中强制注入「终审官」语义整合块（四柱/冲突点/已归档断语），不因 conflict_list 为空而跳过终判 LLM",
    )
    iterative_verdict_round: int = Field(
        0,
        ge=0,
        le=3,
        description="V14 迭代终判：0=关闭；1=结构定性 2=因果分析 3=行动指令（行/禁）。非 0 时优先于 metadata.iterative_verdict_v14.round",
    )


class AssertionFrameBacktraceRequest(BaseModel):
    """V14 帧回溯：从 metadata 中读取断言演化帧。"""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    max_items: int = Field(default=80, ge=1, le=240)


class RealtimeNarratorRequest(BaseModel):
    """V14 异步润色：实时短句，不等待全量 Final Verdict。"""

    metadata: Dict[str, Any] = Field(default_factory=dict)
    physics_tensor: Dict[str, Any] = Field(default_factory=dict)
    lang: str = "ZH"
    max_chars: int = Field(default=220, ge=60, le=600)


class ResolveConflictRequest(BaseModel):
    """裁决人意志指纹：冲突处理选择写入 decision_audit_logs（进化训练集）。"""

    consultation_id: Optional[int] = None
    skill_id: str = Field(..., min_length=1)
    abs_delta: float = 0.0
    processing_preference: str = Field(default="", max_length=120)
    extra: Dict[str, Any] = Field(default_factory=dict)


class InterruptResolveRequest(BaseModel):
    """M3：逻辑断点处理（确认/解决）。"""

    consultation_id: Optional[int] = None
    interrupt_id: str = Field(..., min_length=1)
    action: Literal["acknowledge", "resolve"] = "resolve"
    notes: str = ""
    actor: str = "arbiter"


class InterruptResumeRequest(BaseModel):
    """M3：从 pending 挂起态恢复执行。"""

    consultation_id: Optional[int] = None
    interrupt_id: str = Field(..., min_length=1)
    resume_token: str = Field(..., min_length=1)
    actor: str = "arbiter"


class ResumeCalculationRequest(BaseModel):
    """V12：事务化 Resume（先持久化反馈，再从中断点局部重算）。"""

    session_id: int = Field(..., ge=1)
    user_feedback: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None
    physics_config: Optional[PhysicsConfig] = None
    dayun: Optional[str] = None
    liunian: Optional[str] = None


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
    base_url: Optional[str] = Field(default=None, description="可覆盖 LLM OpenAI 兼容根地址（通常含 /v1）")
    api_key: Optional[str] = Field(default=None, description="可覆盖 API Key")
    model: Optional[str] = Field(default=None, description="可覆盖模型名")
    fast_path: bool = Field(
        default=True,
        description="为 True 时只做一次主模型调用，跳过二次 LLM 重写/压缩，仅本地 strip 与 hard_compact；与基础设施页默认「弱模型兼容」一致。显式传 False 时，长回答会再走一次压缩用 LLM。",
    )
    ollama_options: Optional[Dict[str, Any]] = Field(
        default=None,
        description="并入 Ollama /api/chat 的 options（如 num_ctx、num_batch）；与 QIAZHI_OLLAMA_OPTIONS_JSON、runtime llm.ollama_options 合并，本字段同名键优先。",
    )


class DbStatusRequest(BaseModel):
    db_url: Optional[str] = Field(default=None, description="可覆盖数据库连接串")


class LlmModelsRequest(BaseModel):
    base_url: str = Field(..., description="LLM OpenAI 兼容地址")
    api_key: Optional[str] = Field(default=None, description="可选 API Key")


class RuntimeConfigRequest(BaseModel):
    llm: Dict[str, Any] = Field(
        default_factory=dict,
        description=(
            "LLM 连接与行为开关：base_url、model、provider、audit_prompt_tier、"
            "is_high_reasoning_mode（bool，开启时终判 Prompt 中插件 evidence 不做碎片化截断）、"
            "ollama_options（object，并入 Ollama /api/chat 的 options，如 num_ctx）等"
        ),
    )
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


class ArbitrationOverruleRequest(BaseModel):
    """V12.95：一票否决——按 audit_id 撤销静默 LAW 并恢复追问中断。"""

    audit_id: str = Field(..., min_length=3, max_length=128)
    consultation_id: Optional[int] = Field(default=None, description=">0 时追加 arbitration_logs（M5 统计）")
    assertion_tree: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    arbitration_audit_feed: List[Dict[str, Any]] = Field(default_factory=list)
    physics_meta: Optional[Dict[str, Any]] = Field(default=None, description="缺省时按空 dict 处理 physics_tensor.meta 补丁")
