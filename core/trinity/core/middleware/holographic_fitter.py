
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
import logging

from core.physics_axioms import AXIOM_CONSTRAINTS

logger = logging.getLogger("HolographicMatrixFitter")

class HolographicMatrixFitter:
    """
    FDS-V1.4 Step 3: Matrix Fitting Engine
    Implements Projected Gradient Descent to fit Transfer Matrix T
    subject to Physics Axiom Constraints.
    
    Dimensions: 
    Input (x): [parallel, resource, power, wealth, output, clash, combination] (7D)
    Output (y): [E, O, M, S, R] (5D)
    Matrix T: 5x7
    """
    
    DIM_INPUT = 7
    DIM_OUTPUT = 5
    
    # Key mapping for indexing
    INPUT_KEYS = ["parallel", "resource", "power", "wealth", "output", "clash", "combination"]
    OUTPUT_KEYS = ["E", "O", "M", "S", "R"]

    def __init__(self, learning_rate: float = 0.05, regularization: float = 0.01, saturation_k: float = 3.0):
        self.lr = learning_rate
        self.reg = regularization
        self.saturation_k = saturation_k # Threshold for Diminishing Returns
        # Initialize T (identity-like or small random)
        self.transfer_matrix = np.zeros((self.DIM_OUTPUT, self.DIM_INPUT))
        # Initial guess: diagonal for first 5 ten gods
        for i in range(min(self.DIM_INPUT, self.DIM_OUTPUT)):
            self.transfer_matrix[i, i] = 1.0
            
    def _get_axiom_mask(self, pattern_id: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Returns (min_bounds, max_bounds) matrices for PGD projection.
        """
        min_mask = np.full((self.DIM_OUTPUT, self.DIM_INPUT), -2.0)
        max_mask = np.full((self.DIM_OUTPUT, self.DIM_INPUT), 2.0)
        
        # 1. Start with STANDARD
        self._apply_constraints_to_mask(min_mask, max_mask, AXIOM_CONSTRAINTS["STANDARD"])
        
        # 2. Layer Pattern Specific Overrides
        if pattern_id in AXIOM_CONSTRAINTS:
            self._apply_constraints_to_mask(min_mask, max_mask, AXIOM_CONSTRAINTS[pattern_id])
            
        return min_mask, max_mask

    def _apply_constraints_to_mask(self, min_m, max_m, constraints: Dict):
        for row_key, sub_dict in constraints.items():
            row_idx = self.OUTPUT_KEYS.index(row_key.split('_')[0])
            for ten_god, (low, high) in sub_dict.items():
                if ten_god in self.INPUT_KEYS:
                    col_idx = self.INPUT_KEYS.index(ten_god)
                    min_m[row_idx, col_idx] = low
                    max_m[row_idx, col_idx] = high

    def _apply_saturation(self, x: np.ndarray) -> np.ndarray:
        """
        [V1.4 Saturation Layer]
        Formula: x_sat = saturation_k * tanh(x / saturation_k)
        Limits x to [-saturation_k, saturation_k] with diminishing returns.
        """
        return self.saturation_k * np.tanh(x / self.saturation_k)

    def fit(self, 
            pattern_id: str,
            input_set: np.ndarray, # (N, 7)
            true_tensors: np.ndarray, # (N, 5)
            epochs: int = 1000):
        """
        Optimizes the transfer matrix using Gradient Descent + Axiom Projection.
        """
        N = input_set.shape[0]
        min_mask, max_mask = self._get_axiom_mask(pattern_id)
        
        # Pre-apply saturation to inputs for training stability
        saturated_inputs = self._apply_saturation(input_set)
        
        logger.info(f"🚀 Starting Matrix Fitting with Saturation (k={self.saturation_k}) for {pattern_id}. Samples: {N}")
        
        for epoch in range(epochs):
            # Forward: Y_pred = X_sat @ T.T
            y_pred = saturated_inputs @ self.transfer_matrix.T # (N, 5)
            
            # 1. MSE Loss
            error = y_pred - true_tensors
            loss_mse = np.mean(error**2)
            
            # 2. Physics Regularization (Frobenius Norm)
            loss_reg = self.reg * np.sum(self.transfer_matrix**2)
            
            # Total Loss
            loss = loss_mse + loss_reg
            
            # Gradient Calculation
            # dL/dT = (2/N) * (error.T @ saturated_inputs) + 2 * reg * T
            grad = (2.0 / N) * (error.T @ saturated_inputs) + 2.0 * self.reg * self.transfer_matrix
            
            # SGD Step
            self.transfer_matrix -= self.lr * grad
            
            # PROJECT STEP: Enforce Axioms
            self.transfer_matrix = np.clip(self.transfer_matrix, min_mask, max_mask)
            
            if epoch % 200 == 0:
                logger.info(f"Epoch {epoch}: Loss = {loss:.6f}")

        logger.info(f"✅ Training Complete. Final Loss: {loss:.6f}")
        return self.transfer_matrix

    def calculate_covariance(self, y_samples: np.ndarray) -> np.ndarray:
        """
        [V1.5] 计算样本在5D输出空间的协方差矩阵
        """
        # y_samples shape: (N, 5)
        return np.cov(y_samples.T)

    def export_to_json_format(self, covariance: Optional[np.ndarray] = None) -> Dict[str, Any]:
        """
        Converts the numpy matrix to the Registry friendly format.
        """
        result = {
            "transfer_matrix": {}
        }
        
        # 1. Export Transfer Matrix
        tm_dict = {}
        for r_idx, axis in enumerate(self.OUTPUT_KEYS):
            row_data = {}
            for c_idx, god in enumerate(self.INPUT_KEYS):
                val = round(float(self.transfer_matrix[r_idx, c_idx]), 4)
                if abs(val) > 1e-4:
                    row_data[god] = val
            tm_dict[f"{axis}_row"] = row_data
        result["transfer_matrix"] = tm_dict
        
        # 2. [V1.5] Export Covariance Matrix
        if covariance is not None:
            result["covariance_matrix"] = covariance.tolist()
            
        return result

# --- Unit Test / Boot Data ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # 1. Create Synthetic Gold Anchor for A-03
    # Input: Strong Blade (2.5) + Strong Killer (1.8)
    # Plus some noise in other gods
    x_train = np.array([
        [2.5, 0.4, 1.8, 0.2, 0.1, 0.0, 0.0], # Blade dominant
        [2.8, 0.2, 2.0, 0.1, 0.1, 0.5, 0.0], # Blade/Killer/Clash
        [2.0, 0.8, 1.5, 0.3, 0.2, 0.0, 0.3], # Resource/Combination
    ])
    
    # Target Tensor (y_true) from Instructions:
    # E: 0.95, O: 0.85, M: 0.60, S: 0.30, R: 0.40
    y_target = np.array([0.95, 0.85, 0.60, 0.30, 0.40])
    y_train = np.tile(y_target, (3, 1)) # Replicated for dummy training
    
    fitter = HolographicMatrixFitter(learning_rate=0.02, regularization=0.005)
    matrix = fitter.fit("A-03", x_train, y_train, epochs=2000)
    
    json_matrix = fitter.export_to_json_format()
    import json
    print("\n--- FITTED A-03 TRANSFER MATRIX ---")
    print(json.dumps(json_matrix, indent=2, ensure_ascii=False))
