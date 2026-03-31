"""L2 Conduction: basic clash loss model."""
from __future__ import annotations

from typing import Dict, Optional


def calculate_clash_loss(branch_a: str, branch_b: str, month_branch: Optional[str] = None) -> Dict[str, int]:
    """
    Return energy loss (%) for each branch in a clash pair.

    Rule (v1.2 initial):
    - 子午冲 uses asymmetric loss: seasonal winner loses less.
      - if 子得令: 子-30, 午-60
      - if 午得令: 子-60, 午-30
      - otherwise: 子-45, 午-45
    - other clashes default to symmetric -40/-40.
    """
    pair = {branch_a, branch_b}
    if pair != {"子", "午"}:
        return {branch_a: 40, branch_b: 40}

    if month_branch == "子":
        return {"子": 30, "午": 60}
    if month_branch == "午":
        return {"子": 60, "午": 30}
    return {"子": 45, "午": 45}

