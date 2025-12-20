#!/usr/bin/env python3
"""
V56.0 Step 1: Create Wealth Timeline Data
创建财富时间轴数据文件
"""
import json
import os

def create_wealth_dataset():
    data = [
        {
            "id": "TIMELINE_MUSK_WEALTH",
            "name": "Elon Musk",
            "bazi": ["辛亥", "甲午", "甲申", "甲子"],
            "gender": "男",
            "day_master": "甲",
            # 关键定义：甲木以土为财。辰戌丑未皆为财库。
            # 丑(Wet Earth) - 也是金库(官杀库)
            # 未(Dry Earth) - 木库(比劫库)
            # 戌(Dry Earth) - 火库(食伤库)
            # 辰(Wet Earth) - 水库(印库)
            "wealth_vaults": ["辰", "戌", "丑", "未"],
            "timeline": [
                {
                    "year": 1999,
                    "ganzhi": "己卯",
                    "dayun": "丁酉",
                    "type": "WEALTH",
                    "real_magnitude": 60.0,
                    "desc": "【第一桶金】Zip2获利。流年己土正财透出，卯木强根帮身任财。"
                },
                {
                    "year": 2002,
                    "ganzhi": "壬午",
                    "dayun": "丁酉",
                    "type": "WEALTH",
                    "real_magnitude": 80.0,
                    "desc": "【eBay收购】PayPal获利。午火食伤生财，壬水生身。"
                },
                {
                    "year": 2008,
                    "ganzhi": "戊子",
                    "dayun": "戊戌",
                    "type": "WEALTH",
                    "real_magnitude": -90.0,  # 破产边缘
                    "desc": "【破产危机】子午冲提纲。戊土偏财透出，但身弱不胜财(财多压身)。"
                },
                {
                    "year": 2021,
                    "ganzhi": "辛丑",
                    "dayun": "己亥",
                    "type": "WEALTH",
                    "real_magnitude": 100.0,  # 世界首富
                    "desc": "【登顶首富】大运亥水长生。流年辛丑，丑为金库/财库。关键在于'库'的引动与官印转化。"
                }
            ]
        }
    ]

    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    
    file_path = 'data/golden_timeline.json'
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 财富时间轴数据已生成: {file_path}")
    print(f"   包含 {len(data[0]['timeline'])} 个财富事件")

if __name__ == "__main__":
    create_wealth_dataset()
