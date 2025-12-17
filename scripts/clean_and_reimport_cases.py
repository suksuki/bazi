#!/usr/bin/env python3
"""
清洗并重新导入所有测试案例
1. 删除所有现有的timeline文件
2. 重新导入正确的案例数据
"""

import sys
import json
import shutil
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.bazi_profile import VirtualBaziProfile
from datetime import datetime

# 流年干支映射
GAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
ZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']

def get_year_ganzhi(year):
    """根据年份计算流年干支"""
    gan_index = (year - 4) % 10
    zhi_index = (year - 4) % 12
    return GAN[gan_index] + ZHI[zhi_index]

def calculate_dayun_from_bazi(bazi, gender, year):
    """从八字反推出生日期并计算大运"""
    try:
        # 使用VirtualBaziProfile从八字反推出生日期
        pillars = {
            'year': bazi[0],
            'month': bazi[1],
            'day': bazi[2],
            'hour': bazi[3]
        }
        day_master = bazi[2][0]  # 日主是天干
        
        # 创建VirtualBaziProfile，它会自动反推出生日期
        profile = VirtualBaziProfile(pillars, day_master=day_master, gender=gender)
        
        # 使用反推的profile计算大运
        dayun = profile.get_luck_pillar_at(year)
        if dayun and isinstance(dayun, str) and len(dayun) >= 2:
            return dayun
    except Exception as e:
        print(f"⚠️ 计算大运失败 ({year}年): {e}")
    return '甲子'  # 默认值

def create_musk_case():
    """创建Musk案例（从八字反推出生日期并计算大运）"""
    # Musk的八字
    bazi = ['辛亥', '甲午', '甲申', '甲子']
    gender = 1  # 男性
    
    timeline = []
    events = [
        {
            'year': 1995,
            'ganzhi': '乙亥',
            'real_magnitude': 60.0,
            'desc': '创立 Zip2。流年乙亥(水木)帮身，喜神到位。'
        },
        {
            'year': 1999,
            'ganzhi': '己卯',
            'real_magnitude': 60.0,
            'desc': '出售 Zip2 获利。流年己卯，卯为甲木帝旺(强根)。身弱得强根，担财。'
        },
        {
            'year': 2000,
            'ganzhi': '庚辰',
            'real_magnitude': -50.0,
            'desc': '被踢出 PayPal，感染疟疾。流年庚金七杀透出攻身。辰土生金。杀重身轻。'
        },
        {
            'year': 2002,
            'ganzhi': '壬午',
            'real_magnitude': 80.0,
            'desc': 'eBay收购PayPal获利。午火食伤生财，壬水生身。'
        },
        {
            'year': 2008,
            'ganzhi': '戊子',
            'real_magnitude': -90.0,
            'desc': 'SpaceX 三次爆炸，特斯拉濒临破产，离婚。大运戊戌(财耗身)，流年戊子。子午冲(冲提纲)。水火交战，根基动摇。'
        },
        {
            'year': 2021,
            'ganzhi': '辛丑',
            'real_magnitude': 100.0,
            'desc': '成为世界首富。大运亥水长生。流年辛丑，虽然是官杀库，但可能涉及特殊的\'官印相生\'或库的打开。'
        }
    ]
    
    for event in events:
        year = event['year']
        ganzhi = event['ganzhi']
        # 从八字反推出生日期并计算大运
        dayun = calculate_dayun_from_bazi(bazi, gender, year)
        
        timeline.append({
            'year': year,
            'ganzhi': ganzhi,
            'dayun': dayun,
            'type': 'WEALTH',
            'real_magnitude': event['real_magnitude'],
            'desc': event['desc']
        })
    
    return {
        'id': 'TIMELINE_MUSK_WEALTH',
        'name': 'Elon Musk',
        'bazi': ['辛亥', '甲午', '甲申', '甲子'],
        'day_master': '甲',
        'gender': '男',
        'description': 'Musk财富案例 - 完整时间线',
        'wealth_vaults': ['辰', '戌', '丑', '未'],
        'timeline': timeline
    }

def create_jason_cases():
    """创建5个Jason案例（从八字反推出生日期并计算大运）"""
    cases = []
    
    # Jason A
    bazi_a = ['戊午', '癸亥', '壬戌', '丁未']
    gender_a = 1  # 男性
    cases.append({
        'id': 'JASON_A_T1978_1115',
        'name': 'Jason A (财富爆发)',
        'bazi': bazi_a,
        'day_master': '壬',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身强用财官, 日坐财库, 墓库逢冲',
        'timeline': [
            {
                'year': 2004,
                'ganzhi': get_year_ganzhi(2004),
                'dayun': calculate_dayun_from_bazi(bazi_a, gender_a, 2004),
                'type': 'WEALTH',
                'real_magnitude': 50.0,
                'desc': '辞去稳定高薪工作，首次创业，压力大但收入结构开始转变。'
            },
            {
                'year': 2010,
                'ganzhi': get_year_ganzhi(2010),
                'dayun': calculate_dayun_from_bazi(bazi_a, gender_a, 2010),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '公司获得巨额投资，财富实现质的飞跃。算法焦点：未土官库被寅木合动，财富爆发 (Open Vault)。'
            },
            {
                'year': 2012,
                'ganzhi': get_year_ganzhi(2012),
                'dayun': calculate_dayun_from_bazi(bazi_a, gender_a, 2012),
                'type': 'WEALTH',
                'real_magnitude': -90.0,
                'desc': '投资失误，资金链断裂，承受巨大债务。算法焦点：辰戌冲，财库坍塌 (Broken Tomb)。'
            },
            {
                'year': 2018,
                'ganzhi': get_year_ganzhi(2018),
                'dayun': calculate_dayun_from_bazi(bazi_a, gender_a, 2018),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '重整旗鼓，新项目上市成功，财富恢复且超越先前峰值。'
            }
        ]
    })
    
    # Jason B
    bazi_b = ['甲辰', '癸酉', '己亥', '戊辰']
    gender_b = 1  # 男性
    cases.append({
        'id': 'JASON_B_T1964_0910',
        'name': 'Jason B (身弱用印)',
        'bazi': bazi_b,
        'day_master': '己',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身弱用印, 财官相生, 强金制木',
        'timeline': [
            {
                'year': 1999,
                'ganzhi': get_year_ganzhi(1999),
                'dayun': calculate_dayun_from_bazi(bazi_b, gender_b, 1999),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '第一次创业成功，获得巨大投资，资本金增加。'
            },
            {
                'year': 2007,
                'ganzhi': get_year_ganzhi(2007),
                'dayun': calculate_dayun_from_bazi(bazi_b, gender_b, 2007),
                'type': 'WEALTH',
                'real_magnitude': 70.0,
                'desc': '公司进行重要收购，扩大业务版图，财富稳步增长。'
            },
            {
                'year': 2014,
                'ganzhi': get_year_ganzhi(2014),
                'dayun': calculate_dayun_from_bazi(bazi_b, gender_b, 2014),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '公司上市，财富实现阶跃。算法焦点：验证火印（丙火）流年/大运出现时对身弱日主的扶助效果。'
            }
        ]
    })
    
    # Jason C
    bazi_c = ['庚申', '乙酉', '辛未', '甲午']
    gender_c = 1  # 男性
    cases.append({
        'id': 'JASON_C_T1980_0920',
        'name': 'Jason C (稳定积累)',
        'bazi': bazi_c,
        'day_master': '辛',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身旺用财官, 官印相生, 平衡格局',
        'timeline': [
            {
                'year': 2007,
                'ganzhi': get_year_ganzhi(2007),
                'dayun': calculate_dayun_from_bazi(bazi_c, gender_c, 2007),
                'type': 'WEALTH',
                'real_magnitude': 70.0,
                'desc': '职场上升期，升任高管，财富开始稳定积累。'
            },
            {
                'year': 2013,
                'ganzhi': get_year_ganzhi(2013),
                'dayun': calculate_dayun_from_bazi(bazi_c, gender_c, 2013),
                'type': 'WEALTH',
                'real_magnitude': 70.0,
                'desc': '大笔购入不动产，资产结构优化。'
            },
            {
                'year': 2017,
                'ganzhi': get_year_ganzhi(2017),
                'dayun': calculate_dayun_from_bazi(bazi_c, gender_c, 2017),
                'type': 'WEALTH',
                'real_magnitude': 70.0,
                'desc': '再次升职加薪，权力变现。算法焦点：验证官印相生（丁火官星）的稳定性。'
            }
        ]
    })
    
    # Jason D
    bazi_d = ['辛丑', '丁酉', '庚辰', '丙戌']
    gender_d = 1  # 男性
    cases.append({
        'id': 'JASON_D_T1961_1010',
        'name': 'Jason D (财库连冲)',
        'bazi': bazi_d,
        'day_master': '庚',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 身旺用官, 多财库, 丑未戌三刑',
        'timeline': [
            {
                'year': 1999,
                'ganzhi': get_year_ganzhi(1999),
                'dayun': calculate_dayun_from_bazi(bazi_d, gender_d, 1999),
                'type': 'WEALTH',
                'real_magnitude': 50.0,
                'desc': '公司业务快速扩张，财富开始积累。'
            },
            {
                'year': 2015,
                'ganzhi': get_year_ganzhi(2015),
                'dayun': calculate_dayun_from_bazi(bazi_d, gender_d, 2015),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '重大资产重组，财富暴增。算法焦点：丑未冲触发财库开启 (Open Vault)。'
            },
            {
                'year': 2021,
                'ganzhi': get_year_ganzhi(2021),
                'dayun': calculate_dayun_from_bazi(bazi_d, gender_d, 2021),
                'type': 'WEALTH',
                'real_magnitude': 100.0,
                'desc': '投资获利，财富再次爆发。算法焦点：验证丑土与未土的连续冲动效应。'
            }
        ]
    })
    
    # Jason E
    bazi_e = ['乙未', '戊寅', '壬午', '庚戌']
    gender_e = 1  # 男性
    cases.append({
        'id': 'JASON_E_T1955_0224',
        'name': 'Jason E (截脚测试)',
        'bazi': bazi_e,
        'day_master': '壬',
        'gender': '男',
        'description': '来源: Internal_Mining_Protocol_V9.3, 标签: 极弱格局, 财星强旺, 截脚测试',
        'timeline': [
            {
                'year': 1985,
                'ganzhi': get_year_ganzhi(1985),
                'dayun': calculate_dayun_from_bazi(bazi_e, gender_e, 1985),
                'type': 'WEALTH',
                'real_magnitude': -60.0,
                'desc': '公司结构重组，权力被架空，财富受损。'
            },
            {
                'year': 2003,
                'ganzhi': get_year_ganzhi(2003),
                'dayun': calculate_dayun_from_bazi(bazi_e, gender_e, 2003),
                'type': 'WEALTH',
                'real_magnitude': -80.0,
                'desc': '突发重大健康危机，花费巨额医疗费。'
            },
            {
                'year': 2011,
                'ganzhi': get_year_ganzhi(2011),
                'dayun': calculate_dayun_from_bazi(bazi_e, gender_e, 2011),
                'type': 'WEALTH',
                'real_magnitude': -90.0,
                'desc': '健康状况恶化导致财富重大损失。算法焦点：验证流年截脚结构（辛卯）对极弱格局的负面影响。'
            }
        ]
    })
    
    return cases

def main():
    """主函数"""
    print("=" * 80)
    print("🧹 清洗并重新导入所有测试案例")
    print("=" * 80)
    print()
    
    # 1. 清理所有现有的timeline文件
    print("🗑️ 清理现有数据文件...")
    data_dir = project_root / 'data'
    data_dir.mkdir(exist_ok=True)
    
    timeline_files = list(data_dir.glob('*_timeline.json'))
    deleted_count = 0
    
    for file_path in timeline_files:
        try:
            file_path.unlink()
            deleted_count += 1
            print(f"   ✅ 删除: {file_path.name}")
        except Exception as e:
            print(f"   ❌ 删除失败 {file_path.name}: {e}")
    
    print(f"✅ 已删除 {deleted_count} 个文件")
    print()
    
    # 2. 创建正确的案例数据
    print("=" * 80)
    print("📋 创建案例数据...")
    print("=" * 80)
    
    all_cases = []
    
    # Musk案例
    print("   1. 创建Musk案例...")
    musk_case = create_musk_case()
    all_cases.append(musk_case)
    print(f"      ✅ {musk_case['name']} - {len(musk_case['timeline'])} 个事件")
    
    # Jason案例
    print("   2. 创建Jason案例...")
    jason_cases = create_jason_cases()
    all_cases.extend(jason_cases)
    for case in jason_cases:
        print(f"      ✅ {case['name']} - {len(case['timeline'])} 个事件")
    
    print()
    print(f"✅ 共创建 {len(all_cases)} 个案例")
    print()
    
    # 3. 验证数据完整性
    print("=" * 80)
    print("🔍 验证数据完整性...")
    print("=" * 80)
    
    for case in all_cases:
        case_id = case['id']
        case_name = case['name']
        timeline = case.get('timeline', [])
        
        print(f"\n📋 {case_name} ({case_id}):")
        print(f"   事件数: {len(timeline)}")
        
        # 检查每个事件的real_magnitude
        zero_count = 0
        for event in timeline:
            year = event.get('year', 'N/A')
            real_mag = event.get('real_magnitude', 0.0)
            if real_mag == 0.0:
                zero_count += 1
                print(f"   ⚠️ {year}年: real_magnitude为0")
            else:
                print(f"   ✅ {year}年: real_magnitude={real_mag}")
        
        if zero_count > 0:
            print(f"   ⚠️ 警告: {zero_count} 个事件的real_magnitude为0")
        else:
            print(f"   ✅ 所有事件的real_magnitude都正确")
    
    print()
    
    # 4. 导入到系统
    print("=" * 80)
    print("💾 导入到MVC系统...")
    print("=" * 80)
    
    controller = WealthVerificationController()
    success, message = controller.import_cases(all_cases)
    
    if success:
        print(f"✅ {message}")
        print()
        
        # 5. 验证导入结果
        print("=" * 80)
        print("🔍 验证导入结果...")
        print("=" * 80)
        
        all_imported = controller.get_all_cases()
        print(f"✅ 系统中共有 {len(all_imported)} 个案例")
        print()
        
        # 检查每个案例
        for case in all_imported:
            print(f"📋 {case.name} ({case.id}):")
            print(f"   事件数: {len(case.timeline) if case.timeline else 0}")
            
            if case.timeline:
                zero_count = 0
                for event in case.timeline:
                    if event.real_magnitude == 0.0:
                        zero_count += 1
                
                if zero_count > 0:
                    print(f"   ⚠️ 警告: {zero_count} 个事件的real_magnitude为0")
                else:
                    print(f"   ✅ 所有事件的real_magnitude都正确")
        
        # 6. 测试验证Musk案例
        print()
        print("=" * 80)
        print("🧪 测试验证Musk案例...")
        print("=" * 80)
        
        musk_imported = controller.get_case_by_id('TIMELINE_MUSK_WEALTH')
        if musk_imported:
            results = controller.verify_case(musk_imported)
            if results:
                stats = controller.get_verification_statistics(results)
                print(f"✅ 验证完成")
                print(f"   命中率: {stats['hit_rate']:.1f}% ({stats['correct_count']}/{stats['total_count']})")
                print(f"   平均误差: {stats['avg_error']:.1f}分")
                print()
                print("📋 详细结果：")
                for r in results:
                    status = "✅" if r.get('is_correct') else "❌"
                    real = r.get('real', 0.0)
                    predicted = r.get('predicted', 'N/A')
                    print(f"   {status} {r['year']}年: 真实={real}, 预测={predicted}")
        else:
            print("❌ 未找到Musk案例")
    else:
        print(f"❌ {message}")
    
    print("=" * 80)
    print()
    print("🎉 清洗和重新导入完成！")
    print("💡 提示：现在可以在UI的'💰 财富验证'页面查看所有案例了。")

if __name__ == "__main__":
    main()

