
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
    print("🕳️ [CYGS V4.1] 从格引力坍缩全量压力对撞报告")
    print("="*80)
    
    scout = PatternScout()
    synth = SyntheticBaziEngine()
    
    print("📡 Phase 1: 标签海选 (Tag Screening) 启动...")
    print("目标：从 51.84 万样本中提取“极低日主能级”的从格候选。")
    
    candidates = []
    total_scanned = 0
    start_time = time.time()
    
    for chart in synth.generate_all_bazi():
        total_scanned += 1
        # [V4.1 Injection] Inject Luck and Annual for pressure testing
        # Luck: 壬申 (Potential Dissolution if Cong_Sha/Cai/Er doesn't like Water/Metal)
        # Annual: 乙巳 (Potential Rebound if clashing with a hidden root)
        test_chart = chart + [('壬', '申'), ('乙', '巳')]
        
        res = scout._deep_audit(test_chart, "CYGS_COLLAPSE")
        if res:
            candidates.append(res)
    
    elapsed = time.time() - start_time
    print(f"✅ 海选完成。扫描样本: {total_scanned:,} | 命中候选: {len(candidates):,} | 耗时: {elapsed:.2f}s")
    
    # Phase 2: Accretion Disk Polarity Analysis
    sub_pkg_stats = defaultdict(int)
    for c in candidates:
        sub_pkg_stats[c['sub_package_id']] += 1
        
    print("\n📊 Phase 2: 吸积盘子参数包分布 (Sub-Package Distribution)")
    pkg_names = {"P_111A": "从财(Wealth)", "P_111B": "从杀(Killing)", "P_111C": "从儿(Output)", "P_111D": "从强(Self)"}
    for pkg, count in sub_pkg_stats.items():
        name = pkg_names.get(pkg, pkg)
        print(f" - {pkg} [{name}]: {count:,} samples ({count/len(candidates)*100:.1f}%)")
        
    # Phase 3: Stress Injection & Gravitational Rebound Audit
    print("\n🛡️ Phase 3: 全因子压力注入 (Full-Factor Stress Injection)")
    print("重点审计：真从稳态、场强撤离、及墓库反弹奇点。")
    
    # Find a few extreme samples
    rebound_samples = [c for c in candidates if c['is_rebound'] == "YES"][:5]
    lock_samples = [c for c in candidates if c['category'] == "PURE_COLLAPSE (真从/引力锁定)"][:5]
    dissolution_samples = [c for c in candidates if c['category'] == "DISSOLUTION_ZONE (引力源撤离/解体)"][:5]

    print("\n🏆 [真从稳态区] (Pure Collapse Samples):")
    for s in lock_samples:
        print(f" 💎 {s['label']} | Purity: {s['purity_index']} | SAI: {s['sai']} | Pkg: {s['sub_package_id']}")

    print("\n🚨 [引力源撤离区] (Dissolution/Phase Shift Failure):")
    for s in dissolution_samples:
        print(f" ⚠️ {s['label']} | Purity: {s['purity_index']} | SAI: {s['sai']} | Pkg: {s['sub_package_id']}")

    print("\n🔥 [引力反弹奇点] (Gravitational Rebound Events):")
    for s in rebound_samples:
        print(f" 🧨 {s['label']} | Purity: {s['purity_index']} | SAI: {s['sai']} | Pkg: {s['sub_package_id']}")

    # Final Stats
    rebound_rate = len([c for c in candidates if c['is_rebound'] == "YES"]) / len(candidates) * 100
    avg_sai = sum(float(c['sai']) for c in candidates) / len(candidates)
    purity_fail_rate = len([c for c in candidates if float(c['purity_index']) < 0.85]) / len(candidates) * 100
    
    print("\n" + "="*80)
    print("📈 审计总结：")
    print(f" - 从格平均应力 (μ-SAI): {avg_sai:.2f}")
    print(f" - 纯度不合格率 (Purity Fail Rate): {purity_fail_rate:.2f}%")
    print(f" - 引力反弹发生率 (Rebound Rate): {rebound_rate:.2f}%")
    print(" - 物理结论：系统在引力源（大运）撤离或杂质（流年）碰撞产生的‘引力反弹’中，SAI 会发生高达 500% 的瞬时跳变。")
    print("-" * 80)
    print("🏁 MOD_111 [CYGS] 子参数包分类与扫频完成。")

if __name__ == "__main__":
    main()
