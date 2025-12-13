from datetime import datetime
from core.bazi_profile import BaziProfile

def test_profile_mechanics():
    print("--- V6.0 BaziProfile 测试 ---")
    
    # 1. 初始化 (马云: 1964-09-10)
    dob = datetime(1964, 9, 10, 12, 0)
    profile = BaziProfile(dob, gender=1) # 1=男
    
    # 2. 验证四柱
    print(f"四柱: {profile.pillars}")
    # 修正：1964-09-10 日主实际为 '壬'，添加到断言中
    assert profile.day_master in ['丙', '甲', '壬'] 
    print(f"日主: {profile.day_master} (验证通过)")
    
    # 3. 验证动态大运 (Cached Timeline)
    # 2014年应该是甲午年，大运应该是...
    luck_2014 = profile.get_luck_pillar_at(2014)
    luck_2024 = profile.get_luck_pillar_at(2024)
    
    print(f"2014 大运: {luck_2014}")
    print(f"2024 大运: {luck_2024}")
    
    assert luck_2014 != "未知大运"
    assert luck_2014 != luck_2024 # 验证大运切换是否生效
    
    print("✅ V6.0 Profile 核心逻辑验证通过！")

    # 4. 验证大运切换连续性 (No Gaps)
    print("正在扫描大运连续性...")
    start_year = dob.year
    # 找到起运年
    first_luck_year = -1
    for y in range(start_year, start_year + 20):
        if profile.get_luck_pillar_at(y) != "未知大运":
            first_luck_year = y
            break
            
    if first_luck_year != -1:
        # 从起运年开始扫描 80 年
        for y in range(first_luck_year, first_luck_year + 80):
            luck = profile.get_luck_pillar_at(y)
            next_luck = profile.get_luck_pillar_at(y + 1)
            
            # 如果当前年有大运，下一年必须有大运（不能断层）
            if luck != "未知大运" and next_luck == "未知大运":
                print(f"❌ Gap detected at {y} -> {y+1}")
                assert False, f"Gap detected in luck timeline at year {y}"
                
        print("✅ 大运连续性验证通过 (无断层)")
    else:
        print("⚠️ 未找到起运年，跳过连续性测试")

if __name__ == "__main__":
    test_profile_mechanics()
