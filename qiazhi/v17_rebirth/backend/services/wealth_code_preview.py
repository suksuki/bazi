from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Mapping

from v17_rebirth.backend.logic.L3_modern_narrative.wealth_code_core import (
    WEALTH_CODE_CONTRACT,
    normalize_wealth_code_meta,
    resolve_wealth_code,
)


WEALTH_CODE_PREVIEW_PROTOCOL = "v17.topic.wealth_code_preview.v1"


def _clean_label(value: Any, *, limit: int = 180) -> str:
    text = str(value or "").strip()
    if len(text) <= limit:
        return text
    return text[: limit - 1].rstrip() + "…"


def _safe_float(value: Any, fallback: float = 0.0) -> float:
    try:
        next_value = float(value)
    except (TypeError, ValueError):
        return fallback
    if next_value != next_value:
        return fallback
    return next_value


def _code_from_inputs(
    *,
    wealth_code: Dict[str, Any] | None = None,
    physics_tensor: Dict[str, Any] | None = None,
) -> tuple[Dict[str, Any], str]:
    if isinstance(wealth_code, dict) and wealth_code:
        return normalize_wealth_code_meta(wealth_code), "payload.wealth_code"
    pt = physics_tensor if isinstance(physics_tensor, dict) else {}
    meta = pt.get("meta") if isinstance(pt.get("meta"), dict) else {}
    if isinstance(meta.get("wealth_code"), dict) and meta.get("wealth_code"):
        return normalize_wealth_code_meta(meta.get("wealth_code")), "physics.meta.wealth_code"
    if pt:
        resolved = resolve_wealth_code(pt).get("wealth_code")
        return normalize_wealth_code_meta(resolved), "computed.from_server_physics"
    return {}, "missing"


def build_wealth_code_preview(
    *,
    physics_tensor: Dict[str, Any] | None = None,
    wealth_code: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    code, code_source = _code_from_inputs(wealth_code=wealth_code, physics_tensor=physics_tensor)
    primary = code.get("primary_wealth_path") if isinstance(code.get("primary_wealth_path"), dict) else {}
    source = code.get("wealth_source") if isinstance(code.get("wealth_source"), dict) else {}
    vault = code.get("wealth_vault") if isinstance(code.get("wealth_vault"), dict) else {}
    leakage = code.get("leakage_points") if isinstance(code.get("leakage_points"), list) else []
    secondary = code.get("secondary_paths") if isinstance(code.get("secondary_paths"), list) else []
    rankings = code.get("path_rankings") if isinstance(code.get("path_rankings"), list) else []
    return {
        "protocol": WEALTH_CODE_PREVIEW_PROTOCOL,
        "contract": WEALTH_CODE_CONTRACT,
        "mode": "backstage_preview",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "topic": "wealth",
        "code_source": code_source,
        "code_present": bool(code),
        "safety": {
            "raw_chart_access_for_llm": False,
            "llm_input_scope": "wealth_code_only_if_used_later",
            "physics_mutation": False,
            "parameter_mutation": False,
            "body_use_mutation": False,
        },
        "guardrails": [
            "财富密码预览只读服务端物理快照、bazi_image 与 wealth_profile，不回写体用、格局或参数。",
            "wealth_code 只表示财富路径闭合度、承接条件和风险，不承诺金额、必发财或确定年份。",
            "后续若交给 LLM，只能消费 wealth_code 合同，不能自由读取原始八字。",
        ],
        "wealth_code": code,
        "path_summary": {
            "primary_path_id": _clean_label(primary.get("id")),
            "primary_path_label": _clean_label(primary.get("plain_name")),
            "classic_label": _clean_label(primary.get("classic_label")),
            "score": round(_safe_float(primary.get("score"), 0.0), 3),
            "confidence": round(_safe_float(primary.get("confidence"), 0.0), 3),
            "risk": round(_safe_float(primary.get("risk"), 0.0), 3),
            "wealth_source": _clean_label(source.get("plain_source"), limit=160),
            "wealth_source_material": _clean_label(source.get("material")),
            "vault_present": bool(vault.get("has_vault_signal")),
            "leakage_count": len(leakage),
            "path_rankings": [
                {
                    "rank": int(_safe_float(item.get("rank"), 0)),
                    "id": _clean_label(item.get("id")),
                    "plain_name": _clean_label(item.get("plain_name") or item.get("id") or ""),
                    "size": _clean_label(item.get("size"), limit=8) or "中",
                    "score": round(_safe_float(item.get("combined_score"), _safe_float(item.get("score"), 0.0)), 3),
                }
                for item in rankings[:5]
                if isinstance(item, Mapping) and _clean_label(item.get("id"))
            ],
            "secondary_path_ids": [
                _clean_label(row.get("id"))
                for row in secondary[:5]
                if isinstance(row, Mapping) and _clean_label(row.get("id"))
            ],
        },
    }


def attach_wealth_code_preview_meta(meta: Dict[str, Any], preview: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(meta or {})
    out["wealth_code_preview"] = dict(preview or {})
    code = preview.get("wealth_code") if isinstance(preview.get("wealth_code"), Mapping) else {}
    if code:
        out["wealth_code"] = normalize_wealth_code_meta(code)
    audits = out.get("topic_code_audits") if isinstance(out.get("topic_code_audits"), list) else []
    path_summary = preview.get("path_summary") if isinstance(preview.get("path_summary"), Mapping) else {}
    top_rankings = path_summary.get("path_rankings") if isinstance(path_summary.get("path_rankings"), list) else []
    compact = {
        "protocol": WEALTH_CODE_PREVIEW_PROTOCOL,
        "contract": WEALTH_CODE_CONTRACT,
        "created_at": str(preview.get("created_at") or ""),
        "topic": "wealth",
        "kind": "wealth_code_preview",
        "code_present": bool(preview.get("code_present")),
        "code_source": str(preview.get("code_source") or ""),
        "primary_path_id": str(path_summary.get("primary_path_id") or ""),
        "primary_path_label": str(path_summary.get("primary_path_label") or ""),
        "wealth_source_material": str(path_summary.get("wealth_source_material") or ""),
        "vault_present": bool(path_summary.get("vault_present")),
        "leakage_count": int(path_summary.get("leakage_count") or 0),
        "top_ranked_path_id": _clean_label(top_rankings[0].get("id")) if top_rankings else str(path_summary.get("primary_path_id") or ""),
    }
    out["topic_code_audits"] = [compact, *audits[:9]]
    return out


def summarize_wealth_code_preview(
    preview: Dict[str, Any],
    *,
    include_code: bool = True,
    include_graph: bool = True,
) -> Dict[str, Any]:
    if not isinstance(preview, dict) or not preview:
        return {
            "protocol": WEALTH_CODE_PREVIEW_PROTOCOL,
            "preview_present": False,
        }
    code = preview.get("wealth_code") if isinstance(preview.get("wealth_code"), dict) else {}
    summary: Dict[str, Any] = {
        "protocol": str(preview.get("protocol") or WEALTH_CODE_PREVIEW_PROTOCOL),
        "contract": str(preview.get("contract") or WEALTH_CODE_CONTRACT),
        "preview_present": True,
        "mode": str(preview.get("mode") or "backstage_preview"),
        "created_at": str(preview.get("created_at") or ""),
        "topic": str(preview.get("topic") or "wealth"),
        "code_source": str(preview.get("code_source") or ""),
        "code_present": bool(preview.get("code_present")),
        "safety": preview.get("safety") if isinstance(preview.get("safety"), dict) else {},
        "guardrails": preview.get("guardrails") if isinstance(preview.get("guardrails"), list) else [],
        "path_summary": preview.get("path_summary") if isinstance(preview.get("path_summary"), dict) else {},
    }
    if code:
        summary["wealth_code_summary"] = {
            "score": code.get("score"),
            "confidence": code.get("confidence"),
            "risk": code.get("risk"),
            "primary_wealth_path": code.get("primary_wealth_path") if isinstance(code.get("primary_wealth_path"), dict) else {},
            "wealth_source": code.get("wealth_source") if isinstance(code.get("wealth_source"), dict) else {},
            "monetization_engine": code.get("monetization_engine") if isinstance(code.get("monetization_engine"), dict) else {},
            "carrier": code.get("carrier") if isinstance(code.get("carrier"), dict) else {},
            "wealth_vault": code.get("wealth_vault") if isinstance(code.get("wealth_vault"), dict) else {},
            "leakage_points": code.get("leakage_points") if isinstance(code.get("leakage_points"), list) else [],
            "flow_year_watchlist": code.get("flow_year_watchlist") if isinstance(code.get("flow_year_watchlist"), list) else [],
        }
        if include_graph:
            summary["wealth_code_summary"]["evidence_graph"] = (
                code.get("evidence_graph") if isinstance(code.get("evidence_graph"), dict) else {}
            )
    if include_code:
        summary["wealth_code"] = code
    return summary
