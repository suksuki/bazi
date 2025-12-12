"""
Antigravity Dynamics Engine V32.0 - First Principles Model (Part 2)
===================================================================

Implements Definitions 5-9:
5. Dynamics & Work (Rooting, Projection, Energy Flow)
6. Spacetime System (Da Yun, Liu Nian)
7. Spatial Correction (Geographic modifiers)
8. Probability Calculation (Wave Function)
9. Evolution Mechanism (Parameter optimization)
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from core.physics_kernel import PhysicsParameters, ParticleDefinitions, GeometricInteraction


class DynamicsEngine:
    """
    Definition 5: Dynamics & Work
    
    Implements:
    - Rooting (通根): Vertical energy anchoring
    - Projection (透干): Vertical energy expression
    - Energy Flow: Horizontal transfer with distance decay
    - Work Formula: Work = Energy × Efficiency
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
    
    def calculate_rooting_strength(self, stem: str, branch: str, distance: int) -> float:
        """
        Calculate rooting strength (通根力).
        
        Args:
            stem: Heavenly stem character
            branch: Earthly branch character
            distance: Pillar distance (0=same pillar, 1=adjacent, etc.)
        
        Returns:
            Rooting strength coefficient
        """
        # Get stem element
        stem_props = ParticleDefinitions.get_stem_properties(stem)
        stem_element = stem_props.get('element')
        
        # Get branch hidden stems
        branch_props = ParticleDefinitions.get_branch_properties(branch)
        # Hidden stems are in params
        hidden_stems = self.params.hidden_stems_ratios.get(branch, {})
        
        # Check if stem element exists in hidden stems
        rooting_strength = 0.0
        for hidden_stem, ratio in hidden_stems.items():
            hidden_props = ParticleDefinitions.get_stem_properties(hidden_stem)
            if hidden_props.get('element') == stem_element:
                # Found root!
                rooting_strength += ratio
        
        # Apply distance decay: 1 / D^N
        if distance > 0:
            decay_factor = 1.0 / (distance ** self.params.rooting_distance_decay)
            rooting_strength *= decay_factor
        
        # Apply base strength multiplier
        rooting_strength *= self.params.rooting_base_strength
        
        return rooting_strength
    
    def calculate_projection_strength(self, branch: str, stem: str) -> float:
        """
        Calculate projection strength (透干力).
        
        Args:
            branch: Earthly branch character
            stem: Heavenly stem character being projected
        
        Returns:
            Projection strength coefficient
        """
        hidden_stems = self.params.hidden_stems_ratios.get(branch, {})
        
        # Check if stem exists in hidden stems
        if stem in hidden_stems:
            ratio = hidden_stems[stem]
            return ratio * self.params.projection_efficiency
        
        return 0.0
    
    def calculate_energy_flow(self, 
                             source_element: str, 
                             target_element: str,
                             distance: int,
                             source_energy: float) -> Dict:
        """
        Calculate energy flow between elements.
        
        Args:
            source_element: Source element
            target_element: Target element
            distance: Distance between particles
            source_energy: Source energy level
        
        Returns:
            dict with 'flow_type', 'efficiency', 'transferred_energy'
        """
        # Determine relationship
        gen_cycle = ParticleDefinitions.GENERATION_CYCLE
        ctrl_cycle = ParticleDefinitions.CONTROL_CYCLE
        
        flow_type = "None"
        efficiency = 0.0
        
        if gen_cycle.get(source_element) == target_element:
            # Generation (Sheng) - Energy transfer
            flow_type = "Sheng"
            efficiency = self.params.sheng_transfer_efficiency
        
        elif ctrl_cycle.get(source_element) == target_element:
            # Control (Ke) - Vector opposition
            flow_type = "Ke"
            efficiency = self.params.ke_resistance_factor
        
        elif source_element == target_element:
            # Same element - Resonance
            flow_type = "Resonance"
            efficiency = 1.0
        
        # Apply distance decay
        if distance > 0:
            decay = 1.0 / (distance ** self.params.distance_decay_exponent)
            efficiency *= decay
        
        # Calculate transferred energy
        transferred = source_energy * efficiency
        
        return {
            'flow_type': flow_type,
            'efficiency': efficiency,
            'transferred_energy': transferred,
            'distance': distance
        }
    
    def calculate_work(self, energy: float, efficiency: float) -> float:
        """
        Calculate work done.
        
        Work = Energy × Efficiency × Coefficient
        
        Args:
            energy: Energy available
            efficiency: Efficiency factor
        
        Returns:
            Work done
        """
        work = (energy * 
                efficiency * 
                self.params.work_energy_coefficient * 
                self.params.work_efficiency_base)
        
        return work


class SpacetimeEngine:
    """
    Definition 6: Spacetime System
    
    - Da Yun (大运): Static Background Field
    - Liu Nian (流年): Dynamic Trigger Particle
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
    
    def apply_dayun_field(self, 
                         original_state: Dict,
                         dayun_stem: str,
                         dayun_branch: str) -> Dict:
        """
        Apply Da Yun as static background field.
        Rewrites physical constants of the original chart.
        
        Args:
            original_state: Original chart state
            dayun_stem: Da Yun stem
            dayun_branch: Da Yun branch
        
        Returns:
            Modified state with Da Yun field applied
        """
        modified_state = original_state.copy()
        
        # Da Yun acts as background field modifier
        # It doesn't add particles, but modifies the environment
        
        # Get Da Yun properties
        stem_props = ParticleDefinitions.get_stem_properties(dayun_stem)
        branch_props = ParticleDefinitions.get_branch_properties(dayun_branch)
        
        # Apply field strength
        field_strength = self.params.dayun_field_strength
        
        # Rewrite constants based on Da Yun element
        dayun_element = stem_props.get('element')
        
        modified_state['dayun_field'] = {
            'stem': dayun_stem,
            'branch': dayun_branch,
            'element': dayun_element,
            'field_strength': field_strength,
            'constant_rewrite_factor': self.params.dayun_constant_rewrite_factor
        }
        
        return modified_state
    
    def apply_liunian_trigger(self,
                             current_state: Dict,
                             liunian_stem: str,
                             liunian_branch: str) -> Dict:
        """
        Apply Liu Nian as dynamic trigger.
        High-energy particle collision with chart ports.
        
        Args:
            current_state: Current state (with Da Yun if applicable)
            liunian_stem: Liu Nian stem
            liunian_branch: Liu Nian branch
        
        Returns:
            State with Liu Nian trigger effects
        """
        triggered_state = current_state.copy()
        
        # Liu Nian acts as high-energy particle
        stem_props = ParticleDefinitions.get_stem_properties(liunian_stem)
        branch_props = ParticleDefinitions.get_branch_properties(liunian_branch)
        
        # Calculate impact strength
        impact_strength = self.params.liunian_impact_strength
        
        triggered_state['liunian_trigger'] = {
            'stem': liunian_stem,
            'branch': liunian_branch,
            'element': stem_props.get('element'),
            'impact_strength': impact_strength,
            'trigger_threshold': self.params.liunian_trigger_threshold
        }
        
        return triggered_state


class SpatialCorrection:
    """
    Definition 7: Spatial Correction (K_geo)
    
    Axiom: Destiny = Time + Space
    
    Implements geographic modifiers based on:
    - Latitude (temperature)
    - Longitude (time zone)
    - Terrain (humidity)
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
    
    def calculate_latitude_modifier(self, latitude: float) -> float:
        """
        Calculate temperature modifier based on latitude.
        
        Args:
            latitude: Latitude in degrees (-90 to 90)
        
        Returns:
            Temperature modifier coefficient
        """
        # Higher latitude = colder
        # This affects Water/Fire balance
        abs_lat = abs(latitude)
        modifier = 1.0 - (abs_lat * self.params.latitude_temperature_coefficient)
        
        return max(0.5, min(1.5, modifier))  # Clamp to reasonable range
    
    def calculate_longitude_modifier(self, longitude: float, birth_hour: int) -> float:
        """
        Calculate time zone phase shift.
        
        Args:
            longitude: Longitude in degrees (-180 to 180)
            birth_hour: Birth hour (0-23)
        
        Returns:
            Phase shift in hours
        """
        # Longitude affects true solar time
        # 15 degrees = 1 hour
        time_shift = longitude / 15.0
        
        return time_shift * self.params.longitude_phase_shift
    
    def get_terrain_modifier(self, terrain_type: str) -> float:
        """
        Get humidity modifier based on terrain.
        
        Args:
            terrain_type: 'coastal', 'inland', 'desert', 'mountain'
        
        Returns:
            Humidity modifier coefficient
        """
        return self.params.terrain_humidity_modifier.get(terrain_type, 1.0)
    
    def apply_spatial_correction(self,
                                 base_state: Dict,
                                 latitude: float,
                                 longitude: float,
                                 terrain: str = 'inland') -> Dict:
        """
        Apply complete spatial correction (K_geo).
        
        Args:
            base_state: Base chart state
            latitude: Latitude
            longitude: Longitude
            terrain: Terrain type
        
        Returns:
            Spatially corrected state
        """
        corrected_state = base_state.copy()
        
        lat_mod = self.calculate_latitude_modifier(latitude)
        terrain_mod = self.get_terrain_modifier(terrain)
        
        corrected_state['spatial_correction'] = {
            'latitude': latitude,
            'longitude': longitude,
            'terrain': terrain,
            'temperature_modifier': lat_mod,
            'humidity_modifier': terrain_mod
        }
        
        return corrected_state


class ProbabilityEngine:
    """
    Definition 8: Probability Calculation
    
    Abandons absolute determinism.
    Uses quantum wave function to calculate probability distributions.
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
    
    def create_wavefunction(self, 
                           mean: float, 
                           uncertainty: float = None) -> Dict:
        """
        Create a quantum wave function for an outcome.
        
        Args:
            mean: Expected value
            uncertainty: Standard deviation (if None, use default)
        
        Returns:
            Wave function dict with distribution parameters
        """
        if uncertainty is None:
            uncertainty = self.params.wavefunction_uncertainty_base
        
        return {
            'type': 'gaussian',
            'mean': mean,
            'std': uncertainty,
            'distribution': 'normal'
        }
    
    def calculate_probability(self, 
                            wavefunction: Dict,
                            threshold: float) -> float:
        """
        Calculate probability of exceeding threshold.
        
        Args:
            wavefunction: Wave function dict
            threshold: Threshold value
        
        Returns:
            Probability (0-1)
        """
        mean = wavefunction['mean']
        std = wavefunction['std']
        
        # Calculate z-score
        z = (threshold - mean) / std if std > 0 else 0
        
        # Use cumulative distribution function
        # P(X > threshold) = 1 - CDF(z)
        from scipy.stats import norm
        probability = 1 - norm.cdf(z)
        
        return probability
    
    def classify_outcome(self, probability: float) -> str:
        """
        Classify outcome based on probability.
        
        Args:
            probability: Probability value (0-1)
        
        Returns:
            Classification string
        """
        if probability >= self.params.probability_threshold_high:
            return "High Probability"
        elif probability >= self.params.probability_threshold_low:
            return "Medium Probability"
        else:
            return "Low Probability"
    
    def generate_distribution_samples(self,
                                     wavefunction: Dict,
                                     n_samples: int = 1000) -> np.ndarray:
        """
        Generate samples from wave function distribution.
        
        Args:
            wavefunction: Wave function dict
            n_samples: Number of samples
        
        Returns:
            Array of samples
        """
        mean = wavefunction['mean']
        std = wavefunction['std']
        
        samples = np.random.normal(mean, std, n_samples)
        
        return samples


class ParameterOptimizer:
    """
    Definition 9: Evolution Mechanism
    
    CRITICAL: All parameters must be tunable!
    
    Provides interface for:
    - Parameter regression
    - Data-driven optimization
    - Real case validation
    """
    
    def __init__(self, params: PhysicsParameters):
        self.params = params
        self.optimization_history = []
    
    def validate_against_real_case(self,
                                   predicted_value: float,
                                   real_value: float) -> Dict:
        """
        Validate prediction against real case.
        
        Args:
            predicted_value: Model prediction
            real_value: Actual observed value
        
        Returns:
            Validation metrics
        """
        error = real_value - predicted_value
        relative_error = error / real_value if real_value != 0 else float('inf')
        
        return {
            'predicted': predicted_value,
            'real': real_value,
            'error': error,
            'relative_error': relative_error,
            'accuracy': 1.0 - abs(relative_error)
        }
    
    def suggest_parameter_adjustment(self,
                                    param_name: str,
                                    validation_results: List[Dict]) -> float:
        """
        Suggest parameter adjustment based on validation results.
        
        Args:
            param_name: Parameter to adjust
            validation_results: List of validation dicts
        
        Returns:
            Suggested new parameter value
        """
        # Simple gradient descent approach
        # In production, use more sophisticated optimization
        
        current_value = getattr(self.params, param_name)
        
        # Calculate average error
        avg_error = np.mean([v['error'] for v in validation_results])
        
        # Adjust parameter (simple linear adjustment)
        learning_rate = 0.1
        adjustment = -learning_rate * avg_error
        
        new_value = current_value + adjustment
        
        return new_value
    
    def optimize_parameters(self,
                          training_data: List[Dict],
                          param_names: List[str],
                          max_iterations: int = 100) -> Dict:
        """
        Optimize multiple parameters using training data.
        
        Args:
            training_data: List of {input, output} dicts
            param_names: Parameters to optimize
            max_iterations: Maximum optimization iterations
        
        Returns:
            Optimization results
        """
        # Placeholder for full optimization implementation
        # In production, use gradient descent, genetic algorithms, etc.
        
        results = {
            'optimized_params': {},
            'final_error': 0.0,
            'iterations': 0
        }
        
        # This is where you'd implement:
        # - Loss function calculation
        # - Gradient computation
        # - Parameter updates
        # - Convergence checking
        
        return results
    
    def save_optimization_history(self, filepath: str):
        """Save optimization history to file"""
        import json
        with open(filepath, 'w') as f:
            json.dump(self.optimization_history, f, indent=2)


# Export main classes
__all__ = [
    'DynamicsEngine',
    'SpacetimeEngine',
    'SpatialCorrection',
    'ProbabilityEngine',
    'ParameterOptimizer'
]
