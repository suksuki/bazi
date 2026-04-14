"""Qiazhi-Inference-v1: 专家种子库（静态映射）。"""

from __future__ import annotations

KNOWLEDGE_SEEDS = {
    "harm:寅巳": {
        "aspect": "MARRIAGE_STABILITY",
        "weight": 0.85,
        "probe_query": "探测到年日寅巳穿害，此结构常指向配偶宫震荡，是否已有现实波动或需针对性止损？",
    },
    "clash:子午": {
        "aspect": "SYSTEM_STRESS",
        "weight": 0.9,
        "probe_query": "子午双包形成强对冲，系统负载极高，需确认核心能量输出点。",
    },
    "stagnation:high_lock_no_output": {
        "aspect": "EXCESSIVE_STAGNATION",
        "weight": 0.88,
        "probe_query": "由于能量高度聚集而无处宣泄，是否感到极大的精神内耗或怀才不遇？",
    },
}

SOVEREIGNTY_WEIGHTS = {
    "confirmed_fact": 1.0,
}

SEED_SHORT_CODE_MAP = {
    "harm:寅巳": "marriage_clash",
    "clash:子午": "system_stress",
    "stagnation:high_lock_no_output": "high_lock",
}


def seed_short_code(seed_key: str) -> str:
    return str(SEED_SHORT_CODE_MAP.get(str(seed_key or "").strip(), "unknown_seed"))


__all__ = ["KNOWLEDGE_SEEDS", "SOVEREIGNTY_WEIGHTS", "SEED_SHORT_CODE_MAP", "seed_short_code"]
