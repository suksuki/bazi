#!/usr/bin/env python3
"""
运行A-03羊刃架杀的全量样本海选（升级版：纯度排序+奇点捕获）
"""

import sys
from pathlib import Path
import time
from datetime import datetime

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from controllers.holographic_pattern_controller import HolographicPatternController

def progress_callback(current, total, stats):
    """进度回调函数"""
    pct = (current / total) * 100
    print(f"[进度] {current:,}/{total:,} ({pct:.2f}%) | "
          f"匹配: {stats['matched']} | "
          f"月令拒绝: {stats['rejected_month_lock']:,} | "
          f"透杀拒绝: {stats['rejected_stem_reveal']:,} | "
          f"纯度拒绝: {stats['rejected_purity']:,}")

def main():
    print("=" * 70)
    print("🚀 A-03 羊刃架杀 - 全量样本海选（升级版）")
    print("=" * 70)
    print()
    print("【升级特性】")
    print("-" * 70)
    print("✅ 严格全量扫描：518,400个样本")
    print("✅ 纯度加权排序：取最纯净的500个")
    print("✅ 奇点捕获系统：识别极端样本（Tier X）")
    print("✅ 双文件输出：标准集 + 奇点集")
    print()
    
    controller = HolographicPatternController()
    
    # 设置输出目录
    output_dir = project_root / "data" / "holographic_pattern"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"输出目录: {output_dir}")
    print()
    print("开始全量样本海选...")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    try:
        result = controller.select_samples(
            pattern_id='A-03',
            target_count=500,
            progress_callback=progress_callback,
            output_dir=output_dir
        )
        
        elapsed_time = time.time() - start_time
        
        print()
        print("=" * 70)
        print("✅ 全量样本海选完成")
        print("=" * 70)
        print()
        
        print("【统计结果】")
        print("-" * 70)
        print(f"总扫描数: {result['total_scanned']:,} 个样本")
        print(f"Tier A标准集: {result['tier_a']['count']} 个样本")
        print(f"Tier X奇点集: {result['tier_x']['count']} 个样本")
        print(f"总耗时: {elapsed_time:.2f} 秒 ({elapsed_time/60:.2f} 分钟)")
        print()
        
        print("【拒绝统计】")
        print("-" * 70)
        stats = result['stats']
        print(f"月令锁拒绝: {stats['rejected_month_lock']:,}")
        print(f"透杀拒绝: {stats['rejected_stem_reveal']:,}")
        print(f"纯度拒绝: {stats['rejected_purity']:,}")
        print()
        
        if result['tier_a']['count'] > 0:
            # 显示Tier A纯度统计
            samples = result['tier_a']['samples']
            scores = [s['purity_score'] for s in samples]
            avg_score = sum(scores) / len(scores)
            max_score = max(scores)
            min_score = min(scores)
            
            print("【Tier A标准集纯度统计】")
            print("-" * 70)
            print(f"平均纯度: {avg_score:.2f}")
            print(f"最高纯度: {max_score:.2f}")
            print(f"最低纯度: {min_score:.2f}")
            print()
            
            print("【Tier A前5个样本（最高纯度）】")
            print("-" * 70)
            for i, sample in enumerate(samples[:5], 1):
                chart = sample['chart']
                print(f"{i}. {' '.join(chart)} | "
                      f"日主:{sample['day_master']} | "
                      f"纯度:{sample['purity_score']:.2f}")
            print()
        
        if result['tier_x']['count'] > 0:
            print("【Tier X奇点集】")
            print("-" * 70)
            for i, sample in enumerate(result['tier_x']['samples'], 1):
                chart = sample['chart']
                print(f"{i}. {' '.join(chart)} | "
                      f"日主:{sample['day_master']} | "
                      f"类型:{sample['singularity_type']} | "
                      f"纯度:{sample['purity_score']:.2f}")
            print()
        
        print("【输出文件】")
        print("-" * 70)
        standard_file = output_dir / "A-03_Standard_Dataset.json"
        singularity_file = output_dir / "A-03_Singularities.json"
        
        if standard_file.exists():
            print(f"✅ Tier A标准集: {standard_file}")
        if singularity_file.exists():
            print(f"✅ Tier X奇点集: {singularity_file}")
        print()
        
        print("=" * 70)
        print("🎉 全量样本海选完成！")
        print("=" * 70)
        
    except KeyboardInterrupt:
        print()
        print("⚠️ 用户中断")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()

