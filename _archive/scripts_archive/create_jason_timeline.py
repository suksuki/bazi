#!/usr/bin/env python3
"""
创建 Jason 案例的财富时间轴数据
"""

import json
import os
from pathlib import Path

def create_jason_timeline():
    """
    Jason 案例：金融科技创业者
    八字: 戊午 癸亥 壬戌 丁未
    日主: 壬水
    结构特征: 身强用财官，日坐戌土财库
    """
    data = [
        {
            "id": "TIMELINE_JASON_WEALTH",
            "name": "Jason",
            "bazi": ["戊午", "癸亥", "壬戌", "丁未"],
            "gender": "男",
            "day_master": "壬",
            "description": "金融科技创业者，身强用财官，日坐戌土财库",
            "wealth_vaults": ["戌"],  # 戌为火库，火是壬水的财星
            "timeline": [
                {
                    "year": 2010,
                    "ganzhi": "庚寅",
                    "dayun": "甲子",  # 需要根据实际大运计算
                    "type": "WEALTH",
                    "real_magnitude": 100.0,  # 财富爆发
                    "desc": "【财富爆发】寅未暗合开启官库。流年庚金官杀透出，寅木食伤生财。"
                },
                {
                    "year": 2012,
                    "ganzhi": "壬辰",
                    "dayun": "甲子",  # 需要根据实际大运计算
                    "type": "WEALTH",
                    "real_magnitude": -80.0,  # 重大危机
                    "desc": "【重大危机】辰戌冲，财库坍塌。流年壬水比劫透出，但辰冲戌导致结构破坏。"
                }
            ]
        }
    ]
    
    # Ensure data directory exists
    project_root = Path(__file__).parent.parent
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    file_path = data_dir / 'jason_timeline.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Jason 财富时间轴数据已生成: {file_path}")
    print(f"   包含 {len(data[0]['timeline'])} 个财富事件")
    print()
    print("📋 案例信息：")
    print(f"   八字: {' '.join(data[0]['bazi'])}")
    print(f"   日主: {data[0]['day_master']}水")
    print(f"   财库: {', '.join(data[0]['wealth_vaults'])}")
    print()
    print("📅 关键事件：")
    for event in data[0]['timeline']:
        print(f"   {event['year']} ({event['ganzhi']}): {event['desc']}")
        print(f"      真实财富: {event['real_magnitude']:.1f}")

if __name__ == "__main__":
    create_jason_timeline()

