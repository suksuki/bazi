#!/usr/bin/env python3
"""
V57.0 Failure Diagnostics - Deep-Dive Debug Script
===================================================

专门诊断 5 个失败案例的详细物理快照。
帮助找出"病因"，为冲击 90% 做准备。
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.processors.physics import PhysicsProcessor, GENERATION, CONTROL
from core.engine_graph import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS

# ===========================================
# 1. 目标案例（硬编码）
# ===========================================

TARGET_CASES = [
    {
        'id': 'REAL_S_001',
        'bazi': ['辛卯', '丁酉', '庚午', '丙子'],
        'day_master': '庚',
        'gender': '男',
        'true_label': 'Strong',
        'pred_label': 'Weak',
        'pred_score': 25.9,
        'description': '乾隆皇帝：子午冲，卯酉冲，但在帝王哲学中，阳刃格身旺抗杀，金神得火炼。此为经典身旺抗杀格。'
    },
    {
        'id': 'REAL_S_006',
        'bazi': ['己巳', '辛未', '庚午', '丁亥'],
        'day_master': '庚',
        'gender': '女',
        'true_label': 'Strong',
        'pred_label': 'Balanced',
        'pred_score': 48.2,
        'description': '润局案例2：生于未月燥土，但在亥时，亥水润土生金，且庚金在巳中有长生，在未中有余气。身旺担官杀。'
    },
    {
        'id': 'REAL_W_004',
        'bazi': ['乙酉', '乙酉', '乙酉', '乙酉'],
        'day_master': '乙',
        'gender': '男',
        'true_label': 'Weak',
        'pred_label': 'Strong',
        'pred_score': 71.0,
        'description': '从杀格：乙木无根，地支全金，天干全乙也被金克。不得不从杀。在此体系中标记为 Weak (Ratio < 20%)。'
    },
    {
        'id': 'REAL_W_010',
        'bazi': ['庚午', '壬午', '丙午', '壬辰'],
        'day_master': '丙',
        'gender': '男',
        'true_label': 'Weak',
        'pred_label': 'Balanced',
        'pred_score': 55.5,
        'description': '变格（极弱）：虽是丙午日柱（羊刃），但生于午月火旺，地支三午自刑，天干双壬水冲克丙火。这是一种特殊的弱（羊刃倒戈）。'
    },
    {
        'id': 'REAL_B_011',
        'bazi': ['癸亥', '甲子', '丙戌', '戊子'],
        'day_master': '丙',
        'gender': '男',
        'true_label': 'Balanced',
        'pred_label': 'Weak',
        'pred_score': 25.7,
        'description': '官印相生：水旺，但甲木透干泄水生火，丙火坐戌有根。身弱有气，官印相生达到平衡。'
    }
]


# ===========================================
# 2. 诊断函数
# ===========================================

def calculate_root_status(engine: GraphNetworkEngine, day_master: str, bazi: List[str]) -> Dict[str, Any]:
    """
    计算日主的根气状态。
    """
    dm_element = engine.STEM_ELEMENTS.get(day_master, 'metal')
    
    # 方法1：检查地支藏干中的日主同五行
    total_root_energy = 0.0
    root_details = []
    
    for pillar_idx, pillar in enumerate(bazi):
        if len(pillar) < 2:
            continue
        branch_char = pillar[1]
        
        # 获取地支藏干
        hidden_map = PhysicsProcessor.GENESIS_HIDDEN_MAP.get(branch_char, [])
        for hidden_stem, weight in hidden_map:
            hidden_element = engine.STEM_ELEMENTS.get(hidden_stem, 'earth')
            if hidden_element == dm_element:
                # 找到根气
                root_energy = weight * 0.1  # 简化计算
                total_root_energy += root_energy
                root_details.append({
                    'pillar': pillar,
                    'branch': branch_char,
                    'hidden_stem': hidden_stem,
                    'weight': weight,
                    'energy': root_energy
                })
    
    # 方法2：检查十二长生强根位置
    strong_root_count = 0
    for pillar in bazi:
        if len(pillar) < 2:
            continue
        branch_char = pillar[1]
        life_stage = TWELVE_LIFE_STAGES.get((day_master, branch_char))
        if life_stage in ['长生', '临官', '帝旺', '冠带']:
            strong_root_count += 1
            coefficient = LIFE_STAGE_COEFFICIENTS.get(life_stage, 1.0)
            total_root_energy += coefficient * 0.1
    
    return {
        'total_root_energy': total_root_energy,
        'root_details': root_details,
        'strong_root_count': strong_root_count,
        'status': 'Strong' if total_root_energy >= 1.0 else ('Weak' if total_root_energy < 0.5 else 'Medium')
    }


def check_structure_flags(engine: GraphNetworkEngine, result: Dict[str, Any], bazi: List[str]) -> Dict[str, Any]:
    """
    检查结构标志：通关、冲、特殊格局。
    """
    flags = {
        'mediation': False,
        'clash_detected': False,
        'special_pattern': result.get('special_pattern'),
        'follower_grid': result.get('follower_grid', False),
        'trigger_events': result.get('trigger_events', [])
    }
    
    # 检查是否有冲
    try:
        from core.interactions import BRANCH_CLASHES
    except ImportError:
        # 备用：直接定义冲的关系
        BRANCH_CLASHES = {
            '子': '午', '午': '子', '寅': '申', '申': '寅', 
            '卯': '酉', '酉': '卯', '辰': '戌', '戌': '辰', 
            '丑': '未', '未': '丑'
        }
    clashes = []
    for i in range(len(bazi)):
        for j in range(i + 1, len(bazi)):
            if len(bazi[i]) >= 2 and len(bazi[j]) >= 2:
                branch1 = bazi[i][1]
                branch2 = bazi[j][1]
                if BRANCH_CLASHES.get(branch1) == branch2 or BRANCH_CLASHES.get(branch2) == branch1:
                    clashes.append(f"{branch1}冲{branch2}")
    
    if clashes:
        flags['clash_detected'] = True
        flags['clashes'] = clashes
    
    # 检查通关（从 trigger_events 中查找）
    trigger_events = result.get('trigger_events', [])
    for event in trigger_events:
        if '通关' in str(event) or 'Mediation' in str(event):
            flags['mediation'] = True
            break
    
    return flags


def diagnose_case(engine: GraphNetworkEngine, case: Dict[str, Any]) -> Dict[str, Any]:
    """
    诊断单个案例。
    """
    bazi = case['bazi']
    day_master = case['day_master']
    
    # 运行分析
    result = engine.analyze(
        bazi=bazi,
        day_master=day_master,
        luck_pillar=None,
        year_pillar=None,
        geo_modifiers=None
    )
    
    # 获取关键信息
    strength_score = result.get('strength_score', 0.0)
    strength_label = result.get('strength_label', 'Unknown')
    
    # 计算根气状态
    root_status = calculate_root_status(engine, day_master, bazi)
    
    # 获取净作用力信息
    strength_data = engine.calculate_strength_score(day_master)
    net_force = strength_data.get('net_force', {})
    total_push = net_force.get('total_push', 0.0)
    total_pull = net_force.get('total_pull', 0.0)
    balance_ratio = net_force.get('balance_ratio', 0.0)
    net_force_override = net_force.get('override', False)
    
    # 计算净力比
    force_sum = total_push + total_pull
    if force_sum > 0:
        net_ratio = abs(total_push - total_pull) / force_sum
    else:
        net_ratio = 1.0
    
    # 检查结构标志
    structure_flags = check_structure_flags(engine, result, bazi)
    
    # 获取能量分布
    self_team_energy = strength_data.get('self_team_energy', 0.0)
    total_energy = strength_data.get('total_energy', 1.0)
    
    return {
        'case_id': case['id'],
        'bazi': bazi,
        'true_label': case['true_label'],
        'pred_label': strength_label,
        'pred_score': strength_score,
        'root_status': root_status,
        'flow_check': {
            'force_in': total_push,
            'force_out': total_pull,
            'net_ratio': net_ratio,
            'balance_ratio': balance_ratio,
            'override': net_force_override
        },
        'structure_flags': structure_flags,
        'energy_distribution': {
            'self_team': self_team_energy,
            'total': total_energy,
            'ratio': self_team_energy / total_energy if total_energy > 0 else 0.0
        },
        'description': case.get('description', '')
    }


# ===========================================
# 3. 输出格式化
# ===========================================

def print_diagnosis(diagnosis: Dict[str, Any]):
    """
    打印诊断结果。
    """
    case_id = diagnosis['case_id']
    bazi = ' '.join(diagnosis['bazi'])
    true_label = diagnosis['true_label']
    pred_label = diagnosis['pred_label']
    pred_score = diagnosis['pred_score']
    
    # 判断是否正确
    is_correct = (pred_label == true_label)
    status = "✅" if is_correct else "❌"
    
    print("=" * 80)
    print(f"=== CASE: {case_id} ===")
    print(f"八字: {bazi}")
    print(f"True: {true_label} | Pred: {pred_label} ({pred_score:.1f}%) {status}")
    print(f"描述: {diagnosis['description']}")
    print()
    print("[Diagnosis]")
    
    # Root Status
    root_status = diagnosis['root_status']
    print(f"📊 Root Status:")
    print(f"   - Total Root Energy: {root_status['total_root_energy']:.3f}")
    print(f"   - Strong Root Count: {root_status['strong_root_count']}")
    print(f"   - Status: {root_status['status']}")
    if root_status['root_details']:
        print(f"   - Root Details:")
        for detail in root_status['root_details'][:3]:  # 只显示前3个
            print(f"     * {detail['pillar']}: {detail['hidden_stem']} (weight={detail['weight']:.2f})")
    
    # Flow Check
    flow = diagnosis['flow_check']
    print(f"🌊 Flow Check:")
    print(f"   - Force In (印比): {flow['force_in']:.2f}")
    print(f"   - Force Out (财官食): {flow['force_out']:.2f}")
    print(f"   - Net Ratio: {flow['net_ratio']:.3f}")
    if flow['override']:
        print(f"   - ⚖️  Net Force Override: Balanced (矢量抵消生效)")
    
    # Structure Flags
    flags = diagnosis['structure_flags']
    print(f"🏗️  Structure Flags:")
    print(f"   - Mediation (通关): {'✅' if flags['mediation'] else '❌'}")
    print(f"   - Clash Detected: {'✅' if flags['clash_detected'] else '❌'}")
    if flags['clash_detected']:
        print(f"     Clashes: {', '.join(flags.get('clashes', []))}")
    print(f"   - Special Pattern: {flags['special_pattern'] or 'None'}")
    print(f"   - Follower Grid: {'✅' if flags['follower_grid'] else '❌'}")
    if flags['trigger_events']:
        print(f"   - Trigger Events: {', '.join(str(e) for e in flags['trigger_events'][:3])}")
    
    # Energy Distribution
    energy = diagnosis['energy_distribution']
    print(f"⚡ Energy Distribution:")
    print(f"   - Self Team: {energy['self_team']:.2f}")
    print(f"   - Total: {energy['total']:.2f}")
    print(f"   - Ratio: {energy['ratio']:.3f} ({energy['ratio']*100:.1f}%)")
    
    print("-" * 80)
    print()


# ===========================================
# 4. 主函数
# ===========================================

def main():
    """
    主函数：诊断所有目标案例。
    """
    print("=" * 80)
    print("🔍 V57.0 Failure Diagnostics - Deep-Dive Debug")
    print("=" * 80)
    print()
    print(f"目标案例数: {len(TARGET_CASES)}")
    print()
    
    # 初始化引擎
    print("📥 初始化引擎...")
    engine = GraphNetworkEngine()
    print("✅ 引擎已初始化")
    print()
    
    # 诊断每个案例
    diagnoses = []
    for case in TARGET_CASES:
        try:
            diagnosis = diagnose_case(engine, case)
            diagnoses.append(diagnosis)
            print_diagnosis(diagnosis)
        except Exception as e:
            print(f"❌ 诊断 {case['id']} 时出错: {e}")
            import traceback
            traceback.print_exc()
            print()
    
    # 总结
    print("=" * 80)
    print("📊 诊断总结")
    print("=" * 80)
    print()
    
    # 按问题类型分类
    root_issues = []
    flow_issues = []
    structure_issues = []
    
    for diag in diagnoses:
        # 检查根气问题
        root_status = diag['root_status']
        if root_status['status'] == 'Weak' and diag['true_label'] == 'Strong':
            root_issues.append(diag['case_id'])
        elif root_status['status'] == 'Strong' and diag['true_label'] == 'Weak':
            root_issues.append(diag['case_id'])
        
        # 检查能量流向问题
        flow = diag['flow_check']
        if flow['force_out'] > flow['force_in'] * 2.0 and diag['true_label'] == 'Strong':
            flow_issues.append(diag['case_id'])
        
        # 检查结构问题
        flags = diag['structure_flags']
        if not flags['mediation'] and '官印相生' in diag['description']:
            structure_issues.append(diag['case_id'])
        if not flags['follower_grid'] and '从' in diag['description']:
            structure_issues.append(diag['case_id'])
    
    if root_issues:
        print(f"⚠️  根气问题: {', '.join(root_issues)}")
    if flow_issues:
        print(f"⚠️  能量流向问题: {', '.join(flow_issues)}")
    if structure_issues:
        print(f"⚠️  结构识别问题: {', '.join(structure_issues)}")
    
    print()
    print("✅ 诊断完成！请根据上述信息修复引擎逻辑。")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

