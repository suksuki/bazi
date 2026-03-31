#!/usr/bin/env python3
"""
性能测试脚本：评估格局匹配在大规模样本上的运行时间
====================================================
用途：估算对 51.8 万个样本进行 A-03 格局匹配的耗时

测试流程：
1. 加载单个样本
2. 执行完整的张量投影和模式识别
3. 测量单样本耗时
4. 外推到 51.8 万样本的总耗时
"""

import time
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import sys
import logging

# 添加项目根目录
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

from core.registry_loader import RegistryLoader
from core.physics_engine import compute_energy_flux

logging.basicConfig(level=logging.WARNING)  # 减少日志输出
logger = logging.getLogger(__name__)


def generate_mock_sample() -> tuple:
    """
    生成一个模拟样本（四柱和日主）
    """
    # 随机生成一个四柱
    tiangan = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
    dizhi = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
    
    chart = [
        np.random.choice(tiangan) + np.random.choice(dizhi),
        np.random.choice(tiangan) + np.random.choice(dizhi),
        np.random.choice(tiangan) + np.random.choice(dizhi),
        np.random.choice(tiangan) + np.random.choice(dizhi)
    ]
    day_master = chart[1][0]  # 日柱天干作为日主
    
    return chart, day_master


def benchmark_single_sample(
    registry_loader: RegistryLoader,
    pattern_id: str = "A-03",
    n_samples: int = 100
) -> Dict[str, float]:
    """
    对单个样本进行性能测试
    
    Args:
        registry_loader: RegistryLoader 实例
        pattern_id: 格局ID
        n_samples: 测试样本数
        
    Returns:
        性能统计字典
    """
    print(f"\n{'='*60}")
    print(f"🔬 性能测试：{pattern_id} 格局匹配")
    print(f"{'='*60}")
    print(f"测试样本数: {n_samples}")
    print(f"开始测试...\n")
    
    times = []
    
    for i in range(n_samples):
        # 生成模拟样本
        chart, day_master = generate_mock_sample()
        
        # 测量时间
        start_time = time.perf_counter()
        
        try:
            # 执行完整的匹配流程
            result = registry_loader.calculate_tensor_projection_from_registry(
                pattern_id=pattern_id,
                chart=chart,
                day_master=day_master
            )
            
            end_time = time.perf_counter()
            elapsed = end_time - start_time
            times.append(elapsed)
            
            if (i + 1) % 10 == 0:
                avg_time = np.mean(times)
                print(f"  进度: {i+1}/{n_samples} | 平均耗时: {avg_time*1000:.2f}ms/样本", end='\r')
        
        except Exception as e:
            logger.warning(f"样本 {i+1} 处理失败: {e}")
            continue
    
    print(f"\n  进度: {n_samples}/{n_samples} | 测试完成")
    
    # 统计信息
    times_array = np.array(times)
    
    stats = {
        "n_samples": len(times),
        "mean_time_ms": np.mean(times_array) * 1000,
        "median_time_ms": np.median(times_array) * 1000,
        "std_time_ms": np.std(times_array) * 1000,
        "min_time_ms": np.min(times_array) * 1000,
        "max_time_ms": np.max(times_array) * 1000,
        "total_time_sec": np.sum(times_array)
    }
    
    return stats


def estimate_full_run(stats: Dict[str, float], total_samples: int = 518000) -> Dict[str, float]:
    """
    估算完整运行的时间
    
    Args:
        stats: 单样本性能统计
        total_samples: 总样本数（51.8万）
        
    Returns:
        估算结果字典
    """
    mean_time_per_sample = stats["mean_time_ms"] / 1000  # 转换为秒
    
    # 估算总时间
    total_time_sec = mean_time_per_sample * total_samples
    total_time_min = total_time_sec / 60
    total_time_hour = total_time_min / 60
    
    # 考虑文件I/O开销（假设每个样本读取约0.001秒）
    io_overhead_per_sample = 0.001  # 1ms
    total_io_overhead = io_overhead_per_sample * total_samples
    total_with_io_sec = total_time_sec + total_io_overhead
    total_with_io_min = total_with_io_sec / 60
    total_with_io_hour = total_with_io_min / 60
    
    return {
        "total_samples": total_samples,
        "mean_time_per_sample_ms": stats["mean_time_ms"],
        "estimated_time_sec": total_time_sec,
        "estimated_time_min": total_time_min,
        "estimated_time_hour": total_time_hour,
        "estimated_time_with_io_sec": total_with_io_sec,
        "estimated_time_with_io_min": total_with_io_min,
        "estimated_time_with_io_hour": total_with_io_hour,
        "io_overhead_per_sample_ms": io_overhead_per_sample * 1000
    }


def benchmark_file_reading(file_path: Path, n_lines: int = 1000) -> float:
    """
    测试文件读取性能
    """
    if not file_path.exists():
        print(f"⚠️  文件不存在: {file_path}，跳过文件I/O测试")
        return 0.0
    
    print(f"\n📂 测试文件读取性能: {file_path}")
    print(f"   读取行数: {n_lines}")
    
    times = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= n_lines:
                break
            
            start_time = time.perf_counter()
            try:
                data = json.loads(line.strip())
            except:
                pass
            end_time = time.perf_counter()
            
            times.append(end_time - start_time)
    
    if times:
        avg_time = np.mean(times) * 1000
        print(f"   平均读取耗时: {avg_time:.3f}ms/行")
        return avg_time
    return 0.0


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="格局匹配性能测试")
    parser.add_argument(
        "--pattern",
        type=str,
        default="A-03",
        help="要测试的格局ID (默认: A-03)"
    )
    parser.add_argument(
        "--samples",
        type=int,
        default=100,
        help="测试样本数 (默认: 100)"
    )
    parser.add_argument(
        "--total",
        type=int,
        default=518000,
        help="总样本数估算 (默认: 518000)"
    )
    parser.add_argument(
        "--data-file",
        type=str,
        default=None,
        help="数据文件路径（用于测试文件I/O性能）"
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*80)
    print("🚀 FDS-V3.0 格局匹配性能测试")
    print("="*80)
    
    # 初始化 RegistryLoader
    print("\n📦 初始化 RegistryLoader...")
    try:
        registry_loader = RegistryLoader()
        print("✅ RegistryLoader 初始化成功")
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return
    
    # 测试文件I/O（如果提供文件路径）
    io_time_ms = 0.0
    if args.data_file:
        data_path = Path(args.data_file)
        io_time_ms = benchmark_file_reading(data_path, n_lines=min(1000, args.samples))
    
    # 性能测试
    print(f"\n⏱️  开始性能测试...")
    stats = benchmark_single_sample(
        registry_loader=registry_loader,
        pattern_id=args.pattern,
        n_samples=args.samples
    )
    
    # 输出统计结果
    print(f"\n{'='*80}")
    print("📊 性能统计结果")
    print("="*80)
    print(f"测试样本数: {stats['n_samples']}")
    print(f"平均耗时: {stats['mean_time_ms']:.2f} ms/样本")
    print(f"中位数耗时: {stats['median_time_ms']:.2f} ms/样本")
    print(f"标准差: {stats['std_time_ms']:.2f} ms")
    print(f"最小耗时: {stats['min_time_ms']:.2f} ms")
    print(f"最大耗时: {stats['max_time_ms']:.2f} ms")
    print(f"总测试时间: {stats['total_time_sec']:.2f} 秒")
    
    # 估算完整运行时间
    print(f"\n{'='*80}")
    print(f"🔮 估算：对 {args.total:,} 个样本的完整运行时间")
    print("="*80)
    
    estimate = estimate_full_run(stats, total_samples=args.total)
    
    print(f"单样本平均耗时: {estimate['mean_time_per_sample_ms']:.2f} ms")
    print(f"\n【仅计算时间】")
    print(f"  预估总时间: {estimate['estimated_time_sec']:.2f} 秒")
    print(f"            = {estimate['estimated_time_min']:.2f} 分钟")
    print(f"            = {estimate['estimated_time_hour']:.2f} 小时")
    
    if io_time_ms > 0:
        print(f"\n【包含文件I/O开销】")
        print(f"  文件读取耗时: {io_time_ms:.3f} ms/行")
        print(f"  预估总时间: {estimate['estimated_time_with_io_sec']:.2f} 秒")
        print(f"              = {estimate['estimated_time_with_io_min']:.2f} 分钟")
        print(f"              = {estimate['estimated_time_with_io_hour']:.2f} 小时")
    
    # 性能优化建议
    print(f"\n{'='*80}")
    print("💡 性能优化建议")
    print("="*80)
    
    if estimate['estimated_time_hour'] > 24:
        print("⚠️  预计耗时超过24小时，建议：")
        print("  1. 使用多进程并行处理（multiprocessing）")
        print("  2. 分批处理并保存中间结果")
        print("  3. 考虑使用更高效的数据格式（如 Parquet）")
        print("  4. 优化 compute_energy_flux 等核心函数")
    elif estimate['estimated_time_hour'] > 1:
        print("⏱️  预计耗时1-24小时，建议：")
        print("  1. 考虑并行处理加速")
        print("  2. 分批处理避免内存溢出")
    else:
        print("✅ 预计耗时在可接受范围内（<1小时）")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    main()

