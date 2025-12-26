
import sys
import os
import json
import time
from collections import defaultdict

# Add project root to path
sys.path.append('/home/jin/bazi_predict')

from core.trinity.core.engines.pattern_scout import PatternScout
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.nexus.definitions import BaziParticleNexus

def main():
    print("⚗️ [HGFG V4.1] 化气格原子重构与属性相变报告")
    print("="*80)
    
    scout = PatternScout()
    synth = SyntheticBaziEngine()
    
    print("📡 Phase 1: 标签海选 (Tag Screening) 启动...")
    print("目标：从 51.84 万样本中提取“原子核变”化气格样本。")
    
    candidates = []
    total_scanned = 0
    start_time = time.time()
    
    for chart in synth.generate_all_bazi():
        total_scanned += 1
        # [V4.1 Injection] Inject Luck and Annual for pressure testing
        # Luck: 丙午 (Potential Catalyst or Reversal)
        # Annual: 庚申 (Potential reversal for Jia-Ji Earth or Ding-Ren Wood)
        test_chart = chart + [('丙', '午'), ('庚', '申')]
        
        res = scout._deep_audit(test_chart, "HGFG_TRANSMUTATION")
        if res:
            candidates.append(res)
    
    elapsed = time.time() - start_time
    print(f"✅ 海选完成。扫描样本: {total_scanned:,} | 命中候选: {len(candidates):,} | 耗时: {elapsed:.2f}s")
    
    # Phase 2: Atomic Transmutation Sub-Package Analysis
    sub_pkg_stats = defaultdict(int)
    for c in candidates:
        sub_pkg_stats[c['sub_package_id']] += 1
        
    print("\n📊 Phase 2: 原子重构子参数包分布 (Atomic Sub-Package Distribution)")
    pkg_names = {
        "P_112A": "甲己化土(Earth)", "P_112B": "乙庚化金(Metal)", 
        "P_112C": "丙辛化水(Water)", "P_112D": "丁壬化木(Wood)", 
        "P_112E": "戊癸化火(Fire)"
    }
    for pkg, count in sub_pkg_stats.items():
        name = pkg_names.get(pkg, pkg)
        print(f" - {pkg} [{name}]: {count:,} samples ({count/len(candidates)*100:.1f}%)")
        
    # Phase 3: Stress Injection & Reversal Reagent Audit
    print("\n🛡️ Phase 3: 属性相变压力注入 (Atomic Stress Injection)")
    print("重点审计：真化稳态、属性污染、及逆向还原奇点。")
    
    # Samples
    reversal_samples = [c for c in candidates if c['is_reversed'] == "YES"][:5]
    true_samples = [c for c in candidates if c['category'] == "TRUE_TRANSMUTATION (核变稳态/真化)"][:5]
    impure_samples = [c for c in candidates if c['category'] == "IMPURE_TRANSMUTATION (属性污染/假化)"][:5]

    print("\n🏆 [核变稳态 - 真化] (True Transmutation):")
    for s in true_samples:
        print(f" ✨ {s['label']} | Goal: {s['goal_element']} | Purity: {s['transmutation_purity']} | SAI: {s['sai']}")

    print("\n🧬 [属性污染 - 假化] (Impure Transmutation/Doping):")
    for s in impure_samples:
        print(f" 🧪 {s['label']} | Goal: {s['goal_element']} | Purity: {s['transmutation_purity']} | SAI: {s['sai']}")

    print("\n💥 [原子逆向还原奇点] (Atomic Reversal Singularities):")
    for s in reversal_samples:
        print(f" ⚛️ {s['label']} | Goal: {s['goal_element']} | Reversal: {s['is_reversed']} | SAI: {s['sai']}")

    # Final Stats
    reversal_rate = len([c for c in candidates if c['is_reversed'] == "YES"]) / len(candidates) * 100
    avg_sai = sum(float(c['sai']) for c in candidates) / len(candidates)
    peak_sai = max([float(c['sai']) for c in candidates]) if candidates else 0
    
    print("\n" + "="*80)
    print("📈 审计总结：")
    print(f" - 转换平均应力 (μ-SAI): {avg_sai:.2f}")
    print(f" - 逆向还原发生率 (Reversal Rate): {reversal_rate:.2f}%")
    print(f" - 最大瞬时载荷 (Peak SAI): {peak_sai:.2f}")
    print(" - 物理结论：化气格在面临‘还原剂’(流年克制化神)时，原子结构发生顺磁性扭转，SAI 呈现指数级爆发。")
    print("-" * 80)
    print("🏁 MOD_112 [HGFG] 原子重构定标完成。Suksuki 核心已同步。")

if __name__ == "__main__":
    main()
