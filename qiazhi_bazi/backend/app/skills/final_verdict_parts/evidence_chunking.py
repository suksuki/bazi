"""将 plugin_outputs 中的 evidence 压成短句，供弱模型做语义拼图（不必解析大块 JSON）。"""
from __future__ import annotations

import json
from typing import Any, Dict, List


def format_plugin_evidence_chunks(
    plugin_outputs: Dict[str, Any] | None,
    *,
    max_plugins: int = 24,
    max_items_per_plugin: int = 10,
    max_line_len: int = 168,
    high_reasoning: bool = False,
) -> List[str]:
    """从各插件 payload.evidence 抽取「证据切片」行列表。

    ``high_reasoning=True``（runtime ``llm.is_high_reasoning_mode``）时放宽条数与行长，
    字段值不再压到 96 字，供强模型做全量逻辑溯源。
    """
    if high_reasoning:
        max_plugins = max(max_plugins, 256)
        max_items_per_plugin = max(max_items_per_plugin, 10_000)
        max_line_len = max(max_line_len, 32_000)
        field_cap = 4000
    else:
        field_cap = 96
    if not plugin_outputs or not isinstance(plugin_outputs, dict):
        return []
    lines: List[str] = []
    count = 0
    for pid in sorted(plugin_outputs.keys()):
        if count >= max_plugins:
            break
        row = plugin_outputs.get(pid)
        if not isinstance(row, dict):
            continue
        payload = row.get("payload") if isinstance(row.get("payload"), dict) else row
        evid = payload.get("evidence")
        if not isinstance(evid, list) or not evid:
            continue
        count += 1
        for i, item in enumerate(evid[:max_items_per_plugin]):
            if isinstance(item, dict):
                bits: List[str] = []
                for k in ("claim", "title", "summary", "detail", "text", "desc", "tag"):
                    v = item.get(k)
                    if v is not None and str(v).strip():
                        bits.append(f"{k}={str(v).strip()[:field_cap]}")
                if bits:
                    line = " | ".join(bits)
                else:
                    try:
                        line = json.dumps(item, ensure_ascii=False)[:max_line_len]
                    except (TypeError, ValueError):
                        line = str(item)[:max_line_len]
            else:
                line = str(item).strip()
            line = line.replace("\n", " ").replace("\r", " ")[:max_line_len]
            if line:
                lines.append(f"证据切片.{pid}[{i}] {line}")
    return lines
