from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any


@dataclass
class V17DbBridge:
    """Connection capability only; no business logic."""

    database_url: str | None = None

    def resolve_url(self) -> str:
        return self.database_url or os.getenv("QIAZHI_DATABASE_URL", "sqlite:///qiazhi_v17.db")

    def tagged_record(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = dict(payload or {})
        row["origin"] = "v17_origin"
        return row
