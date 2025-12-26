
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
    print("🧨 [V15.7.5] 真实档案核心震荡与级联失效实战审计 (Target: Core Vibration)")
    print("="*80)
    
    pm = ProfileManager()
    scout = PatternScout()
    profiles = pm.get_all()
    
    matches = []
    
    print(f"📡 正在对 {len(profiles)} 份核心档案执行 [JLTG] 核心震荡扫频...")
    
    # Define a clash-triggering annual pillar for each profile dynamically?
    # Or test a specific High-Impact year, e.g., 2028 (Wu Shen) which clashes Yin/Tiger months.
    # Let's verify charts with Month Branch = Yin, Shen, Si, Hai, Zi, Wu, Mao, You
    
    # We will test against 2028 (Wu Shen - Earth Monkey) which clashes Tiger (Yin) months.
    # We will also test against 2026 (Bing Wu - Fire Horse) which clashes Rat (Zi) months.
    
    test_years = [
        (2026, ('丙', '午'), "Zi-Wu Clash (2026)"),
        (2028, ('戊', '申'), "Yin-Shen Clash (2028)"),
        (2029, ('己', '酉'), "Mao-You Clash (2029)"), 
        (2031, ('辛', '亥'), "Si-Hai Clash (2031)")
    ]
    
    for p in profiles:
        try:
            bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
            profile_obj = BaziProfile(bdt, 1 if p['gender'] == '男' else 0)
            natal = profile_obj.pillars
            month_br = natal['month'][1]
            
            # Find relevant test year
            relevant_year = None
            CLASH_MAP = {"子": "午", "午": "子", "丑": "未", "未": "丑", "寅": "申", "申": "寅", "卯": "酉", "酉": "卯", "辰": "戌", "戌": "辰", "巳": "亥", "亥": "巳"}
            target_clash = CLASH_MAP.get(month_br)
            
            target_y_code = None
            target_y_desc = None
            
            for y, pillar, desc in test_years:
                if pillar[1] == target_clash:
                    target_y_code = y
                    target_y_desc = desc
                    break
            
            if not target_y_code: continue # No clash year in our test set for this profile
            
            # Construct Chart
            luck_pillar_str = profile_obj.get_luck_pillar_at(target_y_code)
            luck_pillar = (luck_pillar_str[0], luck_pillar_str[1])
            
            # Use the test pillar we defined
            annual_pillar = [tp for y, tp, d in test_years if y == target_y_code][0]

            chart = [natal['year'], natal['month'], natal['day'], natal['hour'], luck_pillar, annual_pillar]
            
            # Audit JLTG
            res = scout._deep_audit(chart, "JLTG_CORE_ENERGY")
            
            if res and res.get('is_oscillation') == 'YES':
                 matches.append({
                     "name": p['name'], 
                     "trigger": target_y_desc,
                     "res": res,
                     "month": month_br
                 })

        except Exception as e:
            print(f"⚠️ 档案 {p['name']} 解析异常: {e}")

    print("\n📊 核心震荡高危名单 (Core Oscillation Red List):")
    if not matches:
        print("💡 在测试年份中未发现核心震荡样本。")
    else:
        for m in matches:
            res = m['res']
            print(f"🧨 档案：[{m['name']}] | 月令: {m['month']}")
            print(f" - 触发源: {m['trigger']}")
            print(f" - 核心类型: {res['category']}")
            print(f" - 热平衡系数: {res['thermal_balance']}")
            print(f" - 预测 SAI: {res['sai']}")
            print(f" - 状态: {'🚨 结构解体风险' if float(res['sai']) > 5.0 else '⚠️ 强震荡'}")
            print("-" * 40)

    print("\n🏁 审计报告生成完毕。")

if __name__ == "__main__":
    main()
