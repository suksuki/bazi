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
        verdict = "LLM 无有效输出；物理层已计算完成，请在审计舱查看参数提案与交互张量。"
    zh = (lang or "ZH").upper() == "ZH"
    if zh:
        body_md = (
            "### 核心气象\n"
            + verdict[:900]
            + "\n\n### 裁决共识\n"
            + "（系统兜底）以下摘要来自 `plugin_outputs.sys.core.physics`，非模型自由生成。\n"
            + ("\n".join(f"- {e}" for e in evid) if evid else "- （该插件暂无 evidence 行）")
            + "\n\n### 行为指引\n"
            + "请检查 LLM 连通性/限流或切换更强模型；勿将本段视为终审修辞终稿。\n"
        )
    else:
        body_md = "### Core\n" + verdict[:1200] + "\n### Note\nPhysics-plugin fallback (not full LLM verdict).\n"
    assertions = [
        {
            "assertion_id": "fallback_a0",
            "text": (verdict[:400] + ("…" if len(verdict) > 400 else "")) or "Physics layer produced structured evidence pending LLM recovery.",
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
