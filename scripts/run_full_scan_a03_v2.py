#!/usr/bin/env python3
"""
FDS-V1.1 全量扫描与分层捕获脚本（基于AI分析师最新规范）
执行 [A-03 羊刃架杀] 的全量扫描与分层捕获
"""

import sys
from pathlib import Path
import json
import logging
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def progress_callback(current, total, stats):
    """进度回调函数"""
    percent = (current / total) * 100
    logger.info(f"[进度] {current}/{total} ({percent:.2f}%) | 匹配: {stats['matched']} | 月令拒绝: {stats['rejected_month_lock']:,} | 透杀拒绝: {stats['rejected_stem_reveal']:,} | 纯度拒绝: {stats['rejected_purity']}")

def main():
    print("=" * 70)
    print("🚀 FDS-V1.1 全量扫描与分层捕获：A-03 羊刃架杀")
    print("=" * 70)
    print()
    print("【执行规范】")
    print("-" * 70)
    print("✅ 全量扫描：518,400 个样本")
    print("✅ 奇点捕获：能量溢出（地支三刃）+ 高压临界（2+七杀无制）")
    print("✅ 纯度打分：按分数排序，取前500名")
    print("✅ 双文件输出：Tier A标准集 + Tier X奇点集")
    print()
    
    output_dir = project_root / "data" / "holographic_pattern"
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"输出目录: {output_dir}")
    print()
    
    controller = HolographicPatternController()
    pattern_id = "A-03"
    target_count = 500
    
    start_time = datetime.now()
    logger.info("开始全量扫描...")
    logger.info("=" * 70)
    
    selection_results = controller.select_samples(
        pattern_id=pattern_id,
        target_count=target_count,
        output_dir=output_dir,
        progress_callback=progress_callback
    )
    
    end_time = datetime.now()
    time_taken = (end_time - start_time).total_seconds()
    
    logger.info("=" * 70)
    logger.info("✅ 全量扫描完成")
    logger.info("=" * 70)
    print()
    
    tier_a_samples = selection_results['tier_a']['samples']
    tier_x_samples = selection_results['tier_x']['samples']
    final_stats = selection_results['stats']
    
    print("【统计结果】")
    print("-" * 70)
    print(f"总扫描数: {final_stats['scanned']:,} 个样本")
    print(f"Tier A标准集: {len(tier_a_samples)} 个样本")
    print(f"Tier X奇点集: {len(tier_x_samples)} 个样本")
    print(f"总耗时: {time_taken:.2f} 秒 ({time_taken / 60:.2f} 分钟)")
    print()
    
    print("【拒绝统计】")
    print("-" * 70)
    print(f"月令锁拒绝: {final_stats['rejected_month_lock']:,}")
    print(f"透杀拒绝: {final_stats['rejected_stem_reveal']:,}")
    print(f"纯度拒绝: {final_stats['rejected_purity']:,}")
    print()
    
    if tier_a_samples:
        purity_scores = [s['purity_score'] for s in tier_a_samples]
        print("【Tier A标准集纯度统计】")
        print("-" * 70)
        print(f"平均纯度: {sum(purity_scores) / len(purity_scores):.2f}")
        print(f"最高纯度: {max(purity_scores):.2f}")
        print(f"最低纯度: {min(purity_scores):.2f}")
        print()
        
        print("【Tier A前5个样本（最高纯度）】")
        print("-" * 70)
        for i, sample in enumerate(tier_a_samples[:5]):
            print(f"{i+1}. {' '.join(sample['chart'])} | 日主:{sample['day_master']} | 纯度:{sample['purity_score']:.2f}")
        print()
    
    if tier_x_samples:
        print("【Tier X奇点集统计】")
        print("-" * 70)
        singularity_types = {}
        for sample in tier_x_samples:
            stype = sample.get('singularity_type', 'UNKNOWN')
            singularity_types[stype] = singularity_types.get(stype, 0) + 1
        
        for stype, count in singularity_types.items():
            print(f"{stype}: {count} 个样本")
        print()
        
        print("【Tier X前5个样本】")
        print("-" * 70)
        for i, sample in enumerate(tier_x_samples[:5]):
            print(f"{i+1}. {' '.join(sample['chart'])} | 日主:{sample['day_master']} | 类型:{sample.get('singularity_type', 'UNKNOWN')}")
        print()
    
    print("【输出文件】")
    print("-" * 70)
    print(f"✅ Tier A标准集: {output_dir / f'QGA_{pattern_id}_TierA_Standard.json'}")
    print(f"✅ Tier X奇点集: {output_dir / f'QGA_{pattern_id}_TierX_Singularity.json'}")
    print()
    
    print("=" * 70)
    print("🎉 全量扫描与分层捕获完成！")
    print("=" * 70)

if __name__ == "__main__":
    main()

