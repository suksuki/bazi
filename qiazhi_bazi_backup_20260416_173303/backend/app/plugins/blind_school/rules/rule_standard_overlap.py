"""盲派对基础 L1 规则（伤官见官、枭神夺食等）的语义增益（规则溢价）。"""
from __future__ import annotations

from typing import Any, Dict, List


def _chips_from_core_interactions(jf: Dict[str, Any]) -> List[str]:
    raw = jf.get("l1_core_interactions")
    if not isinstance(raw, list) or not raw:
        return []
    lines: List[str] = []
    for it in raw:
        if not isinstance(it, dict) or not it.get("blind_rule_premium_eligible"):
            continue
        iid = str(it.get("id") or "")
        if iid == "SHANG_GUAN_JIAN_GUAN":
            lines.append("[MANGPAI_CHIP]: 伤官见官，禄神受损，因果权重额外增加 1.5x")
        elif iid == "XIAO_SHEN_DUO_SHI":
            lines.append("[MANGPAI_CHIP]: 枭神夺食，传道受阻，因果权重额外增加 1.5x")
        elif iid == "CAI_XING_PO_YIN":
            lines.append("[MANGPAI_CHIP]: 财星破印，文书之盾受损，因果权重额外增加 1.5x")
        elif iid == "YANG_REN_FENG_CHONG":
            lines.append("[MANGPAI_CHIP]: 羊刃逢冲，顶格耗散，因果权重额外增加 1.5x")
    return lines


def standard_overlap_chip_logs(*, physics_tensor: Dict[str, Any]) -> List[str]:
    """当基础物理层 L1 联结为 Surface 明面且允许溢价时追加盲派 chip（需 classical.blind_school.v1 已执行）。"""
    meta = physics_tensor.get("meta") if isinstance(physics_tensor, dict) else None
    jf = (meta or {}).get("l1_junction_flags") if isinstance(meta, dict) else None
    if not isinstance(jf, dict):
        return []

    lines = _chips_from_core_interactions(jf)
    if lines:
        return lines

    # 兼容旧快照：仅有扁平旗标、无 l1_core_interactions 时沿用原判定
    if jf.get("SHANG_GUAN_JIAN_GUAN") and str(jf.get("sgjg_severity") or "") != "MINOR_INTERFERENCE":
        return ["[MANGPAI_CHIP]: 伤官见官，禄神受损，因果权重额外增加 1.5x"]
    return []
