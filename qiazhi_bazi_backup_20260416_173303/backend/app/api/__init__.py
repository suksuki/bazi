from __future__ import annotations

from typing import Any

__all__ = ["router"]


def __getattr__(name: str) -> Any:
    if name == "router":
        from app.api.router import router

        return router
    raise AttributeError(name)
