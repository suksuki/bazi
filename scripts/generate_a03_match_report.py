#!/usr/bin/env python3
"""
A-03 格局匹配报告生成器
========================
从全量 51.8 万样本中扫描 A-03 格局，生成详细的匹配报告

使用方法:
    python3 scripts/generate_a03_match_report.py
"""

import json
import sys
from pathlib import Path
from collections import Counter
from datetime import datetime
import numpy as np

# 添加项目根目录
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root))

def generate_report():
    """生成 A-03 匹配报告"""
    
    result_file = project_root / "results" / "a03_full_518k_scan.matched.json"
    stats_file = project_root / "data_file" / "holographic_universe_518k.jsonl"
    
    print("=" * 80)
    print("🔬 A-03 羊刃架杀格 - 全量样本匹配验证报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # 1. 读取统计文件
    stats_data = {}
    stats_json_file = project_root / "results" / "a03_full_518k_scan.stats.json"
    if stats_json_file.exists():
        with open(stats_json_file, 'r', encoding='utf-8') as f:
            stats_data = json.load(f)
            # 提取stats字段中的信息
            if 'stats' in stats_data:
                stats_data = stats_data['stats']
    
    # 2. 分析匹配结果
    print("📊 正在分析匹配结果...")
    matched_results = []
    precision_scores = []
    mahalanobis_dists = []
    sai_values = []
    tensor_data = []
    error_count = 0
    
    # 文件是单个JSON对象，不是JSONL格式
    with open(result_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 从JSON对象中提取信息
    matched_count_from_file = data.get('matched_count', 0)
    results = data.get('results', [])
    total_samples = stats_data.get('total_samples', 518400)  # 默认51.8万
    error_count_from_stats = stats_data.get('error_count', 0)
    
    print(f"✅ 从文件中读取到 {len(results):,} 个结果")
    
    # 分析每个结果
    for result in results:
        if result.get('status') == 'error':
            error_count += 1
            continue
        
        if result.get('pattern_status') == 'MATCHED':
            matched_results.append(result)
            precision_scores.append(result.get('precision_score', 0))
            mahalanobis_dists.append(result.get('mahalanobis_dist', 0))
            sai_values.append(result.get('sai', 0))
            if 'tensor' in result:
                tensor_data.append(result['tensor'])
    
    matched_count = len(matched_results)
    match_rate = (matched_count / total_samples * 100) if total_samples > 0 else 0
    # 如果统计文件中有错误数，使用统计文件的错误数
    if error_count == 0 and error_count_from_stats > 0:
        error_count = error_count_from_stats
    
    # 3. 生成报告
    report = {
        "report_meta": {
            "pattern_id": "A-03",
            "pattern_name": "羊刃架杀格 (Blade & Killer)",
            "generated_at": datetime.now().isoformat(),
            "data_source": "holographic_universe_518k.jsonl"
        },
        "summary": {
            "total_samples": total_samples,
            "matched_count": matched_count,
            "error_count": error_count,
            "match_rate_percent": round(match_rate, 2),
            "processing_status": "✅ 完成"
        },
        "statistics": {},
        "top_matches": [],
        "distribution": {}
    }
    
    # Precision Score 统计
    if precision_scores:
        report["statistics"]["precision_score"] = {
            "max": float(np.max(precision_scores)),
            "min": float(np.min(precision_scores)),
            "mean": float(np.mean(precision_scores)),
            "median": float(np.median(precision_scores)),
            "std": float(np.std(precision_scores)),
            "q25": float(np.percentile(precision_scores, 25)),
            "q75": float(np.percentile(precision_scores, 75))
        }
        
        # 分数分布
        bins = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(precision_scores, bins=bins)
        report["distribution"]["precision_score"] = {}
        for i in range(len(bins)-1):
            count = int(hist[i])
            percentage = (count / len(precision_scores) * 100) if len(precision_scores) > 0 else 0
            report["distribution"]["precision_score"][f"{bins[i]:.1f}-{bins[i+1]:.1f}"] = {
                "count": count,
                "percentage": round(percentage, 2)
            }
    
    # Mahalanobis Distance 统计
    if mahalanobis_dists:
        report["statistics"]["mahalanobis_distance"] = {
            "min": float(np.min(mahalanobis_dists)),
            "max": float(np.max(mahalanobis_dists)),
            "mean": float(np.mean(mahalanobis_dists)),
            "median": float(np.median(mahalanobis_dists)),
            "std": float(np.std(mahalanobis_dists))
        }
    
    # SAI 统计
    if sai_values:
        report["statistics"]["sai"] = {
            "min": float(np.min(sai_values)),
            "max": float(np.max(sai_values)),
            "mean": float(np.mean(sai_values)),
            "median": float(np.median(sai_values)),
            "std": float(np.std(sai_values))
        }
    
    # Top 20 匹配案例
    sorted_results = sorted(matched_results, key=lambda x: x.get('precision_score', 0), reverse=True)
    for result in sorted_results[:20]:
        report["top_matches"].append({
            "uid": result.get('uid'),
            "line_number": result.get('line_number'),
            "precision_score": round(result.get('precision_score', 0), 4),
            "mahalanobis_dist": round(result.get('mahalanobis_dist', 0), 4),
            "sai": round(result.get('sai', 0), 4),
            "tensor": result.get('tensor', {})
        })
    
    # 4. 保存报告
    report_file = project_root / "results" / "a03_full_518k_report.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # 5. 打印摘要
    print("\n" + "=" * 80)
    print("📋 匹配摘要")
    print("=" * 80)
    print(f"总样本数: {total_samples:,}")
    print(f"匹配数量: {matched_count:,}")
    print(f"错误数量: {error_count:,}")
    print(f"匹配率: {match_rate:.2f}%")
    
    if precision_scores:
        print(f"\n📈 Precision Score 统计:")
        print(f"  最高分: {max(precision_scores):.4f}")
        print(f"  最低分: {min(precision_scores):.4f}")
        print(f"  平均分: {np.mean(precision_scores):.4f}")
        print(f"  中位数: {np.median(precision_scores):.4f}")
        print(f"  标准差: {np.std(precision_scores):.4f}")
        
        print(f"\n  分数分布:")
        bins = [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        hist, _ = np.histogram(precision_scores, bins=bins)
        for i in range(len(bins)-1):
            count = int(hist[i])
            pct = (count / len(precision_scores) * 100) if len(precision_scores) > 0 else 0
            print(f"    {bins[i]:.1f}-{bins[i+1]:.1f}: {count:,} 个 ({pct:.2f}%)")
    
    if mahalanobis_dists:
        print(f"\n📏 Mahalanobis Distance 统计:")
        print(f"  最小: {min(mahalanobis_dists):.4f}")
        print(f"  最大: {max(mahalanobis_dists):.4f}")
        print(f"  平均: {np.mean(mahalanobis_dists):.4f}")
        print(f"  中位数: {np.median(mahalanobis_dists):.4f}")
    
    if sai_values:
        print(f"\n⚡ SAI (结构总能量) 统计:")
        print(f"  最小: {min(sai_values):.4f}")
        print(f"  最大: {max(sai_values):.4f}")
        print(f"  平均: {np.mean(sai_values):.4f}")
        print(f"  中位数: {np.median(sai_values):.4f}")
    
    print(f"\n🏆 Top 10 最佳匹配案例:")
    for i, result in enumerate(sorted_results[:10], 1):
        uid = result.get('uid', 'N/A')
        precision = result.get('precision_score', 0)
        mdist = result.get('mahalanobis_dist', 0)
        sai = result.get('sai', 0)
        uid_str = str(uid) if uid != 'N/A' else 'N/A'
        print(f"  {i:2d}. UID {uid_str:>6s}: Precision={precision:.4f}, M-Dist={mdist:.4f}, SAI={sai:.4f}")
    
    print(f"\n✅ 报告已保存到: {report_file}")
    print("=" * 80)
    
    return report

if __name__ == "__main__":
    try:
        generate_report()
    except Exception as e:
        print(f"❌ 错误: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

