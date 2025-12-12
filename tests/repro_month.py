
import sys
import os
import time
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trajectory import AdvancedTrajectoryEngine

def test_month_simulation():
    print("--- Testing Monthly Simulation Speed ---")
    
    # Mock Data
    chart = {
        'year': {'stem': '甲', 'branch': '子'},
        'month': {'stem': '乙', 'branch': '丑'},
        'day': {'stem': '丙', 'branch': '寅'},
        'hour': {'stem': '丁', 'branch': '卯'}
    }
    
    luck_cycles = [
        {'start_year': 1984, 'end_year': 1993, 'gan_zhi': ['戊', '辰']},
        {'start_year': 1994, 'end_year': 2003, 'gan_zhi': ['己', '巳']},
        {'start_year': 2004, 'end_year': 2013, 'gan_zhi': ['庚', '午']},
        {'start_year': 2014, 'end_year': 2023, 'gan_zhi': ['辛', '未']},
        {'start_year': 2024, 'end_year': 2033, 'gan_zhi': ['壬', '申']},
        {'start_year': 2034, 'end_year': 2043, 'gan_zhi': ['癸', '酉']},
    ]
    
    start_year = 1984
    granularity = "month"
    
    print(f"Chart: {chart}")
    print(f"Start Year: {start_year}, Granularity: {granularity}")
    
    start_time = time.time()
    
    engine = AdvancedTrajectoryEngine(chart, luck_cycles, start_year)
    timeline = engine.run(end_age=90, granularity=granularity)
    
    end_time = time.time()
    duration = end_time - start_time
    
    print(f"Simulation Complete.")
    print(f"Time Taken: {duration:.4f} seconds")
    print(f"Total Data Points: {len(timeline)}")
    
    if len(timeline) > 0:
        print(f"Sample Point [0]: {timeline[0]}")
        print(f"Sample Point [-1]: {timeline[-1]}")
    else:
        print("❌ Error: Empty Timeline!")

if __name__ == "__main__":
    test_month_simulation()
