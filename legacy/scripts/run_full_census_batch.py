
import sys
import os
import json
import logging
import time
import numpy as np
from datetime import datetime

sys.path.insert(0, os.getcwd())

from core.logic_compiler import get_knowledge_census
from core.protocol_checker import LOGIC_PROTOCOLS

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
BASE_PATTERNS = ["A-01", "A-02", "A-03", "B-01", "B-02", "C-01", "C-02", "D-01", "D-02"]
BRANCHES = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
BRANCH_EN_MAP = {
    '子': 'Rat', '丑': 'Ox', '寅': 'Tiger', '卯': 'Rabbit', '辰': 'Dragon', '巳': 'Snake',
    '午': 'Horse', '未': 'Goat', '申': 'Monkey', '酉': 'Rooster', '戌': 'Dog', '亥': 'Pig'
}

BATCH_LIMIT = 50000  # Scan limit per task
REPORT_PATH = "census_preview_report.md"

def run_full_census():
    """
    Execute Full Universe Census for 108 Patterns.
    """
    start_time = time.time()
    census = get_knowledge_census()
    from core.census_cache import get_census_cache
    cache = get_census_cache()

    results = []
    
    print("🚀 Starting FULL UNIVERSE CENSUS [108 Patterns]...")
    total_tasks = len(BASE_PATTERNS) * len(BRANCHES)
    completed = 0
    
    for base in BASE_PATTERNS:
        base_proto = LOGIC_PROTOCOLS.get(base, {})
        base_name = base_proto.get('name', base)
        
        for branch in BRANCHES:
            target_id = f"{base}@{branch}"
            branch_en = BRANCH_EN_MAP.get(branch, branch)
            
            logger.info(f"[{completed+1}/{total_tasks}] Scanning {target_id} ({base_name} in {branch_en})...")
            
            try:
                # 1. Execute Census
                res = census.request_census(target_id, limit=BATCH_LIMIT, include_tensor=True)
                
                # 2. Cache Result (calculates physics)
                cache_res = cache.cache_census_result(
                    target_id, 
                    res['samples'], 
                    {'name': f"{base_name} @ {branch}"}
                )
                
                # 3. Analyze Physics Confidence
                # We use Abundance and Trace of Covariance (Stability) as proxy
                samples_count = res['matched_count']
                abundance = res['abundance']
                
                stability_score = 0.0
                confidence_score = 0.0
                
                # Get the cached object to see covariance
                cached_obj = cache.get_cached_manifold(target_id)
                if cached_obj:
                    cov = np.array(cached_obj.get('covariance', []))
                    if cov.shape == (5,5):
                        trace_cov = np.trace(cov)
                        # Lower trace = more compact = higher stability
                        stability_score = 1.0 / (trace_cov + 1e-5) 
                        # Mock confidence score
                        confidence_score = min(0.99, stability_score * 0.1 * abundance * 1000)

                results.append({
                    "id": target_id,
                    "name": f"{base_name} @ {branch}",
                    "samples": samples_count,
                    "abundance": abundance,
                    "stability": stability_score,
                    "confidence": confidence_score,
                    "mean_E": cached_obj.get("mean_vector", [0]*5)[0] if cached_obj else 0
                })
                
            except Exception as e:
                logger.error(f"Failed {target_id}: {e}")
            
            completed += 1
            
    elapsed = time.time() - start_time
    generate_report(results, elapsed)
    print(f"\n✅ Census Completed in {elapsed:.2f}s. Report generated at {REPORT_PATH}")

def generate_report(results, elapsed):
    """Generate Markdown report."""
    
    # Sort by Confidence (Stability)
    sorted_by_conf = sorted(results, key=lambda x: x['confidence'], reverse=True)
    # Sort by Abundance
    sorted_by_abun = sorted(results, key=lambda x: x['abundance'], reverse=True)
    
    top_3_conf = sorted_by_conf[:3]
    bottom_3_conf = sorted_by_conf[-3:]
    
    top_3_abun = sorted_by_abun[:3]
    
    md = f"""# 🌌 全量宇宙普查报告 (Census Preview)

**Run ID**: FULL_UNIVERSE_BATCH_001
**Time**: {datetime.now().isoformat()}
**Total Patterns**: 108
**Execution Time**: {elapsed:.2f}s

## 🏆 领奖台 (The Podium)

### 🥇 物理置信度最高 (Most Stable Manifolds)
这些格局在 5D 空间中聚类最紧密，物理定义最稳固。

| 格局 ID | 名称 | 样本数 | 稳定性 (1/Tr) | 丰度 |
| :--- | :--- | :--- | :--- | :--- |
"""
    for r in top_3_conf:
        md += f"| **{r['id']}** | {r['name']} | {r['samples']} | {r['stability']:.2f} | {r['abundance']:.4f} |\n"
        
    md += """
### 👻 量子幽灵 (Quantum Ghosts)
这些格局极其稀缺或物理极其发散，难以被现有物理引擎捕捉。

| 格局 ID | 名称 | 样本数 | 稳定性 | 丰度 |
| :--- | :--- | :--- | :--- | :--- |
"""
    for r in bottom_3_conf:
        md += f"| `{r['id']}` | {r['name']} | {r['samples']} | {r['stability']:.2f} | {r['abundance']:.6f} |\n"

    md += """
## 🚨 丰度异常报警 (Abundance Anomalies)
以下格局覆盖率过高，可能存在“古典定义过宽”的问题。

| 格局 ID | 名称 | 丰度 | 样本数 |
| :--- | :--- | :--- | :--- |
"""
    for r in top_3_abun:
        md += f"| ⚠️ {r['id']} | {r['name']} | **{r['abundance']:.4f}** | {r['samples']} |\n"

    md += """
## 📊 统计摘要
- **总扫描样本**: ~51.8k * 108 (Mock Limit per batch {BATCH_LIMIT})
- **平均丰度**: {sum(r['abundance'] for r in results)/len(results):.6f}
- **平均稳定性**: {sum(r['stability'] for r in results)/len(results):.2f}

"""
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(md)

if __name__ == "__main__":
    run_full_census()
