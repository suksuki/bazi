"""Split balance-school and blind-work verdicts from same physics base."""
from __future__ import annotations

from typing import Dict


def split_balance_and_work_verdict(*, self_abs: float, work_net: float, net_effect: str) -> Dict[str, str]:
    # 旺衰维度：只关心“强弱平衡”。
    if self_abs < 0.8:
        balance_verdict = "身弱偏虚，宜扶助与稳根。"
    elif self_abs <= 5.0:
        balance_verdict = "身势中和，宜维持平衡与节律。"
    elif self_abs <= 10.0:
        balance_verdict = "身强偏旺，宜泄耗降压。"
    else:
        balance_verdict = "身强极旺，急需泄耗与导流。"

    # 盲派维度：只关心“做功效率”。
    if work_net > 1.0 and net_effect == "gain":
        work_verdict = "做功通畅，资源转化效率较高。"
    elif work_net > 0 and net_effect in {"gain", "neutral"}:
        work_verdict = "做功偏弱，存在收益但效率一般。"
    elif abs(work_net) <= 0.3:
        work_verdict = "有能无功，路径受阻，偏向内耗。"
    else:
        work_verdict = "做功反噬明显，需先止损再求进。"

    return {
        "balance_verdict": balance_verdict,
        "work_verdict": work_verdict,
    }

