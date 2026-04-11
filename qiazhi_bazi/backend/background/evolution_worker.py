#!/usr/bin/env python3
"""
静默期推演 Worker：在 518_400 维设计空间上做批量扫描，可选「规则碰撞」双版本插件集对比 Abs。

用法示例：
  python -m background.evolution_worker --start 0 --limit 200 --collision \\
    --plugins-a base.chronos,classical.blind_school.v1 \\
    --plugins-b base.chronos,classical.blind_school.v1,classical.wangshuai.v1

说明：518400 = 60 × 60 × 36 × 4，将线性下标映射为四柱干支组合用于压力多样性（非历法真表）。
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

# 允许从 backend 根以 `python -m background.evolution_worker` 运行
_BACKEND_ROOT = Path(__file__).resolve().parents[1]
if str(_BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(_BACKEND_ROOT))

from app.api.contracts import AnalyzeClashRequest, BlindSchoolFeatureFlags
from app.core.evolution.combination_space import TOTAL_BAZI_COMBINATION_SPACE, four_pillars_from_linear_index
from app.services.analysis_service import analyze_clash_flow


def _self_abs_hint(tensor: Dict[str, Any]) -> float:
    ge = (tensor.get("meta") or {}).get("global_entropy_metrics")
    if isinstance(ge, dict) and ge.get("clash_abs_loss_total") is not None:
        try:
            return float(ge["clash_abs_loss_total"])
        except (TypeError, ValueError):
            pass
    nodes = tensor.get("abs_nodes") or tensor.get("abs_energy_by_deity")
    if isinstance(nodes, dict):
        try:
            return float(sum(float(v) for v in nodes.values() if isinstance(v, (int, float))))
        except Exception:
            return 0.0
    return 0.0


def _log_path() -> Path:
    return _BACKEND_ROOT / "data" / "evolution_logs.jsonl"


def _parse_plugins(s: str) -> List[str]:
    return [p.strip() for p in s.split(",") if p.strip()]


async def _run_one(
    linear_index: int,
    *,
    enabled_plugins: Sequence[str],
) -> Dict[str, Any]:
    pillars = four_pillars_from_linear_index(linear_index)
    body = AnalyzeClashRequest(
        pillars=pillars,
        lang="ZH",
        physics_config=None,
        enabled_plugins=list(enabled_plugins),
        blind_school_features=BlindSchoolFeatureFlags(),
    )
    resp = await analyze_clash_flow(body)
    tensor = resp.get("physics_tensor") or {}
    return {
        "linear_index": linear_index,
        "pillars": pillars.model_dump(),
        "abs_hint": round(_self_abs_hint(tensor if isinstance(tensor, dict) else {}), 4),
        "inbox_block": ((tensor.get("meta") or {}).get("decision_signal_to_noise") or {}),
    }


async def run_batch(args: argparse.Namespace) -> None:
    start = max(0, int(args.start))
    limit = max(1, int(args.limit))
    end = min(start + limit, TOTAL_BAZI_COMBINATION_SPACE)
    plugins_a = _parse_plugins(args.plugins_a)
    plugins_b = _parse_plugins(args.plugins_b) if args.collision else plugins_a
    log_path = _log_path()
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8") as logf:
        for idx in range(start, end):
            if args.collision:
                ra, rb = await asyncio.gather(
                    _run_one(idx, enabled_plugins=plugins_a),
                    _run_one(idx, enabled_plugins=plugins_b),
                )
                delta = round(float(rb["abs_hint"]) - float(ra["abs_hint"]), 6)
                row = {
                    "mode": "collision",
                    "linear_index": idx,
                    "plugins_a": plugins_a,
                    "plugins_b": plugins_b,
                    "delta_abs_hint": delta,
                    "variant_a": ra,
                    "variant_b": rb,
                }
            else:
                row = {
                    "mode": "single",
                    **await _run_one(idx, enabled_plugins=plugins_a),
                    "plugins": plugins_a,
                }
            logf.write(json.dumps(row, ensure_ascii=False) + "\n")
            if (idx - start + 1) % max(1, int(args.progress_every)) == 0:
                print(f"[evolution_worker] {idx - start + 1}/{end - start}", flush=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Causal DNA silent evolution scanner")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--limit", type=int, default=50, help="本批扫描条数（默认小批量，防占满 CPU）")
    ap.add_argument("--collision", action="store_true", help="双版本插件集并行对比")
    ap.add_argument(
        "--plugins-a",
        type=str,
        default="base.chronos,classical.blind_school.v1",
        help="逗号分隔 enabled_plugins（变体 A）",
    )
    ap.add_argument("--plugins-b", type=str, default="", help="变体 B（--collision 时必填有效列表）")
    ap.add_argument("--progress-every", type=int, default=25)
    args = ap.parse_args()
    if args.collision and not args.plugins_b.strip():
        args.plugins_b = "base.chronos,classical.blind_school.v1,classical.wangshuai.v1"
    print(
        json.dumps(
            {
                "total_space": TOTAL_BAZI_COMBINATION_SPACE,
                "radix": list(_RADIX),
                "note": "线性索引经 mixed-radix 映射为四柱；用于统计压力而非历法排盘。",
            },
            ensure_ascii=False,
        ),
        flush=True,
    )
    asyncio.run(run_batch(args))


if __name__ == "__main__":
    main()
