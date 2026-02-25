#!/usr/bin/env python3
"""
B 计划输出验证：在控制台打印 A-02 + A-03 混合案例的完整 Prompt 内容，
确保法理逻辑没有漂移（第 037 号工程指令）。
用法:
  python scripts/run_combined_pattern_prompt_demo.py           # 打印 Prompt 并调用 32B
  python scripts/run_combined_pattern_prompt_demo.py --prompt-only  # 仅打印 Prompt，不调 Ollama
"""
import argparse
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.ai_engine import generate_combined_pattern_verdict

def main():
    parser = argparse.ArgumentParser(description="混合格局判词 Prompt 验证")
    parser.add_argument("--prompt-only", action="store_true", help="仅打印完整 Prompt，不调用 Ollama")
    args = parser.parse_args()
    probabilistic_patterns = [
        {"pattern_id": "A-02", "confidence_pct": 85.0, "d_m": 1.2, "point_5d": {"E": 0.5, "O": 0.3, "M": 0.4, "S": 1.1, "R": 0.6}},
        {"pattern_id": "A-03", "confidence_pct": 15.0, "d_m": 2.1, "point_5d": {"E": 0.5, "O": 0.2, "M": 0.7, "S": 0.9, "R": 0.4}},
    ]
    point_5d = {"E": 0.5, "O": 0.28, "M": 0.45, "S": 1.05, "R": 0.55}
    repair_vector = {
        "delta_vector": {"E": 0.1, "O": -0.2, "M": -0.1, "S": 0.3, "R": -0.05},
        "target_delta_on_axis": 0.3,
    }
    print("正在生成混合格局判词并打印完整 Prompt（A-02 85% + A-03 15%）…\n")
    result = generate_combined_pattern_verdict(
        probabilistic_patterns=probabilistic_patterns,
        point_5d=point_5d,
        repair_vector=repair_vector,
        debug_print_prompt=True,
        prompt_only=args.prompt_only,
    )
    if args.prompt_only:
        print("\n✅ B 计划输出验证：完整 Prompt 已打印至控制台（--prompt-only，未调用 Ollama）。")
        return
    if result.get("success"):
        print("\n--- 32B 返回判词（片段）---")
        text = result.get("text") or ""
        print(text[:500] + "…" if len(text) > 500 else text)
    else:
        print("\n判词调用结果:", result.get("error", "未知错误"))
    print("\n✅ B 计划输出验证：完整 Prompt 已打印至控制台。")

if __name__ == "__main__":
    main()
