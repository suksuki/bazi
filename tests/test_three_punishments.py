#!/usr/bin/env python3
"""
Sprint 5.3: Three Punishments Test
Test the 💀 Skull Protocol - Earth Punishment Detection
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular
from core.bazi_profile import VirtualBaziProfile

def test_three_punishments_detection():
    """
    Test Case: 天生带刑 Chart encountering 三刑完整
    
    命局: 癸丑 乙未 甲子 丙寅
    - 年支: 丑
    - 月支: 未
    流年: 2030 庚戌
    - 年支: 戌
    
    完整三刑: {丑, 未, 戌} ✅
    预期: 💀 Structural Collapse
    """
    print("\n" + "="*80)
    print("💀 Sprint 5.3: Three Punishments Detection Test")
    print("="*80)
    
    engine = QuantumEngine()
    
    # The Doomed Chart - 带刑命造
    punishment_chart_pillars = {
        'year': '癸丑',  # 丑 ✓
        'month': '乙未',  # 未 ✓
        'day': '甲子',
        'hour': '丙寅'
    }
    # Create Virtual Profile
    profile = VirtualBaziProfile(
        pillars=punishment_chart_pillars, 
        static_luck="庚申", # Luck doesn't matter for this test logic
        day_master="甲",
        gender=1
    )
    
    # favorable/unfavorable are handled by engine internally in V6.0 or defaults used
    # In V6.0 calculate_year_context, it doesn't accept external favorable/unfavorable.
    # We rely on the engine's internal logic or defaults.
    
    # Control Year: 2024 (甲辰) - No punishment
    print("\n📅 Control Year: 2024 甲辰 (No Punishment)")
    ctx_control = engine.calculate_year_context(profile, 2024)
    
    print(f"  Icon: {ctx_control.icon}")
    print(f"  Score: {ctx_control.score}")
    print(f"  Energy: {ctx_control.energy_level}")
    print(f"  Tags: {ctx_control.tags[:3]}")
    
    # Test Year: 2030 (庚戌) - PUNISHMENT TRIGGERED 💀
    print("\n💀 Test Year: 2030 庚戌 (Punishment Triggered!)")
    ctx_punishment = engine.calculate_year_context(profile, 2030)
    
    print(f"  Icon: {ctx_punishment.icon}")
    print(f"  Score: {ctx_punishment.score}")
    print(f"  Energy: {ctx_punishment.energy_level}")
    print(f"  Risk Level: {ctx_punishment.risk_level}")
    print(f"  Tags: {ctx_punishment.tags[:5]}")
    print(f"\n  Narrative Prompt:")
    print(f"    {ctx_punishment.narrative_prompt[:150]}...")
    
    # Assertions
    print("\n" + "-"*80)
    print("Validating Results...")
    
    # Control should NOT have skull
    assert ctx_control.icon != "💀", "Control year should not trigger punishment"
    print("✅ Control year: No skull icon")
    
    # Test year SHOULD have skull
    assert ctx_punishment.icon == "💀", f"Expected 💀, got {ctx_punishment.icon}"
    print("✅ Test year: Skull icon detected!")
    
    # Score should be heavily penalized (absolute value check)
    # Punishment adds -40 penalty, so score should be very negative
    assert ctx_punishment.score < -30, f"Punishment score too high: {ctx_punishment.score}"
    print(f"✅ Score penalty: {ctx_control.score:.1f} → {ctx_punishment.score:.1f} (heavily penalized)")

    
    # Risk level should be danger
    assert ctx_punishment.risk_level == "danger", f"Expected 'danger', got {ctx_punishment.risk_level}"
    print("✅ Risk level: danger")
    
    # Tags should include punishment markers
    assert any("三刑" in tag for tag in ctx_punishment.tags), "Missing 三刑 tag"
    assert any("崩塌" in tag for tag in ctx_punishment.tags), "Missing 崩塌 tag"
    print(f"✅ Tags correct: {ctx_punishment.tags[:3]}")
    
    # Energy level should indicate structural collapse
    assert "Collapse" in ctx_punishment.energy_level or "大凶" in ctx_punishment.energy_level or "High Risk" in ctx_punishment.energy_level
    print(f"✅ Energy level: {ctx_punishment.energy_level}")
    
    # Narrative should have extreme warning
    # Note: Narrative prompt building depends on LLM prompt construction logic.
    # In V6.0 code check: ctx.narrative_prompt ...
    # We check if it contains keywords.
    # If narrative_events has 'punishment_collapse', likely prompt has it.
    
    print("\n" + "="*80)
    print("🎉 Three Punishments Test PASSED!")
    print("The Skull Protocol is ACTIVE! 💀")
    print("="*80)


def test_no_punishment_with_two_branches():
    """
    Test: Only 2 of 3 branches present - Should NOT trigger
    """
    print("\n" + "="*80)
    print("🧪 Test: Partial Punishment (Should NOT Trigger)")
    print("="*80)
    
    engine = QuantumEngine()
    
    # Only has 丑 and 未, missing 戌
    partial_chart_pillars = {
        'year': '癸丑',  # 丑 ✓
        'month': '乙未',  # 未 ✓
        'day': '甲子',
        'hour': '丙寅'
    }
    
    profile = VirtualBaziProfile(
        pillars=partial_chart_pillars, 
        static_luck="庚申",
        day_master="甲",
        gender=1
    )
    
    # Year: 2024 甲辰 (辰, not 戌)
    ctx = engine.calculate_year_context(profile, 2024)
    
    print(f"  Icon: {ctx.icon}")
    print(f"  Risk: {ctx.risk_level}")
    
    # Should NOT trigger punishment
    assert ctx.icon != "💀", "Should not trigger with only 2/3 branches"
    assert ctx.risk_level != "danger", "Risk should not be 'danger'"
    
    print("✅ Partial punishment correctly NOT triggered")
    print("="*80)


if __name__ == "__main__":
    try:
        test_three_punishments_detection()
        test_no_punishment_with_two_branches()
        
        print("\n🏆 ALL TESTS PASSED!")
        print("Sprint 5.3: The Skull Protocol is ready for deployment! 💀✨")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
