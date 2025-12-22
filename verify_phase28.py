
import json
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

from core.trinity.core.oracle import TrinityOracle

# Load the new test case
with open('tests/data/oppose_matrix_v21.json', 'r') as f:
    cases = json.load(f)

case = cases[2] # OPPOSE_003_SHANG_GUAN_SHANG_JIN
oracle = TrinityOracle()

print(f"--- Simulating Phase 28: {case['id']} ---")
res = oracle.analyze(case['bazi'], case['day_master'])

verdict = res['verdict']
resonance = res['resonance']

print(f"Verdict: {verdict['label']}")
print(f"Resonance Mode: {resonance.mode}")
print(f"Coherence (Sync): {resonance.sync_state:.4f}")
print(f"Flow Efficiency: {resonance.flow_efficiency:.2f}")

print("\n--- Element Amplitudes ---")
for e, w in res['waves'].items():
    print(f"{e}: {w.amplitude:.2f} (Phase: {w.phase:.2f})")

if resonance.mode == 'COHERENT' and resonance.fragmentation_index < 0.25:
    print("\n✨ SUPERFLUID STATE DETECTED!")
    print("Perfect Vacuum: No Guan, No Damping. Pure Kinetic Flow.")
else:
    print("\nSystem still maintaining structural integrity or experiencing noise.")
