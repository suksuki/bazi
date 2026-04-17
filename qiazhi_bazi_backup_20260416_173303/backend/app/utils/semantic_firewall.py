"""跨阶段语义防火墙：剔除提示词中的浮点字面量，避免弱模型「现场做算术」。"""
from __future__ import annotations

import re

_FLOAT_LITERAL = re.compile(r"\d+\.\d+(?:[eE][+-]?\d+)?")


def strip_float_literals(text: str) -> str:
    """剔除科学计数与普通小数；保留整数与干支等非数字 token。"""
    t = _FLOAT_LITERAL.sub("·", str(text or ""))
    while "··" in t:
        t = t.replace("··", "·")
    return t
