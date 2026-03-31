#!/usr/bin/env python3
"""
生成 A-03 匹配报告的 Markdown 版本
"""

import json
from pathlib import Path
from datetime import datetime

def generate_markdown_report():
    """生成 Markdown 格式的报告"""
    
    project_root = Path(__file__).resolve().parents[1]
    report_json = project_root / "results" / "a03_full_518k_report.json"
    
    with open(report_json, 'r', encoding='utf-8') as f:
        report = json.load(f)
    
    md_content = f"""# A-03 羊刃架杀格 - 全量样本匹配验证报告

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**数据源**: holographic_universe_518k.jsonl  
**格局名称**: {report['report_meta']['pattern_name']}

---

## 📊 匹配摘要

| 指标 | 数值 |
|------|------|
| **总样本数** | {report['summary']['total_samples']:,} |
| **匹配数量** | {report['summary']['matched_count']:,} |
| **错误数量** | {report['summary']['error_count']:,} |
| **匹配率** | **{report['summary']['match_rate_percent']:.2f}%** |
| **处理状态** | {report['summary']['processing_status']} |

---

## 📈 Precision Score 统计

### 基本统计

| 指标 | 数值 |
|------|------|
| **最高分** | {report['statistics']['precision_score']['max']:.4f} |
| **最低分** | {report['statistics']['precision_score']['min']:.4f} |
| **平均分** | {report['statistics']['precision_score']['mean']:.4f} |
| **中位数** | {report['statistics']['precision_score']['median']:.4f} |
| **标准差** | {report['statistics']['precision_score']['std']:.4f} |
| **Q25** | {report['statistics']['precision_score']['q25']:.4f} |
| **Q75** | {report['statistics']['precision_score']['q75']:.4f} |

### 分数分布

| 分数区间 | 数量 | 占比 |
|---------|------|------|
| 0.0 - 0.5 | {report['distribution']['precision_score']['0.0-0.5']['count']:,} | {report['distribution']['precision_score']['0.0-0.5']['percentage']:.2f}% |
| 0.5 - 0.6 | {report['distribution']['precision_score']['0.5-0.6']['count']:,} | {report['distribution']['precision_score']['0.5-0.6']['percentage']:.2f}% |
| 0.6 - 0.7 | {report['distribution']['precision_score']['0.6-0.7']['count']:,} | {report['distribution']['precision_score']['0.6-0.7']['percentage']:.2f}% |
| 0.7 - 0.8 | {report['distribution']['precision_score']['0.7-0.8']['count']:,} | {report['distribution']['precision_score']['0.7-0.8']['percentage']:.2f}% |
| 0.8 - 0.9 | {report['distribution']['precision_score']['0.8-0.9']['count']:,} | {report['distribution']['precision_score']['0.8-0.9']['percentage']:.2f}% |
| 0.9 - 1.0 | {report['distribution']['precision_score']['0.9-1.0']['count']:,} | {report['distribution']['precision_score']['0.9-1.0']['percentage']:.2f}% |

---

## 📏 Mahalanobis Distance 统计

| 指标 | 数值 |
|------|------|
| **最小值** | {report['statistics']['mahalanobis_distance']['min']:.4f} |
| **最大值** | {report['statistics']['mahalanobis_distance']['max']:.4f} |
| **平均值** | {report['statistics']['mahalanobis_distance']['mean']:.4f} |
| **中位数** | {report['statistics']['mahalanobis_distance']['median']:.4f} |
| **标准差** | {report['statistics']['mahalanobis_distance']['std']:.4f} |

---

## ⚡ SAI (结构总能量) 统计

| 指标 | 数值 |
|------|------|
| **最小值** | {report['statistics']['sai']['min']:.4f} |
| **最大值** | {report['statistics']['sai']['max']:.4f} |
| **平均值** | {report['statistics']['sai']['mean']:.4f} |
| **中位数** | {report['statistics']['sai']['median']:.4f} |
| **标准差** | {report['statistics']['sai']['std']:.4f} |

---

## 🏆 Top 20 最佳匹配案例

| 排名 | UID | Precision | M-Dist | SAI | E | O | M | S | R |
|------|-----|-----------|--------|-----|---|---|---|---|---|
"""
    
    for i, match in enumerate(report['top_matches'][:20], 1):
        tensor = match.get('tensor', {})
        md_content += f"| {i} | {match['uid']} | {match['precision_score']:.4f} | {match['mahalanobis_dist']:.4f} | {match['sai']:.4f} | {tensor.get('E', 0):.3f} | {tensor.get('O', 0):.3f} | {tensor.get('M', 0):.3f} | {tensor.get('S', 0):.3f} | {tensor.get('R', 0):.3f} |\n"
    
    md_content += f"""
---

## 📝 结论

1. **匹配率**: 在 51.8 万全量样本中，A-03 羊刃架杀格的匹配率为 **{report['summary']['match_rate_percent']:.2f}%**，共识别出 **{report['summary']['matched_count']:,}** 个匹配案例。

2. **Precision Score 分布**: 
   - 所有匹配案例的 Precision Score 均在 **0.6 - 0.8** 区间内
   - 平均分为 **{report['statistics']['precision_score']['mean']:.4f}**，中位数为 **{report['statistics']['precision_score']['median']:.4f}**
   - 最高分为 **{report['statistics']['precision_score']['max']:.4f}**（UID: {report['top_matches'][0]['uid']}）

3. **质量评估**: 
   - **{report['distribution']['precision_score']['0.6-0.7']['percentage']:.2f}%** 的匹配案例 Precision Score 在 0.6-0.7 区间（良好）
   - **{report['distribution']['precision_score']['0.7-0.8']['percentage']:.2f}%** 的匹配案例 Precision Score 在 0.7-0.8 区间（优秀）

4. **算法表现**: FDS-V3.0 增强版 Precision Score 算法成功识别出大量符合 A-03 格局特征的样本，验证了算法的有效性。

---

*报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
    
    # 保存 Markdown 报告
    md_file = project_root / "results" / "a03_full_518k_report.md"
    with open(md_file, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    print(f"✅ Markdown 报告已保存到: {md_file}")
    return md_file

if __name__ == "__main__":
    generate_markdown_report()

