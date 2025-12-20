
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

try:
    from core.flux import FluxEngine
    print("✅ Successfully imported FluxEngine")

    # Mock Chart Data
    chart = {
        "year": {"stem": "丁", "branch": "巳"},
        "month": {"stem": "乙", "branch": "巳"},
        "day": {"stem": "乙", "branch": "丑"},
        "hour": {"stem": "乙", "branch": "酉"}
    }
    
    print("--- Initializing Engine ---")
    engine = FluxEngine(chart)
    
    print("--- Running Compute Energy State (V5.2 Pipeline) ---")
    # This triggers Layer 1 -> Layer 2 -> Aggregation
    result = engine.calculate_flux()
    
    print("✅ Calculation Complete")
    print("Spectrum:", result['spectrum'])
    print("Logs:")
    for l in result['log']:
        print(f"  > {l}")

except Exception as e:
    print(f"❌ Verification Failed: {e}")
    import traceback
    traceback.print_exc()
