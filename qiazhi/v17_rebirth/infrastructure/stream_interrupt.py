"""V17.14：流式 LLM 被 ActionQueue 截断。"""
from __future__ import annotations

from typing import Any, Dict


class ActionInterruptDuringStream(Exception):
    """SSE 已 aclose；payload 为队列事件 dict。"""

    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__("v17_stream_interrupted")
        self.payload = payload
