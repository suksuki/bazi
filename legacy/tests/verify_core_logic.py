
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# V9.5 MVC: Use adapters instead of direct Model imports
from tests.adapters.test_engine_adapter import (
    BaziCalculatorAdapter as BaziCalculator,
    FluxEngineAdapter as FluxEngine
)
from core.wuxing_engine import WuXingEngine
from core.alchemy import AlchemyEngine
import json
import datetime

def test_core_logic():
    print(">>> 1. Testing BaziCalculator (Static Chart)...")
    # 1990-01-01 12:00
    calc = BaziCalculator(1990, 1, 1, 12, 0)
    chart = calc.get_chart()
    print("Chart generated successfully.")
    print(f"Day Master: {chart['day']['stem']}")
    
    print("\n>>> 2. Testing WuXing & Alchemy...")
    wuxing = WuXingEngine(chart)
    strength = wuxing.calculate_strength()
    print(f"Strength Scores: {strength['scores']}")
    
    alchemy = AlchemyEngine(chart)
    reactions = alchemy.run_reactions()
    print(f"Reactions found: {len(reactions)}")
    
    print("\n>>> 3. Testing FluxEngine (Quantum Furnace)...")
    flux = FluxEngine(chart)
    # Simulate current Da Yun / Liu Nian (Just dummy stems)
    # Jia Zi year
    flux_data = flux.calculate_flux("甲", "子", "乙", "丑")
    # Windows console compatibility
    try:
        print("Flux Data keys:", list(flux_data.keys()))
        print("Sample Flux (Wealth):", flux_data.get("财星 (Wealth/Wife)"))
    except UnicodeEncodeError:
        print("Flux Data keys:", [k.encode('ascii', 'ignore').decode('ascii') if isinstance(k, str) else str(k) for k in flux_data.keys()])
        wealth_key = [k for k in flux_data.keys() if 'Wealth' in str(k) or '财' in str(k)]
        if wealth_key:
            print("Sample Flux (Wealth):", flux_data.get(wealth_key[0]))
    
    # [DEPRECATED] AdvancedTrajectoryEngine removed in V12.2.0
    # Use TemporalShuntingEngine for temporal predictions instead.
    
    print("\n✅ All Core Engines Initialized and Ran Successfully.")

if __name__ == "__main__":
    test_core_logic()
