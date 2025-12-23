"""
Phase 36: Relationship Gravity Engine
=====================================
Models relationship dynamics using Gravitational Physics and Quantum Phase Collapse.

Core Variables:
- Binding Energy (E): Gravitational binding between DM and Spouse Star. E = -G*M1*M2/(2r)
- Orbital Stability (σ): Resistance to perturbation. σ = |E_bind| / E_perturb
- Phase Coherence (η): Quantum coherence of relationship wave function. η = cos²(Δφ/2)
"""

import numpy as np
from core.trinity.core.nexus.definitions import PhysicsConstants, BaziParticleNexus, ArbitrationNexus

class RelationshipGravityEngine:
    """
    Models the Spouse Star and Spouse Palace as a gravitationally bound binary system.
    Analyzes binding energy, perturbation effects, and phase coherence.
    """
    
    # Gravitational Constant (scaled for Bazi energy units)
    G = 6.674  # Analogous to gravitational constant
    
    # Peach Blossom Mapping (Year/Day Branch Triad -> Peach Blossom Branch)
    PEACH_BLOSSOM_MAP = {
        frozenset(['寅', '午', '戌']): '卯',
        frozenset(['申', '子', '辰']): '酉',
        frozenset(['巳', '酉', '丑']): '午',
        frozenset(['亥', '卯', '未']): '子'
    }
    
    def __init__(self, dm_stem: str, gender: str = "男"):
        """
        Args:
            dm_stem: Day Master stem character (e.g., '壬')
            gender: '男' (Male) or '女' (Female)
        """
        self.dm_stem = dm_stem
        self.gender = gender
        
        # Get DM Element
        dm_info = BaziParticleNexus.STEMS.get(dm_stem, ("Unknown", "Unknown", 0))
        self.dm_element = dm_info[0]
        
        # Determine Spouse Star Element
        # Male: Wealth (DM controls) is Spouse Star
        # Female: Control (controls DM) is Spouse Star
        if gender == "男":
            self.spouse_star_element = PhysicsConstants.CONTROL.get(self.dm_element)  # DM controls X
        else:
            # Find what controls DM
            self.spouse_star_element = next(
                (k for k, v in PhysicsConstants.CONTROL.items() if v == self.dm_element), 
                None
            )
    
    def analyze_relationship(self, waves: dict, pillars: list, 
                               luck_pillar: str = None, 
                               annual_pillar: str = None,
                               geo_factor: float = 1.0) -> dict:
        """
        Analyzes relationship dynamics based on wave energies and structural interactions.
        [Phase 36-B] Now includes dynamic spacetime factors.
        
        Args:
            waves: Dict of WaveState objects keyed by element.
            pillars: List of pillar strings ["甲子", "丙寅", ...]
            luck_pillar: Current Major Cycle pillar (e.g., "壬申") - Background Field
            annual_pillar: Current Annual pillar (e.g., "乙巳") - Impulse Perturbation
            geo_factor: Geo-environmental multiplier (0.5-1.5) - Medium Constant
        
        Returns:
            Dict containing Binding Energy, Orbital Stability, Phase Coherence, and State.
        """
        # 1. Extract Day Branch (Spouse Palace)
        day_pillar = pillars[2] if len(pillars) > 2 else ""
        spouse_palace = day_pillar[1] if len(day_pillar) > 1 else ""
        spouse_palace_element = BaziParticleNexus.BRANCHES.get(spouse_palace, ("Unknown",))[0]
        
        # 2. Get Energy Masses
        m_dm = waves.get(self.dm_element).amplitude if waves.get(self.dm_element) else 1.0
        m_spouse = waves.get(self.spouse_star_element).amplitude if waves.get(self.spouse_star_element) else 1.0
        
        # [Phase 36-B] 2b. Apply Luck Modifier to Spouse Mass
        # If Luck Pillar element matches Spouse Star, boost mass; if clashes, reduce
        luck_modifier = 1.0
        if luck_pillar and len(luck_pillar) > 1:
            luck_branch = luck_pillar[1]
            luck_element = BaziParticleNexus.BRANCHES.get(luck_branch, ("Unknown",))[0]
            if luck_element == self.spouse_star_element:
                luck_modifier = 1.3  # Luck supports Spouse Star
            elif PhysicsConstants.CONTROL.get(luck_element) == self.spouse_star_element:
                luck_modifier = 0.7  # Luck controls (weakens) Spouse Star
            # Check if luck clashes with Spouse Palace
            luck_clash = ArbitrationNexus.CLASH_MAP.get(luck_branch)
            if luck_clash == spouse_palace:
                luck_modifier *= 0.6  # Major destabilization
        m_spouse *= luck_modifier
        
        # 3. Calculate Orbital Distance (inversely related to alignment)
        if spouse_palace_element == self.spouse_star_element:
            r = 1.0  # Tight orbit
        elif self._elements_compatible(spouse_palace_element, self.spouse_star_element):
            r = 2.0  # Compatible but not identical
        else:
            r = 5.0  # Distant, weak binding
        
        # [Phase 36-B] Clash-Based Orbital Destabilization (Original Pillars)
        all_branches = [p[1] for p in pillars if len(p) > 1]
        clash_target = ArbitrationNexus.CLASH_MAP.get(spouse_palace)
        if clash_target and clash_target in all_branches:
            r *= 3.0  # Orbital expansion due to clash
        
        # [Phase 36-B] 3b. Annual Impulse - Δr from Annual Pillar
        annual_impulse = 0.0
        if annual_pillar and len(annual_pillar) > 1:
            annual_branch = annual_pillar[1]
            annual_stem = annual_pillar[0]
            
            # Annual Clash with Spouse Palace -> Orbit expansion
            if ArbitrationNexus.CLASH_MAP.get(annual_branch) == spouse_palace:
                r *= 2.0  # Severe annual destabilization
                annual_impulse = 50.0
            # Annual Clash with Spouse Palace (reverse check)
            elif ArbitrationNexus.CLASH_MAP.get(spouse_palace) == annual_branch:
                r *= 2.0
                annual_impulse = 50.0
            
            # Annual Punishment (刑) with Spouse Palace -> Moderate destabilization
            penalty_info = BaziParticleNexus.PENALTY_GROUPS.get(annual_branch)
            if penalty_info and spouse_palace in penalty_info.get('components', []):
                r *= 1.5  # Moderate destabilization
                annual_impulse += 25.0
            
            # Annual Harm (害) with Spouse Palace -> Minor destabilization
            if BaziParticleNexus.HARM_MAPPING.get(annual_branch) == spouse_palace:
                r *= 1.3  # Minor destabilization
                annual_impulse += 15.0
            
            # Annual Join (Liu He) with Spouse Palace -> Orbit contraction
            for pair, _ in ArbitrationNexus.LIU_HE.items():
                if annual_branch in pair and spouse_palace in pair:
                    r *= 0.7  # Orbital tightening
                    annual_impulse = -30.0  # Negative = stabilizing
                    break
            
            # Annual San He (三合) with Spouse Palace -> Moderate stabilization
            for members, element in ArbitrationNexus.SAN_HE.items():
                if annual_branch in members and spouse_palace in members:
                    r *= 0.85  # Moderate tightening
                    annual_impulse -= 15.0
                    break
        
        # [Phase 36-B] 3c. Luck Pillar Effects on Orbital Distance
        if luck_pillar and len(luck_pillar) > 1:
            luck_branch = luck_pillar[1]
            
            # Luck Clash with Spouse Palace -> Chronic destabilization
            if ArbitrationNexus.CLASH_MAP.get(luck_branch) == spouse_palace:
                r *= 1.8  # Chronic destabilization (less severe than annual but persistent)
            elif ArbitrationNexus.CLASH_MAP.get(spouse_palace) == luck_branch:
                r *= 1.8
            
            # Luck Punishment with Spouse Palace
            penalty_info = BaziParticleNexus.PENALTY_GROUPS.get(luck_branch)
            if penalty_info and spouse_palace in penalty_info.get('components', []):
                r *= 1.4
        
        # [Phase 36-B] 3d. Apply Geo Factor to Gravitational Constant
        G_effective = self.G * geo_factor
            
        # 4. Calculate Binding Energy with all modifiers
        # E = -G_eff * M1 * M2 / (2 * r)
        binding_energy = -G_effective * m_dm * m_spouse / (2 * r)
        
        # 5. Calculate Perturbation Energy (from clashes, penalties)
        perturbation_energy = self._calculate_perturbation(pillars)
        
        # 6. Calculate Orbital Stability
        # σ = |E_bind| / E_perturb
        orbital_stability = abs(binding_energy) / max(perturbation_energy, 0.1)
        
        # 7. Calculate Phase Coherence
        # Based on phase difference between DM and Spouse Star waves
        dm_phase = waves.get(self.dm_element).phase if waves.get(self.dm_element) else 0.0
        spouse_phase = waves.get(self.spouse_star_element).phase if waves.get(self.spouse_star_element) else 0.0
        delta_phi = abs(dm_phase - spouse_phase)
        phase_coherence = np.cos(delta_phi / 2) ** 2
        
        # 8. Calculate Peach Blossom Amplitude
        peach_amplitude = self._calculate_peach_blossom(pillars)
        
        # 9. Determine Relationship State (deterministic)
        state = self._determine_state(r, orbital_stability, phase_coherence)
        
        # 10. [Phase 37] Calculate State Confidence via Monte Carlo Sampling
        state_probs, confidence = self._calculate_state_confidence(
            r, orbital_stability, phase_coherence, 
            r_sigma=0.15 * r, sigma_sigma=0.1 * orbital_stability, eta_sigma=0.1
        )
        
        return {
            "Binding_Energy": round(binding_energy, 2),
            "Orbital_Stability": round(orbital_stability, 2),
            "Phase_Coherence": round(phase_coherence, 4),
            "Peach_Blossom_Amplitude": round(peach_amplitude, 2),
            "State": state,
            "State_Confidence": round(confidence, 2),  # [Phase 37]
            "State_Probabilities": state_probs,  # [Phase 37]
            "Metrics": {
                "DM_Mass": round(m_dm, 2),
                "Spouse_Mass": round(m_spouse, 2),
                "Orbital_Distance": round(r, 2),
                "Perturbation_Energy": round(perturbation_energy, 2),
                "Spouse_Star": self.spouse_star_element,
                "Spouse_Palace": spouse_palace,
                "Spouse_Palace_Element": spouse_palace_element,
                # [Phase 36-B] Dynamic Modifiers
                "Luck_Modifier": round(luck_modifier, 2),
                "Annual_Impulse": round(annual_impulse, 2),
                "Geo_Factor": geo_factor,
                "G_Effective": round(G_effective, 3)
            }
        }
    
    def _determine_state(self, r: float, orbital_stability: float, phase_coherence: float) -> str:
        """
        [Phase 37] Deterministic state determination based on r, σ, and η.
        Extracted from analyze_relationship for reuse in Monte Carlo sampling.
        """
        # Low coherence (η < 0.1) indicates quantum decoherence
        if phase_coherence < 0.1:
            if orbital_stability > 1.0:
                return "PERTURBED"
            else:
                return "UNBOUND"
        # Orbital Distance Override - large r means weak binding
        elif r >= 6.0:
            return "UNBOUND"
        elif r >= 4.0:
            return "PERTURBED"
        elif r >= 2.5:
            if orbital_stability > 1.5:
                return "BOUND"
            else:
                return "PERTURBED"
        elif orbital_stability > 2.0 and phase_coherence > 0.7:
            return "ENTANGLED"
        elif orbital_stability > 1.0:
            return "BOUND"
        elif orbital_stability > 0.5:
            return "PERTURBED"
        else:
            return "UNBOUND"
    
    def _calculate_state_confidence(self, r: float, sigma: float, eta: float,
                                     r_sigma: float = 0.3, sigma_sigma: float = 0.5, 
                                     eta_sigma: float = 0.1, n_samples: int = 100) -> tuple:
        """
        [Phase 37] Monte Carlo sampling for state probability distribution.
        
        Args:
            r: Mean orbital distance
            sigma: Mean orbital stability  
            eta: Mean phase coherence
            r_sigma: Standard deviation for r sampling
            sigma_sigma: Standard deviation for sigma sampling
            eta_sigma: Standard deviation for eta sampling
            n_samples: Number of Monte Carlo samples
            
        Returns:
            (state_probs: dict, confidence: float)
        """
        state_counts = {"ENTANGLED": 0, "BOUND": 0, "PERTURBED": 0, "UNBOUND": 0}
        
        for _ in range(n_samples):
            # Add quantum fluctuations (Gaussian noise)
            r_sample = max(0.1, r + np.random.normal(0, r_sigma))
            sigma_sample = max(0.1, sigma + np.random.normal(0, sigma_sigma))
            eta_sample = np.clip(eta + np.random.normal(0, eta_sigma), 0, 1)
            
            # Determine state for this sample
            sampled_state = self._determine_state(r_sample, sigma_sample, eta_sample)
            state_counts[sampled_state] += 1
        
        # Calculate probabilities
        state_probs = {k: round(v / n_samples, 2) for k, v in state_counts.items()}
        
        # Get deterministic state's probability as confidence
        deterministic_state = self._determine_state(r, sigma, eta)
        confidence = state_probs.get(deterministic_state, 0.0)
        
        return state_probs, confidence
    
    def _elements_compatible(self, elem1: str, elem2: str) -> bool:
        """Check if two elements are generatively related."""
        if not elem1 or not elem2:
            return False
        return PhysicsConstants.GENERATION.get(elem1) == elem2 or \
               PhysicsConstants.GENERATION.get(elem2) == elem1
    
    def _calculate_perturbation(self, pillars: list) -> float:
        """
        Calculates perturbation energy from clashes and penalties affecting Day Branch.
        """
        if len(pillars) < 3:
            return 0.0
            
        day_branch = pillars[2][1] if len(pillars[2]) > 1 else ""
        all_branches = [p[1] for p in pillars if len(p) > 1]
        
        perturbation = 0.0
        
        # Check for Clash (冲)
        clash_target = ArbitrationNexus.CLASH_MAP.get(day_branch)
        if clash_target and clash_target in all_branches:
            perturbation += 50.0  # Major perturbation
        
        # Check for Penalty (刑)
        penalty_group = BaziParticleNexus.PENALTY_GROUPS.get(day_branch)
        if penalty_group:
            matches = sum(1 for b in penalty_group['components'] if b in all_branches)
            if matches >= 1:
                perturbation += 30.0 * matches  # Accumulated penalty stress
        
        # Check for Harm (害)
        harm_target = BaziParticleNexus.HARM_MAPPING.get(day_branch)
        if harm_target and harm_target in all_branches:
            perturbation += 20.0  # Phase jitter
        
        return perturbation
    
    def _calculate_peach_blossom(self, pillars: list) -> float:
        """
        Calculates Peach Blossom wave amplitude based on Year/Day Branch.
        """
        if len(pillars) < 3:
            return 0.0
            
        year_branch = pillars[0][1] if len(pillars[0]) > 1 else ""
        day_branch = pillars[2][1] if len(pillars[2]) > 1 else ""
        all_branches = set(p[1] for p in pillars if len(p) > 1)
        
        amplitude = 0.0
        
        # Find Peach Blossom based on Year Branch
        for triad, peach in self.PEACH_BLOSSOM_MAP.items():
            if year_branch in triad:
                if peach in all_branches:
                    amplitude += 30.0  # Peach Blossom present
                break
        
        # Find Peach Blossom based on Day Branch
        for triad, peach in self.PEACH_BLOSSOM_MAP.items():
            if day_branch in triad:
                if peach in all_branches:
                    amplitude += 20.0  # Day-based Peach Blossom
                break
        
        return amplitude
