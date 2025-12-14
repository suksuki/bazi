#!/usr/bin/env python3
"""
Antigravity V3.0 Sprint 4 Verification Script
Test the trajectory generation with treasury detection.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.trajectory import AdvancedTrajectoryEngine
from core.engine_v88 import EngineV88 as QuantumEngine  # V8.8 Modular

def test_treasury_detection():
    print("=" * 80)
    print("🏆 Antigravity V3.0 Sprint 4: Treasury Visualization Test")
    print("=" * 80)
    
    # Setup: Water DM chart with Dog (戌) in day pillar
    # This is a Wealth Treasury for Water DM
    chart = {
        'year_pillar': '乙未',
        'month_pillar': '丙戌',
        'day_pillar': '壬戌',  # Water DM sitting on Dog (Fire Tomb = Wealth Tomb)
        'hour_pillar': '辛亥',
        'day_master': '壬',
        'year': {'stem': '乙', 'branch': '未'},
        'month': {'stem': '丙', 'branch': '戌'},
        'day': {'stem': '壬', 'branch': '戌'},
        'hour': {'stem': '辛', 'branch': '亥'}
    }
    
    luck_cycles = []  # Simplified for test
    start_year = 1955
    
    # Create trajectory engine
    engine = AdvancedTrajectoryEngine(chart, luck_cycles, start_year)
    
    # Generate curve for years including 2024 (甲辰 - Dragon clashes Dog)
    # Dragon (辰) should clash with Dog (戌) in the chart, opening the Wealth Treasury
    favorable = ['Metal', 'Water', 'Fire']  # Water controls Fire (Wealth)
    unfavorable = ['Earth', 'Wood']
    
    print("\n📊 Generating V2.0 Trajectory Curve...")
    print(f"   Favorable Elements: {favorable}")
    print(f"   Unfavorable Elements: {unfavorable}")
    print(f"   Test Years: 2022-2026\n")
    
    timeline = engine.generate_v2_curve(
        start_year=2022,
        end_year=2026,
        favorable_elements=favorable,
        unfavorable_elements=unfavorable
    )
    
    # Display results
    print("-" * 80)
    print(f"{'Year':<8} {'Pillar':<8} {'Score':<8} {'Treasury?':<12} {'Type':<15} {'Comment'}")
    print("-" * 80)
    
    total_treasury_events = 0
    for point in timeline:
        year = point['year']
        pillar = point['pillar']
        score = point['score']
        is_open = "✅ YES" if point.get('is_treasury_open') else "❌ No"
        
        if point.get('is_treasury_open'):
            total_treasury_events += 1
            if point.get('is_wealth_treasury'):
                t_type = "🏆 WEALTH"
            else:
                t_type = f"🗝️ ({point.get('treasury_element', '?')})"
        else:
            t_type = "-"
        
        comment = point.get('comment', '')[:40]
        
        print(f"{year:<8} {pillar:<8} {score:<8.1f} {is_open:<12} {t_type:<15} {comment}")
    
    print("-" * 80)
    print(f"\n📈 Summary:")
    print(f"   Total Years Analyzed: {len(timeline)}")
    print(f"   Treasury Opening Events: {total_treasury_events}")
    
    # Verify specific year
    dragon_year = next((p for p in timeline if '辰' in p['pillar']), None)
    if dragon_year:
        print(f"\n🐉 Dragon Year (2024) Analysis:")
        print(f"   Pillar: {dragon_year['pillar']}")
        print(f"   Score: {dragon_year['score']}")
        print(f"   Treasury Open: {dragon_year.get('is_treasury_open')}")
        print(f"   Wealth Treasury: {dragon_year.get('is_wealth_treasury')}")
        print(f"   Details: {dragon_year.get('details', [])}")
        
        if dragon_year.get('is_treasury_open') and dragon_year.get('is_wealth_treasury'):
            print("\n   ✅ SUCCESS: 辰戌冲 detected and classified as Wealth Treasury opening!")
            print("   🏆 The Golden Trophy should appear on this year in the Dashboard!")
        else:
            print("\n   ❌ FAILURE: Treasury detection logic needs debugging.")
    
    print("\n" + "=" * 80)
    print("🎉 V3.0 Sprint 4 Verification Complete!")
    print("=" * 80)

if __name__ == "__main__":
    test_treasury_detection()
