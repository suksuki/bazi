#!/usr/bin/env python3
"""
将Gemini格式的案例转换为Jason格式并导入
"""

import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.bazi_profile import BaziProfile
from datetime import datetime

# 流年干支映射
GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def get_year_ganzhi(year):
    """根据年份计算流年干支"""
    gan_index = (year - 4) % 10
    zhi_index = (year - 4) % 12
    return GAN[gan_index] + ZHI[zhi_index]

def get_day_master_from_pillar(day_pillar):
    """从日柱提取日主"""
    if len(day_pillar) >= 1:
        return day_pillar[0]
    return None

def calculate_dayun(profile, year):
    """计算指定年份的大运"""
    try:
        dayun = profile.get_luck_pillar_at(year)
        if dayun and isinstance(dayun, str) and len(dayun) >= 2:
            return dayun
    except:
        pass
    return '甲子'  # 默认值

def event_type_to_magnitude(event_type, description):
    """
    将事件类型转换为财富值
    根据描述和类型判断财富影响
    """
    desc = description
    
    # 根据事件类型和描述关键词判断
    # 财富爆发类
    if '爆发' in desc or '暴增' in desc or '上市' in desc or '巨额投资' in desc:
        return 100.0
    elif '获得投资' in desc or '质的飞跃' in desc or '超越峰值' in desc:
        return 100.0
    elif '资产重组' in desc or '财富暴增' in desc:
        return 100.0
    
    # 重大危机类
    elif '巨大债务' in desc or '资金链断裂' in desc or '重大损失' in desc:
        return -90.0
    elif '巨额医疗费' in desc or '重大健康危机' in desc:
        return -80.0
    elif '财富受损' in desc or '权力被架空' in desc:
        return -60.0
    
    # 稳定增长类
    elif '升职加薪' in desc or '权力变现' in desc:
        return 70.0
    elif '重要收购' in desc or '大笔购入' in desc or '资产结构优化' in desc:
        return 70.0
    elif '稳定积累' in desc or '稳步增长' in desc:
        return 60.0
    
    # 创业/起步类
    elif '首次创业' in desc or '创业成功' in desc:
        return 50.0
    elif '业务扩张' in desc or '财富开始积累' in desc:
        return 50.0
    
    # 默认值
    else:
        return 0.0

def convert_gemini_to_jason(gemini_case):
    """
    将Gemini格式转换为Jason格式
    """
    # 提取基本信息
    case_id = gemini_case.get('id', 'UNKNOWN')
    name = gemini_case.get('profile', {}).get('name', 'Unknown')
    gender_gemini = gemini_case.get('profile', {}).get('gender', 'M')
    gender = '男' if gender_gemini == 'M' else '女'
    gender_int = 1 if gender_gemini == 'M' else 0
    
    # 提取出生信息
    profile_data = gemini_case.get('profile', {})
    birth_year = profile_data.get('birth_year')
    birth_month = profile_data.get('birth_month', 1)
    birth_day = profile_data.get('birth_day', 1)
    birth_hour = profile_data.get('birth_hour', 12)
    birth_minute = profile_data.get('birth_minute', 0)
    
    # 创建BaziProfile用于计算大运
    profile = None
    if birth_year:
        try:
            birth_date = datetime(birth_year, birth_month, birth_day, birth_hour, birth_minute)
            profile = BaziProfile(birth_date, gender_int)
        except Exception as e:
            print(f"⚠️ 警告：无法创建BaziProfile ({name}): {e}，将使用默认大运")
    
    # 提取八字
    chart = gemini_case.get('chart', {})
    bazi = [
        chart.get('year_pillar', ''),
        chart.get('month_pillar', ''),
        chart.get('day_pillar', ''),
        chart.get('hour_pillar', '')
    ]
    
    # 提取日主
    day_pillar = chart.get('day_pillar', '')
    day_master = get_day_master_from_pillar(day_pillar)
    
    if not day_master:
        raise ValueError(f"无法从日柱提取日主: {day_pillar}")
    
    # 转换事件
    timeline = []
    life_events = gemini_case.get('life_events', [])
    
    for event in life_events:
        year = event.get('year')
        if not year:
            continue
        
        ganzhi = get_year_ganzhi(year)
        
        # 计算大运
        if profile:
            dayun = calculate_dayun(profile, year)
        else:
            dayun = '甲子'  # 默认大运
        
        description = event.get('description', '')
        real_magnitude = event_type_to_magnitude(
            event.get('event_type', ''),
            description
        )
        
        timeline.append({
            'year': year,
            'ganzhi': ganzhi,
            'dayun': dayun,
            'type': 'WEALTH',
            'real_magnitude': real_magnitude,
            'desc': description
        })
    
    # 构建Jason格式
    jason_case = {
        'id': case_id,
        'name': name,
        'bazi': bazi,
        'day_master': day_master,
        'gender': gender,
        'description': f"来源: {gemini_case.get('source_url', 'Unknown')}, 标签: {', '.join(gemini_case.get('tags', []))}",
        'timeline': timeline
    }
    
    return jason_case

def main():
    """主函数"""
    print("=" * 80)
    print("🔄 Gemini格式转Jason格式并导入")
    print("=" * 80)
    print()
    
    # Gemini格式的5个案例
    gemini_cases = [
        {
            "id": "JASON_A_T1978_1115",
            "source_url": "Internal_Mining_Protocol_V9.3",
            "quality_tier": "A",
            "profile": {
                "name": "Jason A (财富爆发)",
                "gender": "M",
                "birth_year": 1978,
                "birth_month": 11,
                "birth_day": 15,
                "birth_hour": 14,
                "birth_minute": 30,
                "birth_city": "Guangzhou"
            },
            "chart": {
                "year_pillar": "戊午",
                "month_pillar": "癸亥",
                "day_pillar": "壬戌",
                "hour_pillar": "丁未"
            },
            "life_events": [
                {
                    "year": 2004,
                    "event_type": "CareerTurnover",
                    "description": "辞去稳定高薪工作，首次创业，压力大但收入结构开始转变。",
                    "verified": True
                },
                {
                    "year": 2010,
                    "event_type": "MajorInvestmentGain",
                    "description": "公司获得巨额投资，财富实现质的飞跃。算法焦点：未土官库被寅木合动，财富爆发 (Open Vault)。",
                    "verified": True
                },
                {
                    "year": 2012,
                    "event_type": "SevereDebtCrisis",
                    "description": "投资失误，资金链断裂，承受巨大债务。算法焦点：辰戌冲，财库坍塌 (Broken Tomb)。",
                    "verified": True
                },
                {
                    "year": 2018,
                    "event_type": "SecondStartupSuccess",
                    "description": "重整旗鼓，新项目上市成功，财富恢复且超越先前峰值。",
                    "verified": True
                }
            ],
            "tags": ["身强用财官", "日坐财库", "墓库逢冲"]
        },
        {
            "id": "JASON_B_T1964_0910",
            "source_url": "Internal_Mining_Protocol_V9.3",
            "quality_tier": "A",
            "profile": {
                "name": "Jason B (身弱用印)",
                "gender": "M",
                "birth_year": 1964,
                "birth_month": 9,
                "birth_day": 10,
                "birth_hour": 8,
                "birth_minute": 30,
                "birth_city": "Hangzhou"
            },
            "chart": {
                "year_pillar": "甲辰",
                "month_pillar": "癸酉",
                "day_pillar": "己亥",
                "hour_pillar": "戊辰"
            },
            "life_events": [
                {
                    "year": 1999,
                    "event_type": "StartupFunding",
                    "description": "第一次创业成功，获得巨大投资，资本金增加。",
                    "verified": True
                },
                {
                    "year": 2007,
                    "event_type": "MajorAcquisition",
                    "description": "公司进行重要收购，扩大业务版图，财富稳步增长。",
                    "verified": True
                },
                {
                    "year": 2014,
                    "event_type": "CompanyIPO",
                    "description": "公司上市，财富实现阶跃。算法焦点：验证火印（丙火）流年/大运出现时对身弱日主的扶助效果。",
                    "verified": True
                }
            ],
            "tags": ["身弱用印", "财官相生", "强金制木"]
        },
        {
            "id": "JASON_C_T1980_0920",
            "source_url": "Internal_Mining_Protocol_V9.3",
            "quality_tier": "A",
            "profile": {
                "name": "Jason C (稳定积累)",
                "gender": "M",
                "birth_year": 1980,
                "birth_month": 9,
                "birth_day": 20,
                "birth_hour": 12,
                "birth_minute": 0,
                "birth_city": "Nanjing"
            },
            "chart": {
                "year_pillar": "庚申",
                "month_pillar": "乙酉",
                "day_pillar": "辛未",
                "hour_pillar": "甲午"
            },
            "life_events": [
                {
                    "year": 2007,
                    "event_type": "CareerPromotion",
                    "description": "职场上升期，升任高管，财富开始稳定积累。",
                    "verified": True
                },
                {
                    "year": 2013,
                    "event_type": "MajorRealEstate",
                    "description": "大笔购入不动产，资产结构优化。",
                    "verified": True
                },
                {
                    "year": 2017,
                    "event_type": "CareerPromotion",
                    "description": "再次升职加薪，权力变现。算法焦点：验证官印相生（丁火官星）的稳定性。",
                    "verified": True
                }
            ],
            "tags": ["身旺用财官", "官印相生", "平衡格局"]
        },
        {
            "id": "JASON_D_T1961_1010",
            "source_url": "Internal_Mining_Protocol_V9.3",
            "quality_tier": "A",
            "profile": {
                "name": "Jason D (财库连冲)",
                "gender": "M",
                "birth_year": 1961,
                "birth_month": 10,
                "birth_day": 10,
                "birth_hour": 20,
                "birth_minute": 0,
                "birth_city": "Beijing"
            },
            "chart": {
                "year_pillar": "辛丑",
                "month_pillar": "丁酉",
                "day_pillar": "庚辰",
                "hour_pillar": "丙戌"
            },
            "life_events": [
                {
                    "year": 1999,
                    "event_type": "BusinessExpansion",
                    "description": "公司业务快速扩张，财富开始积累。",
                    "verified": True
                },
                {
                    "year": 2015,
                    "event_type": "MajorAssetRestructure",
                    "description": "重大资产重组，财富暴增。算法焦点：丑未冲触发财库开启 (Open Vault)。",
                    "verified": True
                },
                {
                    "year": 2021,
                    "event_type": "InvestmentGain",
                    "description": "投资获利，财富再次爆发。算法焦点：验证丑土与未土的连续冲动效应。",
                    "verified": True
                }
            ],
            "tags": ["身旺用官", "多财库", "丑未戌三刑"]
        },
        {
            "id": "JASON_E_T1955_0224",
            "source_url": "Internal_Mining_Protocol_V9.3",
            "quality_tier": "A",
            "profile": {
                "name": "Jason E (截脚测试)",
                "gender": "M",
                "birth_year": 1955,
                "birth_month": 2,
                "birth_day": 24,
                "birth_hour": 19,
                "birth_minute": 30,
                "birth_city": "San Francisco, USA"
            },
            "chart": {
                "year_pillar": "乙未",
                "month_pillar": "戊寅",
                "day_pillar": "壬午",
                "hour_pillar": "庚戌"
            },
            "life_events": [
                {
                    "year": 1985,
                    "event_type": "BusinessCrisis",
                    "description": "公司结构重组，权力被架空，财富受损。",
                    "verified": True
                },
                {
                    "year": 2003,
                    "event_type": "MajorHealthIssue",
                    "description": "突发重大健康危机，花费巨额医疗费。",
                    "verified": True
                },
                {
                    "year": 2011,
                    "event_type": "HealthAndFinancialLoss",
                    "description": "健康状况恶化导致财富重大损失。算法焦点：验证流年截脚结构（辛卯）对极弱格局的负面影响。",
                    "verified": True
                }
            ],
            "tags": ["极弱格局", "财星强旺", "截脚测试"]
        }
    ]
    
    # 转换并导入
    controller = WealthVerificationController()
    jason_cases = []
    
    print("📋 转换案例...")
    for i, gemini_case in enumerate(gemini_cases, 1):
        try:
            jason_case = convert_gemini_to_jason(gemini_case)
            jason_cases.append(jason_case)
            print(f"   ✅ {i}. {jason_case['name']} ({jason_case['id']})")
            print(f"      八字: {' '.join(jason_case['bazi'])}")
            print(f"      事件数: {len(jason_case['timeline'])}")
        except Exception as e:
            print(f"   ❌ {i}. 转换失败: {e}")
            import traceback
            traceback.print_exc()
    
    print()
    print("=" * 80)
    print("💾 导入案例...")
    print("=" * 80)
    
    # 导入到系统
    success, message = controller.import_cases(jason_cases)
    
    if success:
        print(f"✅ {message}")
        print()
        print("📊 导入的案例列表：")
        for case in jason_cases:
            print(f"   - {case['name']} ({case['id']})")
            print(f"     八字: {' '.join(case['bazi'])}")
            print(f"     日主: {case['day_master']}")
            print(f"     事件: {len(case['timeline'])} 个")
            print()
    else:
        print(f"❌ {message}")
    
    print("=" * 80)
    print()
    print("🎉 转换和导入完成！")
    print("💡 提示：现在可以在UI的'💰 财富验证'页面查看和验证这些案例了。")

if __name__ == "__main__":
    main()

