#!/usr/bin/env python3
"""
检查所有档案，找出符合指定格局的八字
"""

import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.profile_manager import ProfileManager
from core.bazi_profile import BaziProfile
from core.trinity.core.nexus.definitions import BaziParticleNexus
from core.trinity.core.intelligence.symbolic_stars import SymbolicStarsEngine
from core.engine_graph.constants import TWELVE_LIFE_STAGES


def check_yang_ren_jia_sha(chart, day_master):
    """
    检查是否符合羊刃架杀格局
    
    条件：
    1. 月令锁：月支本气必须为日主之帝旺（即羊刃）
    2. 天干透杀：天干必须透出七杀，且七杀必须有根
    3. 清纯度过滤：剔除重食伤制杀、重财党杀
    """
    year_pillar, month_pillar, day_pillar, hour_pillar = chart
    month_branch = month_pillar[1]
    
    # 条件1：月令锁 - 月支必须是日主的帝旺（羊刃）
    life_stage = TWELVE_LIFE_STAGES.get((day_master, month_branch))
    if life_stage != '帝旺':
        return False, f"月支{month_branch}不是日主{day_master}的帝旺（羊刃）"
    
    # 条件2：天干透杀
    stems = [year_pillar[0], month_pillar[0], day_pillar[0], hour_pillar[0]]
    branches = [year_pillar[1], month_pillar[1], day_pillar[1], hour_pillar[1]]
    
    # 检查天干是否有七杀
    qi_sha_stems = []
    for i, stem in enumerate(stems):
        if i == 2:  # 跳过日主
            continue
        ten_god = BaziParticleNexus.get_shi_shen(stem, day_master)
        if ten_god == '七杀':
            qi_sha_stems.append((i, stem))
    
    if not qi_sha_stems:
        return False, "天干未透出七杀"
    
    # 检查七杀是否有根
    has_root = False
    for _, qi_sha_stem in qi_sha_stems:
        # 检查自坐
        pillar_idx = qi_sha_stems[0][0]
        if pillar_idx < len(branches):
            branch = branches[pillar_idx]
            hidden_stems = BaziParticleNexus.get_branch_weights(branch)
            for hidden_stem, weight in hidden_stems:
                if hidden_stem == qi_sha_stem and weight >= 5:  # 主气或中气
                    has_root = True
                    break
        
        # 检查其他地支
        if not has_root:
            for branch in branches:
                hidden_stems = BaziParticleNexus.get_branch_weights(branch)
                for hidden_stem, weight in hidden_stems:
                    if hidden_stem == qi_sha_stem and weight >= 5:
                        has_root = True
                        break
                if has_root:
                    break
        
        if has_root:
            break
    
    if not has_root:
        return False, "七杀无根"
    
    # 条件3：清纯度过滤
    ten_gods = [BaziParticleNexus.get_shi_shen(s, day_master) for s in stems]
    
    # 统计食伤和财星数量
    shi_shen_count = ten_gods.count('食神') + ten_gods.count('伤官')
    cai_count = ten_gods.count('正财') + ten_gods.count('偏财')
    qi_sha_count = ten_gods.count('七杀')
    
    # 剔除重食伤制杀（这会变成A-02食神制杀）
    if shi_shen_count >= 2 and qi_sha_count >= 1:
        return False, f"重食伤制杀（食伤{shi_shen_count}个，会变成食神制杀格局）"
    
    # 剔除重财党杀（这会导致应力轴S爆表）
    if cai_count >= 2 and qi_sha_count >= 1:
        return False, f"重财党杀（财星{cai_count}个，会导致应力轴爆表）"
    
    # 所有条件都满足
    return True, "符合羊刃架杀格局"


def main():
    """主函数"""
    print("=" * 70)
    print("🔍 检查所有档案是否符合'羊刃架杀'格局")
    print("=" * 70)
    print()
    
    # 加载所有档案
    pm = ProfileManager()
    all_profiles = pm.get_all()
    
    print(f"📋 共找到 {len(all_profiles)} 个档案")
    print()
    
    matches = []
    no_matches = []
    
    for profile in all_profiles:
        try:
            # 创建BaziProfile
            birth_date = datetime(
                profile['year'],
                profile['month'],
                profile['day'],
                profile.get('hour', 12),
                profile.get('minute', 0)
            )
            gender = 1 if profile.get('gender') == '男' else 0
            bazi_profile = BaziProfile(birth_date, gender)
            
            # 获取八字
            pillars = bazi_profile.pillars
            chart = [
                pillars['year'],
                pillars['month'],
                pillars['day'],
                pillars['hour']
            ]
            day_master = bazi_profile.day_master
            
            # 检查是否符合格局
            is_match, reason = check_yang_ren_jia_sha(chart, day_master)
            
            profile_info = {
                'name': profile.get('name', 'Unknown'),
                'gender': profile.get('gender', '?'),
                'birth': f"{profile['year']}-{profile['month']}-{profile['day']} {profile.get('hour', 12)}:00",
                'chart': chart,
                'day_master': day_master,
                'reason': reason
            }
            
            if is_match:
                matches.append(profile_info)
            else:
                no_matches.append(profile_info)
                
        except Exception as e:
            print(f"❌ 处理档案 {profile.get('name', 'Unknown')} 时出错: {e}")
            continue
    
    # 显示结果
    print("=" * 70)
    print(f"✅ 符合'羊刃架杀'格局的档案: {len(matches)} 个")
    print("=" * 70)
    print()
    
    if matches:
        for idx, match in enumerate(matches, 1):
            print(f"【{idx}】{match['name']} ({match['gender']})")
            print(f"    出生: {match['birth']}")
            print(f"    八字: {''.join(match['chart'])}")
            print(f"    日主: {match['day_master']}")
            print(f"    ✅ {match['reason']}")
            print()
    else:
        print("❌ 没有找到符合'羊刃架杀'格局的档案")
        print()
    
    print("=" * 70)
    print(f"❌ 不符合'羊刃架杀'格局的档案: {len(no_matches)} 个")
    print("=" * 70)
    print()
    
    if no_matches:
        print("详细分析（前10个）：")
        print()
        for idx, no_match in enumerate(no_matches[:10], 1):
            print(f"【{idx}】{no_match['name']} ({no_match['gender']})")
            print(f"    出生: {no_match['birth']}")
            print(f"    八字: {''.join(no_match['chart'])}")
            print(f"    日主: {no_match['day_master']}")
            
            # 显示月支和日主的十二长生关系
            month_branch = no_match['chart'][1][1]
            life_stage = TWELVE_LIFE_STAGES.get((no_match['day_master'], month_branch), '未知')
            print(f"    月支: {month_branch} (日主{no_match['day_master']}在{month_branch}为{life_stage})")
            
            # 检查是否有七杀
            stems = [no_match['chart'][i][0] for i in range(4)]
            ten_gods = [BaziParticleNexus.get_shi_shen(s, no_match['day_master']) for s in stems]
            qi_sha_count = ten_gods.count('七杀')
            if qi_sha_count > 0:
                print(f"    七杀: 有 {qi_sha_count} 个")
            else:
                print(f"    七杀: 无")
            
            print(f"    ❌ {no_match['reason']}")
            print()
        
        if len(no_matches) > 10:
            print(f"... 还有 {len(no_matches) - 10} 个档案不符合")
            print()
    
    print("=" * 70)
    print("✅ 检查完成")
    print("=" * 70)


if __name__ == '__main__':
    main()

