"""
V9.5 Controller Cache Mechanism Test
=====================================
Test smart result caching in BaziController.
"""

import sys
import os
import time
from datetime import date

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from controllers.bazi_controller import BaziController


def test_cache_mechanism():
    """Test that cache works correctly."""
    print("=" * 60)
    print("V9.5 Controller Cache Mechanism Test")
    print("=" * 60)
    print()
    
    controller = BaziController()
    
    # Set user input
    controller.set_user_input(
        name="TestUser",
        gender="男",
        date_obj=date(1990, 1, 1),
        time_int=12,
        city="Beijing"
    )
    
    # Test 1: First call (cache miss)
    print("Test 1: First call (should be cache miss)")
    start_time = time.time()
    df1, handovers1 = controller.run_timeline_simulation(2020, duration=12)
    time1 = time.time() - start_time
    
    stats1 = controller.get_cache_stats()
    print(f"  Time: {time1:.4f} seconds")
    print(f"  Cache stats: {stats1}")
    print(f"  Expected: misses=1, hits=0")
    assert stats1['misses'] == 1, "First call should be a cache miss"
    assert stats1['hits'] == 0, "First call should have no hits"
    print("  [PASSED]")
    print()
    
    # Test 2: Second call with same parameters (cache hit)
    print("Test 2: Second call with same parameters (should be cache hit)")
    start_time = time.time()
    df2, handovers2 = controller.run_timeline_simulation(2020, duration=12)
    time2 = time.time() - start_time
    
    stats2 = controller.get_cache_stats()
    print(f"  Time: {time2:.4f} seconds")
    print(f"  Cache stats: {stats2}")
    print(f"  Expected: misses=1, hits=1")
    assert stats2['misses'] == 1, "Should still have 1 miss"
    assert stats2['hits'] == 1, "Second call should be a cache hit"
    assert time2 < time1, "Cached call should be faster"
    print("  [PASSED]")
    print()
    
    # Test 3: Verify results are identical
    print("Test 3: Verify cached results are identical")
    assert len(df1) == len(df2), "DataFrames should have same length"
    assert df1.equals(df2), "Cached DataFrame should be identical"
    assert len(handovers1) == len(handovers2), "Handovers should have same length"
    print("  [PASSED]")
    print()
    
    # Test 4: Different parameters (cache miss)
    print("Test 4: Different start_year (should be cache miss)")
    start_time = time.time()
    df3, handovers3 = controller.run_timeline_simulation(2021, duration=12)
    time3 = time.time() - start_time
    
    stats3 = controller.get_cache_stats()
    print(f"  Time: {time3:.4f} seconds")
    print(f"  Cache stats: {stats3}")
    print(f"  Expected: misses=2, hits=1")
    assert stats3['misses'] == 2, "Different parameters should be a miss"
    assert stats3['hits'] == 1, "Should still have 1 hit"
    print("  [PASSED]")
    print()
    
    # Test 5: Cache invalidation on input change
    print("Test 5: Cache invalidation on user input change")
    controller.set_user_input(
        name="TestUser",
        gender="男",
        date_obj=date(1990, 1, 1),
        time_int=13,  # Changed time
        city="Beijing"
    )
    
    stats4 = controller.get_cache_stats()
    print(f"  Cache stats after input change: {stats4}")
    print(f"  Expected: size=0 (cache cleared)")
    assert stats4['size'] == 0, "Cache should be cleared on input change"
    assert stats4['invalidations'] > 0, "Should have recorded invalidations"
    print("  [PASSED]")
    print()
    
    # Test 6: Performance improvement measurement
    print("Test 6: Performance improvement measurement")
    # Warm up
    controller.run_timeline_simulation(2020, duration=12)
    
    # Measure uncached
    controller.clear_cache()
    start_time = time.time()
    for _ in range(10):
        controller.run_timeline_simulation(2020, duration=12, use_cache=False)
    uncached_time = time.time() - start_time
    
    # Measure cached
    controller.clear_cache()
    controller.run_timeline_simulation(2020, duration=12)  # First call (miss)
    start_time = time.time()
    for _ in range(10):
        controller.run_timeline_simulation(2020, duration=12)  # Cached calls
    cached_time = time.time() - start_time
    
    speedup = uncached_time / cached_time if cached_time > 0 else 0
    print(f"  10 uncached calls: {uncached_time:.4f} seconds")
    print(f"  10 cached calls: {cached_time:.4f} seconds")
    print(f"  Speedup: {speedup:.2f}x")
    print(f"  Time saved: {uncached_time - cached_time:.4f} seconds")
    assert speedup > 1.0, "Cached calls should be faster"
    print("  [PASSED]")
    print()
    
    # Final stats
    final_stats = controller.get_cache_stats()
    print("=" * 60)
    print("Final Cache Statistics")
    print("=" * 60)
    print(f"Total hits: {final_stats['hits']}")
    print(f"Total misses: {final_stats['misses']}")
    print(f"Total invalidations: {final_stats['invalidations']}")
    print(f"Cache size: {final_stats['size']}")
    print(f"Hit rate: {final_stats['hit_rate']:.2%}")
    print()
    
    print("=" * 60)
    print("[SUCCESS] All tests passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_cache_mechanism()
    except Exception as e:
        print(f"[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

