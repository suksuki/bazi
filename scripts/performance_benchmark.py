
import time
import sys
import os
from datetime import datetime

# Adjust path to import core modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.oracle import TrinityOracle
from core.trinity.core.unified_arbitrator_master import unified_arbitrator

def benchmark():
    bazi = ["癸卯", "乙卯", "戊辰", "庚申"]
    day_master = "戊"
    luck = "甲子"
    annual = "甲子"
    birth_info = {
        'birth_year': 1963,
        'birth_month': 3,
        'birth_day': 24,
        'birth_hour': 16,
        'gender': '男'
    }
    ctx = {
        'luck_pillar': luck,
        'annual_pillar': annual,
        'months_since_switch': 6.0,
        'scenario': 'GENERAL',
        'data': {
            'city': '北京 (Beijing)',
            'geo_factor': 1.15,
            'geo_element': 'Fire/Earth'
        }
    }
    
    # 1. Benchmark TrinityOracle
    print("Benchmarking TrinityOracle.analyze...")
    oracle = TrinityOracle()
    start = time.time()
    for _ in range(5):
        oracle.analyze(bazi, day_master, luck_pillar=luck, annual_pillar=annual, birth_date=datetime(1963, 3, 24, 16))
    end = time.time()
    print(f"TrinityOracle.analyze avg time: {(end - start)/5:.4f}s")
    
    # 2. Benchmark UnifiedArbitratorMaster
    print("\nBenchmarking UnifiedArbitratorMaster.arbitrate_bazi...")
    start = time.time()
    for _ in range(5):
        unified_arbitrator.arbitrate_bazi(bazi, birth_info, ctx)
    end = time.time()
    print(f"UnifiedArbitratorMaster.arbitrate_bazi avg time: {(end - start)/5:.4f}s")
    
    # 3. Total combined time (as it happens in the UI)
    print("\nTotal combined latency (simulation):")
    duration = ( (end-start)/5 ) + ( some_oracle_val if 'some_oracle_val' in locals() else (end-start)/5 )
    print(f"Estimated page interaction delay: ~{duration:.4f}s")

if __name__ == "__main__":
    benchmark()
