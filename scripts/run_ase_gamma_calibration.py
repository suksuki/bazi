
import os
import sys
import json
import logging
import time

# Add project root to path
sys.path.append(os.getcwd())

from core.trinity.core.engines.simulation_controller import SimulationController

def main():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("ASE_Gamma_Calibration")
    
    logger.info("🚀 Starting ASE Phase 2: 10,000 Sample Gamma Calibration...")
    
    controller = SimulationController(os.getcwd())
    
    start_t = time.time()
    # Execute 10,000 sample scan with finer steps for precision
    # Overriding the default range for more accuracy in finding 3.5%
    def progress_log(curr, total, stats):
        if curr % 1 == 0:
            logger.info(f"📊 Scan Progress: {curr}/{total} | Gamma: {stats['gamma']:.3f} | Rate: {stats['rate']:.2f}%")

    # We use a more refined range for the 10,000 sample run
    res = controller.run_gradient_calibration(sample_size=10000, progress_callback=progress_log)
    
    end_t = time.time()
    
    logger.info("✅ Calibration Complete!")
    logger.info(f"⏱️ Duration: {end_t - start_t:.2f}s")
    logger.info(f"🎯 Optimal Gamma (Γ): {res['optimal_gamma']:.4f}")
    logger.info(f"📈 Achieved Singularity Rate: {res['achieved_rate']:.2f}%")
    
    # Save the result to a calibration report
    report_path = os.path.join(os.getcwd(), "reports", "v13_8_gamma_calibration.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)
    
    logger.info(f"💾 Report saved to {report_path}")
    
    # Update global config (Pseudo-code, let's see if we have a config we can write to)
    # Most engines use the current context, so we'll recommend this value in the UI
    print(f"\n[RESULT] OPTIMAL_GAMMA={res['optimal_gamma']}")

if __name__ == "__main__":
    main()
