#!/usr/bin/env python3
"""Run CF_FLOATING_DECAY regression with LLM audit feedback."""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List
from urllib import error, request

from sqlmodel import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.models import PhysicsInteractionParam  # noqa: E402
from app.db.session import session_scope  # noqa: E402
from app.skills.physics_engine import PhysicsInferenceSkill, WEIGHT_LUCK, WEIGHT_YEAR  # noqa: E402


@dataclass
class CaseSpec:
    name: str
    endpoint: str
    payload: Dict[str, Any]


def _post_json(url: str, payload: Dict[str, Any], headers: Dict[str, str] | None = None) -> Dict[str, Any]:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/json")
    for k, v in (headers or {}).items():
        if v:
            req.add_header(k, v)
    try:
        with request.urlopen(req, timeout=90) as resp:
            raw = resp.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except error.HTTPError as e:
        text = e.read().decode("utf-8", errors="ignore")
        raise RuntimeError(f"HTTP {e.code} {url}: {text}") from e


def _set_decay(value: float) -> None:
    with session_scope() as s:
        row = s.exec(
            select(PhysicsInteractionParam).where(PhysicsInteractionParam.param_key == "CF_FLOATING_DECAY")
        ).first()
        if row is None:
            row = PhysicsInteractionParam(param_key="CF_FLOATING_DECAY", param_value=value)
            s.add(row)
        else:
            row.param_value = value
            s.add(row)
    PhysicsInferenceSkill.instance().refresh_cache()


def _case_specs() -> List[CaseSpec]:
    return [
        CaseSpec(
            name="baseline_1990_seed",
            endpoint="/api/v1/analyze-seed",
            payload={
                "date": "1990-01-01",
                "time": "12:00",
                "calendar": "solar",
                "lang": "ZH",
                "latitude": 31.2304,
                "longitude": 121.4737,
            },
        ),
        CaseSpec(
            name="baseline_dingsi_yisi",
            endpoint="/api/v1/analyze_clash",
            payload={
                "pillars": {
                    "year": {"stem": "丁", "branch": "巳", "energy_value": 100},
                    "month": {"stem": "乙", "branch": "巳", "energy_value": 100},
                    "day": {"stem": "乙", "branch": "酉", "energy_value": 100},
                    "hour": {"stem": "辛", "branch": "丑", "energy_value": 100},
                },
                "lang": "ZH",
                "latitude": 31.2304,
                "longitude": 121.4737,
            },
        ),
    ]


def run(base_url: str, output_csv: Path, decay_values: List[float], admin_token: str | None) -> None:
    headers = {"X-Admin-Token": admin_token or ""}
    rows: List[Dict[str, Any]] = []
    for decay in decay_values:
        _set_decay(decay)
        # keep backend process cache in sync as well
        _post_json(f"{base_url}/api/admin/refresh-physics", {}, headers=headers)
        for spec in _case_specs():
            analyze = _post_json(f"{base_url}{spec.endpoint}", spec.payload)
            metadata = analyze.get("metadata", {})
            physics_tensor = analyze.get("physics_tensor")
            audit = _post_json(
                f"{base_url}/api/v1/audit-physics-with-llm",
                {"metadata": metadata, "physics_tensor": physics_tensor, "lang": "ZH"},
            )
            deity_scores = (audit.get("physics_tensor", {}) or {}).get("deity_scores", {}) or {}
            deity_axes = (audit.get("physics_tensor", {}) or {}).get("deity_energy_axes", {}) or {}
            bijian_axes = deity_axes.get("比肩", {}) or {}
            row = {
                "case": spec.name,
                "cf_floating_decay": decay,
                "alignment_score": audit.get("alignment_score"),
                "structured_hit": bool(audit.get("structured_hit", False)),
                "repair_mode": audit.get("repair_mode", "unknown"),
                "diagnosis": audit.get("diagnosis"),
                "top_anomaly": audit.get("top_anomaly"),
                "bijian_score": deity_scores.get("比肩"),
                "bijian_abs_energy": bijian_axes.get("absolute_energy"),
                "bijian_rel_pct": bijian_axes.get("relative_percentage"),
                "weight_luck": WEIGHT_LUCK,
                "weight_year": WEIGHT_YEAR,
                "sql_patch": audit.get("sql_patch"),
                "param_version_id": ((audit.get("physics_tensor", {}) or {}).get("audit_log", {}) or {}).get("param_version_id", "--"),
                "hard_route_logs": (((audit.get("physics_tensor", {}) or {}).get("audit_log", {}) or {}).get("trace", {}) or {}).get("hard_route_logs", []),
            }
            rows.append(row)
            print(
                f"[{spec.name}] CF_FLOATING_DECAY={decay:.2f} "
                f"alignment={row['alignment_score']} hit={row['structured_hit']} "
                f"比肩={row['bijian_score']} abs={row['bijian_abs_energy']} "
                f"anomaly={row['top_anomaly']} "
                f"param_version_id={row['param_version_id']}"
            )

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "case",
        "cf_floating_decay",
        "alignment_score",
        "structured_hit",
        "repair_mode",
        "bijian_score",
        "bijian_abs_energy",
        "bijian_rel_pct",
        "weight_luck",
        "weight_year",
        "top_anomaly",
        "diagnosis",
        "sql_patch",
        "param_version_id",
        "hard_route_logs",
    ]
    with output_csv.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nRegression report saved: {output_csv}")
    _print_ascii_alignment_chart(rows)
    _print_ascii_collapse_curve(rows)
    _print_confidence_heatmap(rows)
    _print_best_practice_zone(rows)
    _print_disturbance_warning(rows)


def _safe_float(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _print_ascii_alignment_chart(rows: List[Dict[str, Any]]) -> None:
    by_decay: Dict[float, List[float]] = {}
    for r in rows:
        d = _safe_float(r.get("cf_floating_decay"))
        s = _safe_float(r.get("alignment_score"))
        by_decay.setdefault(d, []).append(s)
    if not by_decay:
        return
    decays = sorted(by_decay.keys())
    avg_pairs = [(d, sum(by_decay[d]) / max(1, len(by_decay[d]))) for d in decays]
    max_score = max(s for _, s in avg_pairs) or 1.0
    print("\n=== CF_FLOATING_DECAY 收敛曲线 (ASCII) ===")
    print("Y: LLM_Alignment_Score (avg by decay)")
    print("X: CF_FLOATING_DECAY")
    for d, score in avg_pairs:
        bar_len = int(round((score / max_score) * 40))
        bar = "█" * max(1, bar_len)
        print(f"{d:>4.2f} | {bar:<40} {score:>6.2f}")


def _print_confidence_heatmap(rows: List[Dict[str, Any]]) -> None:
    by_decay: Dict[float, List[bool]] = {}
    for r in rows:
        d = _safe_float(r.get("cf_floating_decay"))
        h = bool(r.get("structured_hit", False))
        by_decay.setdefault(d, []).append(h)
    if not by_decay:
        return
    print("\n=== Confidence Heatmap ===")
    for d in sorted(by_decay.keys()):
        vals = by_decay[d]
        rate = (sum(1 for v in vals if v) / max(1, len(vals))) * 100.0
        level = "GREEN" if rate > 80 else ("YELLOW" if rate >= 50 else "LOW")
        print(f"decay={d:>4.2f}  structured_hit_rate={rate:>5.1f}%  [{level}]")
    total_rate = (sum(1 for r in rows if bool(r.get("structured_hit", False))) / max(1, len(rows))) * 100.0
    print(f"overall structured_hit_rate={total_rate:.1f}%")


def _print_ascii_collapse_curve(rows: List[Dict[str, Any]]) -> None:
    by_decay_abs: Dict[float, List[float]] = {}
    by_decay_rel: Dict[float, List[float]] = {}
    for r in rows:
        d = _safe_float(r.get("cf_floating_decay"))
        by_decay_abs.setdefault(d, []).append(_safe_float(r.get("bijian_abs_energy")))
        by_decay_rel.setdefault(d, []).append(_safe_float(r.get("bijian_rel_pct") or r.get("bijian_score")))
    if not by_decay_abs:
        return
    print("\n=== Collapse Curve (Abs vs Rel%) ===")
    print(f"weights: luck={WEIGHT_LUCK}, year={WEIGHT_YEAR}")
    max_abs = max((sum(v) / max(1, len(v)) for v in by_decay_abs.values()), default=1.0) or 1.0
    max_rel = max((sum(v) / max(1, len(v)) for v in by_decay_rel.values()), default=1.0) or 1.0
    for d in sorted(by_decay_abs.keys()):
        abs_avg = sum(by_decay_abs[d]) / max(1, len(by_decay_abs[d]))
        rel_avg = sum(by_decay_rel.get(d, [0.0])) / max(1, len(by_decay_rel.get(d, [0.0])))
        abs_bar = "█" * max(1, int(round((abs_avg / max_abs) * 24)))
        rel_bar = "▓" * max(1, int(round((rel_avg / max_rel) * 24)))
        print(f"{d:>4.2f} | Abs {abs_bar:<24} {abs_avg:>6.3f} || Rel {rel_bar:<24} {rel_avg:>6.2f}%")


def _print_disturbance_warning(rows: List[Dict[str, Any]]) -> None:
    by_decay: Dict[float, List[float]] = {}
    for r in rows:
        d = _safe_float(r.get("cf_floating_decay"))
        s = _safe_float(r.get("alignment_score"))
        by_decay.setdefault(d, []).append(s)
    if len(by_decay) < 2:
        return
    avg_pairs = [(d, sum(by_decay[d]) / max(1, len(by_decay[d]))) for d in sorted(by_decay.keys())]
    max_jump = 0.0
    jump_pair = None
    for i in range(1, len(avg_pairs)):
        a = avg_pairs[i - 1]
        b = avg_pairs[i]
        jump = abs(b[1] - a[1])
        if jump > max_jump:
            max_jump = jump
            jump_pair = (a[0], b[0], a[1], b[1])
    print("\n=== 收敛扰动检测 ===")
    if jump_pair and max_jump >= 12.0:
        print(
            "逻辑扰动预警: "
            f"decay {jump_pair[0]:.2f}->{jump_pair[1]:.2f} "
            f"alignment {jump_pair[2]:.2f}->{jump_pair[3]:.2f} (Δ={max_jump:.2f})"
        )
    else:
        print("未检测到剧烈波动。")


def _print_best_practice_zone(rows: List[Dict[str, Any]]) -> None:
    candidates: List[Dict[str, Any]] = []
    for r in rows:
        bijian = _safe_float(r.get("bijian_score"))
        score = _safe_float(r.get("alignment_score"))
        if 3.0 <= bijian <= 7.0:
            candidates.append({**r, "_score": score, "_bijian": bijian})
    print("\n=== 最佳实践区筛选 ===")
    print("条件: 比肩分值在 [3.0, 7.0] 且 alignment_score 尽可能高")
    if not candidates:
        print("未命中候选区间（当前样本下无比肩落入 [3.0, 7.0]）。")
        return
    best = max(candidates, key=lambda x: x["_score"])
    print(
        "推荐参数: "
        f"CF_FLOATING_DECAY={_safe_float(best.get('cf_floating_decay')):.2f}, "
        f"case={best.get('case')}, "
        f"alignment_score={best.get('_score'):.2f}, "
        f"比肩={best.get('_bijian'):.2f}"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run CF_FLOATING_DECAY regression tracker.")
    parser.add_argument("--base-url", default="http://127.0.0.1:8001", help="Backend base URL")
    parser.add_argument(
        "--decays",
        default="0.1,0.2,0.3,0.4,0.5",
        help="Comma separated decay values, e.g. 0.1,0.2,0.3,0.4",
    )
    parser.add_argument(
        "--output",
        default=str(ROOT / "scripts" / "physics_regression_report.csv"),
        help="Output CSV path",
    )
    args = parser.parse_args()
    try:
        decays = [float(x.strip()) for x in args.decays.split(",") if x.strip()]
    except Exception as e:
        raise SystemExit(f"Invalid --decays: {e}") from e
    token = os.getenv("QIAZHI_ADMIN_TOKEN")
    run(
        base_url=args.base_url.rstrip("/"),
        output_csv=Path(args.output),
        decay_values=decays,
        admin_token=token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
