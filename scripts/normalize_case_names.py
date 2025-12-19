#!/usr/bin/env python3
"""
规范化校准案例名称脚本
====================

功能：
1. 为缺少名称的案例添加名称
2. 规范化CELEB案例的名称格式
3. 统一命名格式：中文名 (English Name)

使用方法：
    python3 scripts/normalize_case_names.py
"""

import json
import sys
from pathlib import Path
from typing import Dict, List

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# CELEB案例的名称映射（基于特征和八字推断，或使用通用名称）
CELEB_NAME_MAPPING = {
    "STRENGTH_013": "测试案例_013 (Test Case 013)",
    "STRENGTH_014": "测试案例_014 (Test Case 014)",
    "STRENGTH_015": "测试案例_015 (Test Case 015)",
    "STRENGTH_016": "测试案例_016 (Test Case 016)",
    "STRENGTH_017": "测试案例_017 (Test Case 017)",
    "STRENGTH_018": "测试案例_018 (Test Case 018)",
    "STRENGTH_019": "测试案例_019 (Test Case 019)",
    "STRENGTH_020": "测试案例_020 (Test Case 020)",
    "STRENGTH_021": "测试案例_021 (Test Case 021)",
    "STRENGTH_022": "测试案例_022 (Test Case 022)",
    "STRENGTH_023": "测试案例_023 (Test Case 023)",
    "STRENGTH_024": "测试案例_024 (Test Case 024)",
    "STRENGTH_025": "测试案例_025 (Test Case 025)",
    "STRENGTH_026": "测试案例_026 (Test Case 026)",
    "STRENGTH_027": "测试案例_027 (Test Case 027)",
    "STRENGTH_028": "测试案例_028 (Test Case 028)",
    "STRENGTH_029": "测试案例_029 (Test Case 029)",
    "STRENGTH_030": "测试案例_030 (Test Case 030)",
    "STRENGTH_031": "测试案例_031 (Test Case 031)",
    "STRENGTH_032": "测试案例_032 (Test Case 032)",
    "STRENGTH_033": "测试案例_033 (Test Case 033)",
    "STRENGTH_034": "测试案例_034 (Test Case 034)",
    "STRENGTH_035": "测试案例_035 (Test Case 035)",
    "STRENGTH_036": "测试案例_036 (Test Case 036)",
}

# 已知案例的标准名称映射（用于规范化现有名称）
STANDARD_NAME_MAPPING = {
    "STRENGTH_REAL_001": "乾隆皇帝 (Emperor Qianlong)",
    "STRENGTH_REAL_002": "埃隆·马斯克 (Elon Musk)",
    "STRENGTH_REAL_003": "唐纳德·特朗普 (Donald Trump)",
    "STRENGTH_REAL_004": "史蒂夫·乔布斯 (Steve Jobs)",
    "STRENGTH_REAL_005": "阿尔伯特·爱因斯坦 (Albert Einstein)",
    "STRENGTH_REAL_006": "迈克尔·乔丹 (Michael Jordan)",
    "STRENGTH_REAL_007": "沃伦·巴菲特 (Warren Buffett)",
    "STRENGTH_REAL_008": "玛丽莲·梦露 (Marilyn Monroe)",
    "STRENGTH_REAL_009": "比尔·盖茨 (Bill Gates)",
    "STRENGTH_REAL_010": "戴安娜王妃 (Princess Diana)",
    "STRENGTH_REAL_011": "李小龙 (Bruce Lee)",
    "STRENGTH_REAL_012": "李嘉诚 (Li Ka-shing)",
    "STRENGTH_REAL_013": "弗拉基米尔·普京 (Vladimir Putin)",
    "STRENGTH_REAL_014": "阿道夫·希特勒 (Adolf Hitler)",
    "STRENGTH_REAL_015": "Jason E (极弱原型)",
    # C06案例：根据特征描述，这是一个极度身弱的测试案例
    "C06": "测试案例_C06_极弱身弱 (Test Case C06 - Extreme Weak)",
}


def normalize_case_name(case: Dict) -> str:
    """
    规范化案例名称
    
    Args:
        case: 案例字典
        
    Returns:
        规范化后的名称
    """
    case_id = case.get('id', '')
    current_name = case.get('name', '').strip()
    
    # 1. 如果已有标准名称映射，直接使用
    if case_id in STANDARD_NAME_MAPPING:
        return STANDARD_NAME_MAPPING[case_id]
    
    # 2. 如果是CELEB案例，使用映射表
    if case_id in CELEB_NAME_MAPPING:
        return CELEB_NAME_MAPPING[case_id]
    
    # 3. 如果当前名称为Unknown或空，尝试从ID推断
    if not current_name or current_name == 'Unknown':
        # 已经在STANDARD_NAME_MAPPING中处理，这里不再需要
        # 如果无法推断，使用ID作为名称
        return f"测试案例_{case_id} (Test Case {case_id})"
    
    # 4. 如果名称格式不规范，尝试规范化
    # 例如：如果只有英文名，添加中文名占位符
    # 这里可以根据实际需求添加更多规范化逻辑
    
    return current_name


def normalize_all_cases(input_file: str, output_file: str = None, dry_run: bool = False):
    """
    规范化所有案例的名称
    
    Args:
        input_file: 输入文件路径
        output_file: 输出文件路径（如果为None，则覆盖原文件）
        dry_run: 是否为试运行模式（不实际修改文件）
    """
    if output_file is None:
        output_file = input_file
    
    # 读取文件
    with open(input_file, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    
    changes = []
    
    # 规范化每个案例
    for case in cases:
        case_id = case.get('id', 'Unknown')
        old_name = case.get('name', '').strip()
        new_name = normalize_case_name(case)
        
        if old_name != new_name:
            changes.append({
                'id': case_id,
                'old_name': old_name if old_name else '(empty)',
                'new_name': new_name
            })
            case['name'] = new_name
    
    # 显示变更
    if changes:
        print(f"\n{'=' * 80}")
        print(f"发现 {len(changes)} 个需要规范化的案例:")
        print('=' * 80)
        for change in changes:
            print(f"ID: {change['id']:25s}")
            print(f"  旧名称: {change['old_name']}")
            print(f"  新名称: {change['new_name']}")
            print()
        
        if not dry_run:
            # 保存文件
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(cases, f, ensure_ascii=False, indent=2)
            print(f"✅ 已保存到: {output_file}")
        else:
            print("⚠️  试运行模式，未实际修改文件")
    else:
        print("✅ 所有案例名称已规范化，无需修改")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='规范化校准案例名称')
    parser.add_argument('--input', type=str, default='data/calibration_cases.json',
                       help='输入文件路径')
    parser.add_argument('--output', type=str, default=None,
                       help='输出文件路径（如果为None，则覆盖原文件）')
    parser.add_argument('--dry-run', action='store_true',
                       help='试运行模式，不实际修改文件')
    
    args = parser.parse_args()
    
    normalize_all_cases(args.input, args.output, args.dry_run)

