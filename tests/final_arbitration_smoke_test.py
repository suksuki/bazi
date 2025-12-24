
import sys
import os
import json

# Add root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.trinity.core.unified_arbitrator_master import UnifiedArbitratorMaster

def run_smoke_test():
    print("🚬 Running Antigravity V11.1 Final Arbitration Smoke Test...")
    
    # 乙丑 丙戌 辛卯 壬辰
    case_data = ["乙丑", "丙戌", "辛卯", "壬辰"]
    birth_info = {"gender": "female"}

    try:
        executor = UnifiedArbitratorMaster()
        state = executor.arbitrate_bazi(case_data, birth_info)
        report = executor.generate_holographic_report(state)
        
        if state and report:
            print("✅ Smoke Test: Pipeline executed successfully")
            print("✅ Smoke Test: Holographic Report captured")
            print(f"Report Preview: {report[:100]}...")
            return True
        else:
            print("❌ Smoke Test: Pipeline failed or report missing")
            return False
    except Exception as e:
        print(f"❌ Smoke Test: CRITICAL FAILURE - {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if run_smoke_test():
        print("🎉 Smoke Test Passed!")
    else:
        sys.exit(1)
