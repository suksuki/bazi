"""旺衰：将印比阵营 Raw 能量拆为「令 / 地 / 助」三 Skill 并生成审计行。"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Tuple

from app.core.config.physics_settings import resolve_physics_settings
from app.plugins.wangshuai.op_pivot_defense import compute_pivot_defense

PLUGIN_ID = "classical.wangshuai.v1"

_SELF_PARTY = frozenset({"比肩", "劫财", "正印", "偏印"})


def _utc_audit_ts() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _split_self_party_channels(
    trace_details: Dict[str, Any],
) -> Tuple[float, float, float]:
    """返回 (ws_season_abs, ws_root_abs, ws_support_abs) 基于 contribution_sources 的 raw 加总。"""
    ws_season = 0.0
    ws_root = 0.0
    ws_support = 0.0
    for deity in _SELF_PARTY:
        detail = trace_details.get(deity) or {}
        base = detail.get("base_energy") if isinstance(detail.get("base_energy"), dict) else {}
        sources = base.get("contribution_sources")
        if not isinstance(sources, list):
            continue
        for item in sources:
            if not isinstance(item, dict):
                continue
            e = float(item.get("contribution_energy") or 0.0)
            src = str(item.get("source") or "")
            if src.startswith("month."):
                ws_season += e
            elif ".branch:" in src and not src.startswith("month."):
                ws_root += e
            elif ".stem:" in src and not src.startswith("month."):
                ws_support += e
    return ws_season, ws_root, ws_support


def evaluate_wangshuai(
    *,
    physics_tensor: Dict[str, Any],
    metadata: Dict[str, Any],
) -> Dict[str, Any]:
    del metadata
    axes = (physics_tensor or {}).get("deity_energy_axes") or {}
    trace = (physics_tensor or {}).get("deity_trace_details") or {}
    if not isinstance(trace, dict):
        trace = {}

    ws_season, ws_root, ws_support = _split_self_party_channels(trace)
    split_sum = ws_season + ws_root + ws_support

    self_abs = float(
        sum(float((axes.get(name) or {}).get("absolute_energy", 0.0) or 0.0) for name in _SELF_PARTY)
    )

    if self_abs < 1.0:
        verdict = "身弱偏虚，优先扶助。"
        confidence = 0.72
    elif self_abs <= 8.0:
        verdict = "中和可用，维持平衡。"
        confidence = 0.68
    else:
        verdict = "能量过载，优先泄耗降压。"
        confidence = 0.79

    ts = _utc_audit_ts()
    meta_rc = (((physics_tensor or {}).get("meta") or {}).get("runtime_physics_config") or {})
    ws_settings = resolve_physics_settings(meta_rc if isinstance(meta_rc, dict) else None)
    pivot_blob = compute_pivot_defense(
        physics_tensor=physics_tensor if isinstance(physics_tensor, dict) else {},
        self_abs=self_abs,
        settings=ws_settings,
    )

    scale = self_abs / split_sum if split_sum > 1e-9 else 0.0
    contrib_season = round(ws_season * scale, 4) if scale else round(ws_season, 4)
    contrib_root = round(ws_root * scale, 4) if scale else round(ws_root, 4)
    contrib_support = round(ws_support * scale, 4) if scale else round(ws_support, 4)

    audit_items: List[Dict[str, Any]] = [
        {
            "id": "ws-skill-season",
            "step": "WS-令",
            "role": "Wangshuai",
            "action": "ws_season · classical.wangshuai.v1",
            "timestamp": ts,
            "payload": {
                "skill_id": "ws_season",
                "plugin": PLUGIN_ID,
                "channel": "月令提纲（month.*）",
                "raw_channel_energy": round(ws_season, 4),
                "abs_contribution": contrib_season,
            },
        },
        {
            "id": "ws-skill-root",
            "step": "WS-地",
            "role": "Wangshuai",
            "action": "ws_root · classical.wangshuai.v1",
            "timestamp": ts,
            "payload": {
                "skill_id": "ws_root",
                "plugin": PLUGIN_ID,
                "channel": "地支藏根（非月令 .branch）",
                "raw_channel_energy": round(ws_root, 4),
                "abs_contribution": contrib_root,
            },
        },
        {
            "id": "ws-skill-support",
            "step": "WS-助",
            "role": "Wangshuai",
            "action": "ws_support · classical.wangshuai.v1",
            "timestamp": ts,
            "payload": {
                "skill_id": "ws_support",
                "plugin": PLUGIN_ID,
                "channel": "透干扶助（非月令 .stem）",
                "raw_channel_energy": round(ws_support, 4),
                "abs_contribution": contrib_support,
            },
        },
    ]

    return {
        "self_abs": round(self_abs, 4),
        "pivot_defense_v1": pivot_blob,
        "verdict": verdict,
        "confidence_score": confidence,
        "evidence": [
            f"Self_Abs={self_abs:.2f}",
            f"ws_season_raw={ws_season:.2f}",
            f"ws_root_raw={ws_root:.2f}",
            f"ws_support_raw={ws_support:.2f}",
            f"pivot={pivot_blob.get('target_pivot', '')}",
            f"pivot_tags={','.join(pivot_blob.get('llm_assertion_tags') or [])}",
            "rule_source=plugins/wangshuai/readme.md",
        ],
        "rule_source": "plugins/wangshuai/readme.md",
        "wangshuai_axes": {
            "ws_season_raw": round(ws_season, 4),
            "ws_root_raw": round(ws_root, 4),
            "ws_support_raw": round(ws_support, 4),
            "split_scale_to_self_abs": round(scale, 6) if scale else 0.0,
        },
        "audit_items": audit_items,
    }
