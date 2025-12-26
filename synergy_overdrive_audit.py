
import sys
import os
from collections import defaultdict

# Add project root to path
sys.path.append('/home/jin/bazi_predict')

from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine
from core.trinity.core.engines.pattern_scout import PatternScout
from core.trinity.core.nexus.definitions import BaziParticleNexus

def main():
    print("🚀 [SYNERGY_OVERDRIVE] V4.1 全系统协同对撞报告")
    print("="*70)

    engine = SyntheticBaziEngine()
    scout = PatternScout()

    # 模拟毁灭性环境：岁运并临 + 强力冲克
    # 戊午年，大运 戊午 -> 伏吟加压
    # 流年：子年 -> 冲开午库 & 冲击根基
    LUCK = ('戊', '午')
    ANNUAL = ('甲', '子') 

    PATTERNS = [
        "CAI_GUAN_XIANG_SHENG_V4",
        "SHANG_GUAN_PEI_YIN",
        "SHI_SHEN_ZHI_SHA",
        "SHANG_GUAN_JIAN_GUAN",
        "PGB_ULTRA_FLUID",
        "PGB_BRITTLE_TITAN"
    ]

    # Failure indicators
    FAIL_MAP = ["BURNOUT", "COLLAPSE", "OVERLOAD", "LOST", "OFFLINE", "BREAKDOWN", "FRACTURE", "BOUND", "OVERFLOW", "TRANSITION", "CRITICAL"]
    STABLE_MAP = ["STEADY", "TUNNEL", "PRECISE", "LOCK", "SUPER", "BAND_STOP", "OK"]

    stats = {
        "samples_scanned": 0,
        "synergy_hit": 0,
        "cascade_failures": [],
        "quantum_redemptions": [],
        "complex_cases": []
    }

    TARGET_SAMPLES = 50000
    print(f"📡 注入序列: 大运 [{LUCK[0]}{LUCK[1]}] | 流年 [{ANNUAL[0]}{ANNUAL[1]}]")
    print(f"⚙️ 正在执行系统交叉对撞...")

    count = 0
    for chart in engine.generate_all_bazi():
        count += 1
        if count > TARGET_SAMPLES: break
        
        active_states = []
        full_chart = list(chart) + [LUCK, ANNUAL]
        
        has_fail = False
        has_stable = False
        fail_list = []
        
        for pid in PATTERNS:
            res = scout._deep_audit(full_chart, pid)
            if res:
                cat = res.get('category', '')
                active_states.append((pid.split('_')[0], cat))
                if any(x in cat for x in FAIL_MAP):
                    has_fail = True
                    fail_list.append(cat)
                if any(x in cat for x in STABLE_MAP):
                    has_stable = True

        if len(active_states) >= 2:
            stats["synergy_hit"] += 1
            entry = {"chart": " ".join([f"{p[0]}{p[1]}" for p in chart]), "states": active_states}
            
            if len(fail_list) >= 2:
                if has_stable:
                    stats["quantum_redemptions"].append(entry)
                else:
                    stats["cascade_failures"].append(entry)
            
            if len(active_states) >= 3:
                stats["complex_cases"].append(entry)

    print("\n" + "="*70)
    print(f"📊 对撞结论 (Base: {TARGET_SAMPLES})")
    print("-" * 40)
    print(f"协同格局命中率: {stats['synergy_hit']/TARGET_SAMPLES*100:.2f}%")
    print(f"级联失效风险 (Cascade Fail): {len(stats['cascade_failures'])}")
    print(f"量子救赎概率 (Redemption): {len(stats['quantum_redemptions'])}")
    print("-" * 40)

    if stats["complex_cases"]:
        print("\n🔬 [多格局级联表现 - 节点采样]")
        for c in stats["complex_cases"][:3]:
            print(f"  样本: {c['chart']}")
            for pid, cat in c['states']:
                icon = "🛑" if any(x in cat for x in FAIL_MAP) else ("💎" if any(x in cat for x in STABLE_MAP) else "⚪")
                print(f"    {icon} {pid:10} -> {cat}")

if __name__ == "__main__":
    main()
