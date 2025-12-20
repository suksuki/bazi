#!/usr/bin/env python3
"""
Jason B 2014年（甲午）专项自检脚本
==================================

诊断"食神制杀"通道为何未正确触发
分析GAT网络中的节点连通性和势垒强度

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


def diagnose_2014_pathway():
    """诊断2014年（甲午）的通道触发情况"""
    
    logger.info("=" * 80)
    logger.info("🔍 Jason B 2014年（甲午）专项自检")
    logger.info("=" * 80)
    
    # Jason B 案例数据
    bazi = ['甲辰', '癸酉', '己亥', '戊辰']
    day_master = '己'
    gender = '男'
    luck_pillar = '己卯'  # 2014年大运
    year_pillar = '甲午'  # 2014年流年
    
    # 创建引擎
    config = copy.deepcopy(DEFAULT_FULL_ALGO_PARAMS)
    engine = GraphNetworkEngine(config=config)
    
    # 1. 执行完整分析
    logger.info("\n📊 步骤1: 执行完整分析")
    result = engine.analyze(bazi, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
    
    strength_score = result.get('strength_score', 0.0)
    strength_normalized = strength_score / 100.0
    strength_label = result.get('strength_label', 'Unknown')
    
    logger.info(f"  身强分数: {strength_score:.2f} ({strength_label})")
    logger.info(f"  归一化值: {strength_normalized:.4f}")
    
    # 2. 计算财富指数
    logger.info("\n💰 步骤2: 计算财富指数")
    wealth_result = engine.calculate_wealth_index(
        bazi=bazi,
        day_master=day_master,
        gender=gender,
        luck_pillar=luck_pillar,
        year_pillar=year_pillar
    )
    
    predicted = wealth_result.get('wealth_index', 0.0)
    details = wealth_result.get('details', [])
    
    logger.info(f"  预测值: {predicted:.2f}")
    logger.info(f"  真实值: 100.0")
    logger.info(f"  误差: {abs(predicted - 100.0):.2f}")
    
    # 3. 诊断通道触发情况
    logger.info("\n🔍 步骤3: 诊断通道触发情况")
    
    # 检查七杀攻身
    has_seven_kill_attack = any('七杀攻身' in d for d in details)
    logger.info(f"  七杀攻身检测: {'是' if has_seven_kill_attack else '否'}")
    
    # 检查印星通关
    has_seal_mediation = any('通关' in d or '官印相生' in d or '印星' in d for d in details)
    logger.info(f"  印星通关检测: {'是' if has_seal_mediation else '否'}")
    
    # 检查食神制杀
    has_output_officer = any('食神制杀' in d for d in details)
    logger.info(f"  食神制杀通道: {'✅ 已触发' if has_output_officer else '❌ 未触发'}")
    
    # 检查强根
    has_strong_root = any('临官' in d or '帝旺' in d or '长生' in d for d in details)
    logger.info(f"  强根检测: {'是' if has_strong_root else '否'}")
    
    # 4. 分析节点连通性
    logger.info("\n🔗 步骤4: 分析节点连通性")
    
    # 检查流年天干（甲木）和地支（午火）
    year_stem = year_pillar[0]  # 甲
    year_branch = year_pillar[1]  # 午
    
    logger.info(f"  流年天干: {year_stem} (七杀)")
    logger.info(f"  流年地支: {year_branch} (印星强根)")
    logger.info(f"  大运: {luck_pillar}")
    
    # 检查大运是否有印星
    luck_stem = luck_pillar[0] if luck_pillar else None
    luck_branch = luck_pillar[1] if luck_pillar else None
    
    logger.info(f"  大运天干: {luck_stem}")
    logger.info(f"  大运地支: {luck_branch}")
    
    # 5. 计算势垒强度
    logger.info("\n⚡ 步骤5: 计算势垒强度")
    
    # 检查七杀惩罚
    seven_kill_penalty = 0.0
    for detail in details:
        if '七杀攻身' in detail:
            # 尝试提取惩罚值
            if '非线性模型:' in detail:
                try:
                    penalty_str = detail.split('非线性模型:')[1].split(']')[0].strip()
                    seven_kill_penalty = float(penalty_str)
                except:
                    pass
    
    logger.info(f"  七杀惩罚值: {seven_kill_penalty:.2f}")
    
    # 检查印星加成
    seal_bonus = 0.0
    for detail in details:
        if '印星' in detail or '印' in detail:
            # 尝试提取加成值
            if '+' in detail or '加成' in detail:
                try:
                    # 简化提取逻辑
                    if '加成' in detail:
                        bonus_str = detail.split('加成')[1].split()[0] if '加成' in detail else '0'
                        seal_bonus = float(bonus_str) if bonus_str.replace('.', '').isdigit() else 0.0
                except:
                    pass
    
    logger.info(f"  印星加成值: {seal_bonus:.2f}")
    
    # 6. 生成诊断报告
    logger.info("\n📋 步骤6: 生成诊断报告")
    
    diagnosis = {
        'year': 2014,
        'year_pillar': year_pillar,
        'luck_pillar': luck_pillar,
        'strength_score': strength_score,
        'strength_normalized': strength_normalized,
        'strength_label': strength_label,
        'predicted_wealth': predicted,
        'real_wealth': 100.0,
        'error': abs(predicted - 100.0),
        'pathway_analysis': {
            'has_seven_kill_attack': has_seven_kill_attack,
            'has_seal_mediation': has_seal_mediation,
            'has_output_officer': has_output_officer,
            'has_strong_root': has_strong_root,
            'seven_kill_penalty': seven_kill_penalty,
            'seal_bonus': seal_bonus
        },
        'details': details
    }
    
    # 保存诊断报告
    output_dir = project_root / "reports"
    output_dir.mkdir(exist_ok=True)
    
    report_file = output_dir / "jason_b_2014_diagnosis.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(diagnosis, f, ensure_ascii=False, indent=2)
    
    logger.info(f"✅ 诊断报告已保存到: {report_file}")
    
    # 7. 输出诊断结论
    logger.info("\n" + "=" * 80)
    logger.info("📊 诊断结论")
    logger.info("=" * 80)
    
    if not has_output_officer:
        logger.warning("❌ 问题: '食神制杀'通道未触发")
        logger.info("   可能原因:")
        logger.info("   1. 七杀攻身的检测逻辑可能过于严格")
        logger.info("   2. 印星通关的判定条件可能不满足")
        logger.info("   3. 强根（午火）的能量可能未被正确识别")
        logger.info("   4. GAT注意力机制可能未将午火识别为'制化中心'")
    else:
        logger.info("✅ '食神制杀'通道已触发，但预测值仍然偏低")
        logger.info("   可能原因:")
        logger.info("   1. 七杀惩罚的缩减力度不足")
        logger.info("   2. 能量转化的加成值不够")
        logger.info("   3. 其他负向因素抵消了正向加成")
    
    return diagnosis


if __name__ == '__main__':
    diagnose_2014_pathway()

