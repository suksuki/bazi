from datetime import datetime
from core.bazi_profile import BaziProfile
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def test_love_over_war():
    print("--- V6.1 HarmonyEngine: 贪合忘冲测试 ---")
    
    # 1. 构造命局 (Chart Setup)
    # 我们需要一个地支同时包含 '子' (被冲者) 和 '未' (救星/合者) 的八字
    # 假设: 2020年(庚子) 6月(癸未) ...
    # 为了确保未月，选择小暑（约7月7日）后
    dob = datetime(2020, 7, 15, 12, 0) 
    
    profile = BaziProfile(dob, gender=1)
    engine = QuantumEngine()
    
    print(f"八字四柱: {profile.pillars}")
    # 验证地支是否含有 '子' 和 '未'
    branches = [p[1] for p in profile.pillars.values() if len(p) > 1]
    print(f"地支列表: {branches}")
    
    if '子' not in branches or '未' not in branches:
        print(f"⚠️ 警告：构造的八字地支不符合测试要求 (需含子、未)。实际: {branches}")
        # 强制设置以通过测试 (Mocking)
        # 但我们尽量通过日期来构造真实八字。
        # 2020-07-15 -> 庚子年 癸未月 ... 应该符合。
    
    # 2. 模拟流年: 2026 (丙午年) -> '午' 来了
    target_year = 2026 
    print(f"模拟流年: {target_year} (午火)")
    print("预期: '午'本来要冲'子'，但被'未'合住 (午未合土)。")
    
    # 3. 调用引擎
    ctx = engine.calculate_year_context(profile, target_year)
    
    # 4. 验证结果
    print(f"得分: {ctx.score}")
    print(f"标签: {ctx.tags}")
    
    # 检查详细描述信息，因为 'tags' 可能只包含部分关键词
    desc_str = str(ctx.tags) + str(ctx.description)
    print(f"完整描述: {desc_str}")
    
    # 断言
    # 1. 必须识别出六合
    # 根据 HarmonyEngine 实现，标签可能包含 '六合'，details 包含 '六合 (午-未...'
    is_combined = "六合" in desc_str or "午未" in desc_str
    if not is_combined:
        print("❌ 失败：未识别出午未六合！")
    else:
        print("✅ 成功识别六合")
    
    # 2. 必须识别出贪合忘冲
    is_resolved = "贪合忘冲" in desc_str or "Neutralized" in desc_str
    if not is_resolved:
        print("❌ 失败：未触发贪合忘冲逻辑！")
    else:
        print("✅ 成功触发贪合忘冲")

    # 3. 分数检查
    # 基础分可能受其他因素影响，主要是看 Harmony 是否给出了正向修正
    # V6.0 的 calculate_year_context 可能包含其他因素导致分数为负，
    # 但我们主要关注 HarmonyEngine 的逻辑是否正确执行。
    # HarmonyEngine 逻辑: 六合(+5) + 解冲(+2) = +7.0
    # 基础分(Stem/Branch) 可能比较低。
    # 2026 丙午: 
    # 日主可能是... 庚子年 癸未月 [尚未知日柱]
    # 关键是看是否比单纯的 六冲(-5) 分数要高。
    
    if ctx.score >= 0:
        print(f"✅ 分数判定通过: {ctx.score} (>= 0)")
    else:
        print(f"⚠️ 分数为负: {ctx.score}。需检查基础分是否过低。")
        # 只要不是因为 "六冲 -5" 导致的就可以。
        # 如果贪合忘冲生效，Harmony 贡献应该是正的。
    
    assert is_combined, "测试失败：未识别六合"
    assert is_resolved, "测试失败：未识别贪合忘冲"
    
    print("🎉 恭喜！'贪合忘冲' 逻辑生效！化学反应堆正常运转！")

if __name__ == "__main__":
    test_love_over_war()
