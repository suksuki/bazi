
import time
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.calculator import BaziCalculator
from core.trajectory import AdvancedTrajectoryEngine

def run_benchmark():
    print("Initializing Bazi Calculator...")
    # 1990-01-01 12:00
    calc = BaziCalculator(1990, 1, 1, 12, 0)
    chart = calc.get_chart()
    luck_cycles = calc.get_luck_cycles(1) # Male
    
    print("Initializing Engine...")
    engine = AdvancedTrajectoryEngine(chart, luck_cycles, 1990)
    
    modes = ["year", "month", "day"]
    
    for mode in modes:
        print(f"\n--- Benchmarking granularity: {mode} ---")
        start_time = time.time()
        timeline = engine.run(end_age=90, granularity=mode)
        end_time = time.time()
        
        duration = end_time - start_time
        count = len(timeline)
        
        print(f"Time taken: {duration:.4f} seconds")
        print(f"Data points generated: {count}")
        print(f"Speed: {count/duration:.2f} points/sec")

if __name__ == "__main__":
    run_benchmark()
