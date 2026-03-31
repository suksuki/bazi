"""Qiazhi-Bazi 核心协议：BaziMetadata。"""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Locale(str, Enum):
    ZH = "zh"
    EN = "en"
    KO = "ko"


class BasicInfo(BaseModel):
    pillars: Dict[str, str] = Field(
        default_factory=dict,
        description="干支四柱，例如 {'year':'甲子','month':'乙丑','day':'丙寅','hour':'丁卯'}",
    )
    gender: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None


class EnergyProfile(BaseModel):
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="五行相对强弱标签，例如 {'wood':'strong','fire':'weak'}",
    )
    raw_scores: Dict[str, float] = Field(
        default_factory=dict,
        description="可选原始分数（保留追溯），用于标签校验",
    )


class SemanticFeature(BaseModel):
    code: str
    title: str
    narrative: str
    score: Optional[float] = None
    level: str = "unspecified"
    meta: Dict[str, Any] = Field(default_factory=dict)


class BaziMetadata(BaseModel):
    model_config = {"extra": "forbid"}

    schema_version: str = "1.0.0"
    locale: Locale = Locale.ZH
    basic_info: BasicInfo
    energy_profile: EnergyProfile
    clash_combinations: List[str] = Field(default_factory=list)

    # 兼容现有实验端点
    features: List[SemanticFeature] = Field(default_factory=list)
    semantic_refs: List[str] = Field(default_factory=list)
    engine_trace: Dict[str, Any] = Field(default_factory=dict)
