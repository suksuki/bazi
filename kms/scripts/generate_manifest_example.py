"""
FDS-KMS 配置生成示例脚本

演示如何使用聚合器生成pattern_manifest.json
"""

import json
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from kms.core.aggregator import Aggregator


def load_golden_test_data():
    """加载黄金测试数据"""
    data_path = os.path.join(os.path.dirname(__file__), '../data/golden_test_data.json')
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def main():
    """主函数：生成食神格的pattern_manifest.json"""
    
    print("=" * 60)
    print("FDS-KMS 配置生成示例")
    print("=" * 60)
    print()
    
    # 加载测试数据
    print("📚 加载黄金测试数据...")
    entries = load_golden_test_data()
    print(f"   加载了 {len(entries)} 条codex条目")
    print()
    
    # 显示条目信息
    for i, entry in enumerate(entries, 1):
        canon_id = entry.get("canon_id", "unknown")
        logic_type = entry.get("logic_extraction", {}).get("logic_type", "unknown")
        print(f"   [{i}] {canon_id}: {logic_type}")
    print()
    
    # 生成manifest
    print("🔧 生成pattern_manifest.json...")
    aggregator = Aggregator()
    
    manifest = aggregator.generate_manifest(
        pattern_id="B-01",
        pattern_name="食神格",
        entries=entries,
        version="3.0"
    )
    
    # 显示生成结果
    print("✅ 生成完成！")
    print()
    print("=" * 60)
    print("生成的manifest结构:")
    print("=" * 60)
    print(f"  pattern_id: {manifest['pattern_id']}")
    print(f"  version: {manifest['version']}")
    print(f"  logic_rules.format: {manifest['classical_logic_rules']['format']}")
    print(f"  logic_rules.expression: {json.dumps(manifest['classical_logic_rules']['expression'], indent=2, ensure_ascii=False)}")
    print()
    print(f"  tensor_mapping_matrix:")
    print(f"    ten_gods: {manifest['tensor_mapping_matrix']['ten_gods']}")
    print(f"    dimensions: {manifest['tensor_mapping_matrix']['dimensions']}")
    print(f"    weights: (10神 × 5维矩阵)")
    print(f"    strong_correlation: {len(manifest['tensor_mapping_matrix']['strong_correlation'])} 项")
    
    for sc in manifest['tensor_mapping_matrix']['strong_correlation']:
        print(f"      - {sc['ten_god']}-{sc['dimension']}: {sc['reason']}")
    print()
    
    # 保存到文件
    output_path = os.path.join(os.path.dirname(__file__), '../data/pattern_manifest_example.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    print(f"💾 已保存到: {output_path}")
    print()
    print("=" * 60)
    print("✅ 完成！")
    print("=" * 60)


if __name__ == "__main__":
    main()

