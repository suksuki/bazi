from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict


class V50Model(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class CalendarType(str, Enum):
    SOLAR = "solar"
    LUNAR = "lunar"
    UNKNOWN = "unknown"


class SourceEngine(str, Enum):
    BAZI = "bazi"
    ZIWEI = "ziwei"
    KNOWLEDGE = "knowledge"
    BRAIN = "brain"
    USER_REPLY = "user_reply"


class Topic(str, Enum):
    OVERVIEW = "overview"
    STRUCTURE = "structure"
    GENERAL = "general"
    CAREER = "career"
    WEALTH = "wealth"
    RELATIONSHIP = "relationship"
    HEALTH = "health"
    FAMILY = "family"
    TIMING = "timing"
    MIGRATION = "migration"
    SELF = "self"
    TALENT_LEARNING = "talent_learning"
    CHILDREN_LEGACY = "children_legacy"
    SOCIAL_NETWORK = "social_network"
    HEALTH_VITALITY = "health_vitality"
    MIGRATION_ENVIRONMENT = "migration_environment"
    LIFE_TIMING = "life_timing"
    PORTRAIT = "portrait"
    UNKNOWN = "unknown"


class ValidationStatus(str, Enum):
    UNVALIDATED = "unvalidated"
    SYNTHETIC_VALIDATED = "synthetic_validated"
    GOLDEN_VALIDATED = "golden_validated"
    REJECTED = "rejected"


def require_non_empty(value: str, field_name: str) -> str:
    if not value.strip():
        raise ValueError(f"{field_name} is required")
    return value


def require_refs(values: list[str], field_name: str) -> list[str]:
    if not values:
        raise ValueError(f"{field_name} requires at least one reference")
    if any(not str(value).strip() for value in values):
        raise ValueError(f"{field_name} contains empty reference")
    return values
