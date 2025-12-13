#!/usr/bin/env python3
"""
Trinity Architecture Test - Phase 2 Verification
Test the unified calculate_year_context interface
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.quantum_engine import QuantumEngine

def test_strong_dm_treasury():
    """Test: Strong DM + Wealth Treasury = 🏆"""
    print("\n" + "="*80)
    print("🧪 Test 1: Strong DM + Wealth Treasury Opening")
    print("="*80)
    
    engine = QuantumEngine()
    
    # Strong Water DM + Dog Treasury
    strong_chart = {
        'year_pillar': '乙未',
        'month_pillar': '丙戌',
        'day_pillar': '壬戌',  # Water DM on Dog
        'hour_pillar': '辛亥',
        'day_master': '壬',
        'energy_self': 5.0  # Strong
    }
    
    favorable = ['metal', 'water', 'fire']
    unfavorable = ['earth', 'wood']
    
    # 2024 Dragon Year clashes Dog
    year_pillar = "甲辰"
    
    ctx = engine.calculate_year_context(
        year_pillar=year_pillar,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable,
        birth_chart=strong_chart,
        year=2024
    )
    
    print(f"\n📊 Context Generated:")
    print(f"  Year: {ctx.year} {ctx.pillar}")
    print(f"  Score: {ctx.score}")
    print(f"  Icon: {ctx.icon}")
    print(f"  Risk Level: {ctx.risk_level}")
    print(f"  Energy Level: {ctx.energy_level}")
    print(f"  DM Strength: {ctx.day_master_strength}")
    print(f"  Tags: {ctx.tags}")
    print(f"  Treasury: {ctx.is_treasury_open} ({ctx.treasury_type})")
    print(f"\n📝 Narrative Prompt:")
    print(f"  {ctx.narrative_prompt}")
    print(f"\n💰 Dimension Scores:")
    print(f"  Career: {ctx.career:.1f}")
    print(f"  Wealth: {ctx.wealth:.1f}")
    print(f"  Relationship: {ctx.relationship:.1f}")
    
    # Assertions
    assert ctx.score > 0, f"Expected positive score for strong DM, got {ctx.score}"
    assert ctx.icon == '🏆', f"Expected gold trophy, got {ctx.icon}"
    assert ctx.risk_level == 'opportunity', f"Expected opportunity, got {ctx.risk_level}"
    assert ctx.is_treasury_open, "Treasury should be open"
    assert '身强' in ctx.tags or '身强胜财' in ctx.tags, f"Missing '身强' tag in {ctx.tags}"
    
    print("\n✅ Test 1 PASSED: Strong DM gets 🏆 and positive score")
    

def test_weak_dm_treasury():
    """Test: Weak DM + Wealth Treasury = ⚠️"""
    print("\n" + "="*80)
    print("⚠️  Test 2: Weak DM + Wealth Treasury Opening")
    print("="*80)
    
    engine = QuantumEngine()
    
    # Weak Water DM + Dog Treasury
    weak_chart = {
        'year_pillar': '乙未',
        'month_pillar': '丙戌',
        'day_pillar': '壬戌',
        'hour_pillar': '辛亥',
        'day_master': '壬',
        'energy_self': 1.5  # Weak
    }
    
    favorable = ['metal', 'water']
    unfavorable = ['fire', 'earth', 'wood']
    
    year_pillar = "甲辰"
    
    ctx = engine.calculate_year_context(
        year_pillar=year_pillar,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable,
        birth_chart=weak_chart,
        year=2024
    )
    
    print(f"\n📊 Context Generated:")
    print(f"  Year: {ctx.year} {ctx.pillar}")
    print(f"  Score: {ctx.score}")
    print(f"  Icon: {ctx.icon}")
    print(f"  Risk Level: {ctx.risk_level}")
    print(f"  Energy Level: {ctx.energy_level}")
    print(f"  DM Strength: {ctx.day_master_strength}")
    print(f"  Tags: {ctx.tags}")
    print(f"\n📝 Narrative Prompt:")
    print(f"  {ctx.narrative_prompt}")
    
    # Assertions
    assert ctx.score < 0, f"Expected negative score for weak DM, got {ctx.score}"
    assert ctx.icon == '⚠️', f"Expected warning icon, got {ctx.icon}"
    assert ctx.risk_level == 'warning', f"Expected warning, got {ctx.risk_level}"
    assert any('身弱' in tag for tag in ctx.tags), f"Missing '身弱' tag in {ctx.tags}"
    assert '警示' in ctx.narrative_prompt or '谨慎' in ctx.narrative_prompt, "Narrative should mention warning"
    
    print("\n✅ Test 2 PASSED: Weak DM gets ⚠️ and warning narrative")


def test_normal_year():
    """Test: Normal year without treasury"""
    print("\n" + "="*80)
    print("📅 Test 3: Normal Year (No Treasury Event)")
    print("="*80)
    
    engine = QuantumEngine()
    
    chart = {
        'year_pillar': '乙未',
        'month_pillar': '丙戌',
        'day_pillar': '壬戌',
        'hour_pillar': '辛亥',
        'day_master': '壬',
        'energy_self': 3.0  # Medium
    }
    
    favorable = ['metal', 'water']
    unfavorable = ['earth', 'wood']
    
    # 壬寅 year - no clash
    year_pillar = "壬寅"
    
    ctx = engine.calculate_year_context(
        year_pillar=year_pillar,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable,
        birth_chart=chart,
        year=2022
    )
    
    print(f"\n📊 Context Generated:")
    print(f"  Year: {ctx.year} {ctx.pillar}")
    print(f"  Score: {ctx.score}")
    print(f"  Icon: {ctx.icon}")
    print(f"  Treasury Open: {ctx.is_treasury_open}")
    
    # Assertions
    assert not ctx.is_treasury_open, "No treasury should be open"
    assert ctx.icon is None, f"No icon expected, got {ctx.icon}"
    
    print("\n✅ Test 3 PASSED: Normal year has no treasury event")


if __name__ == "__main__":
    print("\n🏛️  Trinity Architecture - Core Interface Verification")
    print("Testing calculate_year_context unified interface...\n")
    
    try:
        test_strong_dm_treasury()
        test_weak_dm_treasury()
        test_normal_year()
        
        print("\n" + "="*80)
        print("🎉 ALL TESTS PASSED! ")
        print("Trinity Architecture Phase 2 Complete!")
        print("="*80)
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
