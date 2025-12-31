
import json
import numpy as np
import logging
from core.trinity.core.middleware.holographic_fitter import HolographicMatrixFitter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("A03Trainer")

def train_a03():
    # 1. Load Stratified Data
    with open("data/stratified_samples_a03.json", "r") as f:
        data = json.load(f)
    
    x_train = np.array([s['x'] for s in data])
    y_train = np.array([s['y'] for s in data])
    
    # 2. Initialize Fitter with Saturation (k=3.0)
    # Higher learning rate for cold start
    fitter = HolographicMatrixFitter(learning_rate=0.05, regularization=0.01, saturation_k=3.0)
    
    # 3. Fit Matrix
    # We run for more epochs to ensure convergence across 500 heterogeneous samples
    matrix_t = fitter.fit("A-03", x_train, y_train, epochs=5000)
    
    # 4. Export Result
    json_matrix = fitter.export_to_json_format()
    
    print("\n--- ✅ FDS-V1.4 OPTIMIZED A-03 MATRIX ---")
    print(json.dumps(json_matrix, indent=2, ensure_ascii=False))
    
    # Optional: Save back to registry? 
    # For now, let's just save to a temporary file
    with open("core/subjects/holographic_pattern/a03_fitted_matrix.json", "w") as f:
        json.dump(json_matrix, f, indent=2, ensure_ascii=False)
    
    logger.info("Matrix saved to core/subjects/holographic_pattern/a03_fitted_matrix.json")

if __name__ == "__main__":
    train_a03()
