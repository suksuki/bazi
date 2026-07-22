from __future__ import annotations

from dataclasses import dataclass
import os


@dataclass(frozen=True)
class DreamFeaturePolicy:
    enabled: bool = False
    allowed_user_ids: frozenset[str] = frozenset()
    policy_version: str = "dream-feature-policy.v1"

    @classmethod
    def from_environment(cls) -> "DreamFeaturePolicy":
        enabled = os.getenv("V50_DREAM_BRIDGE_V1_ENABLED", "0").strip().lower() in {
            "1",
            "true",
            "yes",
            "on",
        }
        allowed = frozenset(
            value.strip()
            for value in os.getenv("V50_DREAM_BRIDGE_V1_USER_IDS", "").split(",")
            if value.strip()
        )
        return cls(enabled=enabled, allowed_user_ids=allowed)

    def allows(self, user_id: str) -> bool:
        return self.enabled and (
            "*" in self.allowed_user_ids or user_id in self.allowed_user_ids
        )


__all__ = ["DreamFeaturePolicy"]
