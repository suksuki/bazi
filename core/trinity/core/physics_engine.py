"""
Quantum Trinity: Physics Engine (V1.0)
========================================
Unified physical definitions and interaction logic.
Consolidates ParticleDefinitions, GeometricInteraction, and physical formulas.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from .math_engine import ProbValue, expit

class ParticleDefinitions:
    """
    Physical Base and Particle Phases.
    """
    SPIN = {"Yang": +1, "Yin": -1}
    
    ELEMENT_PHASES = {
        "Wood": 0.0,
        "Fire": 1.2566,  # 2π/5
        "Earth": 2.5133, # 4π/5
        "Metal": 3.7699, # 6π/5
        "Water": 5.0265  # 8π/5
    }
    
    GENERATION_CYCLE = {
        "Wood": "Fire", "Fire": "Earth", "Earth": "Metal", "Metal": "Water", "Water": "Wood"
    }
    
    CONTROL_CYCLE = {
        "Wood": "Earth", "Earth": "Water", "Water": "Fire", "Fire": "Metal", "Metal": "Wood"
    }
    
    STEM_WAVEFORMS = {
        "甲": {"element": "Wood", "polarity": "Yang", "hetu": 1},
        "乙": {"element": "Wood", "polarity": "Yin", "hetu": 2},
        "丙": {"element": "Fire", "polarity": "Yang", "hetu": 3},
        "丁": {"element": "Fire", "polarity": "Yin", "hetu": 4},
        "戊": {"element": "Earth", "polarity": "Yang", "hetu": 5},
        "己": {"element": "Earth", "polarity": "Yin", "hetu": 6},
        "庚": {"element": "Metal", "polarity": "Yang", "hetu": 7},
        "辛": {"element": "Metal", "polarity": "Yin", "hetu": 8},
        "壬": {"element": "Water", "polarity": "Yang", "hetu": 9},
        "癸": {"element": "Water", "polarity": "Yin", "hetu": 10}
    }
    
    BRANCH_ENVIRONMENTS = {
        "子": {"element": "Water", "angle": 0},
        "丑": {"element": "Earth", "angle": 30},
        "寅": {"element": "Wood", "angle": 60},
        "卯": {"element": "Wood", "angle": 90},
        "辰": {"element": "Earth", "angle": 120},
        "巳": {"element": "Fire", "angle": 150},
        "午": {"element": "Fire", "angle": 180},
        "未": {"element": "Earth", "angle": 210},
        "申": {"element": "Metal", "angle": 240},
        "酉": {"element": "Metal", "angle": 270},
        "戌": {"element": "Earth", "angle": 300},
        "亥": {"element": "Water", "angle": 330}
    }
    
    # === Genesis Hidden Stems Map (V24.0 Source of Truth) ===
    # Format: Branch -> [(Stem, Weight)]
    GENESIS_HIDDEN_MAP = {
        '子': [('癸', 10)],                                      # Zi: Gui (Pure)
        '丑': [('己', 10), ('癸', 7), ('辛', 3)],                 # Chou: Ji, Gui, Xin
        '寅': [('甲', 10), ('丙', 7), ('戊', 3)],                 # Yin: Jia, Bing, Wu
        '卯': [('乙', 10)],                                      # Mao: Yi (Pure)
        '辰': [('戊', 10), ('乙', 7), ('癸', 3)],                 # Chen: Wu, Yi, Gui
        '巳': [('丙', 10), ('戊', 7), ('庚', 3)],                 # Si: Bing, Wu, Geng
        '午': [('丁', 10), ('己', 7)],                           # Wu: Ding, Ji
        '未': [('己', 10), ('丁', 7), ('乙', 3)],                 # Wei: Ji, Ding, Yi
        '申': [('庚', 10), ('壬', 7), ('戊', 3)],                 # Shen: Geng, Ren, Wu
        '酉': [('辛', 10)],                                      # You: Xin (Pure)
        '戌': [('戊', 10), ('辛', 7), ('丁', 3)],                 # Xu: Wu, Xin, Ding
        '亥': [('壬', 10), ('甲', 7)]                            # Hai: Ren, Jia
    }
    
    # Weights and Constants
    PILLAR_WEIGHTS = {'year': 0.5, 'month': 2.0, 'day': 1.0, 'hour': 0.8}
    BASE_SCORE = 1.0
    ROOT_BONUS = 1.2
    SAME_PILLAR_BONUS = 1.5
    
    # V14.0 Non-linear Physics Constants
    PHYSICS_CONSTANTS = {
        "inverse_control_threshold": 1.5, # Ratio at which control reverses
        "saturation_limit": 100.0,
        "excitation_gate": 0.5,
        "media_attenuation_base": 0.1,    # α in medium
        "phase_transition_width": 4.0     # Landau width
    }
    
    # Seasonal state energy field (Wang, Xiang, Xiu, Qiu, Si)
    # Maps to wave gain/attenuation operators
    SEASONAL_STATE_POTENTIAL = {
        "Wang": 2.2,   # Prosperous (Non-linear peak)
        "Xiang": 1.6,  # Assisting
        "Xiu": 1.0,    # Retiring (Unitary)
        "Qiu": 0.5,    # Trapped
        "Si": 0.15     # Dead (Phase noise floor)
    }

class PhysicsEngine:
    """
    Unified Physical Formulas and Interaction Logic.
    """
    @staticmethod
    def get_seasonal_state(element: str, month_branch: str) -> str:
        """
        Calculates the standard 5-state seasonal strength (Wang, Xiang, Xiu, Qiu, Si).
        Based on the Element vs Month Branch Element relationship.
        """
        month_env = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(month_branch)
        if not month_env: return "Xiu"
        
        m_e = month_env['element']
        
        # 1. Same: Wang
        if element == m_e: return "Wang"
        
        # 2. Month generates Element: Xiang
        if ParticleDefinitions.GENERATION_CYCLE.get(m_e) == element: return "Xiang"
        
        # 3. Element generates Month: Xiu
        if ParticleDefinitions.GENERATION_CYCLE.get(element) == m_e: return "Xiu"
        
        # 4. Element controls Month: Qiu
        if ParticleDefinitions.CONTROL_CYCLE.get(element) == m_e: return "Qiu"
        
        # 5. Month controls Element: Si
        return "Si"

    @staticmethod
    def get_state_potential(element: str, month_branch: str) -> float:
        """
        Calculates the Medium Field Potential (G) for a specific element.
        G(e, m) = SEASONAL_STATE_POTENTIAL[state] * Sigmoid(Energy_Flux)
        """
        state = PhysicsEngine.get_seasonal_state(element, month_branch)
        base_pot = ParticleDefinitions.SEASONAL_STATE_POTENTIAL.get(state, 1.0)
        return float(base_pot)

    @staticmethod
    def calculate_control_damage(attacker_e: float, defender_e: float, 
                                 attacker_state: str = "Xiu", 
                                 defender_state: str = "Xiu",
                                 base_impact: float = 0.8) -> float:
        """
        Non-linear control damage. 
        In Wang/Xiang states, defender has exponential immunity.
        In Qiu/Si states, damage conduction is amplified.
        """
        # Map states to immunity/conduction factors
        pot_map = ParticleDefinitions.SEASONAL_STATE_POTENTIAL
        att_pot = pot_map.get(attacker_state, 1.0)
        def_pot = pot_map.get(defender_state, 1.0)
        
        # Immunity Factor: If defender is Wang/Xiang, damage is resisted
        immunity = np.exp(-(def_pot - 1.0)) if def_pot > 1.0 else 1.0
        
        # Conduction Factor: If defender is Qiu/Si, damage is amplified
        conduction = 1.0 + (1.0 - def_pot) * 2.0 if def_pot < 1.0 else 1.0
        
        if attacker_e <= 0 or defender_e <= 0: return 0.0
        
        # Relative intensity with immunity/conduction
        effective_diff = (attacker_e * att_pot) - (defender_e * def_pot)
        activation = expit(effective_diff / 5.0)
        
        damage = defender_e * base_impact * activation * immunity * conduction
        return min(damage, defender_e * 0.95) # Never exceed total energy

    @staticmethod
    def calculate_generation(mother_e: float, efficiency: float, threshold: float = 10.0) -> float:
        effective = mother_e - threshold
        return max(0.0, effective * efficiency)

    @staticmethod
    def calculate_interaction(char1: str, char2: str, params: Dict[str, Any]) -> Optional[Dict]:
        """Identify geometric interaction (Chong, SanHe, etc.)"""
        b1 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(char1)
        b2 = ParticleDefinitions.BRANCH_ENVIRONMENTS.get(char2)
        if not b1 or not b2: return None
        
        diff = abs(b1['angle'] - b2['angle'])
        if diff > 180: diff = 360 - diff
        
        tol = params.get('angle_tolerance', 5.0)
        
        if abs(diff - 180) < tol: return {'type': 'Chong', 'strength': params.get('chong_power', 0.8)}
        if abs(diff - 120) < tol: return {'type': 'SanHe', 'strength': params.get('sanhe_power', 1.5)}
        if abs(diff - 60) < tol: return {'type': 'LiuHe', 'strength': params.get('liuhe_power', 1.2)}
        if abs(diff - 90) < tol: return {'type': 'Xing', 'strength': params.get('xing_power', 0.3)}
        
        return None

    @staticmethod
    def quantum_tunneling(barrier_h: float, particle_e: float, barrier_w: float = 1.0) -> float:
        if particle_e >= barrier_h: return 1.0
        deficit = barrier_h - particle_e
        return np.exp(-2.0 * np.sqrt(max(0, deficit)) * barrier_w)
