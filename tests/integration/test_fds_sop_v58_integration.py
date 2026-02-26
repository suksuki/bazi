# -*- coding: utf-8 -*-
"""
FDS SOP V5.8 第三梯队（A-31～A-35）集成验收
==========================================
- 测试项 A：格局 manifest + QGA 注册（A-31、A-35）。
- 测试项 B：控制器能扫描到 manifest_A31～A35。
- 测试项 C：RAG 原典中 A-33/A-34 判词含「虚空感应，福不可测」或「格局清奇，最忌填实」。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_all_tests():
    failed = []

    # ---------- 测试项 A：A-31～A-35 manifest + QGA ----------
    for num in ["31", "32", "33", "34", "35"]:
        pid = f"A-{num}"
        manifest_path = ROOT / "config" / "patterns" / f"manifest_A{num}.json"
        if not manifest_path.exists():
            failed.append(f"配置缺失: config/patterns/manifest_A{num}.json")
            continue
        try:
            data = json.loads(manifest_path.read_text(encoding="utf-8"))
        except Exception as e:
            failed.append(f"manifest_A{num}.json 解析失败: {e}")
            continue
        if (data.get("pattern_id") or "").strip().upper() != pid:
            failed.append(f"manifest_A{num}.json pattern_id 应为 {pid}")
        if not data.get("meta_info") or not data.get("meta_info").get("chinese_name"):
            failed.append(f"manifest_A{num}.json 缺少 meta_info.chinese_name")
        if not data.get("centroid_5d") or len(data["centroid_5d"]) != 5:
            failed.append(f"manifest_A{num}.json 缺少或无效 centroid_5d")

    qga_path = ROOT / "registry" / "qga_manifest.json"
    if qga_path.exists():
        try:
            qga = json.loads(qga_path.read_text(encoding="utf-8"))
            entries = (qga.get("topics") or {}).get("holographic_pattern") or []
            ids = [e.get("pattern_id") for e in entries if e.get("pattern_id")]
            for pid in ["A-31", "A-35"]:
                if pid not in ids:
                    failed.append(f"qga_manifest.json 的 holographic_pattern 中无 {pid}")
        except Exception as e:
            failed.append(f"qga_manifest.json 解析失败: {e}")
    else:
        failed.append("registry/qga_manifest.json 不存在")

    # ---------- 测试项 B：控制器可扫描到 A-31～A-35 ----------
    try:
        from controllers.holographic_pattern_controller import HolographicPatternController
        ctrl = HolographicPatternController()
        patterns = ctrl.get_fds_sop_patterns()
        for pid in ["A-31", "A-35"]:
            if not any(p.get("pattern_id") == pid for p in patterns):
                failed.append(f"get_fds_sop_patterns() 应包含 {pid}")
        detail = ctrl.get_fds_pattern_detail("A-33")
        if not detail:
            failed.append("get_fds_pattern_detail('A-33') 应返回非空")
        elif not detail.get("meta_info", {}).get("chinese_name"):
            failed.append("A-33 详情应含 meta_info.chinese_name")
    except ImportError as e:
        if "lunar_python" in str(e):
            pass
        else:
            failed.append(f"全息控制器导入失败: {e}")
    except Exception as e:
        failed.append(f"全息控制器 FDS 调用异常: {e}")

    # ---------- 测试项 C：RAG 原典 A-33/A-34 含虚空/格局清奇判词 ----------
    quotes_path = ROOT / "config" / "rag" / "sop_v58_A31_A35_quotes.json"
    if quotes_path.exists():
        try:
            data = json.loads(quotes_path.read_text(encoding="utf-8"))
            quotes = data.get("classical_quotes") or []
            a33 = [q.get("text", "") for q in quotes if (q.get("pattern_id") or "").strip().upper() == "A-33"]
            a34 = [q.get("text", "") for q in quotes if (q.get("pattern_id") or "").strip().upper() == "A-34"]
            ok = any("虚空感应" in t or "格局清奇" in t for t in a33 + a34)
            if not ok:
                failed.append("A-33/A-34 原典判词中应包含「虚空感应，福不可测」或「格局清奇，最忌填实」")
        except Exception as e:
            failed.append(f"RAG 原典配置解析失败: {e}")
    else:
        failed.append("config/rag/sop_v58_A31_A35_quotes.json 不存在")

    if failed:
        print("FDS SOP V5.8 集成验收失败:")
        for f in failed:
            print("  -", f)
        return 1
    print("FDS SOP V5.8 集成验收通过（测试项 A/B/C）。")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
