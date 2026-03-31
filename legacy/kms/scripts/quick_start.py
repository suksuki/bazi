"""
FDS-KMS 快速开始脚本

一键演示完整的KMS工作流：
1. 加载黄金测试数据
2. 生成pattern_manifest.json
3. 显示结果
"""

import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kms.core.aggregator import Aggregator


def main():
    """快速开始演示"""
    
    print("🚀 FDS-KMS 快速开始")
    print("=" * 60)
    print()
    
    # 1. 加载黄金测试数据
    print("📚 步骤1: 加载黄金测试数据...")
    data_path = os.path.join(os.path.dirname(__file__), '../data/golden_test_data.json')
    
    with open(data_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    print(f"   ✅ 加载了 {len(entries)} 条codex条目")
    for i, entry in enumerate(entries, 1):
        canon_id = entry.get("canon_id", "unknown")
        logic_type = entry.get("logic_extraction", {}).get("logic_type", "unknown")
        print(f"      [{i}] {canon_id}: {logic_type}")
    print()
    
    # 2. 生成manifest
    print("🔧 步骤2: 生成pattern_manifest.json...")
    aggregator = Aggregator()
    
    manifest = aggregator.generate_manifest(
        pattern_id="B-01",
        pattern_name="食神格",
        entries=entries,
        version="3.0"
    )
    
    print("   ✅ Manifest生成完成")
    print()
    
    # 3. 显示关键信息
    print("📊 步骤3: 分析生成结果...")
    print()
    
    # 逻辑规则统计
    logic_expr = manifest['classical_logic_rules']['expression']
    and_count = len(logic_expr.get('and', []))
    print(f"   📋 逻辑规则:")
    print(f"      - AND分支数量: {and_count}")
    
    # 权重矩阵统计
    weights = manifest['tensor_mapping_matrix']['weights']
    non_zero_count = sum(
        1 for ten_god in weights.values()
        for w in ten_god
        if abs(w) > 0.01
    )
    print(f"   📊 权重矩阵:")
    print(f"      - 非零权重数量: {non_zero_count}/50")
    
    # 强相关统计
    strong_corr = manifest['tensor_mapping_matrix']['strong_correlation']
    print(f"   🔒 锁定权重:")
    print(f"      - 强相关标记: {len(strong_corr)} 项")
    for sc in strong_corr:
        print(f"        • {sc['ten_god']}-{sc['dimension']}: {sc['reason']}")
    print()
    
    # 4. 保存结果
    print("💾 步骤4: 保存结果...")
    output_path = os.path.join(os.path.dirname(__file__), '../data/pattern_manifest_example.json')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 已保存到: {output_path}")
    print()
    
    # 5. 验证结果
    print("✅ 步骤5: 验证结果...")
    
    # 检查必需字段
    required = ['pattern_id', 'version', 'classical_logic_rules', 'tensor_mapping_matrix']
    missing = [f for f in required if f not in manifest]
    
    if missing:
        print(f"   ❌ 缺少字段: {missing}")
    else:
        print("   ✅ 所有必需字段存在")
    
    # 检查权重范围
    all_weights = [w for ten_god in weights.values() for w in ten_god]
    out_of_range = [w for w in all_weights if not (-1.0 <= w <= 1.0)]
    
    if out_of_range:
        print(f"   ❌ 权重超出范围: {len(out_of_range)} 个")
    else:
        print("   ✅ 所有权重在 [-1.0, 1.0] 范围内")
    
    print()
    print("=" * 60)
    print("🎉 完成！FDS-KMS系统运行正常")
    print("=" * 60)
    print()
    print("📝 下一步建议:")
    print("   1. 查看生成的manifest: kms/data/pattern_manifest_example.json")
    print("   2. 准备更多古籍文本，使用语义蒸馏器处理")
    print("   3. 建立向量索引库")
    print("   4. 集成到SOP工作流")


if __name__ == "__main__":
    main()

