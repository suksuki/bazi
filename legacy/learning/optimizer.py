import numpy as np
from core.flux import FluxEngine

class WeightOptimizer:
    """
    Antigravity Physics Kernel Calibrator (V7.0).
    Uses Gradient Descent to optimize FluxEngine positional weights based on Ground Truth labels.
    """
    
    def __init__(self, cases):
        """
        cases: list of dicts.
               Example: [{'chart': {...}, 'label': 1.0 (Strong) / 0.0 (Weak)}, ...]
        """
        self.cases = cases
        self.learning_rate = 0.05
        # Initial Weights (V7.0 Baseline)
        self.weights = {
            "month_branch": 4.5,
            "hour_branch": 2.5,
            "day_branch": 1.5,
            "year_branch": 1.5,
            "month_stem": 2.5,
            "hour_stem": 1.5,
            "day_stem": 1.0,
            "year_stem": 1.0
        }
        
    def optimize(self, epochs=50):
        print(f"Starting Optimization on {len(self.cases)} cases...")
        
        for epoch in range(epochs):
            total_loss = 0.0
            gradients = {k: 0.0 for k in self.weights}
            
            for case in self.cases:
                chart = case['chart']
                true_label = case['label'] # 1.0 or 0.0
                
                # Forward Pass
                pred_strength = self._predict_strength(chart, self.weights)
                
                # Loss (MSE)
                loss = (pred_strength - true_label) ** 2
                total_loss += loss
                
                # Backward Pass (Approximate Gradient via Finite Difference would be cleaner given the complex FluxEngine logic, 
                # but let's try a heuristic direction)
                # If Pred > True (Too Strong) -> Decrease weights of Dominant Elements? 
                # That's hard.
                # Let's use Finite Difference (Numerical Gradient) for accuracy.
                pass 

            # Numerical Gradient Descent (Batch)
            # Since we only have ~8 params, we can checking dLoss/dWeight individually per epoch
            current_loss = self._calculate_batch_loss(self.weights)
            epsilon = 0.1
            
            for key in self.weights:
                # Perturb +
                temp_weights = self.weights.copy()
                temp_weights[key] += epsilon
                loss_plus = self._calculate_batch_loss(temp_weights)
                
                # Gradient: (f(x+h) - f(x)) / h
                grad = (loss_plus - current_loss) / epsilon
                
                # Update
                self.weights[key] -= self.learning_rate * grad
                
                # Constraint: Weights must be positive
                self.weights[key] = max(0.1, self.weights[key])

            if epoch % 10 == 0:
                print(f"Epoch {epoch}: Loss = {current_loss:.4f}")
                
        return self.weights

    def _calculate_batch_loss(self, weights):
        loss = 0.0
        for case in self.cases:
            pred = self._predict_strength(case['chart'], weights)
            loss += (pred - case['label']) ** 2
        return loss / len(self.cases)

    def _predict_strength(self, chart, weights):
        """
        Runs FluxEngine with proposed weights and returns Day Master Strength Ratio (0.0 - 1.0).
        """
        flux = FluxEngine(chart)
        # Inject weights
        flux.params['positional_weights'] = weights
        
        result = flux.compute_energy_state()
        spec = result['spectrum']
        
        dm_elem = chart.get('day', {}).get('stem_element', 'Wood') # Assume processed chart or lookup
        # Fallback if stem_element not in chart dict, try to derive
        if 'stem' in chart.get('day', {}):
             from core.wuxing_engine import WuXingEngine
             wx = WuXingEngine(chart)
             dm_elem = wx.get_wuxing(chart['day']['stem'])
        
        # Calculate DM Strength Ratio
        total_energy = sum(spec.values())
        if total_energy == 0: return 0.0
        
        # Proper Strength: Same + Resource
        # generating = {"Wood":"Water", ...} # Wait, need Resource. 
        # Resource is element that generates DM.
        resource_map = {"Wood":"Water", "Fire":"Wood", "Earth":"Fire", "Metal":"Earth", "Water":"Metal"}
        resource_elem = resource_map.get(dm_elem)
        
        my_strength = spec.get(dm_elem, 0) + spec.get(resource_elem, 0)
        
        return my_strength / total_energy
