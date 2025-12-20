#!/usr/bin/env python3
"""
Jason E 极弱格局/截脚测试专项诊断脚本
====================================

诊断"极弱格局"、"从格判定"和"截脚结构"对极弱格局的负面影响
分析"结构性坍塌"边缘的非线性表现

作者: Antigravity Team
版本: V10.0
日期: 2025-12-17
"""

import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.engine_graph import GraphNetworkEngine
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
import copy


def diagnose_jason_e():
    """诊断Jason E案例的所有年份"""
    
    logger.info("=" * 80)
    logger.info("🔍 Jason E 极弱格局/截脚测试专项诊断")
    logger.info("=" * 80)
    
    # Jason E 案例数据
    bazi = ['乙未', '戊寅', '壬午', '庚戌']
    day_master = '壬'
    gender = '男'
    
    # 三个关键年份
    years = [
        (1985, '乙丑', '甲戌', -60.0, '公司结构重组，权力被架空，财富受损'),
        (2003, '癸未', '辛巳', None, '突发重大健康危机，花费巨额医疗费'),
        (2011, '辛卯', '壬午', -90.0, '健康状况恶化导致财富重大损失。算法焦点：验证流年截脚结构（辛卯）对极弱格局的负面影响')
    ]
    
    # 创建引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    engine = GraphNetworkEngine(config=config)
    
    results = []
    
    for year, year_pillar, luck_pillar, real_wealth, desc in years:
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 {year}年（{year_pillar}）诊断")
        logger.info(f"{'='*80}")
        logger.info(f"描述: {desc}")
        
        # 1. 执行完整分析
        logger.info(f"\n📊 步骤1: 执行完整分析")
        result = engine.analyze(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
        
        strength_score = result.get('strength_score', 0.0)
        strength_normalized = strength_score / 100.0
        strength_label = result.get('strength_label', 'Unknown')
        
        logger.info(f"  身强分数: {strength_score:.2f} ({strength_label})")
        logger.info(f"  归一化值: {strength_normalized:.4f}")
        
        # 2. 计算财富指数
        logger.info(f"\n💰 步骤2: 计算财富指数")
        wealth_result = engine.calculate_wealth_index(
            bazi=bazi,
            day_master=day_master,
            gender=gender,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar
        )
        
        predicted = wealth_result.get('wealth_index', 0.0)
        details = wealth_result.get('details', [])
        
        if real_wealth is not None:
            error = abs(predicted - real_wealth)
            logger.info(f"  预测值: {predicted:.2f}")
            logger.info(f"  真实值: {real_wealth:.2f}")
            logger.info(f"  误差: {error:.2f}")
        else:
            logger.info(f"  预测值: {predicted:.2f}")
            logger.info(f"  真实值: 未知")
        
        # 3. 诊断关键机制
        logger.info(f"\n🔍 步骤3: 诊断关键机制")
        
        # 检查极弱格局
        is_extreme_weak = strength_normalized < 0.3
        logger.info(f"  极弱格局检测: {'是' if is_extreme_weak else '否'} (归一化值: {strength_normalized:.4f})")
        
        # 检查截脚结构
        has_leg_cutting = any('截脚' in d for d in details)
        logger.info(f"  截脚结构检测: {'是' if has_leg_cutting else '否'}")
        
        # 检查从格判定
        # 从格条件：身极弱 + 财星强旺 + 无帮身
        has_wealth_exposed = any('透财' in d or '天干透财' in d for d in details)
        has_help = any('帮身' in d or '印星' in d or '比劫' in d for d in details)
        is_from_pattern = is_extreme_weak and has_wealth_exposed and not has_help
        logger.info(f"  从格判定: {'是' if is_from_pattern else '否'}")
        logger.info(f"    - 身极弱: {is_extreme_weak}")
        logger.info(f"    - 财星强旺: {has_wealth_exposed}")
        logger.info(f"    - 无帮身: {not has_help}")
        
        # 检查结构性坍塌
        is_structural_collapse = predicted < -50.0
        logger.info(f"  结构性坍塌检测: {'是' if is_structural_collapse else '否'} (预测值: {predicted:.2f})")
        
        # 4. 分析截脚结构的影响
        logger.info(f"\n⚡ 步骤4: 分析截脚结构的影响")
        
        year_stem = year_pillar[0] if year_pillar else None
        year_branch = year_pillar[1] if year_pillar else None
        
        logger.info(f"  流年天干: {year_stem}")
        logger.info(f"  流年地支: {year_branch}")
        
        # 检查截脚惩罚值
        leg_cutting_penalty = 0.0
        for detail in details:
            if '截脚' in detail:
                # 尝试提取惩罚值
                if '非线性模型:' in detail:
                    try:
                        penalty_str = detail.split('非线性模型:')[1].split(']')[0].strip()
                        leg_cutting_penalty = float(penalty_str)
                    except:
                        pass
        
        logger.info(f"  截脚惩罚值: {leg_cutting_penalty:.2f}")
        
        # 5. 分析身弱财重
        logger.info(f"\n💸 步骤5: 分析身弱财重")
        
        has_wealth_heavy = any('财重' in d or '财多' in d or '变债务' in d for d in details)
        logger.info(f"  身弱财重检测: {'是' if has_wealth_heavy else '否'}")
        
        # 6. 生成诊断报告
        diagnosis = {
            'year': year,
            'year_pillar': year_pillar,
            'luck_pillar': luck_pillar,
            'description': desc,
            'strength_score': float(strength_score),
            'strength_normalized': float(strength_normalized),
            'strength_label': str(strength_label),
            'predicted_wealth': float(predicted),
            'real_wealth': float(real_wealth) if real_wealth is not None else None,
            'error': float(abs(predicted - real_wealth)) if real_wealth is not None else None,
            'mechanism_analysis': {
                'is_extreme_weak': bool(is_extreme_weak),
                'has_leg_cutting': bool(has_leg_cutting),
                'is_from_pattern': bool(is_from_pattern),
                'is_structural_collapse': bool(is_structural_collapse),
                'has_wealth_heavy': bool(has_wealth_heavy),
                'leg_cutting_penalty': float(leg_cutting_penalty),
                'has_wealth_exposed': bool(has_wealth_exposed),
                'has_help': bool(has_help)
            },
            'details': [str(d) for d in details]
        }
        
        results.append(diagnosis)
        
        # 7. 输出诊断结论
        logger.info(f"\n{'='*80}")
        logger.info(f"📊 {year}年诊断结论")
        logger.info(f"{'='*80}")
        
        if real_wealth is not None:
            if error > 50:
                logger.warning(f"❌ 问题: 误差过大 ({error:.2f})")
                if predicted > 0 and real_wealth < 0:
                    logger.warning("   预测为正值，但真实值为负值")
                    logger.info("   可能原因:")
                    logger.info("   1. 极弱格局未正确识别")
                    logger.info("   2. 截脚结构惩罚不足")
                    logger.info("   3. 从格判定逻辑未触发")
                elif predicted < 0 and real_wealth < 0:
                    logger.info("   预测方向正确，但数值偏差较大")
                    logger.info("   可能原因:")
                    logger.info("   1. 截脚结构惩罚力度需要调整")
                    logger.info("   2. 结构性坍塌的阈值需要优化")
            else:
                logger.info(f"✅ 预测准确 (误差: {error:.2f})")
        
        if is_extreme_weak and not is_from_pattern:
            logger.warning("⚠️  极弱格局但未判定为从格")
            logger.info("   可能原因:")
            logger.info("   1. 从格判定条件过于严格")
            logger.info("   2. 帮身检测可能误判")
        
        if has_leg_cutting and leg_cutting_penalty > -20.0:
            logger.warning("⚠️  截脚结构惩罚可能不足")
            logger.info(f"   当前惩罚: {leg_cutting_penalty:.2f}")
            logger.info("   对于极弱格局，截脚结构应该导致更严重的损失")
    
    # 保存诊断报告
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "jason_e_extreme_weak_diagnosis.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"\n✅ 诊断报告已保存到: {report_file}")
    
    # 生成总结
    logger.info(f"\n{'='*80}")
    logger.info("📊 总体诊断总结")
    logger.info(f"{'='*80}")
    
    total_error = sum(r['error'] for r in results if r['error'] is not None)
    error_count = sum(1 for r in results if r['error'] is not None)
    avg_error = total_error / error_count if error_count > 0 else 0.0
    
    logger.info(f"总体平均误差: {avg_error:.2f}")
    logger.info(f"极弱格局识别率: {sum(1 for r in results if r['mechanism_analysis']['is_extreme_weak']) / len(results) * 100:.1f}%")
    logger.info(f"截脚结构检测率: {sum(1 for r in results if r['mechanism_analysis']['has_leg_cutting']) / len(results) * 100:.1f}%")
    logger.info(f"从格判定率: {sum(1 for r in results if r['mechanism_analysis']['is_from_pattern']) / len(results) * 100:.1f}%")
    
    return results


if __name__ == '__main__':
    diagnose_jason_e()

