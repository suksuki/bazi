"""Consultation + DecisionStep：存过程，不单存结果。"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.types import JSON
from sqlmodel import Field, SQLModel

# SQLite 用 JSON；PostgreSQL 可用 JSONB
_JSON_TYPE = JSON().with_variant(JSONB(), "postgresql")


class Consultation(SQLModel, table=True):
    """单次测算主记录。"""

    __tablename__ = "consultation"

    id: Optional[int] = Field(default=None, primary_key=True)
    subject_ref: Optional[str] = Field(default=None, index=True)
    # 公历/真太阳时等由前端传入，MVP 用 JSON 存原始输入
    input_meta: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(_JSON_TYPE))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionStep(SQLModel, table=True):
    """推演链上的一步：类型 + 当时物理快照 + 人裁决。"""

    __tablename__ = "decision_step"

    id: Optional[int] = Field(default=None, primary_key=True)
    consultation_id: int = Field(foreign_key="consultation.id", index=True)
    step_type: str = Field(
        index=True,
        description="如：旺衰判定、墓库确认、刑冲扫描",
    )
    raw_data: Dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(_JSON_TYPE),
        description="该步当时的物理指标/中间态",
    )
    human_choice: Optional[Dict[str, Any]] = Field(
        default=None,
        sa_column=Column(_JSON_TYPE),
        description="裁决人打钩/选项结果",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicsPositionWeight(SQLModel, table=True):
    """四柱位置权重（年/月/日/时）。"""

    __tablename__ = "physics_position_weights"

    pillar_type: str = Field(primary_key=True)
    weight: float = Field(default=0.25)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicsSeasonalMatrix(SQLModel, table=True):
    """节气对五行修正系数。"""

    __tablename__ = "physics_seasonal_matrix"

    solar_term: str = Field(primary_key=True)
    element_wood: float = Field(default=1.0)
    element_fire: float = Field(default=1.0)
    element_earth: float = Field(default=1.0)
    element_metal: float = Field(default=1.0)
    element_water: float = Field(default=1.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicsInteractionParam(SQLModel, table=True):
    """交互衰减/激发等超参数。"""

    __tablename__ = "physics_interaction_params"

    param_key: str = Field(primary_key=True)
    param_value: float = Field(default=1.0)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DecisionAuditLog(SQLModel, table=True):
    """裁决意志与进化训练集：记录冲突处理指纹等。"""

    __tablename__ = "decision_audit_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    consultation_id: Optional[int] = Field(default=None, index=True)
    record_type: str = Field(
        index=True,
        description="如 evolution_training_set、manual_audit",
    )
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(_JSON_TYPE))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class SessionConsensus(SQLModel, table=True):
    """Session 级共识追踪：记录裁决人已确认的原子决策。"""

    __tablename__ = "session_consensus"

    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(index=True)
    decision_key: str = Field(index=True)
    confirmed_value: Optional[float] = Field(default=None)
    reasoning: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PhysicsSettingsRegistry(SQLModel, table=True):
    """物理键全局基准：DB 持久化层（API 单次请求覆盖优先级更高）。"""

    __tablename__ = "physics_settings_registry"

    key: str = Field(primary_key=True, max_length=128)
    value: float = Field(default=0.0, description="当前生效的全局基准值")
    default_value: float = Field(default=0.0, description="与代码 DEFAULT 同步的出厂默认")
    category: str = Field(default="base.physics", max_length=256, index=True, description="归口插件 ID")
    description: str = Field(default="", description="参数物理意义")


class CausalManifestMeta(SQLModel, table=True):
    """Skill manifest 片段（如 operator_to_skill），支持零代码覆盖。"""

    __tablename__ = "causal_manifest_meta"

    scope: str = Field(primary_key=True, max_length=128)
    payload: Dict[str, Any] = Field(default_factory=dict, sa_column=Column(_JSON_TYPE))


class CausalSkill(SQLModel, table=True):
    """因果 Skill 定义（可由 DB 覆盖磁盘 skill_manifest）。"""

    __tablename__ = "causal_skills"

    skill_id: str = Field(primary_key=True, max_length=128)
    scope: str = Field(default="base_physics", max_length=64, index=True)
    name: str = Field(default="", max_length=512)
    description: str = Field(default="")
    impact_factor: str = Field(default="", max_length=256)
    physics_weight: Optional[float] = Field(default=None)
    physics_setting_key: Optional[str] = Field(default=None, max_length=128)
    assertion_template: str = Field(default="")
    description_tags: List[Any] = Field(default_factory=list, sa_column=Column(_JSON_TYPE))


class L0ElementRegistry(SQLModel, table=True):
    """L0：天干/地支 → 阴阳、五行（可 DB 覆盖，缺行则回退代码常量）。"""

    __tablename__ = "l0_element_registry"

    glyph: str = Field(primary_key=True, max_length=8)
    kind: str = Field(max_length=16, index=True, description="stem | branch")
    element: str = Field(max_length=32, description="wood/fire/earth/metal/water")
    polarity: Optional[str] = Field(default=None, max_length=16, description="yang | yin，支可为空")


class L0BranchHiddenSchema(SQLModel, table=True):
    """L0：地支藏干比例（本/中/余 + 百分比）。"""

    __tablename__ = "l0_branch_hidden_schema"

    branch: str = Field(primary_key=True, max_length=8)
    hidden_stem: str = Field(primary_key=True, max_length=8)
    ratio_pct: float = Field(ge=0.0, description="0..100")
    tier: str = Field(default="main", max_length=16, description="main | middle | residual")


class L0ResonanceRules(SQLModel, table=True):
    """L0：透干通根等加权系数（与 `get_root_resonance` 对齐）。"""

    __tablename__ = "l0_resonance_rules"

    rule_key: str = Field(primary_key=True, max_length=128)
    coefficient: float = Field(default=1.0)
    description: str = Field(default="", max_length=2000)
