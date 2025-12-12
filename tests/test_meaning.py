
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.flux import FluxEngine
from core.meaning import MeaningEngine

def test_meaning_engine():
    print("Testing Meaning Engine V24.0...")
    
    # 1. Entrepreneur Chart (QiSha + ShiShen)
    # Day: Jia (Wood)
    # Year: Geng (Metal, QiSha) - Strong
    # Month: Bing (Fire, ShiShen) - Strong
    # Scenario: Eating God curbing Seven Killings (Zhi Heng)
    
    chart = {
        'year': {'stem': '庚', 'branch': '申'}, # Strong QiSha
        'month': {'stem': '丙', 'branch': '寅'}, # Strong ShiShen
        'day': {'stem': '甲', 'branch': '午'}, # Self
        'hour': {'stem': '戊', 'branch': '辰'}  # Wealth
    }
    
    print("\n--- Simulating Flux ---")
    flux = FluxEngine(chart)
    flux_res = flux.calculate_flux()
    
    print("\n--- Analyzing Meaning ---")
    meaning = MeaningEngine(chart, flux_res)
    report = meaning.analyze()
    
    print("\n[Report]")
    print("\n[Report]")
    print(f"Work Modes: {report['work_modes']}")
    print(f"Wealth Potential: {report['wealth_potential']['score']:.2f}")
    print(f"Macro Patterns: {report['macro_patterns']}")
    
    # Validation
    patterns = report['macro_patterns']
    # Check if Entrepreneur pattern exists in the list of dicts
    has_entrepreneur = any("Entrepreneur" in p['name'] for p in patterns)
    if has_entrepreneur:
        print("✅ Entrepreneur Pattern Detected")
    else:
        print("❌ Entrepreneur Pattern Missed")
        
    modes = report['work_modes']
    # Check for Zhi Heng in mode types
    has_zhiheng = any("Zhi Heng" in m['type'] for m in modes)
    if has_zhiheng:
        print("✅ Zhi Heng Work Mode Detected")
    else:
        print("❌ Zhi Heng Work Mode Missed")
        
    # 2. Influencer Chart (Fire Output)
    has_influencer = any("Influencer" in p['name'] for p in patterns)
    if has_influencer:
        print("✅ Influencer Pattern Detected")
    else:
        print("⚠️ Influencer Pattern Not Detected (Maybe Amplitude too low?)")

if __name__ == "__main__":
    test_meaning_engine()
