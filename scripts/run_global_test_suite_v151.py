import os
import sys
import subprocess
import time

# ==========================================
# QGA Global Test Suite (FDS-V1.5.1)
# ==========================================
# Target: Validate all registered patterns used in the A-01/B-02 development cycle.

def run_test_script(script_path, name):
    print(f"\n🚀 [TEST SUITE] Launching {name} ({script_path})...")
    start = time.time()
    try:
        # Run using the same python interpreter
        result = subprocess.run(
            [sys.executable, script_path], 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        duration = time.time() - start
        
        if result.returncode == 0:
            print(f"✅ {name}: PASS ({duration:.2f}s)")
            # Print indented output for verification
            for line in result.stdout.splitlines():
                if "PASS" in line or "MATCH" in line or "REJECT" in line:
                    print(f"   | {line.strip()}")
            return True
        else:
            print(f"❌ {name}: FAIL (Return Code {result.returncode})")
            print(f"   | Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {name}: CRITICAL ERROR ({e})")
        return False

def main():
    print("==================================================")
    print("      Antigravity Engine - Global Validation      ")
    print("      Spec: FDS-V1.5.1 | Date: 2025-12-31         ")
    print("==================================================")

    tests = [
        # 1. A-01 正官格 (Direct Officer)
        # Goal: Verify Single-State Router + E-Gating + Purity
        ("scripts/a01_step6_testing_v151.py", "A-01 Load Test"),
        
        # 2. B-02 伤官格 (Hurting Officer)
        # Goal: Verify Multi-State Router + E-Gating + Bifurcation
        ("scripts/b02_step6_testing_v151.py", "B-02 Load Test"),
    ]
    
    # Check for D-02 script just in case, but keep it optional if it fails
    if os.path.exists("scripts/d02_step6_testing.py"):
        tests.append(("scripts/d02_step6_testing.py", "D-02 Load Test (Optional)"))

    overall_pass = True
    for script, name in tests:
        if not run_test_script(script, name):
            overall_pass = False
            
    print("\n==================================================")
    if overall_pass:
        print("✅ ALL SYSTEMS GREEN. RELEASE CANDIDATE VALID.")
    else:
        print("❌ SYSTEM FAILURE. CHECK LOGS.")
    print("==================================================")

if __name__ == "__main__":
    main()
