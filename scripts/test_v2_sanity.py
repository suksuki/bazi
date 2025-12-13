
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from core.quantum_engine import QuantumEngine

def test_synergy_boost():
    print("--- V2.0 算法回归测试: 赏善与罚恶 ---")
    
    engine = QuantumEngine()
    
    # 案例 1: 乔布斯 2011 (辛卯) - 金坐绝地 [预期: 低分]
    # 假设喜用神: Metal, Earth
    # Unfavorable: Wood, Fire
    score_jobs, _ = engine.calculate_year_score(
        year_pillar="辛卯", 
        favorable_elements=['Metal', 'Earth'], 
        unfavorable_elements=['Wood', 'Fire']
    )
    print(f"Jobs 2011 (截脚): {score_jobs} [预期: 负分]")

    # 案例 2: 马云 2014 (甲午) - 木火相生 [预期: 高分]
    # 假设喜用神: Fire, Earth
    # Unfavorable: Water, Metal (and maybe Wood if it's mixed, but let's follow user prompt logic)
    # The user prompt assumes Wood is not "Most Fav" (maybe Unfav?) but generates Fire.
    # User says: "If Jack likes Fire... Wood feeds Fire... Structure matches"
    # If Wood is Fav, score is higher. If Wood is Unfav, base score is lower.
    # Let's assume Wood is 'Neutral' or 'Unfavorable' to test the synergy boost of Unfav -> Fav?
    # User prompt: "Wood (Unfavorable elements list?)" 
    # In the code calling calculate_year_score: Unfavorable=['Water', 'Metal']. 
    # Wait, where is Wood? Favorable=['Fire', 'Earth']. 
    # Wood is neither? Or maybe in Unfavorable?
    # Usually consistent Bazi: if Earth/Fire are Fav, Wood might be Unfav (controls Earth) or Fav (feeds Fire).
    # Let's stick to the prompt's lists.
    # Prompt call: unfavorable_elements=['Water', 'Metal'] -> Wood is Neutral?
    # Let's add 'Wood' to Unfav to clearly test "Bad Stem feeds Good Branch" scenario?
    # User code snippet: unfavorable_elements=['Water', 'Metal'] -> Wood is NOT in unfav list.
    # So Wood is Neutral. 
    # If Wood is Neutral: Stem=0. Branch=10 (Fire). Base = 6.0.
    # If synergy boost is +5, Total = 11.0. This fits expectation.
    
    score_jack, _ = engine.calculate_year_score(
        year_pillar="甲午", 
        favorable_elements=['Fire', 'Earth'], 
        unfavorable_elements=['Water', 'Metal'] # Wood is not here, so it is Neutral
    )
    print(f"Jack 2014 (相生): {score_jack} [预期: 极高分]")
    
    threshold = 10.0
    if score_jack > threshold and score_jobs < 0:
        print("✅ V2.0 算法通过双向验证！")
    else:
        print("⚠️ 算法可能对'相生'结构的奖励不足，需调整权重。")
        print(f"DEBUG: Jobs Score: {score_jobs}, Jack Score: {score_jack}")

if __name__ == "__main__":
    test_synergy_boost()
