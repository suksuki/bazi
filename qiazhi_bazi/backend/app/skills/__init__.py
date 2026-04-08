from __future__ import annotations

from typing import Any

from app.skills.base import AuditLog, BaseSkill

__all__ = [
    "BaseSkill",
    "AuditLog",
    "PhysicsInferenceSkill",
    "FinalVerdictSkill",
    "ClimateInferenceSkill",
    "seed_physics_defaults",
    "audit_spatial_sovereignty",
    "BlindSchoolEncyclopediaSkill",
    "build_blind_school_digest",
    "audit_host_guest_vectors",
]


def __getattr__(name: str) -> Any:
    if name == "FinalVerdictSkill":
        from app.skills.final_verdict import FinalVerdictSkill

        return FinalVerdictSkill
    if name in {"PhysicsInferenceSkill", "seed_physics_defaults"}:
        from app.skills.physics_engine import PhysicsInferenceSkill, seed_physics_defaults

        return {
            "PhysicsInferenceSkill": PhysicsInferenceSkill,
            "seed_physics_defaults": seed_physics_defaults,
        }[name]
    if name == "ClimateInferenceSkill":
        from app.skills.climate_inference import ClimateInferenceSkill

        return ClimateInferenceSkill
    if name == "audit_spatial_sovereignty":
        from app.skills.spatial_sovereignty import audit_spatial_sovereignty

        return audit_spatial_sovereignty
    if name in {"BlindSchoolEncyclopediaSkill", "build_blind_school_digest", "audit_host_guest_vectors"}:
        from app.skills.blind_school_encyclopedia import (
            BlindSchoolEncyclopediaSkill,
            audit_host_guest_vectors,
            build_blind_school_digest,
        )

        return {
            "BlindSchoolEncyclopediaSkill": BlindSchoolEncyclopediaSkill,
            "build_blind_school_digest": build_blind_school_digest,
            "audit_host_guest_vectors": audit_host_guest_vectors,
        }[name]
    raise AttributeError(name)
