#!/usr/bin/env python3
"""
从原始数据文件中查找指定UID的四柱数据
用于更新演示案例
"""

import json
import sys
from pathlib import Path

def find_case_by_uid(data_file: str, target_uid: int):
    """
    从JSONL文件中查找指定UID的案例
    
    Args:
        data_file: 数据文件路径
        target_uid: 目标UID
    
    Returns:
        找到的案例数据，或None
    """
    if not Path(data_file).exists():
        print(f"❌ 数据文件不存在: {data_file}")
        return None
    
    print(f"查找UID {target_uid}...")
    line_count = 0
    
    with open(data_file, 'r', encoding='utf-8') as f:
        for line in f:
            line_count += 1
            if line_count % 50000 == 0:
                print(f"  已扫描: {line_count} 行...")
            
            try:
                data = json.loads(line.strip())
                # 检查uid字段（可能是uid或id）
                uid = data.get('uid') or data.get('id')
                if uid == target_uid:
                    print(f"\n✅ 找到UID {target_uid}!")
                    print(f"  行号: {line_count}")
                    
                    # 提取四柱
                    chart = data.get('chart') or data.get('bazi')
                    day_master = data.get('day_master', '')
                    
                    if chart:
                        if isinstance(chart, list):
                            year_pillar = chart[0] if len(chart) > 0 else ''
                            month_pillar = chart[1] if len(chart) > 1 else ''
                            day_pillar = chart[2] if len(chart) > 2 else ''
                            hour_pillar = chart[3] if len(chart) > 3 else ''
                        elif isinstance(chart, dict):
                            year_pillar = chart.get('year', '')
                            month_pillar = chart.get('month', '')
                            day_pillar = chart.get('day', '')
                            hour_pillar = chart.get('hour', '')
                        else:
                            year_pillar = month_pillar = day_pillar = hour_pillar = ''
                        
                        if not day_master and day_pillar:
                            day_master = day_pillar[0] if isinstance(day_pillar, str) and len(day_pillar) > 0 else ''
                        
                        result = {
                            'uid': target_uid,
                            'year_pillar': year_pillar,
                            'month_pillar': month_pillar,
                            'day_pillar': day_pillar,
                            'hour_pillar': hour_pillar,
                            'day_master': day_master,
                            'raw_data': data
                        }
                        
                        print(f"\n四柱数据:")
                        print(f"  year_pillar: '{year_pillar}'")
                        print(f"  month_pillar: '{month_pillar}'")
                        print(f"  day_pillar: '{day_pillar}'")
                        print(f"  hour_pillar: '{hour_pillar}'")
                        print(f"  day_master: '{day_master}'")
                        
                        return result
                    else:
                        print(f"  ⚠️ 该记录没有四柱数据")
                        return data
                        
            except json.JSONDecodeError:
                continue
    
    print(f"\n❌ 未找到UID {target_uid}")
    print(f"  总扫描行数: {line_count}")
    return None


if __name__ == '__main__':
    # 默认查找UID 486138（A-03最接近标准流形的案例）
    target_uid = int(sys.argv[1]) if len(sys.argv) > 1 else 486138
    data_file = sys.argv[2] if len(sys.argv) > 2 else 'core/data/holographic_universe_518k.jsonl'
    
    print(f"=== 查找UID {target_uid}的四柱数据 ===\n")
    result = find_case_by_uid(data_file, target_uid)
    
    if result and 'year_pillar' in result:
        print(f"\n✅ 找到完整数据！")
        print(f"\n更新演示案例的代码:")
        print(f"  'year_pillar': '{result['year_pillar']}',")
        print(f"  'month_pillar': '{result['month_pillar']}',")
        print(f"  'day_pillar': '{result['day_pillar']}',")
        print(f"  'hour_pillar': '{result['hour_pillar']}',")
        print(f"  'day_master': '{result['day_master']}',")
    elif result:
        print(f"\n⚠️ 找到数据但缺少四柱信息")
        print(f"  可能需要从其他数据源查找")
    else:
        print(f"\n提示: 如果数据文件不包含四柱信息，需要:")
        print(f"  1. 查找包含完整四柱数据的原始数据文件")
        print(f"  2. 或者使用select_samples方法生成符合格局定义的案例")

