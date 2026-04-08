from __future__ import annotations

from typing import Any

from app.skills.base import AuditLog, BaseSkill

__all__ = ["BaseSkill", "AuditLog", "PhysicsInferenceSkill", "FinalVerdictSkill", "seed_physics_defaults"]


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
    raise AttributeError(name)
