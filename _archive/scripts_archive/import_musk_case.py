#!/usr/bin/env python3
"""
导入Musk案例到新的MVC系统
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.bazi_profile import BaziProfile
from datetime import datetime

def get_year_ganzhi(year):
    """根据年份计算流年干支"""
    GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    gan_index = (year - 4) % 10
    zhi_index = (year - 4) % 12
    return GAN[gan_index] + ZHI[zhi_index]

def calculate_dayun(profile, year):
    """计算指定年份的大运"""
    try:
        dayun = profile.get_luck_pillar_at(year)
        if dayun and isinstance(dayun, str) and len(dayun) >= 2:
            return dayun
    except:
        pass
    return '甲子'  # 默认值

def main():
    """主函数"""
    print("=" * 80)
    print("📥 导入Musk案例到MVC系统")
    print("=" * 80)
    print()
    
    # 1. 尝试从旧文件加载
    old_data_path = project_root / 'data' / 'golden_timeline.json'
    musk_data = None
    
    if old_data_path.exists():
        print("📂 从旧文件加载Musk案例...")
        with open(old_data_path, 'r', encoding='utf-8') as f:
            cases = json.load(f)
            if cases and len(cases) > 0:
                musk_data = cases[0]
                print(f"✅ 找到Musk案例: {musk_data.get('name', 'Unknown')}")
    else:
        print("⚠️ 旧文件不存在，使用默认数据...")
        # 使用默认数据
        musk_data = {
            "id": "TIMELINE_MUSK_WEALTH",
            "name": "Elon Musk",
            "bazi": ["辛亥", "甲午", "甲申", "甲子"],
            "gender": "男",
            "day_master": "甲",
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
                    "real_magnitude": -90.0,
                    "desc": "【破产危机】子午冲提纲。戊土偏财透出，但身弱不胜财(财多压身)。"
                },
                {
                    "year": 2021,
                    "ganzhi": "辛丑",
                    "dayun": "己亥",
                    "type": "WEALTH",
                    "real_magnitude": 100.0,
                    "desc": "【登顶首富】大运亥水长生。流年辛丑，丑为金库/财库。关键在于'库'的引动与官印转化。"
                }
            ]
        }
    
    if not musk_data:
        print("❌ 无法加载Musk案例数据")
        return
    
    # 2. 创建BaziProfile计算大运
    # Musk出生日期：1971年6月28日，假设辰时（7:30）
    try:
        profile = BaziProfile(datetime(1971, 6, 28, 7, 30), 1)  # 男性
        print("✅ BaziProfile创建成功")
    except Exception as e:
        print(f"⚠️ BaziProfile创建失败: {e}，将使用默认大运")
        profile = None
    
    # 3. 转换格式
    print()
    print("🔄 转换数据格式...")
    
    # 结果映射（兼容旧格式的result字段）
    result_to_magnitude = {
        "TERRIBLE": -90.0,
        "BAD": -50.0,
        "GOOD": 60.0,
        "GREAT": 100.0
    }
    
    # 正确的real_magnitude值（如果数据中没有，使用这些默认值）
    default_real_magnitudes = {
        1995: 60.0,   # 创业起步
        1999: 60.0,   # Zip2获利
        2000: -50.0,  # 被踢出PayPal
        2002: 80.0,   # PayPal收购（如果存在）
        2008: -90.0,  # 破产危机
        2021: 100.0   # 登顶首富
    }
    
    timeline = []
    for event in musk_data.get('timeline', []):
        year = event.get('year')
        ganzhi = event.get('ganzhi', get_year_ganzhi(year))
        
        # 计算大运
        if profile:
            dayun = calculate_dayun(profile, year)
        else:
            dayun = event.get('dayun', '甲子')
        
        # 获取real_magnitude（兼容多种格式）
        real_mag = None
        
        # 1. 优先使用real_magnitude字段
        if 'real_magnitude' in event:
            real_mag = event.get('real_magnitude')
        
        # 2. 如果没有，尝试从result字段转换
        elif 'result' in event:
            result = event.get('result')
            real_mag = result_to_magnitude.get(result, None)
            if real_mag is not None:
                print(f"   ✅ {year}年: 从result字段转换 ({result} → {real_mag})")
        
        # 3. 如果还是没有，使用默认值
        if real_mag is None or real_mag == 0.0:
            real_mag = default_real_magnitudes.get(year, 0.0)
            if real_mag != 0.0:
                print(f"   ⚠️ {year}年: real_magnitude缺失或为0，使用默认值: {real_mag}")
            else:
                print(f"   ⚠️ {year}年: 无法确定real_magnitude，使用0.0")
        
        timeline.append({
            'year': year,
            'ganzhi': ganzhi,
            'dayun': dayun,
            'type': event.get('type', 'WEALTH'),
            'real_magnitude': real_mag,
            'desc': event.get('desc', '')
        })
    
    # 构建Jason格式
    jason_case = {
        'id': musk_data.get('id', 'TIMELINE_MUSK_WEALTH'),
        'name': musk_data.get('name', 'Elon Musk'),
        'bazi': musk_data.get('bazi', ['辛亥', '甲午', '甲申', '甲子']),
        'day_master': musk_data.get('day_master', '甲'),
        'gender': musk_data.get('gender', '男'),
        'description': f"Musk财富案例 - {musk_data.get('name', 'Elon Musk')}",
        'wealth_vaults': musk_data.get('wealth_vaults', ['辰', '戌', '丑', '未']),
        'timeline': timeline
    }
    
    print(f"✅ 格式转换完成")
    print(f"   案例: {jason_case['name']}")
    print(f"   八字: {' '.join(jason_case['bazi'])}")
    print(f"   事件数: {len(timeline)}")
    print()
    
    # 4. 导入到系统
    print("=" * 80)
    print("💾 导入到MVC系统...")
    print("=" * 80)
    
    controller = WealthVerificationController()
    success, message = controller.import_cases([jason_case])
    
    if success:
        print(f"✅ {message}")
        print()
        
        # 验证导入
        print("🔍 验证导入结果...")
        imported_case = controller.get_case_by_id(jason_case['id'])
        if imported_case:
            print(f"✅ 案例已成功导入: {imported_case.name}")
            print(f"   事件数: {len(imported_case.timeline) if imported_case.timeline else 0}")
        else:
            print("⚠️ 警告：导入后无法找到案例")
    else:
        print(f"❌ {message}")
    
    # 5. 测试验证
    print()
    print("=" * 80)
    print("🧪 测试验证...")
    print("=" * 80)
    
    test_case = controller.get_case_by_id(jason_case['id'])
    if test_case:
        print(f"📊 验证案例: {test_case.name}")
        results = controller.verify_case(test_case)
        
        if results:
            stats = controller.get_verification_statistics(results)
            print(f"✅ 验证完成")
            print(f"   命中率: {stats['hit_rate']:.1f}% ({stats['correct_count']}/{stats['total_count']})")
            print(f"   平均误差: {stats['avg_error']:.1f}分")
            print()
            print("📋 详细结果：")
            for r in results:
                status = "✅" if r.get('is_correct') else "❌"
                predicted = r.get('predicted', 'N/A')
                real = r.get('real', 'N/A')
                error = r.get('error', 'N/A')
                print(f"   {status} {r['year']}年: 真实={real}, 预测={predicted}, 误差={error}")
        else:
            print("⚠️ 验证结果为空")
    else:
        print("❌ 无法找到案例进行验证")
    
    print("=" * 80)
    print()
    print("🎉 导入和验证完成！")
    print("💡 提示：现在可以在UI的'💰 财富验证'页面查看和验证Musk案例了。")

if __name__ == "__main__":
    main()

