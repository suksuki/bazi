"""推演状态机占位：后续接旺衰、墓库、岁运等步骤。"""
from __future__ import annotations

from enum import Enum


class WorkflowPhase(str, Enum):
    IDLE = "idle"
    INPUT = "input"
    SCAN = "scan"
    RESOLVE = "resolve"
    DONE = "done"


def next_phase(current: WorkflowPhase, event: str) -> WorkflowPhase:
    """极简占位：事件驱动切换。"""
    _ = event
    return current
