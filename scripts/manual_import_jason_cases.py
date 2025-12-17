#!/usr/bin/env python3
"""
手动导入5个Jason案例（如果转换脚本未运行）
"""

import sys
from pathlib import Path

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
    """将事件类型转换为财富值"""
    desc = description
    
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

def create_jason_cases():
    """创建5个Jason案例"""
    cases = []
    
    # Jason A
    profile_a = BaziProfile(datetime(1978, 11, 15, 14, 30), 1)
    cases.append({
        'id': 'JASON_A_T1978_1115',
        'name': 'Jason A (财富爆发)',
        'bazi': ['戊午', '癸亥', '壬戌', '丁未'],
        'day_master': '壬',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身强用财官, 日坐财库, 墓库逢冲',
        'timeline': [
            {
                'year': 2004,
                'ganzhi': get_year_ganzhi(2004),
                'dayun': calculate_dayun(profile_a, 2004),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('CareerTurnover', '辞去稳定高薪工作，首次创业，压力大但收入结构开始转变。'),
                'desc': '辞去稳定高薪工作，首次创业，压力大但收入结构开始转变。'
            },
            {
                'year': 2010,
                'ganzhi': get_year_ganzhi(2010),
                'dayun': calculate_dayun(profile_a, 2010),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('MajorInvestmentGain', '公司获得巨额投资，财富实现质的飞跃。算法焦点：未土官库被寅木合动，财富爆发 (Open Vault)。'),
                'desc': '公司获得巨额投资，财富实现质的飞跃。算法焦点：未土官库被寅木合动，财富爆发 (Open Vault)。'
            },
            {
                'year': 2012,
                'ganzhi': get_year_ganzhi(2012),
                'dayun': calculate_dayun(profile_a, 2012),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('SevereDebtCrisis', '投资失误，资金链断裂，承受巨大债务。算法焦点：辰戌冲，财库坍塌 (Broken Tomb)。'),
                'desc': '投资失误，资金链断裂，承受巨大债务。算法焦点：辰戌冲，财库坍塌 (Broken Tomb)。'
            },
            {
                'year': 2018,
                'ganzhi': get_year_ganzhi(2018),
                'dayun': calculate_dayun(profile_a, 2018),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('SecondStartupSuccess', '重整旗鼓，新项目上市成功，财富恢复且超越先前峰值。'),
                'desc': '重整旗鼓，新项目上市成功，财富恢复且超越先前峰值。'
            }
        ]
    })
    
    # Jason B
    profile_b = BaziProfile(datetime(1964, 9, 10, 8, 30), 1)
    cases.append({
        'id': 'JASON_B_T1964_0910',
        'name': 'Jason B (身弱用印)',
        'bazi': ['甲辰', '癸酉', '己亥', '戊辰'],
        'day_master': '己',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身弱用印, 财官相生, 强金制木',
        'timeline': [
            {
                'year': 1999,
                'ganzhi': get_year_ganzhi(1999),
                'dayun': calculate_dayun(profile_b, 1999),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('StartupFunding', '第一次创业成功，获得巨大投资，资本金增加。'),
                'desc': '第一次创业成功，获得巨大投资，资本金增加。'
            },
            {
                'year': 2007,
                'ganzhi': get_year_ganzhi(2007),
                'dayun': calculate_dayun(profile_b, 2007),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('MajorAcquisition', '公司进行重要收购，扩大业务版图，财富稳步增长。'),
                'desc': '公司进行重要收购，扩大业务版图，财富稳步增长。'
            },
            {
                'year': 2014,
                'ganzhi': get_year_ganzhi(2014),
                'dayun': calculate_dayun(profile_b, 2014),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('CompanyIPO', '公司上市，财富实现阶跃。算法焦点：验证火印（丙火）流年/大运出现时对身弱日主的扶助效果。'),
                'desc': '公司上市，财富实现阶跃。算法焦点：验证火印（丙火）流年/大运出现时对身弱日主的扶助效果。'
            }
        ]
    })
    
    # Jason C
    profile_c = BaziProfile(datetime(1980, 9, 20, 12, 0), 1)
    cases.append({
        'id': 'JASON_C_T1980_0920',
        'name': 'Jason C (稳定积累)',
        'bazi': ['庚申', '乙酉', '辛未', '甲午'],
        'day_master': '辛',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身旺用财官, 官印相生, 平衡格局',
        'timeline': [
            {
                'year': 2007,
                'ganzhi': get_year_ganzhi(2007),
                'dayun': calculate_dayun(profile_c, 2007),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('CareerPromotion', '职场上升期，升任高管，财富开始稳定积累。'),
                'desc': '职场上升期，升任高管，财富开始稳定积累。'
            },
            {
                'year': 2013,
                'ganzhi': get_year_ganzhi(2013),
                'dayun': calculate_dayun(profile_c, 2013),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('MajorRealEstate', '大笔购入不动产，资产结构优化。'),
                'desc': '大笔购入不动产，资产结构优化。'
            },
            {
                'year': 2017,
                'ganzhi': get_year_ganzhi(2017),
                'dayun': calculate_dayun(profile_c, 2017),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('CareerPromotion', '再次升职加薪，权力变现。算法焦点：验证官印相生（丁火官星）的稳定性。'),
                'desc': '再次升职加薪，权力变现。算法焦点：验证官印相生（丁火官星）的稳定性。'
            }
        ]
    })
    
    # Jason D
    profile_d = BaziProfile(datetime(1961, 10, 10, 20, 0), 1)
    cases.append({
        'id': 'JASON_D_T1961_1010',
        'name': 'Jason D (财库连冲)',
        'bazi': ['辛丑', '丁酉', '庚辰', '丙戌'],
        'day_master': '庚',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身旺用官, 多财库, 丑未戌三刑',
        'timeline': [
            {
                'year': 1999,
                'ganzhi': get_year_ganzhi(1999),
                'dayun': calculate_dayun(profile_d, 1999),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('BusinessExpansion', '公司业务快速扩张，财富开始积累。'),
                'desc': '公司业务快速扩张，财富开始积累。'
            },
            {
                'year': 2015,
                'ganzhi': get_year_ganzhi(2015),
                'dayun': calculate_dayun(profile_d, 2015),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('MajorAssetRestructure', '重大资产重组，财富暴增。算法焦点：丑未冲触发财库开启 (Open Vault)。'),
                'desc': '重大资产重组，财富暴增。算法焦点：丑未冲触发财库开启 (Open Vault)。'
            },
            {
                'year': 2021,
                'ganzhi': get_year_ganzhi(2021),
                'dayun': calculate_dayun(profile_d, 2021),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('InvestmentGain', '投资获利，财富再次爆发。算法焦点：验证丑土与未土的连续冲动效应。'),
                'desc': '投资获利，财富再次爆发。算法焦点：验证丑土与未土的连续冲动效应。'
            }
        ]
    })
    
    # Jason E
    profile_e = BaziProfile(datetime(1955, 2, 24, 19, 30), 1)
    cases.append({
        'id': 'JASON_E_T1955_0224',
        'name': 'Jason E (截脚测试)',
        'bazi': ['乙未', '戊寅', '壬午', '庚戌'],
        'day_master': '壬',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 极弱格局, 财星强旺, 截脚测试',
        'timeline': [
            {
                'year': 1985,
                'ganzhi': get_year_ganzhi(1985),
                'dayun': calculate_dayun(profile_e, 1985),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('BusinessCrisis', '公司结构重组，权力被架空，财富受损。'),
                'desc': '公司结构重组，权力被架空，财富受损。'
            },
            {
                'year': 2003,
                'ganzhi': get_year_ganzhi(2003),
                'dayun': calculate_dayun(profile_e, 2003),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('MajorHealthIssue', '突发重大健康危机，花费巨额医疗费。'),
                'desc': '突发重大健康危机，花费巨额医疗费。'
            },
            {
                'year': 2011,
                'ganzhi': get_year_ganzhi(2011),
                'dayun': calculate_dayun(profile_e, 2011),
                'type': 'WEALTH',
                'real_magnitude': event_type_to_magnitude('HealthAndFinancialLoss', '健康状况恶化导致财富重大损失。算法焦点：验证流年截脚结构（辛卯）对极弱格局的负面影响。'),
                'desc': '健康状况恶化导致财富重大损失。算法焦点：验证流年截脚结构（辛卯）对极弱格局的负面影响。'
            }
        ]
    })
    
    return cases

def main():
    """主函数"""
    print("=" * 80)
    print("📥 手动导入5个Jason案例")
    print("=" * 80)
    print()
    
    controller = WealthVerificationController()
    
    # 创建案例
    print("📋 创建案例...")
    jason_cases = create_jason_cases()
    print(f"✅ 已创建 {len(jason_cases)} 个案例")
    print()
    
    # 导入案例
    print("=" * 80)
    print("💾 导入案例...")
    print("=" * 80)
    
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
    
    # 验证导入
    print("=" * 80)
    print("🔍 验证导入结果...")
    print("=" * 80)
    
    all_cases = controller.get_all_cases()
    print(f"✅ 系统中共有 {len(all_cases)} 个案例")
    
    for case in all_cases:
        print(f"   - {case.name} ({case.id})")
    
    print("=" * 80)
    print()
    print("🎉 导入完成！")
    print("💡 提示：现在可以在UI的'💰 财富验证'页面查看所有案例了。")

if __name__ == "__main__":
    main()

