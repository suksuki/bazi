import math
import random
from core.config_manager import ConfigManager

class QuantumEngine:
    """
    Quantum Bazi Engine V16.0
    Simulates the collapse of the Bazi Wavefunction into concrete life aspects using Flux Dynamics.
    Integrates Real-time Particle Energy, Entropy, and Dynamic Weights.
    """
    def __init__(self, chart_gods, reactions, flux_data=None, wuxing_engine=None):
        self.gods = chart_gods # Legacy support
        self.reactions = reactions
        self.flux_data = flux_data or {}
        self.we = wuxing_engine
        self.cm = ConfigManager()
        
        # Load Evolution Weights (Vreal Feedback)
        self.weights = self._load_dynamic_weights()
        
    def _load_dynamic_weights(self):
        # Default Weights (V16 Baseline)
        defaults = {
            "Wealth": {"PianCai": 0.9, "ZhengCai": 0.8, "ShiShen": 0.4, "ShangGuan": 0.5, "Entropy": 0.2},
            "Career": {"ZhengGuan": 0.9, "QiSha": 0.95, "ZhengYin": 0.4, "PianYin": 0.3, "ShangGuan": 0.2, "Entropy": 0.1},
            "Friendship": {"BiJian": 0.8, "JieCai": 0.9, "ShiShen": 0.3},
            "Education": {"ZhengYin": 0.95, "PianYin": 0.85, "ZhengGuan": 0.5},
            "Creativity": {"ShiShen": 0.9, "ShangGuan": 1.1, "PianYin": 0.7, "Entropy": 0.5}
        }
        # In future, self.cm.get('quantum_weights') could override this
        return defaults

    def simulate(self):
        """
        Returns a dictionary of life aspects with their Probability Density Code (Mu, Sigma).
        Uses High-Dimensional Tensor Mapping based on Flux Data.
        """
        results = {}
        
        # 1. Parse Flux Data directly (Energy > Static Count)
        # If flux_data is provided (V16 mode), we build a dynamic strength map
        dynamic_strength = {}
        
        if self.flux_data:
            # Extract Ten Gods Map from Flux Data
            # Note: Flux Data keys are like "七杀 (Warrior)"
            for key, val in self.flux_data.items():
                if isinstance(val, dict) and 'score' in val:
                    # Parse code from label? e.g. "七杀 (Warrior)" -> "QiSha"
                    # We need a robust mapper or use Chinese keys.
                    # Let's use Chinese keys mapping to our internal codes
                    if "七杀" in key: dynamic_strength["QiSha"] = val['score']
                    elif "正官" in key: dynamic_strength["ZhengGuan"] = val['score']
                    elif "食神" in key: dynamic_strength["ShiShen"] = val['score']
                    elif "伤官" in key: dynamic_strength["ShangGuan"] = val['score']
                    elif "偏财" in key: dynamic_strength["PianCai"] = val['score']
                    elif "正财" in key: dynamic_strength["ZhengCai"] = val['score']
                    elif "偏印" in key: dynamic_strength["PianYin"] = val['score']
                    elif "正印" in key: dynamic_strength["ZhengYin"] = val['score']
                    elif "比肩" in key: dynamic_strength["BiJian"] = val['score']
                    elif "劫财" in key: dynamic_strength["JieCai"] = val['score']
        
        # Fallback to static gods if dynamic not available
        source_map = dynamic_strength if dynamic_strength else self.gods

        # 2. Get Global Entropy
        global_entropy = 0.0
        # If Flux V16, sum particle entropy
        if self.flux_data:
             # Extract interactions from trace to estimate entropy
             interactions = self.flux_data.get('trace', {}).get('interactions', [])
             if interactions:
                 global_entropy = len(interactions) * 5.0  # Estimator
        
        # Calculate Aspect Energy via Dot Product
        # Map aspect keys to Chinese for UI consistency
        aspect_map = {
            "Wealth": "财富 (Wealth)",
            "Career": "事业 (Career)",
            "Friendship": "人际 (Friendship)",
            "Education": "学业 (Education)",
            "Creativity": "创造 (Creativity)"
        }

        for aspect_code, weights in self.weights.items():
            aspect_ui = aspect_map.get(aspect_code, aspect_code)
            
            # A. Dot Product: [Energy Vector] • [Weight Vector]
            base_score = 0.0
            for god, weight in weights.items():
                if god == "Entropy": continue
                god_strength = source_map.get(god, 0)
                base_score += god_strength * weight
                
            # B. Volatility (Sigma)
            # Base Volatility + Entropy Contribution
            # Start from minimal base to ensure entropy has visible effect
            volatility = 0.1  # Near zero baseline
            entropy_weight = weights.get("Entropy", 0.0)
            volatility += global_entropy * entropy_weight

            # C. Reaction modifier (Interference Patterns)
            # Constructive vs Destructive
            # Simplified: More interactions = More volatility
            reaction_chaos = len(self.reactions) * 2.0
            
            final_mu = base_score
            final_sigma = volatility + reaction_chaos
            
            # D. Probability Math (CDF)
            try:
                # P(X > 60) Success Threshold
                z = (60 - final_mu) / max(1, final_sigma)
                p_success = 0.5 * (1 - math.erf(z / math.sqrt(2)))
                
                # P(X < 30) Failure Threshold
                z_fail = (30 - final_mu) / max(1, final_sigma)
                p_fail = 0.5 * (1 + math.erf(z_fail / math.sqrt(2)))
                
            except:
                p_success = 0.5; p_fail = 0.5

            results[aspect_ui] = {
                "Expected_Value": final_mu,
                "Uncertainty": final_sigma,
                "P_High": p_success,
                "P_Low": p_fail,
                "Composition": weights
            }
            
        return results

class TenGodsWaveFunction:
    """
    Simple wave function sampler for Monte Carlo trajectories.
    Generates stochastic samples around a base energy using Gaussian distribution.
    """
    def __init__(self, chart_structure=None, wuxing_report=None):
        self.chart = chart_structure or {}
        self.wuxing = wuxing_report or {}
    
    def collapse_wave_function(self, dominant_god, base_energy=50):
        """
        Collapse the wave function to get a random sample.
        base_energy: Expected value (mean)
        Returns: A random sample from Gaussian distribution
        """
        import random
        # Add some quantum uncertainty (sigma ~ 20% of base)
        sigma = max(5, base_energy * 0.2)
        return random.gauss(base_energy, sigma)
