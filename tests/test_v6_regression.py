from datetime import datetime
from core.bazi_profile import BaziProfile
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def test_skull_protocol_survival():
    print("--- V6.0 骷髅协议回归测试 ---")
    
    # 1. 构造一个"天生带刑"的八字 (丑未全)
    # 假设: 2021年(辛丑) 7月(乙未) ... 
    # 只要年支是丑，月支是未，就满足 2/3 的条件
    dob = datetime(2021, 7, 20, 12, 0) 
    
    # 初始化 Oracle
    profile = BaziProfile(dob, gender=1)
    engine = QuantumEngine()
    
    print(f"八字四柱: {profile.pillars}")
    # 预期: Year='..丑', Month='..未'
    
    # 2. 模拟流年: 2030 (庚戌年) -> 凑齐 丑-未-戌 三刑
    target_year = 2030
    print(f"模拟流年: {target_year} (应该触发三刑)")
    
    # 3. 调用 V6.0 统一接口
    ctx = engine.calculate_year_context(profile, target_year)
    
    # 4. 验证结果
    print(f"得分: {ctx.score}")
    print(f"图标: {ctx.icon}")
    print(f"标签: {ctx.tags}")
    
    # 断言
    assert ctx.icon == '💀', "错误：骷髅图标丢失！三刑检测失效。"
    assert ctx.score <= -40, "错误：惩罚分数不足！"
    assert "三刑崩塌 (The Skull)" in ctx.tags, "错误：逻辑标签缺失！"
    
    print("✅ 恭喜！V6.0 架构成功继承了 V5.3 的风控能力！")

if __name__ == "__main__":
    test_skull_protocol_survival()
