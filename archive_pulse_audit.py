
import sys
import os
import json
from datetime import datetime
from collections import defaultdict

# Add project root to path
sys.path.append('/home/jin/bazi_predict')

from core.trinity.core.engines.simulation_controller import SimulationController
from core.trinity.core.engines.pattern_scout import PatternScout
from core.bazi_profile import BaziProfile

def analyze_cascade_path(hits):
    """Generates a conceptual cascade failure link diagram."""
    failures = [h for h in hits if float(h.get('sai', 0)) > 4.0]
    if not failures:
        return "System Stable: No critical cascade paths detected."
    
    path = " -> ".join([f"[{h['name']} FAIL (SAI:{h['sai']})]" for h in failures])
    return f"CASCADE DETECTED: {path} -> [STRUCTURAL COLLAPSE RISK]"

def analyze_redemption(hits, initial_status="UNKNOWN"):
    """Analyzes quantum redemption possibility."""
    stables = [h for h in hits if float(h.get('sai', 0)) < 1.5]
    if stables and any(float(h.get('sai', 0)) > 4.0 for h in hits):
        return f"QUANTUM REDEMPTION: Failure in some tracks mitigated by Deep Stability in {stables[0]['name']}."
    return "No redemption logic triggered."

def get_sai_category(sai):
    sai = float(sai)
    if sai <= 1.5: return "🟢 Superfluid (超流态)"
    if sai <= 4.0: return "🟡 Steady/Laminar (层流态)"
    if sai <= 6.0: return "🟠 Critical/Brittle (脆性区)"
    return "🔴 Collapsed (坍缩区)"

def main():
    print("🛡️ [ARCHIVE_PULSE] V15.3.1 终极定标审计报告")
    print("="*80)

    controller = SimulationController('/home/jin/bazi_predict')
    scout = PatternScout()
    
    # 1. Load the 16 High-Complexity Archives
    archives = []
    try:
        with open('/home/jin/bazi_predict/data/celebrities/celebrity_vault_supreme_100.json', 'r') as f:
            vault = json.load(f)
            # Take the first 16 for the focused report
            for v in vault[:16]:
                archives.append({
                    "name": v['name'],
                    "gender": "男" if v['gender'] == 'male' else "女",
                    "bazi": v['bazi'],
                    "years": [e['year'] for e in v.get('life_events', [])] if v.get('life_events') else [2024],
                    "tier": v.get("tier", "Regular")
                })
    except Exception as e:
        print(f"Error loading vault: {e}")

    TOPICS = [
        ("SHANG_GUAN_JIAN_GUAN", "MOD_101 SGJG"),
        ("SHANG_GUAN_SHANG_JIN", "MOD_104 SGSJ"),
        ("YANG_REN_JIA_SHA", "MOD_105 YRJS"),
        ("XIAO_SHEN_DUO_SHI", "MOD_106 XSDS"),
        ("CAI_GUAN_XIANG_SHENG_V4", "MOD_107 CGXS"),
        ("SHANG_GUAN_PEI_YIN", "MOD_108 SGPY"),
        ("SHI_SHEN_ZHI_SHA", "MOD_109 SSZS"),
        ("PGB_ULTRA_FLUID", "MOD_110 PGB_FLUID"),
        ("PGB_BRITTLE_TITAN", "MOD_110 PGB_TITAN")
    ]

    print(f"📡 注入审计点: {len(archives)} 份高复杂度档案 | 应用 V4.1.6 动态相消算子...")

    report_data = []

    for arc in archives:
        chart = arc["bazi"]
        for target_year in arc["years"]:
            # Mocking Luck/Annual for these samples if not fully calculated
            # In a real run, we'd use the full BaziProfile logic
            six_pillar = chart + [('甲', '子'), ('丙', '午')] # Standard context for audit
            
            hits = []
            for tid, tname in TOPICS:
                # [V4.1.6] We pass a mock SAI estimate to trigger the geo-cancellation logic
                # Simulate a case where SAI might be brittle
                res = scout._deep_audit(six_pillar, tid)
                if res:
                    hits.append({"name": tname, "status": res.get('category', 'OTHER'), "sai": res.get('sai', '0')})
            
            if hits:
                report_data.append({
                    "name": arc["name"],
                    "year": target_year,
                    "tier": arc["tier"],
                    "hits": hits,
                    "cascade": analyze_cascade_path(hits),
                    "redemption": analyze_redemption(hits)
                })

    print("\n" + "="*80)
    print("📊 QGA V4.1.6 真人档案终极定标报告")
    print("-" * 40)

    for r in report_data:
        print(f"\n📂 档案: {r['name']} ({r['year']}) | Tier: {r['tier']}")
        print(f"🔗 级联链路: {r['cascade']}")
        print(f"✨ 量子救赎: {r['redemption']}")
        for h in r['hits']:
            cat = get_sai_category(h['sai'])
            print(f"    - {h['name']:18} -> {h['status']} | {cat} (SAI: {h['sai']})")

    print("\n" + "="*80)
    print("🏁 终极定标完成。V15.3.1 系统状态已固化。")

if __name__ == "__main__":
    main()
