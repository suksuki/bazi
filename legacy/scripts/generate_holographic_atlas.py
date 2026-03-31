#!/usr/bin/env python3
"""
FDS SOP V6.1：全量格局全息图谱
==============================
汇总 A-01～A-60 的质心、丰度、SOP 版本号，产出 atlas_v6.1_final.json。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _centroid_from_manifest(pid: str) -> list | None:
    num = pid.replace("A-", "").replace("-", "").strip()
    path = ROOT / "config" / "patterns" / f"manifest_A{num}.json"
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        c = data.get("centroid_5d")
        if c and len(c) == 5:
            return [float(x) for x in c]
    except Exception:
        pass
    return None


def _abundance_from_reports() -> dict:
    """从各批次丰度报告汇总 pattern_id -> match_count（若有）。"""
    out = {}
    # 已知报告路径
    reports = [
        ("v57_batch_1_abundance.json", list(range(14, 21))),
        ("v57_batch_2_abundance.json", list(range(21, 31))),
        ("v58_batch_3_abundance.json", list(range(31, 36))),
        ("v59_batch_4_abundance.json", list(range(36, 41))),
        ("v60_batch_5_abundance.json", list(range(41, 51))),
    ]
    for name, pids in reports:
        path = ROOT / "audit_logs" / name
        if not path.exists():
            continue
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            total = data.get("total_scanned") or 0
            for pr in data.get("pattern_results") or []:
                pid = (pr.get("pattern_id") or "").strip().upper()
                if not pid:
                    continue
                c = pr.get("match_count", 0)
                pct = (c / total * 100) if total else 0
                out[pid] = {"match_count": c, "percentage": round(pct, 4), "total_scanned": total}
        except Exception:
            continue
    return out


def _version_from_manifest(pid: str) -> str:
    num = pid.replace("A-", "").replace("-", "").strip()
    path = ROOT / "config" / "patterns" / f"manifest_A{num}.json"
    if not path.exists():
        return ""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return str(data.get("version", ""))
    except Exception:
        return ""


def _chinese_name_from_manifest(pid: str) -> str:
    num = pid.replace("A-", "").replace("-", "").strip()
    path = ROOT / "config" / "patterns" / f"manifest_A{num}.json"
    if not path.exists():
        return pid
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        meta = data.get("meta_info") or {}
        return meta.get("chinese_name") or meta.get("display_name") or pid
    except Exception:
        return pid


def main():
    physics = None
    try:
        from core.database import get_physics
        physics = get_physics()
    except Exception:
        pass

    abundance = _abundance_from_reports()
    atlas = {
        "schema": "FDS_atlas_v6.1_final",
        "description": "FDS 全量格局全息图谱（A-01～A-60）",
        "total_patterns": 60,
        "patterns": [],
    }

    for i in range(1, 61):
        pid = f"A-{i:02d}" if i < 10 else f"A-{i}"
        centroid = None
        if physics:
            cen = physics.get_centroid(pid)
            if cen:
                centroid = [round(float(x), 4) for x in cen[0]]
        if centroid is None:
            centroid = _centroid_from_manifest(pid)
        if centroid is None:
            centroid = [0.0, 0.0, 0.0, 0.0, 0.0]
        if len(centroid) != 5:
            centroid = (list(centroid) + [0.0] * 5)[:5]
        entry = {
            "pattern_id": pid,
            "chinese_name": _chinese_name_from_manifest(pid),
            "centroid_5d": centroid,
            "dimensions": DIM_ORDER,
            "sop_version": _version_from_manifest(pid),
        }
        if pid in abundance:
            entry["abundance"] = abundance[pid]
        atlas["patterns"].append(entry)

    if physics:
        try:
            physics.close()
        except Exception:
            pass

    out_path = ROOT / "audit_logs" / "atlas_v6.1_final.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(atlas, f, ensure_ascii=False, indent=2)
    print(f"📄 《FDS 全量格局全息图谱》已写入: {out_path}")
    print(f"   共 {len(atlas['patterns'])} 个格局（A-01～A-60）。")
    sys.exit(0)


if __name__ == "__main__":
    main()
