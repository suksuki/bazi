
import json
import numpy as np
import logging
from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("DSeriesTrainer")

def train_d_series():
    # 1. Load Stratified Data
    with open("data/stratified_samples_d_series.json", "r") as f:
        all_data = json.load(f)
    
    for pattern_id in ["D-01", "D-02"]:
        data = [s for s in all_data if s['pattern_id'] == pattern_id]
        if not data: continue
        
        x_train = np.array([s['x'] for s in data])
        y_train = np.array([s['y'] for s in data])
        
        logger.info(f"--- Training {pattern_id} ---")
        
        # 2. Initialize Fitter
        # Use axioms for D-01/D-02
        fitter = HolographicMatrixFitter(learning_rate=0.05, regularization=0.01, saturation_k=3.0)
        
        # 3. Fit Matrix
        matrix_t = fitter.fit(pattern_id, x_train, y_train, epochs=2000)
        
        # 4. Export Result
        json_matrix = fitter.export_to_json_format()
        
        output_path = f"core/subjects/holographic_pattern/{pattern_id.lower()}_fitted_matrix.json"
        with open(output_path, "w") as f:
            json.dump(json_matrix, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ {pattern_id} Matrix saved to {output_path}")

if __name__ == "__main__":
    train_d_series()
