from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AccessRolePolicy:
    role_key: str
    label: str
    purpose: str
    allowed_runtime_fields: tuple[str, ...]
    blocked_runtime_fields: tuple[str, ...]
    default_locale: str = "zh"
    guardrails: tuple[str, ...] = (
        "ROLE_POLICY_IS_SERVER_SIDE",
        "NO_CROSS_USER_PRIVATE_DATA",
        "NO_SECRET_VALUES_RENDERED",
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
