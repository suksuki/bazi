
import sys
import os
import json
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine

def debug_case_05():
    bazi = ["丙午", "甲午", "丁巳", "壬子"]
    dm = "丁"
    month = "午"
    
    engine = QuantumEngine()
    res = engine.analyze_bazi(bazi, dm, month)
    resonance = res.get('resonance_state')
    report = resonance.resonance_report
    
    print(f"Case ID 05 Analyze Result:")
    print(f"Vibration Mode: {report.vibration_mode}")
    print(f"Locking Ratio: {report.locking_ratio}")
    print(f"Envelop Freq: {report.envelop_frequency}")
    print(f"Description: {resonance.description}")

if __name__ == "__main__":
    debug_case_05()
