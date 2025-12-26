
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
    print("⛩️ [V15.6] 真实档案专题格局深度穿透审计 (Target: 2025)")
    print("="*80)
    
    pm = ProfileManager()
    scout = PatternScout()
    profiles = pm.get_all()
    
    target_year = 2025
    annual_pillar = ('乙', '巳')
    
    matches = []
    
    print(f"📡 正在对 {len(profiles)} 份核心档案执行 [CYGS] & [HGFG] 物理对撞...")
    
    for p in profiles:
        try:
            # 1. 解析基础档案
            bdt = datetime(p['year'], p['month'], p['day'], p['hour'], p.get('minute', 0))
            profile_obj = BaziProfile(bdt, 1 if p['gender'] == '男' else 0)
            
            # 2. 获取大运与地理
            luck_pillar_str = profile_obj.get_luck_pillar_at(target_year) # e.g., "壬申"
            luck_pillar = (luck_pillar_str[0], luck_pillar_str[1])
            city = p.get('city', 'Beijing')
            
            # 3. 构建全因子 Chart (Year, Month, Day, Hour + Luck + Annual)
            natal = profile_obj.pillars
            chart = [natal['year'], natal['month'], natal['day'], natal['hour'], luck_pillar, annual_pillar]
            
            # 4. 专题扫描
            # Check CYGS
            cygs_res = scout._deep_audit(chart, "CYGS_COLLAPSE")
            if cygs_res:
                matches.append({"name": p['name'], "topic": "CYGS (从格)", "res": cygs_res})
                
            # Check HGFG
            hgfg_res = scout._deep_audit(chart, "HGFG_TRANSMUTATION")
            if hgfg_res:
                matches.append({"name": p['name'], "topic": "HGFG (化气)", "res": hgfg_res})
                
        except Exception as e:
            print(f"⚠️ 档案 {p['name']} 解析异常: {e}")

    print("\n📊 审计穿透结果:")
    if not matches:
        print("💡 在当前 16 份核心档案中，未发现匹配 CYGS 或 HGFG 原子级能级的样本。")
    else:
        for m in matches:
            res = m['res']
            print(f"🎯 命中档案：[{m['name']}]")
            print(f" - 专题格局: {m['topic']}")
            print(f" - 物理分类: {res['category']}")
            print(f" - SAI 指数: {res['sai']}")
            if m['topic'] == "CYGS (从格)":
                print(f" - 引力锁定率: {res['locking_ratio']} | 场强极向: {res['field_polarity']}")
            else:
                print(f" - 转换纯度: {res['transmutation_purity']} | 目标化神: {res['goal_element']}")
            print(f" - 对撞状态: {'🔥 奇点爆发' if res.get('is_rebound') == 'YES' or res.get('is_reversed') == 'YES' else '✅ 稳态运行'}")
            print("-" * 40)

    print("\n🏁 审计报告生成完毕。")

if __name__ == "__main__":
    main()
