#!/usr/bin/env python3
"""
FDS SOP V5.7：第一梯队（A-14～A-20）质心对比审计
================================================
迁库后执行：从 DuckDB pattern_points 取实测 5D 均值，与审计师签发质心对比，
产出 audit_logs/v57_batch_1_centroid_report.json。
专项检查：A-16（化水）R 轴为化气五格 Top1；A-19（魁罡）S 轴显著高于 A-01。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _signed_centroids() -> dict:
    """从 config/patterns/manifest_A14.json～manifest_A20.json 读取签发质心。"""
    out = {}
    for i in range(14, 21):
        pid = f"A-{i}"
        path = ROOT / "config" / "patterns" / f"manifest_A{i}.json"
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            c = data.get("centroid_5d")
            if c and len(c) == 5:
                out[pid] = [float(x) for x in c]
        except Exception:
            continue
    return out


def main():
    out_path = ROOT / "audit_logs" / "v57_batch_1_centroid_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)

    signed = _signed_centroids()
    if not signed:
        print("⚠️ 未找到任何签发质心（config/patterns/manifest_A14～A20.json）")
        report = {"schema": "FDS_V57_batch_1_centroid_audit", "error": "no_signed_centroids", "patterns": {}}
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        sys.exit(0)

    try:
        from core.database import get_physics
        physics = get_physics()
    except Exception as e:
        report = {
            "schema": "FDS_V57_batch_1_centroid_audit",
            "error": str(e),
            "signed_centroids": signed,
            "measured_centroids": {},
            "patterns": {},
        }
        out_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"⚠️ DuckDB 不可用: {e}，仅写入签发质心。")
        sys.exit(0)

    patterns = {}
    measured = {}
    for pid in [f"A-{i}" for i in range(14, 21)]:
        sc = signed.get(pid)
        cen = physics.get_centroid(pid)
        if cen is not None:
            mu, n = cen
            measured[pid] = {"centroid_5d": mu.tolist(), "sample_count": n}
        else:
            measured[pid] = None
        diff = None
        if sc and measured.get(pid) and measured[pid].get("centroid_5d"):
            mc = measured[pid]["centroid_5d"]
            diff = [round(mc[i] - sc[i], 4) for i in range(5)]
        m = measured.get(pid)
        patterns[pid] = {
            "signed_centroid_5d": sc,
            "measured_centroid_5d": m["centroid_5d"] if m else None,
            "measured_sample_count": (m["sample_count"] if m else 0),
            "delta_5d": diff,
        }

    # A-16 专项：R 轴在化气五格中是否为 Top1
    hua_ids = ["A-14", "A-15", "A-16", "A-17", "A-18"]
    r_vals = {}
    for pid in hua_ids:
        m = measured.get(pid)
        if m and m.get("centroid_5d"):
            r_vals[pid] = m["centroid_5d"][4]  # R 轴
    a16_r_top1 = False
    if r_vals and "A-16" in r_vals:
        r_max = max(r_vals.values())
        a16_r_top1 = r_vals["A-16"] >= r_max - 1e-6

    # A-19 专项：S 轴是否显著高于 A-01
    a19_s_above_a01 = None
    if measured.get("A-19") and measured["A-19"].get("centroid_5d"):
        s_a19 = measured["A-19"]["centroid_5d"][3]
        cen_a01 = physics.get_centroid("A-01")
        if cen_a01:
            s_a01 = cen_a01[0][3]
            a19_s_above_a01 = s_a19 > s_a01

    report = {
        "schema": "FDS_V57_batch_1_centroid_audit",
        "signed_centroids": signed,
        "measured_centroids": {k: (v.get("centroid_5d") if v else None) for k, v in measured.items()},
        "patterns": patterns,
        "audit_checks": {
            "A16_R_axis_top1_among_hua": bool(a16_r_top1),
            "A19_S_axis_above_A01": bool(a19_s_above_a01) if a19_s_above_a01 is not None else None,
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 质心审计报告已写入: {out_path}")
    if not a16_r_top1 and r_vals:
        print("⚠️ 审计提示: A-16（化水）R 轴未在化气五格中为 Top1，建议重审 L1/克神抑制。")
    if a19_s_above_a01 is False and measured.get("A-19"):
        print("⚠️ 审计提示: A-19（魁罡）S 轴未显著高于 A-01，建议重审。")
    sys.exit(0)


if __name__ == "__main__":
    main()
