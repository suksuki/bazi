#!/usr/bin/env python3
"""
V55.0 Step 1: Create Timeline Dataset
创建马斯克的时间线数据集用于回测
"""

import json
import os
from pathlib import Path

# 项目根目录
project_root = Path(__file__).parent.parent

# 时间线数据
timeline_data = [
    {
        "id": "TIMELINE_MUSK",
        "name": "Elon Musk",
        "bazi": ["辛亥", "甲午", "甲申", "甲子"],
        "gender": "男",
        "day_master": "甲",
        "true_structure": "Weak",
        "useful_god": ["水", "木"],
        "taboo_god": ["火", "土", "金"],
        "start_year": 1971,
        "timeline": [
            {
                "year": 1995,
                "ganzhi": "乙亥",
                "dayun": "丁酉",
                "event_type": "CAREER_START",
                "result": "GOOD",
                "desc": "创立 Zip2。流年乙亥(水木)帮身，喜神到位。"
            },
            {
                "year": 1999,
                "ganzhi": "己卯",
                "dayun": "丁酉",
                "event_type": "WEALTH_BOOM",
                "result": "GREAT",
                "desc": "出售 Zip2 获利。流年己卯，卯为甲木帝旺(强根)。身弱得强根，担财。"
            },
            {
                "year": 2000,
                "ganzhi": "庚辰",
                "dayun": "丁酉",
                "event_type": "CRISIS",
                "result": "BAD",
                "desc": "被踢出 PayPal，感染疟疾。流年庚金七杀透出攻身。辰土生金。杀重身轻。"
            },
            {
                "year": 2008,
                "ganzhi": "戊子",
                "dayun": "戊戌",
                "event_type": "DISASTER",
                "result": "TERRIBLE",
                "desc": "SpaceX 三次爆炸，特斯拉濒临破产，离婚。大运戊戌(财耗身)，流年戊子。子午冲(冲提纲)。水火交战，根基动摇。"
            },
            {
                "year": 2021,
                "ganzhi": "辛丑",
                "dayun": "己亥",
                "event_type": "WEALTH_PEAK",
                "result": "GREAT",
                "desc": "成为世界首富。大运亥水长生。流年辛丑，虽然是官杀库，但可能涉及特殊的'官印相生'或库的打开。"
            }
        ]
    }
]

# 确保 data 目录存在
data_dir = project_root / "data"
data_dir.mkdir(exist_ok=True)

# 写入文件
output_path = data_dir / "golden_timeline.json"
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(timeline_data, f, indent=2, ensure_ascii=False)

print(f"✅ 已创建时间线数据文件: {output_path}")
print(f"   包含 {len(timeline_data)} 个案例，共 {sum(len(case['timeline']) for case in timeline_data)} 个事件")

