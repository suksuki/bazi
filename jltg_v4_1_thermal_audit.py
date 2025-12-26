
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
    print("🔥 [JLTG V4.1] 建禄月劫核心热失控审计报告")
    print("="*80)
    
    scout = PatternScout()
    synth = SyntheticBaziEngine()
    
    print("📡 Phase 1: 标签海选 (Tag Screening) 启动...")
    print("目标：从 51.84 万样本中提取“建禄/月劫”高内能结构。")
    
    candidates = []
    total_scanned = 0
    start_time = time.time()
    
    # 模拟一个“冲禄”流年
    # 例如：甲子月(Zi) vs 午(Wu) Annual
    test_annual = ('壬', '午') # Clashes with Zi month
    
    # We need to test against charts that have Zi month for clash, or just generic
    # Let's inject a generic clash trigger based on the chart's month later in the logic?
    # No, PatternScout logic checks against inputted Annual.
    # To test oscillation, we need the annual branch to clash the month branch.
    # Since we scan ALL charts, some will have month that clashes with 'Wu'.
    
    for chart in synth.generate_all_bazi():
        total_scanned += 1
        year_pillar = chart[0] # Not used for clash check in logic directly, month is chart[1]
        
        # Inject standard Luck
        test_chart = chart + [('庚', '寅'), test_annual]
        
        res = scout._deep_audit(test_chart, "JLTG_CORE_ENERGY")
        if res:
            candidates.append(res)
    
    elapsed = time.time() - start_time
    print(f"✅ 海选完成。扫描样本: {total_scanned:,} | 命中候选: {len(candidates):,} | 耗时: {elapsed:.2f}s")
    
    # Phase 2: Core Sub-Package Analysis
    sub_pkg_stats = defaultdict(int)
    for c in candidates:
        sub_pkg_stats[c['sub_package_id']] += 1
        
    print("\n📊 Phase 2: 核心构型分布 (Core Configuration)")
    pkg_names = {
        "P_114A": "建禄-稳态核心 (Jian Lu)", 
        "P_114B": "月劫-湍流核心 (Yue Jie)"
    }
    for pkg, count in sub_pkg_stats.items():
        name = pkg_names.get(pkg, pkg)
        print(f" - {pkg} [{name}]: {count:,} samples ({count/len(candidates)*100:.1f}%)")
        
    # Phase 3: Thermal Balance & Runaway Audit
    print("\n🛡️ Phase 3: 热失控与核心震荡审计 (Thermal Runaway Audit)")
    
    stable_samples = [c for c in candidates if "STABLE_CORE" in c['category']][:5]
    runaway_samples = [c for c in candidates if "THERMAL_RUNAWAY" in c['category']][:5]
    oscillation_samples = [c for c in candidates if "CORE_OSCILLATION" in c['category']][:5]

    print("\n🧊 [热平衡稳态] (Stable Core):")
    for s in stable_samples:
        print(f" ✅ {s['label']} | Balance: {s['thermal_balance']} | SAI: {s['sai']}")

    print("\n🔥 [核心熔毁/热失控] (Thermal Runaway):")
    for s in runaway_samples:
        print(f" ☢️ {s['label']} | Balance: {s['thermal_balance']} | SAI: {s['sai']}")

    print("\n🌋 [核心震荡/冲禄] (Core Oscillation):")
    for s in oscillation_samples:
        print(f" 🧨 {s['label']} | Balance: {s['thermal_balance']} | Clash: YES | SAI: {s['sai']}")

    # Final Stats
    avg_sai = sum(float(c['sai']) for c in candidates) / len(candidates)
    runaway_rate = len([c for c in candidates if c['is_runaway'] == "YES"]) / len(candidates) * 100
    oscillation_rate = len([c for c in candidates if c['is_oscillation'] == "YES"]) / len(candidates) * 100
    
    print("\n" + "="*80)
    print("📈 审计总结：")
    print(f" - 平均热应力 (μ-SAI): {avg_sai:.2f}")
    print(f" - 热失控发生率 (Runaway Rate): {runaway_rate:.2f}%")
    print(f" - 核心震荡率 (Oscillation Rate): {oscillation_rate:.2f}%")
    print(" - 物理结论：建禄/月劫核心自带高电位，若缺乏负载(官杀食伤)或遭遇冲禄(年冲月)，SAI 将因内能溢出而发生结构性崩塌。")
    print("-" * 80)
    print("🏁 MOD_114 [JLTG] 核心热失控模型定标完成。")

if __name__ == "__main__":
    main()
