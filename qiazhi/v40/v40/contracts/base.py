from __future__ import annotations

from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict


V40_CONTRACT_VERSION = "v40.contracts.v1"

RoleKey = Literal["guest", "user", "practitioner", "analyst", "admin", "lab"]
LocaleKey = Literal["zh", "en", "ko", "zh-CN", "en-US", "ko-KR", "zh-TW"]
ClientKey = Literal["web", "mobile", "desktop", "tablet", "admin", "lab"]


class V40Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Topic(str, Enum):
    OVERVIEW = "overview"
    CHART = "chart"
    STRUCTURE = "structure"
    USEFUL_GOD = "useful_god"
    TIMING = "timing"
    WEALTH = "wealth"
    CAREER = "career"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    FAMILY = "family"
    HIDDEN_ATTRIBUTE = "hidden_attribute"
    ADVICE = "advice"
    PROBE = "probe"
    LLM = "llm"
    SURFACE = "surface"
    UNKNOWN = "unknown"


class AssertionLevel(str, Enum):
    CONFIRMED = "confirmed"
    SUPPORTED = "supported"
    MIXED = "mixed"
    WEAK_CANDIDATE = "weak_candidate"
    BLOCKED = "blocked"


class Polarity(str, Enum):
    SUPPORT = "support"
    OPPOSE = "oppose"
    MIXED = "mixed"
    NEUTRAL = "neutral"


class EngineKey(str, Enum):
    BAZI = "bazi"
    ZIWEI = "ziwei"
    REALITY_PROBE = "reality_probe"
    CONVERSATION = "conversation"


class EngineMode(str, Enum):
    FACT_ONLY = "fact_only"
    SIGNAL_SIDECAR = "signal_sidecar"
    DECISION_AUX = "decision_aux"
    PROBE_TRIGGER = "probe_trigger"
    EXPRESSION_CONTEXT = "expression_context"


class SurfaceKey(str, Enum):
    READING = "reading"
    CALIBRATION = "calibration"
    CONVERSATION = "conversation"
    THINKING = "thinking"
    ADMIN = "admin"


class ReleaseRecommendation(str, Enum):
    APPROVE = "approve"
    NEEDS_REVIEW = "needs_review"
    REJECT = "reject"
    ROLLBACK = "rollback"
