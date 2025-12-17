#!/usr/bin/env python3
"""
详细分析Musk案例的6个事件，诊断预测失败原因
"""

import sys
import json
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.wealth_verification_controller import WealthVerificationController
from core.engine_graph import GraphNetworkEngine, TWELVE_LIFE_STAGES
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy

def check_life_stage(day_master, branch):
    """检查十二长生状态"""
    return TWELVE_LIFE_STAGES.get((day_master, branch), None)

def get_expected_mechanisms(year, day_master, ganzhi, dayun):
    """根据年份返回预期的触发机制"""
    expected = {
        1995: {
            'strong_root': True,
            'strong_root_type': '长生',
            'strong_root_branch': '亥',
            'startup_bonus': True,
            'has_wealth_exposed': False,
            'reason': '流年乙亥，亥为甲木长生（强根），无财透，应该触发创业加成'
        },
        1999: {
            'strong_root': True,
            'strong_root_type': '帝旺',
            'strong_root_branch': '卯',
            'has_wealth_exposed': True,
            'wealth_stem': '己',
            'reason': '流年己卯，卯为甲木帝旺（强根），己土正财透出，应该能担财'
        },
        2000: {
            'seven_kill': True,
            'kill_stem': '庚',
            'reason': '流年庚辰，庚金七杀透出攻身，辰土生金，杀重身轻，应该为负值'
        },
        2002: {
            'resource_help': True,
            'resource_stem': '壬',
            'output_branch': '午',
            'reason': '流年壬午，壬水印星帮身，午火食伤生财，应该触发食伤生财和印星帮身'
        },
        2008: {
            'clash_commander': True,
            'clash_branch': '子',
            'month_branch': '午',
            'reason': '流年戊子，子午冲提纲（子冲午），应该触发-150惩罚，最终值接近-90'
        },
        2021: {
            'strong_root': True,
            'strong_root_type': '长生',
            'strong_root_branch': '亥',
            'strong_root_source': '大运',
            'officer_resource': True,
            'officer_stem': '辛',
            'resource_branch': '亥',
            'reason': '大运己亥，亥为甲木长生（强根），流年辛丑，辛金正官+大运亥水印星，应该触发官印相生'
        }
    }
    return expected.get(year, {})

def analyze_event(engine, case, event, detailed=True):
    """详细分析单个事件"""
    year = event.year
    ganzhi = event.ganzhi
    dayun = event.dayun
    real = event.real_magnitude
    
    print(f"\n{'='*80}")
    print(f"📅 {year}年 ({ganzhi}) - {event.desc}")
    print(f"{'='*80}")
    print(f"真实值: {real:.1f}")
    print(f"流年: {ganzhi}")
    print(f"大运: {dayun}")
    print()
    
    # 获取预期机制
    expected_mech = get_expected_mechanisms(year, case.day_master, ganzhi, dayun)
    if expected_mech:
        print(f"📋 预期触发机制:")
        print(f"   {expected_mech.get('reason', 'N/A')}")
        if 'strong_root' in expected_mech:
            print(f"   - 强根: {expected_mech.get('strong_root_type', 'N/A')} ({expected_mech.get('strong_root_branch', 'N/A')})")
        if 'startup_bonus' in expected_mech:
            print(f"   - 创业加成: 应该触发")
        if 'seven_kill' in expected_mech:
            print(f"   - 七杀攻身: {expected_mech.get('kill_stem', 'N/A')}")
        if 'clash_commander' in expected_mech:
            print(f"   - 冲提纲: {expected_mech.get('clash_branch', 'N/A')}冲{expected_mech.get('month_branch', 'N/A')}")
        if 'officer_resource' in expected_mech:
            print(f"   - 官印相生: 流年{expected_mech.get('officer_stem', 'N/A')} + 大运{expected_mech.get('resource_branch', 'N/A')}")
        print()
    
    # 详细分析流年和大运
    if len(ganzhi) >= 2:
        year_stem = ganzhi[0]
        year_branch = ganzhi[1]
        print(f"🔍 流年分析:")
        print(f"   天干: {year_stem}")
        print(f"   地支: {year_branch}")
        
        # 检查十二长生
        life_stage = check_life_stage(case.day_master, year_branch)
        if life_stage:
            print(f"   十二长生: {life_stage}")
            if life_stage in ['帝旺', '临官', '长生']:
                print(f"   ✅ 强根检测: {life_stage}（应该触发强根加成）")
            else:
                print(f"   ❌ 非强根: {life_stage}")
        else:
            print(f"   ⚠️ 未找到十二长生数据")
        print()
    
    if len(dayun) >= 2:
        luck_stem = dayun[0]
        luck_branch = dayun[1]
        print(f"🔍 大运分析:")
        print(f"   天干: {luck_stem}")
        print(f"   地支: {luck_branch}")
        
        # 检查十二长生
        luck_life_stage = check_life_stage(case.day_master, luck_branch)
        if luck_life_stage:
            print(f"   十二长生: {luck_life_stage}")
            if luck_life_stage in ['帝旺', '临官', '长生']:
                print(f"   ✅ 大运强根检测: {luck_life_stage}（应该触发大运强根加成）")
            else:
                print(f"   ❌ 大运非强根: {luck_life_stage}")
        else:
            print(f"   ⚠️ 未找到大运十二长生数据")
        print()
    
    # 计算预测值
    try:
        result = engine.calculate_wealth_index(
            bazi=case.bazi,
            day_master=case.day_master,
            gender=case.gender,
            luck_pillar=dayun,
            year_pillar=ganzhi
        )
        
        if isinstance(result, dict):
            predicted = result.get('wealth_index', 0.0)
            strength_score = result.get('strength_score', 0.0)
            strength_label = result.get('strength_label', 'Unknown')
            details = result.get('details', [])
            opportunity = result.get('opportunity', 0.0)
        else:
            predicted = result
            strength_score = 0.0
            strength_label = 'Unknown'
            details = []
            opportunity = 0.0
        
        error = abs(predicted - real)
        is_correct = error <= 20.0
        
        print(f"预测值: {predicted:.1f}")
        print(f"误差: {error:.1f}分")
        print(f"状态: {'✅ 正确' if is_correct else '❌ 错误'}")
        print()
        
        # 身强身弱分析
        print(f"📊 身强身弱分析:")
        print(f"   身强分数: {strength_score:.1f}%")
        print(f"   身强标签: {strength_label}")
        print()
        
        # 机会能量和容量
        if opportunity:
            print(f"💡 机会能量 (wealth_energy): {opportunity:.1f}")
        capacity = result.get('capacity', 0.0) if isinstance(result, dict) else 0.0
        if capacity:
            print(f"💪 承载力 (capacity): {capacity:.2f}")
        print()
        
        # 计算过程分析
        if isinstance(result, dict):
            print(f"📐 计算过程分析:")
            print(f"   机会能量: {opportunity:.1f}")
            print(f"   承载力: {capacity:.2f}")
            print(f"   最终指数: {predicted:.1f}")
            
            # 估算计算过程
            if opportunity > 0:
                estimated_base = opportunity * abs(capacity) if capacity != 0 else opportunity
                print(f"   估算基础值: {estimated_base:.1f} (机会能量 × 承载力)")
            
            # 检查是否有特殊加成或惩罚
            if has_startup_bonus:
                print(f"   + 创业加成: +40.0")
            if has_vault_opened:
                print(f"   + 财库冲开加成: +100.0 (身强) 或 +80.0 (身弱)")
            if has_vault_collapsed:
                print(f"   - 冲提纲惩罚: -150.0")
            
            print()
        
        # 触发机制详细分析
        if details:
            print(f"🔍 触发机制 ({len(details)} 个):")
            for i, detail in enumerate(details, 1):
                print(f"   {i}. {detail}")
            print()
            
            # 分析关键触发机制
            has_strong_root = any('强根' in str(d) or '帝旺' in str(d) or '临官' in str(d) or '长生' in str(d) for d in details)
            has_vault_opened = any('冲开财库' in str(d) or '🏆' in str(d) for d in details)
            has_vault_collapsed = any('冲提纲' in str(d) or '灾难' in str(d) or '💀' in str(d) for d in details)
            has_startup_bonus = any('创业加成' in str(d) or '🚀' in str(d) for d in details)
            has_officer_resource = any('官印相生' in str(d) for d in details)
            
            print(f"📊 关键机制检测:")
            print(f"   强根: {'✅ 已触发' if has_strong_root else '❌ 未触发'}")
            print(f"   财库冲开: {'✅ 已触发' if has_vault_opened else '❌ 未触发'}")
            print(f"   财库坍塌/冲提纲: {'✅ 已触发' if has_vault_collapsed else '❌ 未触发'}")
            print(f"   创业加成: {'✅ 已触发' if has_startup_bonus else '❌ 未触发'}")
            print(f"   官印相生: {'✅ 已触发' if has_officer_resource else '❌ 未触发'}")
            print()
            
            # 对比预期和实际
            if expected_mech:
                print(f"🔍 预期 vs 实际对比:")
                if 'strong_root' in expected_mech:
                    expected_type = expected_mech.get('strong_root_type', '')
                    if has_strong_root:
                        # 检查类型是否匹配
                        found_type = None
                        for d in details:
                            if '帝旺' in str(d):
                                found_type = '帝旺'
                            elif '临官' in str(d):
                                found_type = '临官'
                            elif '长生' in str(d):
                                found_type = '长生'
                        if found_type == expected_type:
                            print(f"   ✅ 强根类型匹配: {expected_type}")
                        else:
                            print(f"   ⚠️ 强根类型不匹配: 预期{expected_type}，实际{found_type}")
                    else:
                        print(f"   ❌ 预期有强根({expected_type})，但未检测到")
                
                if 'startup_bonus' in expected_mech:
                    if has_startup_bonus:
                        print(f"   ✅ 创业加成已触发")
                    else:
                        print(f"   ❌ 预期有创业加成，但未触发")
                
                if 'clash_commander' in expected_mech:
                    if has_vault_collapsed:
                        print(f"   ✅ 冲提纲已触发")
                    else:
                        print(f"   ❌ 预期有冲提纲，但未触发")
                
                if 'officer_resource' in expected_mech:
                    if has_officer_resource:
                        print(f"   ✅ 官印相生已触发")
                    else:
                        print(f"   ❌ 预期有官印相生，但未触发")
                print()
            
            # 根据真实值判断应该触发什么
            if real > 0:
                if not has_strong_root and not has_vault_opened:
                    print(f"   ⚠️ 预期问题: 真实为正值，但未检测到强根或财库冲开")
                if has_vault_collapsed:
                    print(f"   ⚠️ 预期问题: 真实为正值，但检测到冲提纲（可能惩罚过重）")
            elif real < 0:
                if has_vault_opened:
                    print(f"   ⚠️ 预期问题: 真实为负值，但检测到财库冲开（可能逻辑误判）")
                if not has_vault_collapsed and abs(real) > 80:
                    print(f"   ⚠️ 预期问题: 真实为极端负值，但未检测到冲提纲（可能遗漏）")
            print()
        
        # 错误分析
        if not is_correct:
            print(f"❌ 预测失败分析:")
            print(f"   真实值: {real:.1f}")
            print(f"   预测值: {predicted:.1f}")
            print(f"   偏差: {error:.1f}分")
            print()
            
            # 方向分析
            if real > 0 and predicted < 0:
                print(f"   ⚠️ 方向错误: 真实为正（财富增长），预测为负（财富损失）")
            elif real < 0 and predicted > 0:
                print(f"   ⚠️ 方向错误: 真实为负（财富损失），预测为正（财富增长）")
            elif abs(real) > 80 and abs(predicted) < 50:
                print(f"   ⚠️ 幅度不足: 真实为极端值（{real:.1f}），预测幅度太小（{predicted:.1f}）")
            elif abs(real) < 50 and abs(predicted) > 80:
                print(f"   ⚠️ 幅度过大: 真实为中等值（{real:.1f}），预测幅度太大（{predicted:.1f}）")
            else:
                print(f"   ⚠️ 数值偏差: 方向可能正确，但数值偏差较大")
            print()
            
            # 详细原因分析
            print(f"💭 详细原因分析:")
            
            # 1. 强根相关
            if real > 0:
                expected_strong_root = False
                if year == 1995:  # 乙亥，亥为甲木长生
                    expected_strong_root = True
                    print(f"   - 1995年应该检测到: 亥为甲木长生（强根）")
                elif year == 1999:  # 己卯，卯为甲木帝旺
                    expected_strong_root = True
                    print(f"   - 1999年应该检测到: 卯为甲木帝旺（强根）")
                elif year == 2021:  # 辛丑，大运己亥，亥为甲木长生
                    expected_strong_root = True
                    print(f"   - 2021年应该检测到: 大运亥为甲木长生（强根）")
                
                if expected_strong_root and not has_strong_root:
                    print(f"   ⚠️ 问题: 应该检测到强根但未检测到")
                    # 手动检查
                    if year == 1995 and len(ganzhi) >= 2:
                        branch = ganzhi[1]
                        life_stage = check_life_stage(case.day_master, branch)
                        print(f"      手动检查: {case.day_master}在{branch}的十二长生 = {life_stage}")
                elif not expected_strong_root and has_strong_root:
                    print(f"   ⚠️ 问题: 检测到强根但可能不应该有（需要验证）")
            
            # 2. 财库相关
            if '冲开财库' in str(details) or '🏆' in str(details):
                if real < 0:
                    print(f"   - 财库冲开逻辑可能误判（真实为负值，但检测到财库冲开）")
                elif real > 0 and abs(real) < 50:
                    print(f"   - 财库冲开但财富值偏低（可能需要增加库开加成）")
            
            # 3. 冲提纲相关
            if '冲提纲' in str(details) or '灾难' in str(details):
                if real > 0:
                    print(f"   - 冲提纲惩罚可能过重（真实为正值，但检测到冲提纲）")
                elif real < 0 and abs(real) < 50:
                    print(f"   - 冲提纲但惩罚可能不足（真实为极端负值，但预测不够负）")
                elif year == 2008:
                    print(f"   - 2008年子午冲提纲，应该触发-150惩罚，最终值应该接近-90")
                    print(f"      当前预测: {predicted:.1f}，如果不够负，可能是惩罚被其他因素抵消")
            
            # 4. 身强身弱相关
            if strength_score < 40:
                if real > 0:
                    print(f"   - 身弱判断可能不准确（身弱但真实为正值，可能需要强根加成）")
                    if not has_strong_root:
                        print(f"      建议: 检查强根检测逻辑，确保身弱得强根时能正确加成")
            elif strength_score > 60:
                if real < 0:
                    print(f"   - 身强判断可能不准确（身强但真实为负值，可能有特殊事件）")
            
            # 5. 创业加成相关
            if year == 1995:
                if not has_startup_bonus:
                    print(f"   - 1995年应该触发创业加成（身弱+长生强根+无财透）")
                    print(f"      检查条件: 身弱({strength_score:.1f} < 45), 长生强根, 无财透")
                else:
                    print(f"   ✅ 1995年已触发创业加成")
            
            # 6. 官印相生相关
            if year == 2021:
                if not has_officer_resource:
                    print(f"   - 2021年可能应该触发官印相生（流年辛金正官+大运亥水印星）")
                else:
                    print(f"   ✅ 2021年已触发官印相生")
            
            print()
        
        return {
            'year': year,
            'real': real,
            'predicted': predicted,
            'error': error,
            'is_correct': is_correct,
            'strength_score': strength_score,
            'strength_label': strength_label,
            'details': details
        }
        
    except Exception as e:
        print(f"❌ 计算失败: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """主函数"""
    print("=" * 80)
    print("🔍 详细分析Musk案例的6个事件")
    print("=" * 80)
    print()
    
    # 初始化引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    
    # 加载用户配置
    config_path = project_root / "config" / "parameters.json"
    if config_path.exists():
        with open(config_path, 'r', encoding='utf-8') as f:
            user_config = json.load(f)
            def deep_merge(base, update):
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
            deep_merge(config, user_config)
    
    engine = GraphNetworkEngine(config=config)
    
    # 加载Musk案例
    controller = WealthVerificationController()
    musk_case = controller.get_case_by_id('TIMELINE_MUSK_WEALTH')
    
    if not musk_case:
        print("❌ 未找到Musk案例")
        print("💡 请先运行: python3 scripts/clean_and_reimport_cases.py")
        return
    
    print(f"✅ 找到Musk案例: {musk_case.name}")
    print(f"   八字: {' '.join(musk_case.bazi)}")
    print(f"   日主: {musk_case.day_master}")
    print(f"   事件数: {len(musk_case.timeline) if musk_case.timeline else 0}")
    print()
    
    # 分析每个事件
    results = []
    for event in musk_case.timeline:
        result = analyze_event(engine, musk_case, event)
        if result:
            results.append(result)
    
    # 总结
    print()
    print("=" * 80)
    print("📊 总结分析")
    print("=" * 80)
    print()
    
    if results:
        total = len(results)
        correct = sum(1 for r in results if r['is_correct'])
        avg_error = sum(r['error'] for r in results) / total
        
        print(f"总事件数: {total}")
        print(f"正确预测: {correct} ({correct/total*100:.1f}%)")
        print(f"平均误差: {avg_error:.1f}分")
        print()
        
        # 按误差排序
        results_sorted = sorted(results, key=lambda x: x['error'], reverse=True)
        
        print("📋 误差最大的事件:")
        for r in results_sorted[:3]:
            print(f"   {r['year']}年: 误差 {r['error']:.1f}分 (真实={r['real']:.1f}, 预测={r['predicted']:.1f})")
        print()
        
        # 方向错误统计
        direction_errors = []
        for r in results:
            real = r['real']
            predicted = r['predicted']
            if (real > 0 and predicted < 0) or (real < 0 and predicted > 0):
                direction_errors.append(r['year'])
        
        if direction_errors:
            print(f"⚠️ 方向错误的事件: {direction_errors}")
            print()
        
        # 建议
        print("💡 优化建议:")
        if correct < total * 0.5:
            print("   1. 命中率低于50%，需要大幅调整算法")
        elif correct < total * 0.7:
            print("   1. 命中率在50-70%之间，需要中等调整")
        else:
            print("   1. 命中率超过70%，只需要微调")
        
        if direction_errors:
            print("   2. 存在方向错误，需要检查身强身弱判断和财库逻辑")
        
        if avg_error > 40:
            print("   3. 平均误差较大，需要调整财富能量计算权重")
        elif avg_error > 25:
            print("   3. 平均误差中等，需要微调参数")
        
        # 检查常见问题
        strong_root_missing = []
        vault_logic_issues = []
        
        for r in results:
            if r['real'] > 0 and not any('强根' in str(d) or '帝旺' in str(d) or '临官' in str(d) for d in r['details']):
                strong_root_missing.append(r['year'])
            if r['real'] < 0 and ('冲开财库' in str(r['details']) or '🏆' in str(r['details'])):
                vault_logic_issues.append(r['year'])
        
        if strong_root_missing:
            print(f"   4. 可能遗漏强根检测: {strong_root_missing}年")
        if vault_logic_issues:
            print(f"   5. 财库逻辑可能有问题: {vault_logic_issues}年")
    
    print("=" * 80)

if __name__ == "__main__":
    main()

