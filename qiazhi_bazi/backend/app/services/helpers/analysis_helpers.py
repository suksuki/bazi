"""Pure helpers for analysis service orchestration."""
from __future__ import annotations

import json
from typing import Any, Dict, List, Tuple


def normalize_translation_texts(texts: List[str], target_lang: str, guess_lang: Any) -> Tuple[List[str], bool]:
    filtered = [item for item in texts if isinstance(item, str) and item.strip()]
    if not filtered:
        return [], True
    if target_lang.upper() == "ZH":
        return filtered, True
    target = target_lang.upper()
    if all(guess_lang(text) in {target, "UNKNOWN"} for text in filtered):
        return filtered, True
    return filtered, False


def build_translation_messages(texts: List[str], target_lang: str) -> List[Dict[str, str]]:
    lang_name = {"EN": "English", "KO": "Korean", "ZH": "Chinese"}.get(target_lang.upper(), "English")
    return [
        {
            "role": "system",
            "content": (
                "You are a translation engine. Return STRICT JSON only: "
                '{"items":["..."]}. Keep same count and order, no explanation.'
            ),
        },
        {
            "role": "user",
            "content": json.dumps({"target": lang_name, "items": texts}, ensure_ascii=False),
        },
    ]


def parse_translation_response(raw: str, fallback_items: List[str]) -> Dict[str, List[str]]:
    try:
        parsed = json.loads(raw)
        items = parsed.get("items", [])
        if isinstance(items, list) and len(items) == len(fallback_items):
            return {"items": [str(item) for item in items]}
    except Exception:
        pass
    return {"items": fallback_items}


def fallback_clash_prompt(observed: List[str]) -> str:
    if not observed:
        return "我暂未观察到明显的冲合。我们是否继续做下一层扫描？"
    return (
        "我先汇报观察到的物理点：" + "、".join(observed) + "。"
        "我发现局部正在对撞/耦合，我们是否需要深入分析这个局部？"
    )


def build_seed_audit_summary(
    body: Any,
    metadata: Dict[str, Any],
    llm_prompt: str,
    llm_meta: Dict[str, Any],
    physics_tensor: Dict[str, Any],
    now_iso_value: str,
    snapshot_summary: str,
) -> List[Dict[str, Any]]:
    model_name = str(llm_meta.get("model_name") or "LLM")
    llm_elapsed_ms = float(llm_meta.get("elapsed_ms") or 0.0)
    llm_approx_tokens = float(llm_meta.get("approx_tokens") or 0.0)
    param_version_id = str((physics_tensor or {}).get("audit_log", {}).get("param_version_id", "--"))
    hard_route_logs = (
        ((physics_tensor or {}).get("audit_log", {}) or {}).get("trace", {}).get("hard_route_logs", [])
    )
    root_check = (((physics_tensor or {}).get("audit_log", {}) or {}).get("trace", {}).get("root_check", {}) or {})
    local_decay_applied = bool(root_check.get("no_root", False))
    points = metadata.get("conflict_matrix", {}).get("points", [])
    point_labels = [point.get("detail", "") for point in points]
    return [
        {
            "step": "01",
            "role": "Arbiter",
            "action": f"提交生辰 {body.date} {body.time}，请求物理建模。",
            "relay_to": "Core",
            "timestamp": now_iso_value,
            "payload": {"date": body.date, "time": body.time, "calendar": body.calendar},
        },
        {
            "step": "02",
            "role": "Core",
            "action": (
                f"完成排盘 [{metadata['pillars']['year']['stem']}{metadata['pillars']['year']['branch']}/"
                f"{metadata['pillars']['month']['stem']}{metadata['pillars']['month']['branch']}/"
                f"{metadata['pillars']['day']['stem']}{metadata['pillars']['day']['branch']}/"
                f"{metadata['pillars']['hour']['stem']}{metadata['pillars']['hour']['branch']}] "
                f"及物理探测 [{('、'.join(point_labels) if point_labels else '未见明显冲合')}]。"
                "数据已移交审计员。"
            ),
            "relay_to": "Auditor",
            "timestamp": now_iso_value,
            "payload": {
                "pillars": metadata.get("pillars"),
                "conflicts": points,
                "snapshot_summary": snapshot_summary,
                "hard_route_logs": hard_route_logs,
                "local_decay_applied": local_decay_applied,
                "self_deity_only": True,
            },
        },
        {
            "step": "03",
            "role": "Auditor",
            "action": "基于物理冲突，生成初级判词与诱导问句。",
            "relay_to": "Arbiter",
            "timestamp": now_iso_value,
            "payload": {
                "llm_prompt": llm_prompt,
                "model_name": model_name,
                "llm_elapsed_ms": llm_elapsed_ms,
                "llm_approx_tokens": llm_approx_tokens,
                "param_version_id": param_version_id,
                "snapshot_summary": snapshot_summary,
            },
        },
    ]
