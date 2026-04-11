"""实验室全局 η 卡片占位：仅用于 Admin manifest 绑定 Skill，不参与 L1 原子流水线。"""
from __future__ import annotations

from typing import Any, Dict, List, Mapping, MutableMapping


def apply_op_lab_runtime_stub(
    *,
    physics_tensor: MutableMapping[str, Any],
    settings: Mapping[str, float],
) -> List[Dict[str, Any]]:
    del physics_tensor, settings
    return []
