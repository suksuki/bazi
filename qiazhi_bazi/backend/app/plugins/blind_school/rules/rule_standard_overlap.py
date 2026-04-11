"""盲派对基础 L1 规则（如伤官见官）的语义增益（规则溢价）。"""
from __future__ import annotations

from typing import Any, Dict, List


def standard_overlap_chip_logs(*, physics_tensor: Dict[str, Any]) -> List[str]:
    """当基础物理层标记伤官见官时追加盲派 chip（需 classical.blind_school.v1 已执行）。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor, dict) else None
    jf = (meta or {}).get("l1_junction_flags") if isinstance(meta, dict) else None
    if not isinstance(jf, dict):
        return []
    if not jf.get("SHANG_GUAN_JIAN_GUAN"):
        return []
    # 藏干余气级（不见）不触发盲派剧烈溢价
    if str(jf.get("sgjg_severity") or "") == "MINOR_INTERFERENCE":
        return []
    return ["[MANGPAI_CHIP]: 伤官见官，禄神受损，因果权重额外增加 1.5x"]
