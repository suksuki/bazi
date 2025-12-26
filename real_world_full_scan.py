
import sys
import os
from datetime import datetime

# Add project root to path
sys.path.append('/home/jin/bazi_predict')

from core.profile_manager import ProfileManager
from core.bazi_profile import BaziProfile
from core.trinity.core.engines.pattern_scout import PatternScout
from core.trinity.core.nexus.definitions import BaziParticleNexus

def main():
    print("⛩️ [V15.7.5] 真实档案全物理格局深度扫描")
    print("="*80)
    
    pm = ProfileManager()
    scout = PatternScout()
    profiles = pm.get_all()
    
    # Target Year for context (2025 Yi-Si)
    target_year = 2025
    annual_2025 = ('乙', '巳')
    
    all_matches = []
    
    # Patterns to scan (New V4.1 additions)
    # SSSC (Amplifier), JLTG (Core Energy), CYGS (Collapse), HGFG (Transmutation)
    modes = ["SSSC_AMPLIFIER", "JLTG_CORE_ENERGY", "CYGS_COLLAPSE", "HGFG_TRANSMUTATION"]
    
    print(f"📡 正在对 {len(profiles)} 份核心档案执行 [SSSC/JLTG/CYGS/HGFG] 并发审计...")
    
    for p in profiles:
        try:
            bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
            profile_obj = BaziProfile(bdt, 1 if p['gender'] == '男' else 0)
            
            luck_pillar_str = profile_obj.get_luck_pillar_at(target_year)
            luck_pillar = (luck_pillar_str[0], luck_pillar_str[1])
            natal = profile_obj.pillars
            chart = [natal['year'], natal['month'], natal['day'], natal['hour'], luck_pillar, annual_2025]
            
            p_matches = []
            for mode in modes:
                res = scout._deep_audit(chart, mode)
                if res:
                    p_matches.append(res)
            
            if p_matches:
                # Sort by SAI
                p_matches.sort(key=lambda x: float(x.get('stress', 0)), reverse=True)
                top_match = p_matches[0]
                
                all_matches.append({
                    "name": p['name'],
                    "main_pattern": top_match['topic_name'],
                    "category": top_match['category'],
                    "sai": top_match['stress'],
                    "all_patterns": [m['topic_name'] for m in p_matches]
                })

        except Exception as e:
            print(f"⚠️ 档案 {p['name']} 解析异常: {e}")

    print("\n📊 真实档案新格局匹配名录:")
    if not all_matches:
        print("💡 未发现匹配样本。")
    else:
        # Group by pattern
        grouped = {}
        for m in all_matches:
            pat = m['main_pattern']
            if pat not in grouped: grouped[pat] = []
            grouped[pat].append(m)
            
        for pat, items in grouped.items():
            print(f"\n🏷️ {pat}:")
            for item in items:
                print(f"  - [{item['name']}] -> {item['category']} (SAI: {item['sai']})")
                if len(item['all_patterns']) > 1:
                     print(f"    * 复合命中: {', '.join(item['all_patterns'])}")

    print("\n🏁 扫描完毕。")

if __name__ == "__main__":
    main()
