"""
V9.5 Performance Profiler - QuantumEngine Bottleneck Analysis
=============================================================
Stage 1: Performance Benchmarking and Bottleneck Identification

This script profiles QuantumEngine performance to identify bottlenecks.
"""

import cProfile
import pstats
import io
import time
import sys
import os
from datetime import date
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.bazi_controller import BaziController
from core.engine_v88 import EngineV88
from core.engine_v88 import EngineV88 as EngineV91  # Alias for compatibility


def create_test_case_data():
    """Create a standard test case for performance testing."""
    return {
        'id': 1,
        'gender': '男',
        'day_master': '甲',
        'wang_shuai': '身旺',
        'physics_sources': {
            'self': {'stem_support': 5.0},
            'output': {'base': 5.0},
            'officer': {'base': 5.0},
            'wealth': {'base': 3.0},
            'resource': {'base': 2.0}
        },
        'bazi': ['甲子', '乙丑', '丙寅', '丁卯'],
        'birth_info': {
            'year': 1990,
            'month': 1,
            'day': 1,
            'hour': 12,
            'gender': 1
        },
        'city': 'Beijing'
    }


def benchmark_quantum_engine_direct():
    """Benchmark QuantumEngine.calculate_energy() directly."""
    print("=" * 60)
    print("Benchmark 1: QuantumEngine.calculate_energy() Direct Call")
    print("=" * 60)
    
    engine = EngineV91()
    case_data = create_test_case_data()
    dynamic_context = {'year': '甲子', 'dayun': '乙丑', 'luck': '乙丑'}
    
    # V9.5: Load cached era_multipliers for performance optimization
    era_multipliers = {}
    try:
        era_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/era_constants.json")
        if os.path.exists(era_path):
            with open(era_path, 'r', encoding='utf-8') as f:
                era_data = json.load(f)
                era_multipliers = era_data.get('physics_multipliers', {})
    except:
        pass
    
    # Warm-up
    for _ in range(3):
        engine.calculate_energy(case_data, dynamic_context, era_multipliers=era_multipliers)
    
    # Actual benchmark
    iterations = 100
    start_time = time.time()
    
    for _ in range(iterations):
        result = engine.calculate_energy(case_data, dynamic_context, era_multipliers=era_multipliers)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / iterations
    
    print(f"Total iterations: {iterations}")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per call: {avg_time:.6f} seconds")
    print(f"Throughput: {iterations/total_time:.2f} calls/second")
    print()
    
    return avg_time


def benchmark_controller_timeline():
    """Benchmark BaziController.run_timeline_simulation()."""
    print("=" * 60)
    print("Benchmark 2: BaziController.run_timeline_simulation()")
    print("=" * 60)
    
    controller = BaziController()
    controller.set_user_input(
        name="TestUser",
        gender="男",
        date_obj=date(1990, 1, 1),
        time_int=12,
        city="Beijing",
        enable_solar=False,
        longitude=116.46
    )
    
    # Warm-up
    controller.run_timeline_simulation(1990, duration=5)
    
    # Actual benchmark
    iterations = 10
    duration = 12  # 12 years
    
    start_time = time.time()
    
    for _ in range(iterations):
        df, handover_years = controller.run_timeline_simulation(1990, duration=duration)
    
    end_time = time.time()
    total_time = end_time - start_time
    avg_time = total_time / iterations
    
    print(f"Total iterations: {iterations}")
    print(f"Duration per simulation: {duration} years")
    print(f"Total time: {total_time:.4f} seconds")
    print(f"Average time per simulation: {avg_time:.4f} seconds")
    print(f"Time per year: {avg_time/duration:.4f} seconds/year")
    print(f"Throughput: {iterations/total_time:.2f} simulations/second")
    print()
    
    return avg_time


def profile_quantum_engine():
    """Profile QuantumEngine using cProfile."""
    print("=" * 60)
    print("Profiling: QuantumEngine.calculate_energy()")
    print("=" * 60)
    
    engine = EngineV91()
    case_data = create_test_case_data()
    dynamic_context = {'year': '甲子', 'dayun': '乙丑', 'luck': '乙丑'}
    
    # V9.5: Load cached era_multipliers for performance optimization
    era_multipliers = {}
    try:
        era_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data/era_constants.json")
        if os.path.exists(era_path):
            with open(era_path, 'r', encoding='utf-8') as f:
                era_data = json.load(f)
                era_multipliers = era_data.get('physics_multipliers', {})
    except:
        pass
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Profile
    iterations = 50
    profiler.enable()
    
    for _ in range(iterations):
        engine.calculate_energy(case_data, dynamic_context, era_multipliers=era_multipliers)
    
    profiler.disable()
    
    # Generate report
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    
    report = s.getvalue()
    print(report)
    
    # Save to file
    output_file = 'performance_profile_quantum.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("QuantumEngine.calculate_energy() Performance Profile\n")
        f.write("=" * 60 + "\n\n")
        f.write(report)
    
    print(f"Profile saved to: {output_file}")
    print()
    
    return ps


def profile_controller_timeline():
    """Profile BaziController.run_timeline_simulation() using cProfile."""
    print("=" * 60)
    print("Profiling: BaziController.run_timeline_simulation()")
    print("=" * 60)
    
    controller = BaziController()
    controller.set_user_input(
        name="TestUser",
        gender="男",
        date_obj=date(1990, 1, 1),
        time_int=12,
        city="Beijing",
        enable_solar=False,
        longitude=116.46
    )
    
    # Create profiler
    profiler = cProfile.Profile()
    
    # Profile
    profiler.enable()
    
    df, handover_years = controller.run_timeline_simulation(1990, duration=12)
    
    profiler.disable()
    
    # Generate report
    s = io.StringIO()
    ps = pstats.Stats(profiler, stream=s)
    ps.sort_stats('cumulative')
    ps.print_stats(30)  # Top 30 functions
    
    report = s.getvalue()
    print(report)
    
    # Save to file
    output_file = 'performance_profile_timeline.txt'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("BaziController.run_timeline_simulation() Performance Profile\n")
        f.write("=" * 60 + "\n\n")
        f.write(report)
    
    print(f"Profile saved to: {output_file}")
    print()
    
    return ps


def analyze_bottlenecks(ps, top_n=10):
    """Analyze and extract top bottlenecks from profile stats."""
    print("=" * 60)
    print(f"Top {top_n} Bottlenecks (by cumulative time)")
    print("=" * 60)
    
    bottlenecks = []
    
    # Extract top functions
    for func, (cc, nc, tt, ct, callers) in ps.stats.items():
        if ct > 0:  # Only include functions that took time
            bottlenecks.append({
                'function': f"{func[0]}:{func[1]}({func[2]})",
                'cumulative_time': ct,
                'total_time': tt,
                'call_count': nc
            })
    
    # Sort by cumulative time
    bottlenecks.sort(key=lambda x: x['cumulative_time'], reverse=True)
    
    # Print top N
    total_cumulative = sum(b['cumulative_time'] for b in bottlenecks)
    
    print(f"{'Rank':<6} {'Function':<50} {'Cumulative Time':<20} {'% of Total':<15}")
    print("-" * 90)
    
    for i, bottleneck in enumerate(bottlenecks[:top_n], 1):
        percentage = (bottleneck['cumulative_time'] / total_cumulative * 100) if total_cumulative > 0 else 0
        func_name = bottleneck['function'][:48]  # Truncate if too long
        print(f"{i:<6} {func_name:<50} {bottleneck['cumulative_time']:<20.4f} {percentage:<15.2f}%")
    
    print()
    
    return bottlenecks[:top_n]


def generate_performance_report():
    """Generate comprehensive performance report."""
    print("\n" + "=" * 60)
    print("V9.5 Performance Analysis Report")
    print("=" * 60)
    print()
    
    # Benchmark 1: Direct QuantumEngine
    t_quantum = benchmark_quantum_engine_direct()
    
    # Benchmark 2: Controller Timeline
    t_timeline = benchmark_controller_timeline()
    
    # Profile 1: QuantumEngine
    ps_quantum = profile_quantum_engine()
    bottlenecks_quantum = analyze_bottlenecks(ps_quantum, top_n=10)
    
    # Profile 2: Controller Timeline
    ps_timeline = profile_controller_timeline()
    bottlenecks_timeline = analyze_bottlenecks(ps_timeline, top_n=10)
    
    # Generate summary report
    report = {
        'benchmarks': {
            'quantum_engine_direct': {
                'average_time_seconds': t_quantum,
                'description': 'QuantumEngine.calculate_energy() direct call'
            },
            'controller_timeline': {
                'average_time_seconds': t_timeline,
                'description': 'BaziController.run_timeline_simulation() for 12 years'
            }
        },
        'bottlenecks': {
            'quantum_engine': [
                {
                    'rank': i + 1,
                    'function': b['function'],
                    'cumulative_time': b['cumulative_time'],
                    'call_count': b['call_count']
                }
                for i, b in enumerate(bottlenecks_quantum)
            ],
            'controller_timeline': [
                {
                    'rank': i + 1,
                    'function': b['function'],
                    'cumulative_time': b['cumulative_time'],
                    'call_count': b['call_count']
                }
                for i, b in enumerate(bottlenecks_timeline)
            ]
        }
    }
    
    # Save JSON report
    with open('performance_report.json', 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print("=" * 60)
    print("Performance Report Summary")
    print("=" * 60)
    print(f"QuantumEngine.calculate_energy() average: {t_quantum:.4f} seconds")
    print(f"Controller.run_timeline_simulation() (12 years) average: {t_timeline:.4f} seconds")
    print(f"Time per year: {t_timeline/12:.4f} seconds/year")
    print()
    print("Top 3 Bottlenecks (QuantumEngine):")
    for i, b in enumerate(bottlenecks_quantum[:3], 1):
        print(f"  {i}. {b['function']} - {b['cumulative_time']:.4f}s")
    print()
    print("Top 3 Bottlenecks (Controller Timeline):")
    for i, b in enumerate(bottlenecks_timeline[:3], 1):
        print(f"  {i}. {b['function']} - {b['cumulative_time']:.4f}s")
    print()
    print("Detailed reports saved to:")
    print("  - performance_profile_quantum.txt")
    print("  - performance_profile_timeline.txt")
    print("  - performance_report.json")
    print()


if __name__ == "__main__":
    try:
        generate_performance_report()
    except Exception as e:
        print(f"Error during profiling: {e}")
        import traceback
        traceback.print_exc()

