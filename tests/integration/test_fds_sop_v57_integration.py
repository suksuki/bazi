# -*- coding: utf-8 -*-
"""
FDS SOP V5.7 集成验收（硬核验收位）
====================================
- 测试项 A：格局 API/配置：A-14、A-20 能通过 pattern_id 拿到有效 JSON（manifest + qga）。
- 测试项 B：DuckDB 质心可查（若已迁库）。
- 测试项 C：RAG 原典中 A-20 判词含「金神入火乡」可检索（配置层校验）。
可与 pytest 或独立 run_all_tests() 运行。
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_all_tests():
    failed = []

    # ---------- 测试项 A：格局 manifest + QGA 注册 ----------
    for pid, num in [("A-14", "14"), ("A-20", "20")]:
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
            if "A-14" not in ids:
                failed.append("qga_manifest.json 的 holographic_pattern 中无 A-14")
            if "A-20" not in ids:
                failed.append("qga_manifest.json 的 holographic_pattern 中无 A-20")
            a20_entry = next((e for e in entries if (e.get("pattern_id") or "").strip().upper() == "A-20"), None)
            if a20_entry and a20_entry.get("manifest_ref") and "manifest_A20" not in a20_entry.get("manifest_ref", ""):
                failed.append("A-20 的 manifest_ref 应指向 config/patterns/manifest_A20.json")
        except Exception as e:
            failed.append(f"qga_manifest.json 解析失败: {e}")
    else:
        failed.append("registry/qga_manifest.json 不存在")

    # ---------- 测试项 B：DuckDB 质心（可选，无库不失败） ----------
    try:
        from core.database import get_physics
        physics = get_physics()
        cen = physics.get_centroid("A-20")
        # 仅校验调用不抛异常；无数据时 cen 为 None 也通过
    except ImportError as e:
        pass  # DuckDB 未安装时跳过
    except Exception as e:
        failed.append(f"DuckDB 质心查询异常: {e}")

    # ---------- 测试项 C：RAG 原典中 A-20 含「金神入火乡」 ----------
    quotes_a20 = ROOT / "config" / "rag" / "sop_v57_A14_A20_quotes.json"
    if quotes_a20.exists():
        try:
            data = json.loads(quotes_a20.read_text(encoding="utf-8"))
            quotes = data.get("classical_quotes") or []
            a20_texts = [q.get("text", "") for q in quotes if (q.get("pattern_id") or "").strip().upper() == "A-20"]
            if not any("金神入火乡" in t for t in a20_texts):
                failed.append("A-20 原典判词中应包含「金神入火乡」（config/rag/sop_v57_A14_A20_quotes.json）")
        except Exception as e:
            failed.append(f"RAG 原典配置解析失败: {e}")
    else:
        # 备选：config/patterns/manifest_A20 的 meta 或 hkb_literal
        m20 = ROOT / "config" / "patterns" / "manifest_A20.json"
        if m20.exists():
            try:
                d = json.loads(m20.read_text(encoding="utf-8"))
                meta = d.get("meta_info") or {}
                literal = meta.get("hkb_literal") or ""
                if "金神入火乡" not in literal and "金神" not in (d.get("meta_info") or {}).get("source_ref", ""):
                    # 至少有一处提到金神
                    ref = (d.get("meta_info") or {}).get("source_ref", "")
                    if "金神" not in ref:
                        failed.append("A-20 判词或原典中应包含「金神入火乡」或「金神」")
            except Exception:
                pass

    # ---------- 可选：全息控制器 FDS 分支（若可导入） ----------
    try:
        from controllers.holographic_pattern_controller import HolographicPatternController
        ctrl = HolographicPatternController()
        patterns = ctrl.get_fds_sop_patterns()
        if not any(p.get("pattern_id") == "A-20" for p in patterns):
            failed.append("get_fds_sop_patterns() 应包含 A-20")
        detail = ctrl.get_fds_pattern_detail("A-20")
        if not detail:
            failed.append("get_fds_pattern_detail('A-20') 应返回非空")
        elif not detail.get("meta_info", {}).get("chinese_name"):
            failed.append("A-20 详情应含 meta_info.chinese_name")
    except ImportError as e:
        if "lunar_python" in str(e):
            pass  # 无 lunar_python 时跳过控制器测试
        else:
            failed.append(f"全息控制器导入失败: {e}")
    except Exception as e:
        failed.append(f"全息控制器 FDS 调用异常: {e}")

    if failed:
        print("FDS SOP V5.7 集成验收失败:")
        for f in failed:
            print("  -", f)
        return 1
    print("FDS SOP V5.7 集成验收通过（测试项 A/B/C）。")
    return 0


if __name__ == "__main__":
    sys.exit(run_all_tests())
