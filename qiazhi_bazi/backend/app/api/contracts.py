"""Shared API request/response contracts."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Literal

from pydantic import BaseModel, Field

from app.schemas.bazi_metadata import BaziMetadata, FourPillars


class BlindSchoolFeatureFlags(BaseModel):
    """盲派子开关：可由前端 Plugin 面板传入。"""

    enable_pierce_harm: bool = True
    enable_tomb_vault: bool = True
    enable_host_guest_bonus: bool = True


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


class AnalyzeSeedRequest(BaseModel):
    date: str
    time: str = "12:00"
    calendar: str = "solar"
    gender: Literal["male", "female"]
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    lang: str = "ZH"
    session_id: Optional[int] = None
    physics_config: Optional[PhysicsConfig] = None
    enabled_plugins: List[str] = Field(default_factory=list)
    blind_school_features: Optional[BlindSchoolFeatureFlags] = None


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


class ApplyPhysicsSqlRequest(BaseModel):
    sql_patch: str = Field(..., description="仅允许更新 physics_interaction_params 的单条 UPDATE")
    auto_refresh: bool = Field(default=True, description="执行后是否自动 refresh physics cache")
