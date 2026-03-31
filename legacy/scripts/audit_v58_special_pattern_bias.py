#!/usr/bin/env python3
"""
EDR-058：奇格稀有度与质心偏态报告
==================================
产出 A-31～A-35 在 5D 空间相对于「正八格中心」的偏移向量 ΔV；
并核验 A-33/A-34（虚空感应）的 S 轴波动与 R 轴抬升。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _centroid_from_manifest(pid: str) -> np.ndarray | None:
    """从 config/patterns/manifest_A{num}.json 读取 centroid_5d。"""
    num = pid.replace("A-", "").strip()
    path = ROOT / "config" / "patterns" / f"manifest_A{num}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        c = data.get("centroid_5d")
        if c and len(c) == 5:
            return np.array([float(x) for x in c], dtype=np.float64)
    except Exception:
        pass
    return None


def main():
    from core.database import PHYSICS_DB
    from core.database.fds_physics import FDSPhysics

    physics = FDSPhysics(PHYSICS_DB)

    # 正八格中心：A-01～A-08 质心均值
    oct_pids = [f"A-{i:02d}" if i < 10 else f"A-{i}" for i in range(1, 9)]
    oct_centroids = []
    for pid in oct_pids:
        cen = physics.get_centroid(pid)
        if cen:
            oct_centroids.append(cen[0])
        else:
            c = _centroid_from_manifest(pid)
            if c is not None:
                oct_centroids.append(c)
    if not oct_centroids:
        # 回退：用 A-01 或零向量
        c = _centroid_from_manifest("A-01")
        center_oct = np.array(c, dtype=np.float64) if c is not None else np.zeros(5, dtype=np.float64)
    else:
        center_oct = np.mean(oct_centroids, axis=0)

    special_pids = [f"A-{i}" for i in range(31, 36)]
    report = {
        "schema": "EDR_058_special_pattern_bias",
        "reference": {
            "name": "正八格中心",
            "pattern_ids": oct_pids,
            "centroid_5d": center_oct.tolist(),
        },
        "special_patterns": [],
        "void_patterns_note": "A-33/A-34 为暗冲格局，S 轴预期高频波动、R 轴抬升。",
    }

    for pid in special_pids:
        cen = physics.get_centroid(pid)
        if not cen:
            mu = _centroid_from_manifest(pid)
            n = 0
        else:
            mu, n = cen
        if mu is None:
            mu = _centroid_from_manifest(pid)
        if mu is None:
            report["special_patterns"].append({
                "pattern_id": pid,
                "centroid_5d": None,
                "sample_count": 0,
                "delta_V": None,
                "S_axis_std": None,
                "R_axis": None,
            })
            continue
        mu = np.asarray(mu, dtype=np.float64)
        if len(mu) != 5:
            mu = np.array([float(mu[i]) for i in range(5)] if len(mu) >= 5 else list(mu) + [0.0] * (5 - len(mu)))
        delta_V = (mu - center_oct).tolist()
        entry = {
            "pattern_id": pid,
            "centroid_5d": [round(float(mu[i]), 4) for i in range(5)],
            "sample_count": int(n),
            "delta_V": [round(float(delta_V[i]), 4) for i in range(5)],
            "delta_V_labels": DIM_ORDER,
        }
        # R 轴（直觉/灵性）
        entry["R_axis"] = round(float(mu[4]), 4)
        # A-33/A-34：S 轴波动（虚空震荡）
        if pid in ("A-33", "A-34") and n >= 2:
            cov_result = physics.get_centroid_and_cov(pid)
            if cov_result and cov_result[1] is not None:
                _, cov, _ = cov_result
                s_var = float(cov[3, 3])
                entry["S_axis_std"] = round(np.sqrt(max(0, s_var)), 4)
                entry["S_axis_note"] = "虚空格局 S 轴标准差（偏高表示应力不稳定）"
            else:
                entry["S_axis_std"] = None
        else:
            entry["S_axis_std"] = None
        report["special_patterns"].append(entry)

    physics.close()

    out_path = ROOT / "audit_logs" / "edr_058_special_pattern_bias.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 《奇格稀有度与质心偏态报告》已写入: {out_path}")
    print(f"   正八格中心 5D: {[round(x, 3) for x in center_oct]}")
    for e in report["special_patterns"]:
        pid = e["pattern_id"]
        dv = e.get("delta_V") or []
        print(f"   {pid} ΔV = {dv}  n={e.get('sample_count', 0)}  R={e.get('R_axis')}  S_std={e.get('S_axis_std')}")
    sys.exit(0)


if __name__ == "__main__":
    main()
