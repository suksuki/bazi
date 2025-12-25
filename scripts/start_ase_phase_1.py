
import sys
import os
import time
import json
import logging
from datetime import datetime

# Add project root to path
# Script is in /home/jin/bazi_predict/scripts/start_ase_phase_1.py
# Root is /home/jin/bazi_predict/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(project_root)

from core.trinity.core.unified_arbitrator_master import QuantumUniversalFramework
from core.trinity.core.engines.synthetic_bazi_engine import SyntheticBaziEngine, ExpectedValueCollector

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ASE_Phase_1")

def run_ase_census(sample_size=10000):
    """
    启动 ASE 专题阶段一：全样本合成与统计定标
    """
    logger.info(f"🚀 Starting ASE Phase 1: Great Fate Census [Sample Size: {sample_size}]")
    
    framework = QuantumUniversalFramework()
    engine = SyntheticBaziEngine()
    collector = ExpectedValueCollector()
    
    start_time = time.time()
    processed = 0
    
    # We use a generator to save memory
    bazi_gen = engine.generate_all_bazi()
    
    # For full 52w run, we would use bazi_gen directly. 
    # For this task, we process a significant sample to establish the baseline.
    for _ in range(sample_size):
        try:
            chart = next(bazi_gen)
            
            # 随机挂载实证参数 (Luck, Annual, Geo)
            # 模拟全量注入
            import random
            luck = random.choice(engine.JIA_ZI)
            annual = random.choice(engine.JIA_ZI)
            geo_factor = random.uniform(0.8, 1.2)
            geo_element = random.choice(["Wood", "Fire", "Earth", "Metal", "Water", "Neutral"])
            
            ctx = {
                "luck_pillar": luck,
                "annual_pillar": annual,
                "geo_factor": geo_factor,
                "data": {
                    "geo_factor": geo_factor,
                    "geo_element": geo_element
                },
                "scenario": "ASE_SYNTHETIC_EVOLUTION"
            }
            
            # Execute Physics Pipeline
            report = framework.arbitrate_bazi(chart, current_context=ctx)
            
            # Inject chart back for collector meta
            report["meta"]["chart"] = chart
            
            # Collect Metrics
            collector.collect(report)
            
            processed += 1
            if processed % 1000 == 0:
                elapsed = time.time() - start_time
                speed = processed / elapsed
                logger.info(f"📊 Processed {processed}/{sample_size} | Speed: {speed:.2f} charts/s")
                
        except StopIteration:
            break
        except Exception as e:
            logger.error(f"❌ Error processing chart {chart}: {e}")
            continue

    total_time = time.time() - start_time
    summary = collector.get_summary()
    
    logger.info(f"✅ ASE Phase 1 Census Completed in {total_time:.2f}s")
    logger.info(f"📊 Summary Stats: {json.dumps(summary, indent=2, ensure_ascii=False)}")
    
    # Output to File
    output_path = os.path.join(project_root, "reports/ase_phase_1_baseline.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "sample_size": processed,
            "total_time": total_time,
            "summary": summary,
            "singularities": collector.singularities[:100] # Save first 100 for inspection
        }, f, indent=2, ensure_ascii=False)
        
    logger.info(f"💾 Report saved to {output_path}")

if __name__ == "__main__":
    # If called with an argument, use that as sample size
    size = 10000
    if len(sys.argv) > 1:
        size = int(sys.argv[1])
    run_ase_census(size)
