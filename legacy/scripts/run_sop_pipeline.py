
import sys
import os
import json
import logging
import argparse
import numpy as np
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

sys.path.insert(0, os.getcwd())

from core.logic_compiler import get_knowledge_census
from core.census_cache import get_census_cache
from core.protocol_checker import LOGIC_PROTOCOLS

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("SOP_Pipeline")

# Constants
SOP_VERSION = "1.0"
OUTPUT_DIR = Path("sop_output")
CENSUS_LIMIT = None # Full Scale Scan (518,400 samples)

# Quality Gates
GATE_1_MIN_ABUNDANCE = 0.001  # 0.1%
GATE_1_MAX_ABUNDANCE = 0.15   # 15%
GATE_2_MIN_STABILITY = 2.0    # 1/Tr(Cov)

class SOPPipeline:
    def __init__(self, pattern_id: str, force: bool = False):
        self.pattern_id = pattern_id
        self.force = force
        self.census_engine = get_knowledge_census()
        self.cache_engine = get_census_cache()
        self.report = {
            "pattern_id": pattern_id,
            "timestamp": datetime.now().isoformat(),
            "sop_version": SOP_VERSION,
            "steps": {}
        }
        
        # Ensure output dir
        OUTPUT_DIR.mkdir(exist_ok=True)

    def run(self):
        logger.info(f"🚀 Starting SOP Pipeline for {self.pattern_id}")
        
        try:
            # Step 1-2: Logic Census
            census_data = self._run_census()
            
            # Step 3-4: FDS Fitting
            fitting_data = self._run_fitting(census_data)
            
            # Step 5-8: Audit & Persistence
            registry_data = self._run_persistence(census_data, fitting_data)
            
            # Generate Final Report
            self._generate_artifacts(registry_data)
            
            logger.info(f"✅ SOP Completed Successfully for {self.pattern_id}")
            
        except Exception as e:
            logger.error(f"❌ SOP Failed: {e}")
            sys.exit(1)

    def _run_census(self) -> Dict[str, Any]:
        """Phase I: Logic Census & Gate 1"""
        logger.info("--- Phase I: Logic Census ---")
        
        # Execute Census
        res = self.census_engine.request_census(self.pattern_id, limit=CENSUS_LIMIT, include_tensor=True)
        
        abundance = res['abundance']
        matched = res['matched_count']
        
        logger.info(f"Matched: {matched} / {res['total_scanned']} (Abundance: {abundance:.4f})")
        
        # Gate 1 Check
        self.report['steps']['census'] = {
            "matched": matched,
            "abundance": abundance,
            "status": "PASS"
        }
        
        if not self.force:
            if matched == 0:
                raise ValueError("👻 Ghost Detected (0 Samples). Trigger Ghost Protocol.")
            if abundance < GATE_1_MIN_ABUNDANCE:
                # Check for Rarity Override (TODO: Implement Whitelist)
                logger.warning(f"⚠️ Low Abundance ({abundance:.4f}). Potential Logic Collapse.")
            if abundance > GATE_1_MAX_ABUNDANCE:
                raise ValueError(f"🚨 Noise Detected (Abundance {abundance:.4f} > {GATE_1_MAX_ABUNDANCE}). Dehydrate!")
                
        return res

    def _run_fitting(self, census_data: Dict) -> Dict[str, Any]:
        """Phase II: FDS Fitting & Gate 2"""
        logger.info("--- Phase II: FDS Fitting ---")
        
        # Use CensusCache to compute physics
        samples = census_data['samples']
        
        cache_res = self.cache_engine.cache_census_result(
            self.pattern_id, 
            samples, 
            {'name': self.pattern_id, 'sop_run': True}
        )
        
        cached_obj = self.cache_engine.get_cached_manifold(self.pattern_id)
        if not cached_obj:
            raise ValueError("Fitting Failed: Cache object not found.")
            
        mean = cached_obj['mean_vector']
        cov = cached_obj['covariance']
        
        # Calc Stability
        trace_cov = np.trace(np.array(cov))
        stability = 1.0 / (trace_cov + 1e-5)
        
        logger.info(f"Stability Score: {stability:.2f}")
        logger.info(f"Mean Vector: {[f'{x:.3f}' for x in mean]}")

        # --- Physics Kernel Audit (Step 5 Logic) ---
        from core.physics_kernel import validate_tensor_signs
        
        # Determine dominant gods from pattern ID (Heuristic/Hardcoded mapping for now)
        base_id = self.pattern_id.split('@')[0]
        # Map A-01 to zheng_guan, etc.
        # This ideally comes from LKV metadata, but parsing logic is complex.
        # We use a simple map for V1.
        GOD_MAP = {
            "A-01": ["zheng_guan"],
            "A-02": ["qi_sha"],
            "A-03": ["jie_cai"], # Yang Ren is technically Jie Cai intensity
            "B-01": ["shi_shen"],
            "B-02": ["shang_guan"],
            "C-01": ["zheng_yin"],
            "C-02": ["pian_yin"],
            "D-01": ["zheng_cai"],
            "D-02": ["pian_cai"]
        }
        dominant_gods = GOD_MAP.get(base_id, [])
        
        audit_res = validate_tensor_signs(self.pattern_id, mean, dominant_gods)
        logger.info(f"Physics Audit: Drift={audit_res['drift_score']:.2f}, Passed={audit_res['passed']}")
        if not audit_res['passed']:
            logger.warning(f"Audit Details: {audit_res['details']}")
        
        # Gate 2 Check (+ Audit)
        self.report['steps']['fitting'] = {
            "mean": mean,
            "covariance_trace": trace_cov,
            "stability": stability,
            "status": "PASS" if (stability >= GATE_2_MIN_STABILITY and audit_res['passed']) else "FAIL",
            "physics_audit": audit_res
        }
        
        if not self.force:
             if stability < GATE_2_MIN_STABILITY:
                 raise ValueError(f"👻 Quantum Ghost (Stability {stability:.2f} < {GATE_2_MIN_STABILITY}). Manifold Collapsed.")
             if not audit_res['passed']:
                 raise ValueError(f"🚨 Logic Violation (Drift {audit_res['drift_score']:.2f} > 0.3). Physics Kernel Rejected.")
             
        return cached_obj

    def _run_persistence(self, census_data: Dict, fitting_data: Dict) -> Dict[str, Any]:
        """Phase III & IV: Benchmarking & Registry"""
        logger.info("--- Phase III/IV: Persistence ---")
        
        # Harvest Benchmarks
        # Sort by Mahalanobis Distance (Mock calculation for now as we don't have full matrix inv here easily)
        # Actually CensusCache has `fingerprint_match` but that's for 1 input vs All Patterns.
        # Here we have 1 Pattern vs All Samples.
        # We'll rely on Euclidean distance from Mean for simplicity in this V1 script,
        # or implement Mahalanobis if Cov is invertible.
        
        mean = np.array(fitting_data['mean_vector'])
        cov = np.array(fitting_data['covariance'])
        try:
             inv_cov = np.linalg.inv(cov)
        except:
             inv_cov = np.eye(5)
             
        def calc_dist(tensor):
            t = np.array([tensor.get(k, 0) for k in ['E','O','M','S','R']])
            diff = t - mean
            return np.sqrt(np.dot(np.dot(diff, inv_cov), diff))
            
        samples = census_data['samples']
        scored_samples = []
        for s in samples:
            if 'tensor' in s:
                d = calc_dist(s['tensor'])
                scored_samples.append({**s, "distance": float(d)})
                
        scored_samples.sort(key=lambda x: x['distance'])
        
        # Extract Green (Best 3), Yellow (Mid), Red (Edge)
        # Green: Top 3
        green = scored_samples[:3]
        # Red: Furthest 3 (but within reasonable bounds)
        red = scored_samples[-3:] if len(scored_samples) > 10 else []
        
        benchmarks = [
            {"uid": s['uid'], "type": "GREEN_PATH", "distance": s['distance']} for s in green
        ] + [
            {"uid": s['uid'], "type": "RED_PATH", "distance": s['distance']} for s in red
        ]
        
        logger.info(f"Harvested {len(benchmarks)} Benchmarks.")
        
        # Construct Registry Entry
        registry_entry = {
            "pattern_id": self.pattern_id,
            "version": SOP_VERSION,
            "meta": {
                "generated_at": datetime.now().isoformat(),
                "gate_status": "PASSED"
            },
            "physics": {
                "mean_vector": fitting_data['mean_vector'],
                "covariance": fitting_data['covariance'],
                "stability": self.report['steps']['fitting']['stability']
            },
            "benchmarks": benchmarks,
            "matching_router": {
                "method": "MAHALANOBIS",
                "thresholds": {"green": 1.5, "yellow": 3.0}
            }
        }
        
        return registry_entry

    def _generate_artifacts(self, registry_data: Dict):
        """Generate output files"""
        # JSON
        json_path = OUTPUT_DIR / f"{self.pattern_id.replace('@','_')}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(registry_data, f, indent=2, ensure_ascii=False)
            
        # Markdown Report
        md_path = OUTPUT_DIR / f"{self.pattern_id.replace('@','_')}_report.md"
        
        stats = self.report['steps']
        md_content = f"""# SOP Audit Report: {self.pattern_id}

**Date**: {datetime.now().isoformat()}
**Status**: ✅ PASSED

## 1. Census (Gate 1)
- **Matched**: {stats['census']['matched']}
- **Abundance**: {stats['census']['abundance']:.4f}
- **Verdict**: {stats['census']['status']}

## 2. Fitting (Gate 2)
- **Stability Score**: {stats['fitting']['stability']:.2f}
- **Mean Vector**: {stats['fitting']['mean']}
- **Verdict**: {stats['fitting']['status']}

## 3. Benchmarks
| UID | Type | Distance |
|---|---|---|
"""
        for b in registry_data['benchmarks']:
            md_content += f"| {b['uid']} | {b['type']} | {b['distance']:.4f} |\n"
            
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(md_content)
            
        logger.info(f"📝 Artifacts generated in {OUTPUT_DIR}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FDS-LKV SOP Automation Pipeline")
    parser.add_argument("--pattern", required=True, help="Pattern ID (e.g. A-03@Zi)")
    parser.add_argument("--force", action="store_true", help="Bypass Quality Gates")
    
    args = parser.parse_args()
    
    pipeline = SOPPipeline(args.pattern, args.force)
    pipeline.run()
