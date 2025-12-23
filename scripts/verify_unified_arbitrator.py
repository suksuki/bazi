
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from core.trinity.core.unified_arbitrator_master import unified_arbitrator

def verify_arbitrator():
    print("🚀 Initiating Unified Arbitrator Verification...")
    
    # Test Case: "Wang Jinxing" (High Stress Proxy)
    # 辛酉 丁酉 庚申 丙子
    test_chart = ["辛酉", "丁酉", "庚申", "丙子"]
    
    context = {
        "luck_pillar": "乙亥",
        "annual_pillar": "甲辰",
        "geo_factor": 1.3
    }
    
    # 1. Run Arbitration
    print("\n[1] Running Arbitration Pipeline...")
    state = unified_arbitrator.arbitrate_bazi(test_chart, current_context=context)
    
    # Check Metric Presence
    assert "physics" in state
    print("✅ Physics State Generated")
    print(f"   - Gravity Weights: {state['physics']['gravity']}")
    print(f"   - Stress SAI: {state['physics']['stress'].get('SAI')}")
    
    # 2. Generate Report
    print("\n[2] Generating Holographic Mantra...")
    report = unified_arbitrator.generate_holographic_report(state)
    
    print("\n" + "="*50)
    print(report)
    print("="*50 + "\n")
    
    print("✅ Unified Arbitrator Verification Complete.")

if __name__ == "__main__":
    verify_arbitrator()
