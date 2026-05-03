from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class TestCommand:
    name: str
    argv: tuple[str, ...]
    purpose: str
    opt_in_env: str = ""
    command_timeout_seconds: float | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TestTier:
    name: str
    purpose: str
    budget_seconds: int
    default_for: tuple[str, ...]
    commands: tuple[TestCommand, ...]
    guardrails: tuple[str, ...] = field(
        default_factory=lambda: (
            "TEST_TIER_IS_EXPLICIT",
            "SLOW_TESTS_REQUIRE_OPT_IN",
            "NO_NETWORK_BY_DEFAULT",
        )
    )

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["commands"] = [row.to_dict() for row in self.commands]
        return payload
