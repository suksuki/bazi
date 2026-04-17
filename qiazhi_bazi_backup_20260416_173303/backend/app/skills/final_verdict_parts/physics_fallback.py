"""终判 LLM 空响应/异常时：用 sys.core.physics 插件行生成可解析的最小 JSON 兜底。"""
from __future__ import annotations

import json
from typing import Any, Dict, List


def build_minimal_verdict_json_from_core_physics(physics_tensor: Dict[str, Any], *, lang: str) -> str:
    po = physics_tensor.get("plugin_outputs") if isinstance(physics_tensor.get("plugin_outputs"), dict) else {}
    row = po.get("sys.core.physics") if isinstance(po.get("sys.core.physics"), dict) else {}
    verdict = str(row.get("verdict") or "").strip()
    inner = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    if not verdict:
        verdict = str(inner.get("verdict") or "").strip()
    evid: List[str] = []
    raw_ev = row.get("evidence") if isinstance(row.get("evidence"), list) else []
    for x in raw_ev[:12]:
        s = str(x).strip()
        if s:
            evid.append(s[:220])
    if not verdict and evid:
        verdict = "；".join(evid[:3])
    if not verdict:
        verdict = "盘局物理层已收敛；干支张力与芯片证据链已登记，可就气机枢轴作子平式整编。"
    zh = (lang or "ZH").upper() == "ZH"
    if zh:
        cons = (
            "\n".join(f"- {e}" for e in evid)
            if evid
            else "据 `sys.core.physics` 已登记之结论与芯片证据链，与四柱气机相互参证。"
        )
        body_md = (
            "### 核心气象\n"
            + verdict[:900]
            + "\n\n### 裁决共识\n"
            + cons
            + "\n\n### 行为指引\n"
            + "宜据 VF 与柱位锚点重写语气与分疏，使三标题与盘气相扣；可再次发起终审以润色辞章。\n"
        )
    else:
        body_md = "### Core\n" + verdict[:1200] + "\n### Note\nPhysics-plugin fallback (not full LLM verdict).\n"
    assertions = [
        {
            "assertion_id": "fallback_a0",
            "text": (verdict[:400] + ("…" if len(verdict) > 400 else "")) or "物理层已给出结构化证据，待辞章润色。",
            "evidence_refs": ["plugin.sys.core.physics"],
        }
    ]
    obj: Dict[str, Any] = {
        "verdict_body": body_md,
        "change_log": {
            "physics_diff": [],
            "consensus_diff": [],
            "text_diff_hint": "llm_empty_or_error_physics_fallback",
        },
        "assertions": assertions,
    }
    return json.dumps(obj, ensure_ascii=False)
