"""Human-readable classical nomenclature mapping for structure decisions."""
from __future__ import annotations

from typing import Any, Dict


def map_structure_nomenclature(
    *,
    code_name: str,
    self_abs: float,
    deity_axes: Dict[str, Any] | None = None,
    work_net: float = 0.0,
    month_deity: str | None = None,
    heterogeneous_abs: float = 0.0,
) -> Dict[str, str]:
    code = str(code_name or "REGULAR_STRUCTURE")
    if code == "STRONG_STRUCTURE":
        # Heterogeneous interference guardrail:
        # if异类(财官食伤)绝对能量显著，禁止贴“专旺”标签。
        if self_abs > 20 and heterogeneous_abs <= 1.0 and work_net >= 1.0:
            return {"humanized": "从旺/专旺格", "status": "物理极端态，宜顺不宜逆"}
        if self_abs > 15 and month_deity == "比肩":
            return {"humanized": "建禄格（气盈格）", "status": "能量极度过剩，必须见财官导流"}
        if self_abs > 15 and month_deity == "劫财":
            return {"humanized": "月劫格（争夺态）", "status": "能量攻击性强，急需食伤泄秀"}
        if self_abs > 5 and work_net < 1.0:
            return {"humanized": "身强无依格", "status": "有能无功，能量空转，内耗风险高"}
        if self_abs > 8:
            return {"humanized": "建禄/专旺倾向格", "status": "身强待泄，宜导出做功"}
        return {"humanized": "身强正格（待舒发）", "status": "可用但需防内耗"}
    if code == "FOLLOW_WEALTH_POWER":
        return {"humanized": "从财官势格", "status": "顺势取财，忌逆势强扶"}
    return {"humanized": "中和常规格", "status": "平衡运行，按做功微调"}
