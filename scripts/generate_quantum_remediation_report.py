
import sys
import os
import json
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from core.trinity.core.quantum_engine import QuantumEngine
from core.trinity.core.entanglement_engine import EntanglementEngine
from core.trinity.core.resonance_engine import ResonanceEngine, ResonanceResult

def generate_report():
    mantra_path = Path("tests/data/quantum_mantra_v93.json")
    if not mantra_path.exists():
        print(f"Error: {mantra_path} not found.")
        return

    with open(mantra_path, "r", encoding="utf-8") as f:
        cases = json.load(f)

    engine = QuantumEngine()
    report_lines = [
        "# 🌌 Phase 24: Quantum Remediation & Active SNR Filtering Report",
        f"**Engine Version**: Quantum Trinity V24.0 (Adaptive Remediation)",
        f"**Objective**: Calculate the minimum 'Filtering Charge' (Coupling) required to achieve Stable Resonance (COHERENT/High SNR).",
        "",
        "| ID | Case Name | Initial State (SNR) | Recommended Particle | Filtering Charge (Req) | Final State (SNR) | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |"
    ]

    for case in cases:
        bazi = case['bazi']
        dm = case['day_master']
        month = case['month_branch']
        
        # 1. Baseline
        analysis_base = engine.analyze_bazi(bazi, dm, month)
        res_base = analysis_base['resonance_state'].resonance_report
        initial_str = f"{res_base.vibration_mode} ({res_base.snr:.2f})"
        
        # 2. Find Optimal Particle
        suggestion = analysis_base.get('suggestion')
        best_p = suggestion['best_particle'] if suggestion else "None"
        
        # 3. Search for Minimum Filtering Charge (Coupling)
        # Search range 0.1 to 3.0
        req_charge = "N/A"
        final_state = initial_str
        status = "Fixed"
        
        # If already coherent and high snr, charge is 0
        if res_base.vibration_mode == "COHERENT" and res_base.snr > 0.8:
            req_charge = "0.00"
            status = "Optimal"
        else:
            found = False
            # Extract internal state for faster scanning
            # Need dm_wave_init and field_wave_list from analyze_bazi logic
            # Let's just use engine.analyze_bazi for simplicity (though slower)
            for c_val in np.arange(0.1, 3.1, 0.1):
                # We need a way to pass custom coupling to analyze_bazi if we want to test
                # But analyze_bazi uses hardcoded coupling=0.3 in the loop
                # Let's simulate the scan manually using ResEngine and EntangleEngine
                
                # Mock analysis logic
                # This is a bit of a hack since analyze_bazi is the orchestrator
                # We'll re-fetch dm_wave and field from a mock run
                from core.trinity.core.physics_engine import ParticleDefinitions
                dm_elem = ParticleDefinitions.STEM_WAVEFORMS.get(dm, {}).get('element', 'Earth')
                waves_init = engine._initialize_waves(bazi, dm, month)
                dm_wave_init = waves_init[dm_elem]
                
                # We need the final_system_waves which is internal to analyze_bazi
                full_analysis = engine.analyze_bazi(bazi, dm, month)
                field_waves = full_analysis['resonance_state'].field_waves
                
                injected_dm = EntanglementEngine.inject_particle(dm_wave_init, best_p, coupling=float(c_val))
                filtered_field = EntanglementEngine.apply_active_filtering(field_waves, best_p, coupling=float(c_val))
                res_test = ResonanceEngine.analyze_vibration_mode(injected_dm, filtered_field)
                
                if res_test.vibration_mode == "COHERENT" and res_test.snr > 0.80:
                    req_charge = f"{c_val:.2f}"
                    final_state = f"{res_test.vibration_mode} ({res_test.snr:.2f})"
                    found = True
                    break
            
            if not found:
                status = "Resistant"
                # Get best possible at 3.0
                injected_dm = EntanglementEngine.inject_particle(dm_wave_init, best_p, coupling=3.0)
                filtered_field = EntanglementEngine.apply_active_filtering(field_waves, best_p, coupling=3.0)
                res_last = ResonanceEngine.analyze_vibration_mode(injected_dm, filtered_field)
                final_state = f"{res_last.vibration_mode} ({res_last.snr:.3f})"
                req_charge = ">3.0"

        report_lines.append(f"| {case['id']} | {case['name']} | {initial_str} | {best_p} | {req_charge} | {final_state} | {status} |")

    report_lines.append("")
    report_lines.append("## 🔬 Logic Summary")
    report_lines.append("- **Filtering Charge**: The amount of external particle energy needed to suppress noise and force phase-locking.")
    report_lines.append("- **Resistant Cases**: Instances like '01-SYNC-METAL' where the initial noise (SNR < 0.2) is so loud that simple injection isn't enough; it might require the macro-level 'Spatial Remediation' (Phase 22) in addition to quantum intervention.")
    
    report_content = "\n".join(report_lines)
    
    report_path = Path("reports/quantum_remediation_report_v93.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    
    print(f"Report generated: {report_path}")

if __name__ == "__main__":
    generate_report()
