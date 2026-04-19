from __future__ import annotations

import json
from typing import Any, Dict, Iterable, List

from .decision_brain_protocol import build_plan_claim

LLM_PROMPT_CONTRACT_VERSION = "v17.prompt.contract.v1.0"
PLAN_PROMPT_VERSION = "v17.plan.arbitration.v1.0"
CONFLICT_PROMPT_VERSION = "v17.conflict.arbitration.v1.0"


def _safe_str(value: Any, default: str = "") -> str:
    return str(value or "").strip() or default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_list(value: Any) -> List[Any]:
    return [x for x in (value or []) if x is not None]


def _normalize_decision_rows(rows: Iterable[Dict[str, Any]], max_rows: int = 16) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        label = _safe_str(row.get("label") or row.get("title"))
        impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
        target = _safe_str(impact.get("target_god") or row.get("target_god"), default="未定目标")
        ratio = _safe_float(impact.get("impact_ratio"), 0.0)
        source = _safe_str(row.get("source") or row.get("plugin_id"), default="unknown")
        out.append(
            {
                "id": _safe_str(row.get("id")),
                "label": label,
                "target_god": target,
                "source": source,
                "ratio": round(ratio, 6),
                "direction": "enhance" if ratio > 0 else "weaken" if ratio < 0 else "neutral",
                "priority": _safe_float(row.get("priority"), 0.0),
                "severity_hint": _safe_str(row.get("routing_claim", {}).get("severity"))
                if isinstance(row.get("routing_claim"), dict)
                else "",
                "raw": row,
            }
        )
        if len(out) >= max_rows:
            break
    return out


def build_plan_prompt_contract(
    *,
    rows: List[Dict[str, Any]],
    action: str,
    anchor: str,
    max_rows: int = 16,
) -> Dict[str, Any]:
    safe_action = _safe_str(action)
    safe_anchor = _safe_str(anchor)
    compact_rows = _normalize_decision_rows(rows=rows, max_rows=max_rows)
    decision_count = len([dict(row or {}).get("id") for row in _safe_list(rows) if dict(row or {}).get("id")])
    total_abs = sum(abs(_safe_float(r.get("physical_impact", {}).get("impact_ratio"), 0.0)) for r in _safe_list(rows) if isinstance(r, dict))
    net_ratio = sum(_safe_float(r.get("physical_impact", {}).get("impact_ratio"), 0.0) for r in _safe_list(rows) if isinstance(r, dict))
    contract = {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_id": f"decision_plan:{safe_action}:{safe_anchor or 'anchor'}:{decision_count}",
        "task_type": "decision_batch_arbitration",
        "policy_version": PLAN_PROMPT_VERSION,
        "anchor": safe_anchor,
        "action": safe_action,
        "summary": {
            "decision_count": decision_count,
            "truncated": max(0, len(_safe_list(rows)) - len(compact_rows)),
            "total_abs_ratio": round(total_abs, 6),
            "net_ratio": round(net_ratio, 6),
        },
        "decision_rows": compact_rows,
        "output_contract": {
            "required_fields": ["decision_id", "action", "reason"],
            "action_scope": ["KEEP", "DROP", "ESCALATE"],
            "reason_charset": "zh-CN",
            "max_reason_chars": 120,
            "output_format": "json_array",
            "example": {
                "decision_id": compact_rows[0]["id"] if compact_rows else "d1",
                "action": "KEEP",
                "reason": "方向与十神主脉一致，保持为主。",
            },
            "fallback_when_unparseable": "保守处理（优先KEEP）",
        },
    }
    return contract


def build_plan_prompt_text(
    *,
    rows: List[Dict[str, Any]],
    action: str,
    anchor: str,
    max_rows: int = 16,
) -> str:
    contract = build_plan_prompt_contract(rows=rows, action=action, anchor=anchor, max_rows=max_rows)
    lines: List[str] = [
        "你是 V17 决策仲裁子系统（协议 v17.prompt.contract.v1.0）。",
        "任务：对同一批决策候选做统一裁决，只输出 JSON，不允许解释性文本。",
        "",
        "规则：",
        "1) 只给出可执行结果，不改写系统物理边界。",
        "2) 每条输出必须包含 decision_id/action/reason 三字段。",
        "3) action 仅可为 KEEP / DROP / ESCALATE。",
        "4) 仅使用给定候选；不得新增决策项。",
        "5) 字段 reason 用中文，建议≤120字。",
        "",
        "【任务摘要】",
    ]
    lines.extend(
        [
            f"action={contract['action'] or '未给动作'}",
            f"anchor={contract['anchor'] or '未命名锚点'}",
            f"decision_count={contract['summary']['decision_count']}",
            f"truncated={contract['summary']['truncated']}",
            "",
        ]
    )
    lines.append("【候选决策】")
    if compact := contract["decision_rows"]:
        for idx, row in enumerate(compact, start=1):
            reason = _safe_str(row.get("label") or row.get("raw", {}).get("label") or row.get("raw", {}).get("title"), default=f"决策{idx}")
            lines.append(
                f"{idx}. id={row['id']} | label={reason} | target={row['target_god']} | "
                f"direction={row['direction']} {abs(float(row['ratio']) * 100):.1f}% | source={row['source']}"
            )
        if len(_safe_list(rows)) > len(compact):
            lines.append(f"...其余 {len(_safe_list(rows)) - len(compact)} 条按相同规则处理。")
    else:
        lines.append("当前无有效候选。")

    lines.extend(
        [
            "",
            "【输出格式】",
            "请仅输出标准 JSON 数组，示例：",
            json.dumps(
                {
                    "version": "v17.decision.choices.v1",
                    "decisions": [
                        {
                            "decision_id": compact[0]["id"] if compact else "d1",
                            "action": "KEEP",
                            "reason": "与命局主线一致，默认保留。",
                        },
                    ],
                },
                ensure_ascii=False,
            ),
        ]
    )
    return "\n".join(lines).strip()


def build_conflict_prompt_bundle(
    *,
    bundle: Dict[str, Any],
) -> Dict[str, Any]:
    conflicts = _safe_list(bundle.get("conflicts"))
    claims = _safe_list(bundle.get("claims"))
    conflict_ids = [str(c.get("conflict_id") or "").strip() for c in conflicts if str(c.get("conflict_id") or "").strip()]
    conflict_count = len(conflict_ids)
    claim_ids = [str(c.get("claim_id") or "").strip() for c in claims if str(c.get("claim_id") or "").strip()]
    return {
        "prompt_contract_version": LLM_PROMPT_CONTRACT_VERSION,
        "task_type": "conflict_bundle_arbitration",
        "policy_version": CONFLICT_PROMPT_VERSION,
        "summary": {
            "conflict_count": conflict_count,
            "conflict_ids": conflict_ids,
            "claim_count": len(claim_ids),
        },
        "conflicts": conflicts,
        "claims": claims,
        "output_contract": {
            "required_fields": [
                "resolution_type",
                "preferred_arbiter",
                "winner_claim_ids",
                "dropped_claim_ids",
                "reason",
                "confidence",
            ],
            "resolution_type_scope": ["merge", "reject", "escalate_user", "context_only"],
            "preferred_arbiter_scope": ["system", "llm", "user"],
            "confidence_range": "[0.0,1.0]",
            "map_mode": "results_by_conflict" if conflict_count > 1 else "single",
            "output_format": "json",
            "fallback_when_unparseable": "context_only + 0.0",
        },
    }


def build_conflict_prompt_text(
    *,
    bundle: Dict[str, Any],
) -> str:
    contract = build_conflict_prompt_bundle(bundle=bundle)
    conflicts = contract["conflicts"]
    claims = contract["claims"]
    knowledge_snapshot = contract.get("knowledge_snapshot", {})
    lines: List[str] = [
        "你是 V17 冲突仲裁器（协议 v17.prompt.contract.v1.0），只输出结构化 JSON。",
        "任务：对冲突簇给出合规模型化裁决。",
        "约束：禁止输出解释文本，不要改写事实，只给出字段化结论。",
        "输出仅为 JSON，不要附加代码块与解释。",
        "只输出 JSON，不要带解释文本。",
        "",
    ]
    conflict_count = int(contract["summary"]["conflict_count"])
    if conflict_count > 1:
        lines.append("## Conflict")
        lines.append("说明：这是多冲突批处理。请返回 results_by_conflict 字典。")
        lines.append(json.dumps({"results_by_conflict": {cid: "..." for cid in contract["summary"]["conflict_ids"]},}, ensure_ascii=False))
    else:
        lines.append("## Conflict")
        lines.append("说明：这是单冲突裁决。返回 resolution_type 等字段。")
    lines.append("")
    lines.append("## Claims")
    lines.append("以下是冲突对象：")
    lines.extend([json.dumps(c, ensure_ascii=False, indent=2) for c in conflicts])
    lines.append("")
    lines.append("## Claims Detail")
    lines.extend([json.dumps(c, ensure_ascii=False, indent=2) for c in claims])
    lines.append("")
    lines.append("## Knowledge Snapshot")
    lines.append(json.dumps(knowledge_snapshot, ensure_ascii=False, indent=2))
    lines.append("")
    lines.append("## Output JSON")
    if conflict_count > 1:
        lines.append(
            json.dumps(
                {
                    "results_by_conflict": {
                        contract["summary"]["conflict_ids"][0]: {
                            "resolution_type": "merge",
                            "preferred_arbiter": "system",
                            "winner_claim_ids": [],
                            "dropped_claim_ids": [],
                            "reason": "统一约束下的候选处理",
                            "confidence": 0.7,
                        },
                    },
                },
                ensure_ascii=False,
            )
        )
    else:
        lines.append(
            json.dumps(
                {
                    "resolution_type": "merge",
                    "preferred_arbiter": "system",
                    "winner_claim_ids": [],
                    "dropped_claim_ids": [],
                    "reason": "统一约束下的候选处理",
                    "confidence": 0.7,
                },
                ensure_ascii=False,
            )
        )
    return "\n".join(lines).strip()
