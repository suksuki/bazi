from __future__ import annotations

from typing import Any, Dict, List, Tuple


def _bucket_name(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"manual", "system", "llm"}:
        return normalized
    return "manual"


def _source_family(row: Dict[str, Any]) -> str:
    source = str(row.get("source") or row.get("plugin_id") or "unknown").strip().lower()
    if not source:
        return "unknown"
    if "." in source:
        parts = [part for part in source.split(".") if part]
        return ".".join(parts[:3]) if parts else source
    return source


def _impact_ratio(row: Dict[str, Any]) -> float:
    impact = row.get("physical_impact") if isinstance(row.get("physical_impact"), dict) else {}
    try:
        ratio = float(impact.get("impact_ratio", 0.0) or 0.0)
    except (TypeError, ValueError):
        ratio = 0.0
    try:
        significance = float(impact.get("significance_weight", 1.0) or 1.0)
    except (TypeError, ValueError):
        significance = 1.0
    return ratio * significance


def _direction_key(ratio: float) -> str:
    if ratio > 0:
        return "up"
    if ratio < 0:
        return "down"
    return "neutral"


def _bucket_key(bucket: str, row: Dict[str, Any]) -> Tuple[str, str, str, str]:
    ratio = _impact_ratio(row)
    target_god = str(row.get("target_god") or ((row.get("physical_impact") or {}) if isinstance(row.get("physical_impact"), dict) else {}).get("target_god") or "").strip()
    source_family = _source_family(row)
    anchor = str(row.get("source_event") or row.get("exclusivity_key") or "").strip()
    if anchor:
        return (bucket, target_god or "untargeted", source_family, anchor)
    return (bucket, target_god or "untargeted", source_family, _direction_key(ratio))


def _summary_line(batch: Dict[str, Any]) -> str:
    bucket = str(batch.get("bucket") or "manual").strip().upper()
    target = str(batch.get("target_god") or "未定目标").strip()
    count = int(batch.get("decision_count") or 0)
    net_ratio = float(batch.get("net_impact_ratio") or 0.0)
    families = [str(x).strip() for x in (batch.get("source_families") or []) if str(x).strip()]
    direction = "增强" if net_ratio > 0 else "抑制" if net_ratio < 0 else "观察"
    family_text = " / ".join(families[:3]) if families else "mixed"
    return (
        f"决策批次[{bucket}]：围绕 {target} 聚合 {count} 条主张，"
        f"来源 {family_text}，净效应 {direction} {abs(net_ratio) * 100:.1f}% 。"
        "请按批次理解，不逐条复述。"
    )


def build_decision_batches(*, arbitration: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
    buckets = {
        "manual": list(arbitration.get("manual_decisions") or []),
        "system": list(arbitration.get("auto_resolutions") or []),
        "llm": list(arbitration.get("llm_arbitration_context") or []),
    }
    grouped: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = {}
    for bucket, rows in buckets.items():
        for row in rows:
            if not isinstance(row, dict):
                continue
            grouped.setdefault(_bucket_key(bucket, row), []).append(dict(row))

    all_batches: List[Dict[str, Any]] = []
    for (bucket, target_god, source_family, anchor), rows in grouped.items():
        ratios = [_impact_ratio(row) for row in rows]
        labels = [str(row.get("label") or row.get("title") or "").strip() for row in rows if str(row.get("label") or row.get("title") or "").strip()]
        decision_ids = [str(row.get("id") or "").strip() for row in rows if str(row.get("id") or "").strip()]
        families = sorted({_source_family(row) for row in rows if _source_family(row)})
        max_priority = max((float(row.get("priority", 0.0) or 0.0) for row in rows), default=0.0)
        batch = {
            "batch_id": f"{bucket}:{target_god}:{source_family}:{anchor}",
            "bucket": _bucket_name(bucket),
            "target_god": target_god if target_god != "untargeted" else "",
            "source_anchor": anchor,
            "source_families": families,
            "decision_ids": decision_ids,
            "decision_count": len(rows),
            "net_impact_ratio": round(sum(ratios), 4),
            "max_priority": round(max_priority, 4),
            "labels": labels[:6],
        }
        batch["prompt_line"] = _summary_line(batch)
        all_batches.append(batch)

    all_batches.sort(
        key=lambda row: (
            {"manual": 3, "llm": 2, "system": 1}.get(str(row.get("bucket") or ""), 0),
            abs(float(row.get("net_impact_ratio") or 0.0)),
            float(row.get("max_priority") or 0.0),
            int(row.get("decision_count") or 0),
        ),
        reverse=True,
    )

    return {
        "all": all_batches,
        "manual": [row for row in all_batches if row.get("bucket") == "manual"],
        "system": [row for row in all_batches if row.get("bucket") == "system"],
        "llm": [row for row in all_batches if row.get("bucket") == "llm"],
        "prompt_lines": [str(row.get("prompt_line") or "").strip() for row in all_batches[:8] if str(row.get("prompt_line") or "").strip()],
    }
