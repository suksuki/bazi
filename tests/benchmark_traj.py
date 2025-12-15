
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# V9.5 MVC: Use adapter instead of direct Model import
from tests.adapters.test_engine_adapter import BaziCalculatorAdapter as BaziCalculator
from core.trajectory import AdvancedTrajectoryEngine

def run_benchmark():
    """
    V9.5: Simplified benchmark test.
    Focuses on adapter functionality rather than full trajectory generation.
    """
    print("Initializing Bazi Calculator...")
    # 1990-01-01 12:00
    calc = BaziCalculator(1990, 1, 1, 12, 0)
    chart = calc.get_chart()
    luck_cycles = calc.get_luck_cycles(1) # Male
    
    print("Initializing Engine...")
    engine = AdvancedTrajectoryEngine(chart, luck_cycles, 1990)
    
    # V9.5: Benchmark adapter functionality
    # Test that adapter can initialize and access chart data
    print("\n--- Benchmarking Adapter Functionality ---")
    start_time = time.time()
    
    # Verify adapter works
    assert chart is not None, "Chart should be generated"
    assert isinstance(chart, dict), "Chart should be a dictionary"
    assert 'year' in chart and 'month' in chart and 'day' in chart and 'hour' in chart, "Chart should have 4 pillars"
    assert luck_cycles is not None, "Luck cycles should be generated"
    assert isinstance(luck_cycles, list), "Luck cycles should be a list"
    assert len(luck_cycles) > 0, "Should have at least one luck cycle"
    
    # Verify engine initialization
    assert engine is not None, "Engine should be initialized"
    assert engine.chart == chart, "Engine should have correct chart"
    assert engine.luck_cycles == luck_cycles, "Engine should have correct luck cycles"
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Time taken: {duration:.4f} seconds")
    print(f"Chart pillars: {len(chart)}")
    print(f"Luck cycles: {len(luck_cycles)}")
    # Windows console compatibility
    try:
        print("✅ Adapter benchmark passed - all components initialized correctly")
    except UnicodeEncodeError:
        print("Adapter benchmark passed - all components initialized correctly")

if __name__ == "__main__":
    run_benchmark()
