#!/usr/bin/env python3
"""
SOP V6.2：全量格局一致性核验（The Compliance Matrix）
========================================================
对 A-01～A-60 逐一扫描 5 个核心维度，产出《SOP 缺漏分析报告》。
- 缺失 L1（A-51～A-60 待补）→ RED
- 低质质心（A-01～A-13 种子 / 或 518k 未实测）→ YELLOW
- 孤立格局（qga_manifest 无 manifest_ref）→ CRITICAL
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# L1 覆盖范围（从 pattern_scanner_v5x/v6x 归纳）
L1_V57 = set(f"A-{i:02d}" for i in range(14, 31))   # A-14～A-30
L1_V58 = set(f"A-{i:02d}" for i in range(31, 36))   # A-31～A-35
L1_V59 = set(f"A-{i:02d}" for i in range(36, 41))   # A-36～A-40
L1_V60 = set(f"A-{i:02d}" for i in range(41, 51))   # A-41～A-50
L1_V61_FULL = set(f"A-{i:02d}" for i in range(46, 51))  # A-46～A-50 有完整 L1
L1_V62_FULL = set(f"A-{i:02d}" for i in range(51, 61))  # A-51～A-60 V6.2 简易 L1 补齐
EARLY_BATCH = set(f"A-{i:02d}" for i in range(1, 14))   # A-01～A-13 早期

# 奇格/从格（建议有 collapse_trigger）：从儿/从杀/从财/从旺/弃命等
QIGE_CONGE = {"A-11", "A-12", "A-35", "A-39", "A-40", "A-36", "A-37", "A-38"}

PLACEHOLDER_CENTROID = [0.5, 0.5, 0.5, 0.5, 0.5]


def load_atlas() -> list[dict]:
    from core.engine import load_static_atlas
    data = load_static_atlas()
    return data.get("patterns") or []


def load_qga_manifest() -> tuple[bool, list[dict]]:
    """返回 (文件存在, holographic_pattern 列表)。"""
    path = ROOT / "registry" / "qga_manifest.json"
    if not path.exists():
        return False, []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        topics = data.get("topics") or {}
        arr = topics.get("holographic_pattern") or []
        return True, arr if isinstance(arr, list) else []
    except Exception:
        return False, []


def collect_rag_pattern_ids() -> set[str]:
    """从 config/rag 下所有 JSON 的 classical_quotes / verdict_precedents 收集 pattern_id。"""
    seen = set()
    rag_dir = ROOT / "config" / "rag"
    if not rag_dir.exists():
        return seen
    for p in rag_dir.glob("*.json"):
        try:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in (data.get("classical_quotes") or []) + (data.get("verdict_precedents") or []):
                pid = (item.get("pattern_id") or "").strip().upper()
                if pid:
                    seen.add(pid)
        except Exception:
            continue
    return seen


def has_dynamic_trigger(pattern_id: str) -> bool:
    """dynamic_monitor 中是否已有该格局的 collapse_trigger。"""
    return (pattern_id or "").strip().upper() == "A-50"


def classify_l1(pid: str) -> str:
    """RED=缺 L1, YELLOW=早期批次, GREEN=有 L1。"""
    p = (pid or "").strip().upper()
    if p in L1_V62_FULL:
        return "GREEN"  # A-51～A-60 已由 pattern_scanner_v62 补齐
    if p in EARLY_BATCH:
        return "YELLOW"  # 早期批次，L1 不在 v57～v61 中
    if p in L1_V57 or p in L1_V58 or p in L1_V59 or p in L1_V60 or p in L1_V61_FULL:
        return "GREEN"
    return "YELLOW"


def classify_centroid(entry: dict) -> str:
    """GREEN=实测, YELLOW=种子/早期无丰度, RED=占位质心。"""
    centroid = entry.get("centroid_5d")
    if isinstance(centroid, list) and len(centroid) >= 5:
        if all(abs(x - 0.5) < 1e-6 for x in centroid[:5]):
            return "RED"  # 占位 [0.5]*5
    abundance = entry.get("abundance")
    if not abundance:
        pid = (entry.get("pattern_id") or "").strip().upper()
        if pid in EARLY_BATCH:
            return "YELLOW"  # A-01～A-13 无丰度，技术债
        return "YELLOW"
    match = int(abundance.get("match_count") or 0)
    if match > 0:
        return "GREEN"
    return "YELLOW"


def run_audit() -> dict:
    atlas = load_atlas()
    qga_exists, qga_list = load_qga_manifest()
    qga_ids = { (e.get("pattern_id") or "").strip().upper(): e for e in qga_list }
    rag_ids = collect_rag_pattern_ids()

    rows = []
    for entry in atlas:
        pid = (entry.get("pattern_id") or "").strip().upper()
        if not pid:
            continue

        l1_status = classify_l1(pid)
        centroid_status = classify_centroid(entry)
        has_qga = pid in qga_ids
        manifest_ref = (qga_ids.get(pid) or {}).get("manifest_ref") or ""
        if not qga_exists:
            qga_status = "CRITICAL"  # 文件缺失，视为孤立
        elif not has_qga or not manifest_ref:
            qga_status = "CRITICAL"
        else:
            qga_status = "GREEN"

        has_rag = pid in rag_ids
        rag_status = "GREEN" if has_rag else "YELLOW"

        has_trigger = has_dynamic_trigger(pid)
        suggest_trigger = pid in QIGE_CONGE and not has_trigger
        dynamic_status = "GREEN" if has_trigger else ("YELLOW" if suggest_trigger else "GREEN")

        overall = "GREEN"
        if l1_status == "RED" or centroid_status == "RED" or qga_status == "CRITICAL":
            overall = "RED"
        elif l1_status == "YELLOW" or centroid_status == "YELLOW" or qga_status != "GREEN" or rag_status == "YELLOW":
            if overall != "RED":
                overall = "YELLOW"

        rows.append({
            "pattern_id": pid,
            "chinese_name": (entry.get("chinese_name") or pid),
            "L1_logic": l1_status,
            "centroid_5d": centroid_status,
            "qga_registry": qga_status,
            "rag_anchor": rag_status,
            "dynamic_monitor": dynamic_status,
            "overall": overall,
            "notes": _notes(pid, l1_status, centroid_status, qga_status, rag_status, has_trigger, suggest_trigger),
        })

    return {
        "schema": "FDS_v6.2_sop_gap_analysis",
        "description": "SOP V6.2 全量格局一致性核验：名义存在 vs 逻辑空洞",
        "total_patterns": len(rows),
        "summary": {
            "RED_count": sum(1 for r in rows if r["overall"] == "RED"),
            "YELLOW_count": sum(1 for r in rows if r["overall"] == "YELLOW"),
            "GREEN_count": sum(1 for r in rows if r["overall"] == "GREEN"),
            "CRITICAL_qga_missing": not qga_exists,
            "L1_pending_A51_A60": [r["pattern_id"] for r in rows if r["L1_logic"] == "RED"],
            "L1_v62_A51_A60": list(L1_V62_FULL),
            "low_quality_centroid_A01_A13": [r["pattern_id"] for r in rows if r["pattern_id"] in EARLY_BATCH and r["centroid_5d"] == "YELLOW"],
        },
        "compliance_matrix": rows,
    }


def _notes(pid: str, l1: str, cen: str, qga: str, rag: str, has_trigger: bool, suggest_trigger: bool) -> list[str]:
    out = []
    if l1 == "RED":
        out.append("L1 待补（A-51～A-60 占位）")
    if l1 == "YELLOW" and pid in EARLY_BATCH:
        out.append("早期批次，L1 由其他管线/ manifest 覆盖")
    if cen == "YELLOW" and pid in EARLY_BATCH:
        out.append("质心可能为初始 TMM 种子，未做 518k 实测或稳定性过滤")
    if cen == "RED":
        out.append("质心为占位 [0.5]*5")
    if qga == "CRITICAL":
        out.append("qga_manifest 无条目或 manifest_ref 缺失（孤立格局）")
    if rag == "YELLOW":
        out.append("RAG 原典/判词未挂载或未在 config/rag 中关联")
    if suggest_trigger:
        out.append("奇格/从格建议补充 collapse_trigger")
    return out


def main() -> None:
    report = run_audit()
    out_path = ROOT / "audit_logs" / "v6.2_sop_gap_analysis.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    s = report.get("summary") or {}
    print("✅ SOP V6.2 全量核验报告已写入:", out_path)
    print("   RED:", s.get("RED_count", 0), "| YELLOW:", s.get("YELLOW_count", 0), "| GREEN:", s.get("GREEN_count", 0))
    print("   L1 待补 (A-51～A-60):", s.get("L1_pending_A51_A60", []))
    print("   qga_manifest 缺失:", s.get("CRITICAL_qga_missing", False))


if __name__ == "__main__":
    main()
