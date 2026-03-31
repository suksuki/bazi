#!/usr/bin/env python3
"""
第 030 号工程指令：矩阵觉醒 — TMM 逻辑审计
============================================
利用 Qwen-32B 对十神→5D 张量映射矩阵 (TMM) 逐项进行语义审计，
输出合理性得分 (0-100) 与修改建议，并可选生成 V5.0-ALPHA 矩阵。

用法:
  python scripts/matrix_logic_auditor.py [--manifest config/patterns/manifest_A01.json] [--out results]
  python scripts/matrix_logic_auditor.py --generate-v5  # 根据审计报告生成 V5.0-ALPHA
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

# 全链路生效矩阵（第 021 号）：物理核心优先，与 tensor_mapping_loader 一致
PHYSICS_V4_PATH = ROOT / "config" / "physics" / "tensor_mapping_matrix_V4.0_BETA.json"
DEFAULT_MANIFEST_PATH = ROOT / "config" / "patterns" / "manifest_A01.json"

# 十神 / 维度 中文标签（审计提示用）
GOD_LABELS = {
    "ZG": "正官", "PG": "七杀", "ZR": "正财", "PR": "偏财",
    "ZS": "食神", "PS": "伤官", "ZC": "正印", "PC": "枭神",
    "ZB": "比肩", "PB": "劫财",
}
DIM_LABELS = {"E": "能量", "O": "秩序", "M": "财富", "S": "压力", "R": "关系"}


def load_tmm(manifest_path: Path) -> Dict[str, Any]:
    """从 manifest 或独立 TMM 文件加载矩阵（单文件）。"""
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tmm = data.get("tensor_mapping_matrix") if "tensor_mapping_matrix" in data else data
    if not tmm or not tmm.get("weights"):
        raise ValueError("tensor_mapping_matrix.weights not found")
    return tmm


def load_tmm_physics_first(manifest_path: Optional[Path] = None) -> Tuple[Dict[str, Any], Path, str]:
    """
    多级加载：优先 config/physics/tensor_mapping_matrix_V4.0_BETA.json（全链路生效），
    不存在时回退到 manifest（法律基准）。与 core/tensor_mapping_loader 策略一致。
    Returns:
        (tmm_dict, source_path, version)
    """
    manifest_path = manifest_path or DEFAULT_MANIFEST_PATH
    if PHYSICS_V4_PATH.exists():
        try:
            with open(PHYSICS_V4_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            tmm = data.get("tensor_mapping_matrix", data)
            if tmm and tmm.get("weights"):
                return tmm, PHYSICS_V4_PATH, data.get("version", "4.0-BETA")
        except Exception:
            pass
    if manifest_path.exists():
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        tmm = data.get("tensor_mapping_matrix")
        if tmm and tmm.get("weights"):
            return tmm, manifest_path, "3.0"
    raise FileNotFoundError(
        f"未找到 TMM：请确保存在 {PHYSICS_V4_PATH} 或 {manifest_path}"
    )


def get_ollama():
    try:
        import ollama
        return ollama.Client()
    except ImportError:
        return None


def audit_one_god(
    god: str,
    weights: List[float],
    dimensions: List[str],
    model: str = "qwen2.5:32b",
) -> Dict[str, Any]:
    """
    让 32B 对单个十神的 5 维权重进行审计，返回合理性得分与建议。
    """
    client = get_ollama()
    if not client:
        return {"god": god, "scores": {}, "suggestions": [], "error": "Ollama 不可用"}

    god_cn = GOD_LABELS.get(god, god)
    dims_cn = [DIM_LABELS.get(d, d) for d in dimensions]
    w_str = "、".join([f"{d}({dims_cn[i]}):{weights[i]:.2f}" for i, d in enumerate(dimensions)])

    sys_prompt = (
        "你是命理物理学家与古典命理专家。任务：评估「十神」与「五维命运流形」映射权重的合理性。"
        "五维含义：E=能量/身强身弱，O=秩序/官星约束，M=财富/财星，S=压力/应力，R=关系/智慧。"
        "请结合《渊海子平》《三命通会》等古籍中该十神的典型用法，给出每维权重的合理性得分(0-100)及一句话修改建议。"
        "必须按以下格式输出，便于程序解析：\n"
        "【得分】E:xx,O:xx,M:xx,S:xx,R:xx\n"
        "【建议】E:...; O:...; M:...; S:...; R:..."
    )
    user_prompt = (
        f"请审计「{god_cn}」({god}) 在当前 TMM 中对五维的权重：{w_str}。\n"
        "输出【得分】与【建议】两行，得分为 0-100 整数，建议为一句话。"
    )

    try:
        r = client.chat(
            model=model,
            messages=[
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": user_prompt},
            ],
            options={"num_predict": 400},
        )
        content = (r.get("message") or {}).get("content", "") if isinstance(r, dict) else ""
        if not content:
            return {"god": god, "scores": {}, "suggestions": [], "error": "模型返回空"}

        scores = {}
        suggestions = {}
        for line in content.split("\n"):
            line = line.strip()
            if line.startswith("【得分】"):
                # E:85,O:90,... 或 E: 85, O: 90
                for part in re.split(r"[,，]", line.replace("【得分】", "").strip()):
                    m = re.match(r"([EOMSR])\s*[:：]\s*(\d+)", part.strip(), re.I)
                    if m:
                        scores[m.group(1).upper()] = min(100, max(0, int(m.group(2))))
            if line.startswith("【建议】"):
                text = line.replace("【建议】", "").strip()
                for sep in [";", "；"]:
                    for part in text.split(sep):
                        m = re.match(r"([EOMSR])\s*[:：]\s*(.+)", part.strip(), re.I)
                        if m:
                            suggestions[m.group(1).upper()] = m.group(2).strip()

        return {
            "god": god,
            "god_cn": god_cn,
            "weights_current": weights,
            "scores": scores,
            "suggestions": suggestions,
            "raw_response": content[:500],
        }
    except Exception as e:
        return {"god": god, "scores": {}, "suggestions": [], "error": str(e)}


def run_full_audit(manifest_path: Optional[Path], out_dir: Path, model: str) -> Path:
    """对 10 个十神逐一审计，写入 report JSON。优先读取物理核心 V4.0-BETA。"""
    tmm, source_path, matrix_version = load_tmm_physics_first(manifest_path)
    gods = tmm.get("ten_gods", list(tmm["weights"].keys()))
    dims = tmm.get("dimensions", ["E", "O", "M", "S", "R"])
    weights = tmm["weights"]

    out_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "version": "1.0",
        "source_path": str(source_path),
        "matrix_version": matrix_version,
        "ten_gods": gods,
        "dimensions": dims,
        "audits": [],
        "weights_current": weights,
    }
    print(f"  读取矩阵: {source_path} (版本 {matrix_version})")

    for god in gods:
        w = weights.get(god)
        if not w or len(w) != 5:
            report["audits"].append({"god": god, "error": "权重缺失或长度非5"})
            continue
        print(f"  审计 {GOD_LABELS.get(god, god)} ({god})...")
        result = audit_one_god(god, w, dims, model=model)
        report["audits"].append(result)

    out_path = out_dir / "tmm_audit_report.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f"  已写入 {out_path}")
    return out_path


def generate_v5_alpha_from_audit(audit_path: Path, out_path: Path) -> Dict[str, List[float]]:
    """
    根据审计报告中的得分，对权重做微调生成 V5.0-ALPHA。
    策略：得分低于 70 的维度，按 (100-score)/100 比例向 0 方向收缩 20%；得分>=90 保持不变。
    """
    with open(audit_path, "r", encoding="utf-8") as f:
        report = json.load(f)
    weights_current = report.get("weights_current", {})
    dims = report.get("dimensions", ["E", "O", "M", "S", "R"])
    new_weights = {}

    for audit in report.get("audits", []):
        god = audit.get("god")
        if god not in weights_current or audit.get("error"):
            if god in weights_current:
                new_weights[god] = weights_current[god][:5]
            continue
        w_cur = weights_current[god][:5]
        scores = audit.get("scores", {})
        w_new = []
        for i, d in enumerate(dims):
            s = scores.get(d, 80)
            if s >= 90:
                w_new.append(w_cur[i])
            elif s < 70:
                # 低分：向 0 收缩 20%
                w_new.append(w_cur[i] * 0.8)
            else:
                # 70-89：轻微收缩
                w_new.append(w_cur[i] * (0.9 + 0.1 * (s - 70) / 20))
        new_weights[god] = [round(x, 4) for x in w_new]

    for g in weights_current:
        if g not in new_weights:
            new_weights[g] = [round(x, 4) for x in weights_current[g][:5]]

    payload = {
        "version": "5.0-ALPHA",
        "description": "由 matrix_logic_auditor 根据 32B 审计建议生成的实验矩阵",
        "ten_gods": report.get("ten_gods", list(new_weights.keys())),
        "dimensions": dims,
        "weights": new_weights,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  已生成 V5.0-ALPHA: {out_path}")
    return new_weights


def load_weights_from_path(path: Path) -> Tuple[Dict[str, List[float]], List[str], List[str]]:
    """从 manifest 或独立 TMM JSON 加载 weights, ten_gods, dimensions。"""
    with open(path, "r", encoding="utf-8") as f:
        d = json.load(f)
    tmm = d.get("tensor_mapping_matrix", d)
    w = tmm.get("weights", {})
    gods = tmm.get("ten_gods", list(w.keys()))
    dims = tmm.get("dimensions", ["E", "O", "M", "S", "R"])
    return w, gods, dims


def compare_tmm_sensitivity(
    manifest_or_v4_path: Path,
    v5_path: Path,
    num_samples: int = 50,
) -> Dict[str, float]:
    """
    对比两版矩阵在随机十神向量上的投影差异（L2 范数）。
    若存在 A-01 全量缓存，可基于其 ten_gods 做更真实对比；此处用随机向量近似。
    """
    import numpy as np

    w1, gods, dims = load_weights_from_path(manifest_or_v4_path)
    gods = tmm1.get("ten_gods", list(w1.keys()))
    dims = tmm1.get("dimensions", ["E", "O", "M", "S", "R"])

    if not v5_path.exists():
        return {"mean_l2_diff": 0.0, "max_l2_diff": 0.0, "note": "V5 file not found"}

    w2, _, _ = load_weights_from_path(v5_path)

    np.random.seed(42)
    diffs = []
    for _ in range(num_samples):
        vec = np.random.rand(len(gods)) * 2 - 0.5  # 十神向量
        p1 = np.zeros(len(dims))
        p2 = np.zeros(len(dims))
        for i, g in enumerate(gods):
            row1 = w1.get(g, [0] * len(dims))[: len(dims)]
            row2 = w2.get(g, row1)[: len(dims)]
            for j in range(len(dims)):
                p1[j] += vec[i] * (row1[j] if j < len(row1) else 0)
                p2[j] += vec[i] * (row2[j] if j < len(row2) else 0)
        diffs.append(float(np.linalg.norm(p1 - p2)))
    return {
        "mean_l2_diff": round(float(np.mean(diffs)), 4),
        "max_l2_diff": round(float(np.max(diffs)), 4),
        "num_samples": num_samples,
    }


def ensure_physics_v4_from_manifest(manifest_path: Path) -> Path:
    """若物理核心 V4 不存在，则从 manifest 生成一份，作为全链路生效矩阵的初始值。"""
    if PHYSICS_V4_PATH.exists():
        return PHYSICS_V4_PATH
    if not manifest_path.exists():
        raise FileNotFoundError(manifest_path)
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    tmm = data.get("tensor_mapping_matrix")
    if not tmm or not tmm.get("weights"):
        raise ValueError("manifest 中无 tensor_mapping_matrix.weights")
    PHYSICS_V4_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "4.0-BETA",
        "description": "由 manifest_A01 同步，作为全链路生效矩阵（第 021 号）",
        "ten_gods": tmm.get("ten_gods"),
        "dimensions": tmm.get("dimensions", ["E", "O", "M", "S", "R"]),
        "weights": tmm.get("weights"),
    }
    with open(PHYSICS_V4_PATH, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print(f"  已从 manifest 生成物理核心: {PHYSICS_V4_PATH}")
    return PHYSICS_V4_PATH


def main():
    parser = argparse.ArgumentParser(description="TMM 矩阵逻辑审计（第 030 号）")
    parser.add_argument("--manifest", type=Path, default=None, help="manifest 路径，仅在不使用物理核心时作回退或 --ensure-v4 时作源")
    parser.add_argument("--out", type=Path, default=ROOT / "results")
    parser.add_argument("--model", type=str, default="qwen2.5:32b")
    parser.add_argument("--generate-v5", action="store_true", help="根据已有审计报告生成 V5.0-ALPHA")
    parser.add_argument("--audit-report", type=Path, default=None, help="--generate-v5 时使用的报告路径")
    parser.add_argument("--compare", action="store_true", help="对比 V4 与 V5 敏感度")
    parser.add_argument("--ensure-v4", action="store_true", help="若 config/physics 下无 V4，则从 manifest 生成")
    parser.add_argument("--show", action="store_true", help="仅打印当前生效矩阵（物理优先）供 32B 第一印象")
    parser.add_argument("--first-impression", action="store_true", help="将当前矩阵发给 32B 请求一段「第一印象」评价")
    args = parser.parse_args()

    manifest_path = args.manifest or DEFAULT_MANIFEST_PATH
    if args.ensure_v4 and not PHYSICS_V4_PATH.exists():
        ensure_physics_v4_from_manifest(manifest_path)

    if args.show:
        tmm, source_path, ver = load_tmm_physics_first(manifest_path)
        print(f"# 当前生效矩阵来源: {source_path} (版本 {ver})\n")
        print(json.dumps({"ten_gods": tmm.get("ten_gods"), "dimensions": tmm.get("dimensions"), "weights": tmm.get("weights")}, ensure_ascii=False, indent=2))
        return

    if args.first_impression:
        tmm, source_path, ver = load_tmm_physics_first(manifest_path)
        client = get_ollama()
        if not client:
            print("Ollama 不可用，无法请求 32B 第一印象。")
            sys.exit(1)
        summary = json.dumps(tmm.get("weights", {}), ensure_ascii=False, indent=2)
        prompt = (
            "作为命理物理学家，请对下面这份「十神→五维(E/O/M/S/R)」映射权重矩阵给出你的「第一印象」："
            "是否符合古典命理中十神与秩序/能量/财富/压力/关系的对应？用 2～4 句话概括。\n\n"
            + summary
        )
        try:
            r = client.chat(model=args.model, messages=[{"role": "user", "content": prompt}], options={"num_predict": 300})
            content = (r.get("message") or {}).get("content", "") if isinstance(r, dict) else ""
            print(f"# 矩阵来源: {source_path} ({ver})\n\n【32B 第一印象】\n{content}")
        except Exception as e:
            print(f"第一印象请求失败: {e}")
        return

    if args.generate_v5:
        audit_path = args.audit_report or args.out / "tmm_audit_report.json"
        v5_path = ROOT / "config" / "physics" / "tensor_mapping_matrix_V5.0_ALPHA.json"
        if not audit_path.exists():
            print("  请先运行审计生成报告: python scripts/matrix_logic_auditor.py")
            sys.exit(1)
        generate_v5_alpha_from_audit(audit_path, v5_path)
        if args.compare:
            cmp = compare_tmm_sensitivity(PHYSICS_V4_PATH if PHYSICS_V4_PATH.exists() else manifest_path, v5_path)
            print("  敏感度对比 (随机向量 L2 差):", cmp)
        return

    run_full_audit(manifest_path, args.out, args.model)


if __name__ == "__main__":
    main()
