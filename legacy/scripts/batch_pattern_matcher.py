#!/usr/bin/env python3
"""
批量格局匹配器（并行版）
========================
功能：对大规模样本（如 51.8 万）进行格局匹配，支持多进程并行处理

使用方法：
    # 单进程模式（用于测试）
    python3 scripts/batch_pattern_matcher.py --pattern A-03 --data-file core/data/holographic_universe_518k.jsonl --workers 1
    
    # 多进程模式（推荐）
    python3 scripts/batch_pattern_matcher.py --pattern A-03 --data-file core/data/holographic_universe_518k.jsonl --workers 8
    
    # 仅处理前 N 个样本（用于测试）
    python3 scripts/batch_pattern_matcher.py --pattern A-03 --data-file core/data/holographic_universe_518k.jsonl --limit 1000
"""

import json
import time
import sys
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from multiprocessing import Pool, cpu_count
from functools import partial
import numpy as np

# 尝试导入 tqdm（进度条）
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False
    # 简单的进度条实现（如果没有tqdm）
    class tqdm:
        def __init__(self, iterable=None, total=None, desc=None, unit=None, ncols=None):
            self.iterable = iterable
            self.total = total
            self.desc = desc or ""
            self.unit = unit or "it"
            self.current = 0
            self.start_time = time.time()
            
        def __iter__(self):
            if self.iterable:
                for item in self.iterable:
                    yield item
                    self.current += 1
                    self._update()
            return self
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            self._close()
            
        def update(self, n=1):
            self.current += n
            self._update()
            
        def _update(self):
            if self.total:
                pct = (self.current / self.total) * 100
                elapsed = time.time() - self.start_time
                if self.current > 0:
                    rate = self.current / elapsed
                    eta = (self.total - self.current) / rate if rate > 0 else 0
                    print(f"\r{self.desc}: {self.current}/{self.total} ({pct:.1f}%) | "
                          f"速度: {rate:.1f} {self.unit}/s | ETA: {eta:.0f}s", end="", flush=True)
                    
        def _close(self):
            print()  # 换行

# 添加项目根目录
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

# 配置日志（减少输出）
logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

# 全局变量（用于worker进程）
_global_registry_loader = None
_global_pattern_id = None


def init_worker(pattern_id: str):
    """初始化worker进程（每个进程只初始化一次RegistryLoader）"""
    global _global_registry_loader, _global_pattern_id
    from core.registry_loader import RegistryLoader
    _global_registry_loader = RegistryLoader()
    _global_pattern_id = pattern_id


def process_single_sample(args: Tuple[int, Dict]) -> Dict[str, Any]:
    """
    处理单个样本（worker函数）
    
    Args:
        args: (line_number, sample_data) 元组
        
    Returns:
        处理结果字典
    """
    global _global_registry_loader, _global_pattern_id
    
    line_number, sample_data = args
    
    try:
        start_time = time.perf_counter()
        
        # 模式1: 如果有chart，使用完整流程
        chart = sample_data.get('chart')
        day_master = sample_data.get('day_master')
        
        if chart:
            # 完整匹配流程（需要chart和day_master）
            if not day_master:
                # 从chart推断日主（日柱天干）
                if len(chart) >= 2 and len(chart[1]) >= 1:
                    day_master = chart[1][0]
                else:
                    return {
                        'line_number': line_number,
                        'uid': sample_data.get('uid'),
                        'status': 'error',
                        'error': 'Cannot infer day_master'
                    }
            
            result = _global_registry_loader.calculate_tensor_projection_from_registry(
                pattern_id=_global_pattern_id,
                chart=chart,
                day_master=day_master
            )
            
        else:
            # 模式2: 如果只有tensor，直接从tensor计算匹配度
            tensor_data = sample_data.get('tensor')
            if not tensor_data:
                return {
                    'line_number': line_number,
                    'uid': sample_data.get('uid'),
                    'status': 'error',
                    'error': 'Missing both chart and tensor data'
                }
            
            # 将tensor转换为向量格式
            if isinstance(tensor_data, dict):
                tensor_vector = np.array([
                    tensor_data.get('E', 0.0),
                    tensor_data.get('O', 0.0),
                    tensor_data.get('M', 0.0),
                    tensor_data.get('S', 0.0),
                    tensor_data.get('R', 0.0)
                ])
            elif isinstance(tensor_data, list) and len(tensor_data) == 5:
                tensor_vector = np.array(tensor_data)
            else:
                return {
                    'line_number': line_number,
                    'uid': sample_data.get('uid'),
                    'status': 'error',
                    'error': f'Invalid tensor format: {type(tensor_data)}'
                }
            
            # 使用pattern_recognition直接匹配
            pattern = _global_registry_loader.get_pattern(_global_pattern_id)
            if not pattern:
                return {
                    'line_number': line_number,
                    'uid': sample_data.get('uid'),
                    'status': 'error',
                    'error': f'Pattern {_global_pattern_id} not found'
                }
            
            # 解析@config引用
            pattern = _global_registry_loader.resolve_config_refs_in_dict(pattern)
            
            # 获取特征锚点（使用RegistryLoader的方法）
            feature_anchors = _global_registry_loader.get_feature_anchors(_global_pattern_id)
            
            if not feature_anchors:
                return {
                    'line_number': line_number,
                    'uid': sample_data.get('uid'),
                    'status': 'error',
                    'error': 'No feature anchors found'
                }
            
            # 提取流形数据（支持standard_manifold或直接mean_vector）
            manifold = feature_anchors.get('standard_manifold') or feature_anchors
            mean_vector_dict = manifold.get('mean_vector', {})
            
            if not mean_vector_dict:
                return {
                    'line_number': line_number,
                    'uid': sample_data.get('uid'),
                    'status': 'error',
                    'error': 'No mean_vector found in feature anchors'
                }
            
            # 计算匹配度（使用pattern_recognition的逻辑）
            from core.math_engine import (
                calculate_mahalanobis_distance,
                calculate_precision_score,
                calculate_cosine_similarity
            )
            
            mean_vector = np.array([
                mean_vector_dict.get('E', 0.0),
                mean_vector_dict.get('O', 0.0),
                mean_vector_dict.get('M', 0.0),
                mean_vector_dict.get('S', 0.0),
                mean_vector_dict.get('R', 0.0)
            ])
            
            # 获取协方差矩阵
            cov_data = manifold.get('covariance_matrix') or feature_anchors.get('covariance_matrix')
            if cov_data:
                covariance_matrix = np.array(cov_data)
            else:
                # 如果没有协方差矩阵，使用单位矩阵（会退化为欧式距离）
                covariance_matrix = np.eye(5)
            
            # 计算余弦相似度
            similarity = calculate_cosine_similarity(tensor_vector, mean_vector)
            
            # 计算马氏距离
            m_dist = calculate_mahalanobis_distance(tensor_vector, mean_vector, covariance_matrix)
            
            # 计算SAI（简化版本，使用tensor的均值作为SAI）
            sai = np.mean(tensor_vector)
            
            # 计算精确度评分
            precision_score = calculate_precision_score(similarity, m_dist, sai)
            
            # 获取阈值（从manifold或feature_anchors）
            # V3.1修正：提高匹配阈值至0.7，避免泛化过度
            thresholds = manifold.get('thresholds', {}) or feature_anchors.get('thresholds', {})
            max_m_dist = thresholds.get('max_mahalanobis_dist', 3.0)
            match_threshold = thresholds.get('match_threshold', 0.7)  # V3.1: 从0.6提高到0.7
            
            # 判断状态
            if precision_score > match_threshold and m_dist <= max_m_dist:
                status = 'MATCHED'
            elif precision_score < 0.6:
                status = 'BROKEN'
            else:
                status = 'EDGE'
            
            result = {
                'projection': {
                    'E': float(tensor_vector[0]),
                    'O': float(tensor_vector[1]),
                    'M': float(tensor_vector[2]),
                    'S': float(tensor_vector[3]),
                    'R': float(tensor_vector[4])
                },
                'recognition': {
                    'status': status,
                    'precision_score': float(precision_score),
                    'mahalanobis_dist': float(m_dist),
                    'cosine_similarity': float(similarity)
                },
                'sai': float(sai)
            }
        
        elapsed_time = (time.perf_counter() - start_time) * 1000  # 转换为ms
        
        # 提取关键信息
        recognition = result.get('recognition', {})
        precision_score = recognition.get('precision_score', 0.0)
        mahalanobis_dist = recognition.get('mahalanobis_dist', 0.0)
        status = recognition.get('status', 'UNKNOWN')
        
        return {
            'line_number': line_number,
            'uid': sample_data.get('uid'),
            'status': 'success',
            'precision_score': precision_score,
            'mahalanobis_dist': mahalanobis_dist,
            'pattern_status': status,
            'elapsed_ms': elapsed_time,
            'tensor': result.get('projection', {}),
            'sai': result.get('sai', 0.0)
        }
        
    except Exception as e:
        import traceback
        return {
            'line_number': line_number,
            'uid': sample_data.get('uid', 'unknown'),
            'status': 'error',
            'error': str(e),
            'traceback': traceback.format_exc()
        }


def load_samples_from_file(
    file_path: Path,
    limit: Optional[int] = None
) -> List[Tuple[int, Dict]]:
    """
    从文件加载样本（惰性加载，只返回元数据）
    
    Args:
        file_path: JSONL文件路径
        limit: 限制加载数量（None表示全部）
        
    Returns:
        [(line_number, sample_data), ...] 列表
    """
    samples = []
    line_count = 0
    
    print(f"📂 正在加载样本: {file_path}")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, start=1):
                if not line.strip():
                    continue
                
                try:
                    data = json.loads(line.strip())
                    
                    # 跳过meta行
                    if 'meta' in data:
                        continue
                    
                    # 验证必需字段（支持tensor或chart）
                    if 'tensor' in data or 'chart' in data:
                        samples.append((line_num, data))
                        line_count += 1
                        
                        if limit and line_count >= limit:
                            break
                        
                        # 进度提示
                        if line_count % 10000 == 0:
                            print(f"  已加载: {line_count:,} 个样本...", end='\r')
                
                except json.JSONDecodeError:
                    continue
                except Exception as e:
                    logger.warning(f"行 {line_num} 解析失败: {e}")
                    continue
    
    except FileNotFoundError:
        print(f"❌ 文件不存在: {file_path}")
        return []
    except Exception as e:
        print(f"❌ 加载文件失败: {e}")
        return []
    
    print(f"\n✅ 成功加载 {len(samples):,} 个样本")
    return samples


def process_batch(
    samples: List[Tuple[int, Dict]],
    pattern_id: str,
    workers: int = None,
    batch_size: int = 1000
) -> Dict[str, Any]:
    """
    批量处理样本（支持并行）
    
    Args:
        samples: 样本列表
        pattern_id: 格局ID
        workers: 进程数（None表示使用CPU核心数）
        batch_size: 每批处理的样本数
        
    Returns:
        统计结果字典
    """
    if workers is None:
        workers = cpu_count()
    
    total_samples = len(samples)
    print(f"\n{'='*80}")
    print(f"🚀 开始批量处理: {pattern_id} 格局")
    print(f"{'='*80}")
    print(f"总样本数: {total_samples:,}")
    print(f"工作进程数: {workers}")
    print(f"批次大小: {batch_size:,}")
    print(f"{'='*80}\n")
    
    # 结果统计
    results = []
    errors = []
    start_time = time.time()
    
    # 分批处理（避免内存问题）
    n_batches = (total_samples + batch_size - 1) // batch_size
    
    # 使用进度条
    with tqdm(total=total_samples, desc="🚀 匹配进度", unit="样本", ncols=100) as pbar:
        for batch_idx in range(n_batches):
            batch_start = batch_idx * batch_size
            batch_end = min(batch_start + batch_size, total_samples)
            batch_samples = samples[batch_start:batch_end]
            
            batch_num = batch_idx + 1
            batch_start_time = time.time()
            
            # 并行处理当前批次
            with Pool(processes=workers, initializer=init_worker, initargs=(pattern_id,)) as pool:
                batch_results = pool.map(process_single_sample, batch_samples)
            
            batch_elapsed = time.time() - batch_start_time
            
            # 统计批次结果
            batch_success = sum(1 for r in batch_results if r.get('status') == 'success')
            batch_errors = sum(1 for r in batch_results if r.get('status') == 'error')
            batch_matched = sum(1 for r in batch_results if r.get('status') == 'success' and r.get('precision_score', 0) > 0.6)
            
            results.extend(batch_results)
            errors.extend([r for r in batch_results if r.get('status') == 'error'])
            
            # 更新进度条
            processed = len(results)
            elapsed_total = time.time() - start_time
            rate = processed / elapsed_total if elapsed_total > 0 else 0
            eta = (total_samples - processed) / rate if rate > 0 else 0
            
            # 更新进度条描述
            pbar.set_description(f"📦 批次 {batch_num}/{n_batches}")
            pbar.update(len(batch_samples))
            
            # 在进度条后显示详细信息
            pbar.set_postfix({
                '成功': f"{batch_success}",
                '匹配': f"{batch_matched}",
                '速度': f"{rate:.0f}/s",
                'ETA': f"{eta/60:.1f}min"
            })
    
    # 统计汇总
    total_time = time.time() - start_time
    
    success_results = [r for r in results if r.get('status') == 'success']
    precision_scores = [r.get('precision_score', 0) for r in success_results]
    
    # 匹配度统计（修正：只有 MATCHED 状态才算真正成格）
    matched = [r for r in success_results if r.get('pattern_status') == 'MATCHED']
    edge_cases = [r for r in success_results if r.get('pattern_status') == 'EDGE']
    # V3.1: 强匹配阈值保持0.8（相对于新的match_threshold=0.7）
    strong_matched = [r for r in matched if r.get('precision_score', 0) > 0.8]
    
    stats = {
        'total_samples': total_samples,
        'success_count': len(success_results),
        'error_count': len(errors),
        'matched_count': len(matched),
        'strong_matched_count': len(strong_matched),
        'match_rate': len(matched) / len(success_results) * 100 if success_results else 0,
        'strong_match_rate': len(strong_matched) / len(success_results) * 100 if success_results else 0,
        'avg_precision': np.mean(precision_scores) if precision_scores else 0,
        'median_precision': np.median(precision_scores) if precision_scores else 0,
        'total_time_sec': total_time,
        'total_time_min': total_time / 60,
        'processing_rate': total_samples / total_time if total_time > 0 else 0,
        'precision_distribution': {
            '0.0-0.2': sum(1 for p in precision_scores if 0.0 <= p < 0.2),
            '0.2-0.4': sum(1 for p in precision_scores if 0.2 <= p < 0.4),
            '0.4-0.6': sum(1 for p in precision_scores if 0.4 <= p < 0.6),
            '0.6-0.8': sum(1 for p in precision_scores if 0.6 <= p < 0.8),
            '0.8-1.0': sum(1 for p in precision_scores if 0.8 <= p <= 1.0),
        }
    }
    
    return {
        'stats': stats,
        'results': results,
        'errors': errors
    }


def save_results(
    output_path: Path,
    pattern_id: str,
    stats: Dict,
    results: List[Dict],
    errors: List[Dict]
):
    """保存结果到文件"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 保存统计信息
    stats_path = output_path.with_suffix('.stats.json')
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump({
            'pattern_id': pattern_id,
            'stats': stats,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2, ensure_ascii=False)
    
    # 保存详细结果（仅保存匹配的样本，避免文件过大）
    # V3.1: 只保存MATCHED状态的样本（已经是高质量筛选）
    matched_results = [r for r in results if r.get('status') == 'success' and r.get('pattern_status') == 'MATCHED']
    
    results_path = output_path.with_suffix('.matched.json')
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump({
            'pattern_id': pattern_id,
            'matched_count': len(matched_results),
            'results': matched_results,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }, f, indent=2, ensure_ascii=False)
    
    # 保存错误日志
    if errors:
        errors_path = output_path.with_suffix('.errors.json')
        with open(errors_path, 'w', encoding='utf-8') as f:
            json.dump({
                'pattern_id': pattern_id,
                'error_count': len(errors),
                'errors': errors[:100],  # 只保存前100个错误
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 结果已保存:")
    print(f"   统计信息: {stats_path}")
    print(f"   匹配结果: {results_path} ({len(matched_results):,} 个匹配样本)")
    if errors:
        print(f"   错误日志: {errors_path} ({len(errors)} 个错误)")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="批量格局匹配器（并行版）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 测试模式（单进程，1000个样本）
  python3 scripts/batch_pattern_matcher.py --pattern A-03 \\
      --data-file core/data/holographic_universe_518k.jsonl \\
      --workers 1 --limit 1000
  
  # 完整运行（8进程）
  python3 scripts/batch_pattern_matcher.py --pattern A-03 \\
      --data-file core/data/holographic_universe_518k.jsonl \\
      --workers 8
  
  # 自定义输出路径
  python3 scripts/batch_pattern_matcher.py --pattern A-03 \\
      --data-file core/data/holographic_universe_518k.jsonl \\
      --output results/a03_full_match.json
        """
    )
    
    parser.add_argument(
        '--pattern',
        type=str,
        required=True,
        help='格局ID (如: A-03, D-01, D-02)'
    )
    parser.add_argument(
        '--data-file',
        type=str,
        required=True,
        help='数据文件路径 (JSONL格式)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='输出文件路径 (默认: results/{pattern}_match.json)'
    )
    parser.add_argument(
        '--workers',
        type=int,
        default=None,
        help=f'并行进程数 (默认: CPU核心数={cpu_count()})'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制处理的样本数 (用于测试)'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=1000,
        help='每批处理的样本数 (默认: 1000)'
    )
    
    args = parser.parse_args()
    
    # 设置输出路径
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = project_root / "results" / f"{args.pattern}_match.json"
    
    # 加载样本
    data_path = Path(args.data_file)
    samples = load_samples_from_file(data_path, limit=args.limit)
    
    if not samples:
        print("❌ 没有可处理的样本")
        return
    
    # 批量处理
    result_data = process_batch(
        samples=samples,
        pattern_id=args.pattern,
        workers=args.workers,
        batch_size=args.batch_size
    )
    
    # 输出统计信息
    stats = result_data['stats']
    print(f"\n{'='*80}")
    print("📊 处理结果统计")
    print(f"{'='*80}")
    print(f"总样本数: {stats['total_samples']:,}")
    print(f"成功处理: {stats['success_count']:,}")
    print(f"处理失败: {stats['error_count']:,}")
    print(f"\n匹配统计:")
    print(f"  匹配样本 (Precision > 0.6): {stats['matched_count']:,} ({stats['match_rate']:.2f}%)")
    print(f"  强匹配 (Precision > 0.8): {stats['strong_matched_count']:,} ({stats['strong_match_rate']:.2f}%)")
    print(f"\n精确度分布:")
    for range_name, count in stats['precision_distribution'].items():
        pct = count / stats['success_count'] * 100 if stats['success_count'] > 0 else 0
        print(f"  {range_name}: {count:,} ({pct:.1f}%)")
    print(f"\n性能统计:")
    print(f"  平均精确度: {stats['avg_precision']:.4f}")
    print(f"  中位数精确度: {stats['median_precision']:.4f}")
    print(f"  总耗时: {stats['total_time_min']:.2f} 分钟 ({stats['total_time_sec']:.2f} 秒)")
    print(f"  处理速度: {stats['processing_rate']:.1f} 样本/秒")
    print(f"{'='*80}\n")
    
    # 保存结果
    save_results(
        output_path=output_path,
        pattern_id=args.pattern,
        stats=stats,
        results=result_data['results'],
        errors=result_data['errors']
    )


if __name__ == "__main__":
    main()

