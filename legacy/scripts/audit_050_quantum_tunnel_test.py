#!/usr/bin/env python3
"""
EDR-050：A-21→A-22 量子隧道测试（从强格在岁运坏印下的断裂式坍缩）
======================================================================
取一例 L1 从强格，施加「坏印」扰动（财官杀增强、印比减弱），观测 5D 与 D_M 从 A-21 向 A-22 的跳变，
并输出 collision_meta 中 PATH_A21_TO_A22_CRASH 的判词。
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import numpy as np

DIM_ORDER = ["E", "O", "M", "S", "R"]


def _load_v4_tmm():
    v4 = ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
    if not v4.exists():
        return None, None
    with open(v4, "r", encoding="utf-8") as f:
        data = json.load(f)
    gods = data.get("ten_gods") or []
    weights = data.get("weights") or {}
    if not gods or not weights:
        return None, None
    matrix = np.array([weights.get(g, [0] * 5) for g in gods], dtype=np.float64)
    return matrix, gods


def _ten_gods_to_5d(ten_gods: dict, weights: np.ndarray, god_index: dict) -> np.ndarray:
    vec = np.zeros(weights.shape[0])
    for g, idx in god_index.items():
        val = ten_gods.get(g, 0)
        if isinstance(val, dict):
            val = val.get("mean", val.get("strength", 0))
        vec[idx] = float(val) if val is not None else 0.0
    return np.dot(weights.T, vec)


def _get_centroid(pid: str, physics=None) -> np.ndarray | None:
    """优先 DuckDB，否则 config/patterns manifest 签发质心。"""
    if physics:
        cen = physics.get_centroid(pid)
        if cen is not None:
            return cen[0]
    path = ROOT / "config" / "patterns" / f"manifest_{pid.replace('-', '')}.json"
    if path.exists():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            c = data.get("centroid_5d")
            if c and len(c) == 5:
                return np.array([float(x) for x in c], dtype=np.float64)
        except Exception:
            pass
    return None


def _euclidean(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.linalg.norm(a - b))


def main():
    weights, gods = _load_v4_tmm()
    if weights is None or gods is None:
        print("⚠️ 未找到 V4 矩阵，无法计算 5D")
        sys.exit(1)
    god_index = {g: i for i, g in enumerate(gods)}

    physics = None
    try:
        from core.database import get_physics
        physics = get_physics()
    except Exception:
        pass

    mu_a21 = _get_centroid("A-21", physics)
    mu_a22 = _get_centroid("A-22", physics)
    if mu_a21 is None or mu_a22 is None:
        print("⚠️ 缺少 A-21 或 A-22 质心（DuckDB 或 config/patterns）")
        sys.exit(1)

    # 从 518k 取一例 L1 从强
    from pattern_scanner_v57 import l1_match_a21_through_a30

    data_path = ROOT / "data" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        data_path = ROOT / "data_local" / "holographic_universe_518k.jsonl"
    if not data_path.exists():
        print("⚠️ 未找到 518k 数据，使用合成从强 ten_gods")
        # 合成：印比主导
        base_ten_gods = {
            "ZG": 0.1, "PG": 0.1, "ZR": 0.35, "PR": 0.35, "ZS": 0.02, "PS": 0.02,
            "ZC": 0.02, "PC": 0.02, "ZB": 0.01, "PB": 0.01,
        }
        case_ref = "synthetic_cong_qiang"
    else:
        base_ten_gods = None
        case_ref = None
        with open(data_path, "r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    case = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not case.get("bazi") or not case.get("ten_gods"):
                    continue
                matched = l1_match_a21_through_a30(case)
                if "A-21" not in matched or "A-22" in matched:
                    continue
                raw = case.get("ten_gods") or {}
                base_ten_gods = {}
                for k, v in raw.items():
                    if isinstance(v, dict):
                        base_ten_gods[k] = float(v.get("mean", v.get("strength", 0)))
                    else:
                        base_ten_gods[k] = float(v) if v is not None else 0.0
                case_ref = case.get("uid") or case.get("id") or f"line_{i}"
                break
        if base_ten_gods is None:
            base_ten_gods = {
                "ZG": 0.1, "PG": 0.1, "ZR": 0.35, "PR": 0.35, "ZS": 0.02, "PS": 0.02,
                "ZC": 0.02, "PC": 0.02, "ZB": 0.01, "PB": 0.01,
            }
            case_ref = "synthetic_cong_qiang"

    # 原局 5D 与 D_M
    pt_before = _ten_gods_to_5d(base_ten_gods, weights, god_index)
    d21_before = _euclidean(pt_before, mu_a21)
    d22_before = _euclidean(pt_before, mu_a22)
    s_before = float(pt_before[3])

    # 扰动：坏印（减弱印比、增强财官杀）
    perturbed = {k: float(v) for k, v in base_ten_gods.items()}
    for k in ("ZR", "PR", "ZB", "PB"):
        perturbed[k] = max(0.0, perturbed.get(k, 0) * 0.4)
    for k in ("ZG", "PG", "ZS", "PS", "ZC", "PC"):
        perturbed[k] = perturbed.get(k, 0) * 1.5
    total = sum(perturbed.values()) or 1.0
    perturbed = {k: v / total for k, v in perturbed.items()}

    pt_after = _ten_gods_to_5d(perturbed, weights, god_index)
    d21_after = _euclidean(pt_after, mu_a21)
    d22_after = _euclidean(pt_after, mu_a22)
    s_after = float(pt_after[3])

    # 判词
    collision_meta_path = ROOT / "config" / "rag" / "collision_meta.json"
    verdict = ""
    if collision_meta_path.exists():
        try:
            meta = json.loads(collision_meta_path.read_text(encoding="utf-8"))
            path_meta = (meta.get("paths") or {}).get("PATH_A21_TO_A22_CRASH") or {}
            verdict = path_meta.get("verdict_template", verdict)
        except Exception:
            pass
    if not verdict:
        verdict = "大厦将倾，弃守为上。岁运克泄交加，身局由强转弱，宜顺势而为，勿逆势硬扛。"

    # 跳变判定：扰动后更近 A-22 且更远 A-21
    jumped = d22_after < d21_after and d21_after > d21_before
    s_rise = s_after > s_before
    # S 应力比：S_after / S_before，审计要求 > 2.5 为应力增幅
    s_before_safe = max(s_before, 1e-9)
    s_stress_ratio = round(float(s_after) / s_before_safe, 4)
    # 坍缩/跳变时置为 PATH_A21_TO_A22_CRASH
    collision_type = "PATH_A21_TO_A22_CRASH" if jumped else ""

    report = {
        "schema": "EDR_050_quantum_tunnel",
        "case_ref": case_ref,
        "before": {
            "point_5d": pt_before.tolist(),
            "D_M_to_A21": round(d21_before, 4),
            "D_M_to_A22": round(d22_before, 4),
            "S_axis": round(s_before, 4),
        },
        "after_perturbation": {
            "point_5d": pt_after.tolist(),
            "D_M_to_A21": round(d21_after, 4),
            "D_M_to_A22": round(d22_after, 4),
            "S_axis": round(s_after, 4),
        },
        "observations": {
            "jumped_to_A22_capture_zone": jumped,
            "S_axis_rising": s_rise,
            "delta_S": round(s_after - s_before, 4),
            "S_stress_ratio": s_stress_ratio,
            "Collision_Type": collision_type,
        },
        "verdict": verdict,
    }

    out_path = ROOT / "audit_logs" / "edr_050_quantum_tunnel_report.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"📄 报告已写入: {out_path}")
    print(f"  原局 D_M(A-21)={d21_before:.3f}  D_M(A-22)={d22_before:.3f}  S={s_before:.3f}")
    print(f"  扰动后 D_M(A-21)={d21_after:.3f}  D_M(A-22)={d22_after:.3f}  S={s_after:.3f}")
    print(f"  跳入 A-22 捕获区: {jumped}  S 轴上升: {s_rise}")
    print(f"  判词: {verdict[:50]}...")
    sys.exit(0)


if __name__ == "__main__":
    main()
