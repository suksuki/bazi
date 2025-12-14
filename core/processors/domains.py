"""
Antigravity V9.3 Domain Processor
==================================
Restores the "Lost Logic" of Ten Gods (Shishen) and Useful God (Yong Shen).

This processor interprets raw elemental energy into human life domains:
- Wealth (财运)
- Career (事业)
- Relationship (感情)

It applies critical corrections for:
- Body Strength (身强/身弱): Can you obtain the wealth?
- Ten Gods Interactions (十神生克): Is Wealth being robbed? Is Officer attacking you?
- Gender Differences (男女命): Wife vs Husband stars.
"""

import json
import os
from typing import Dict, Any
from core.processors.base import BaseProcessor
from core.processors.physics import GENERATION, CONTROL

class DomainProcessor(BaseProcessor):
    """
    Layer 4: Domain Translation
    
    Translates Elemental Physics -> Human Destinies.
    """
    
    @property
    def name(self) -> str:
        return "Domain Layer 4"
    
    def __init__(self):
        # Load Domain Rules
        self.rules = self._load_rules()
        
    def _load_rules(self) -> Dict:
        """Load domain coefficients and thresholds"""
        try:
            path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "domain_rules.json")
            if os.path.exists(path):
                with open(path, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
            
        # Fallback Defaults (Restored from Legacy V8.1)
        return {
            "weights": {
                "wealth_cai": 0.6,
                "wealth_output": 0.4,
                "career_officer": 0.8,
                "career_resource": 0.2,
                "rel_spouse": 0.35, # Base spouse star weight
                "rel_self": 0.20    # Self strength contribution
            },
            "penalties": {
                "wealth_burden": 1.0,   # 财多身弱
                "robbery": 1.2,         # 比劫夺财
                "officer_attack": 1.0,  # 七杀攻身
                "mutiny": 1.8           # 伤官见官
            },
            "thresholds": {
                "weak_self": 20.0,      # Legacy score < 20 is Weak
                "strong_self": 50.0,
                "heavy_wealth": 60.0,   # Raw energy > 60 is Heavy
                "heavy_officer": 50.0
            }
        }

    def process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate Domain Scores.
        
        Requires in context:
        - raw_energy: {wood: 10, ...}
        - dm_element: 'wood'
        - strength: {verdict: 'Strong'/'Weak', final_score: 50.0}
        - gender: 1 (Male) or 0 (Female)
        """
        raw_energy = context.get('raw_energy', {})
        dm_elem = context.get('dm_element', 'wood')
        strength_info = context.get('strength', {})
        verdict = strength_info.get('verdict', 'Weak')
        body_score = strength_info.get('raw_score', 0.0) # Use raw physics score for calculation
        
        if body_score <= 0: body_score = 1.0 # Prevent div by zero
        
        # 1. Map Ten Gods
        gods_strength = self._map_ten_gods(raw_energy, dm_elem)
        
        # 2. Calculate Domains
        wealth_result = self._calc_wealth(gods_strength, body_score, verdict)
        career_result = self._calc_career(gods_strength, body_score, verdict)
        rel_result = self._calc_relationship(gods_strength, body_score, verdict, context.get('gender', 1))
        
        return {
            'gods_strength': gods_strength,
            'wealth': wealth_result,
            'career': career_result,
            'relationship': rel_result
        }

    def _map_ten_gods(self, energy: Dict[str, float], dm_elem: str) -> Dict[str, float]:
        """Map 5 Elements to 5 Gods (Self, Output, Wealth, Officer, Resource)"""
        mapping = {}
        
        # Self (Bi Jian / Robinson)
        mapping['self'] = energy.get(dm_elem, 0)
        
        # Output (Shi Shang)
        output_elem = GENERATION.get(dm_elem)
        mapping['output'] = energy.get(output_elem, 0)
        
        # Wealth (Cai)
        wealth_elem = CONTROL.get(dm_elem)
        mapping['wealth'] = energy.get(wealth_elem, 0)
        
        # Officer (Guan Sha)
        # Find who controls DM
        officer_elem = None
        for k, v in CONTROL.items():
            if v == dm_elem:
                officer_elem = k
                break
        mapping['officer'] = energy.get(officer_elem, 0) if officer_elem else 0
        
        # Resource (Yin)
        # Find who generates DM
        resource_elem = None
        for k, v in GENERATION.items():
            if v == dm_elem: # GENERATION: wood->fire. if fire is DM, wood is resource
                resource_elem = k
                break
        mapping['resource'] = energy.get(resource_elem, 0) if resource_elem else 0
        
        return mapping

    def _calc_wealth(self, gods: Dict[str, float], body: float, verdict: str) -> Dict:
        """
        Genesis Wealth Logic: Capacity Model.
        """
        raw_wealth = gods['wealth']
        raw_output = gods['output'] # Output generates Wealth
        
        # 1. Total Wealth Potential (Source + Wealth itself)
        # Using 0.3/0.7 split
        potential = (raw_wealth * 0.7) + (raw_output * 0.3)
        
        # 2. Capacity Factor (Can you hold it?)
        # Standard Strong Body = 40.0 points (4 stems)
        capacity_ratio = body / 40.0 
        
        modifier = 1.0
        reason = "Normal"
        
        if capacity_ratio < 0.5: # Very Weak (<20)
            modifier = 0.4
            reason = "Wealth Burden (财多身弱)"
        elif capacity_ratio > 1.2: # Strong (>48)
            modifier = 1.3
            reason = "Strong Self Handles Wealth (身强任财)"
        else:
            # Balanced range
            modifier = 1.0
            
        final_score = potential * modifier
        return {'score': max(0.0, final_score), 'reason': reason}

    def _calc_career(self, gods: Dict[str, float], body: float, verdict: str) -> Dict:
        """
        Genesis Career Logic: Path Selection.
        """
        officer = gods['officer']
        output = gods['output']
        resource = gods['resource']
        
        # Path A: Bureaucracy (Officer/Resource)
        score_officer = officer + (resource * 0.3)
        
        # Path B: Entrepreneurship/Art (Output)
        score_output = output
        
        final_score = 0.0
        reason = "Normal"
        
        if score_officer >= score_output:
            # Officer Path Selected
            # Needs Strength to handle Pressure (Officer attacks Self)
            # Or Resource to flow (Officer -> Resource -> Self)
            
            if body < 20.0 and resource < 10.0:
                 # Weak, No Resource -> Pressure
                 final_score = score_officer * 0.4
                 reason = "Pressure Attack (七杀攻身)"
            elif body > 40.0:
                 # Strong -> Authority
                 final_score = score_officer * 1.3
                 reason = "In Command (身杀两停)"
            else:
                 final_score = score_officer
                 reason = "Officer Career (正官格)"
        else:
            # Output Path Selected (Talent)
            # Talent requires Body Strength too (Consumes Self)
            if body < 15.0:
                 final_score = score_output * 0.6
                 reason = "Exhausted by Talent (泄身太过)"
            else:
                 final_score = score_output * 1.2
                 reason = "Artistic/Tech Talent (食伤生财)"
                 
        return {'score': max(0.0, final_score), 'reason': reason}

    def _calc_relationship(self, gods: Dict[str, float], body: float, verdict: str, gender: int) -> Dict:
        """
        Calculate Love/Romance Score.
        Gender: 1=Male (Wealth is Wife), 0=Female (Officer is Husband)
        """
        w = self.rules['weights']
        
        is_male = (gender == 1)
        spouse_star = gods['wealth'] if is_male else gods['officer']
        
        # Base Score
        # Self strength matters for holding relationship
        base = (spouse_star * w['rel_spouse']) + (body * w['rel_self'])
        
        modifier = 1.0
        reason = "Normal"
        
        # Case 1: No Spouse Star
        if spouse_star < 5.0:
            reason = "Weak Spouse Star (缘分浅)"
            modifier = 0.5
            
        # Case 2: Male Robbery (比劫争财)
        # If Male, Strong Self (Robbers) attacks Wealth (Wife)
        if is_male and verdict == 'Strong' and gods['self'] > spouse_star * 2:
            reason = "Robbery Attacks Wife (克妻)"
            modifier = 0.6
            
        # Case 3: Female Mutiny (伤官克官)
        # If Female, Strong Output attacks Officer (Husband)
        if not is_male and gods['output'] > gods['officer'] * 1.5:
            reason = "Talent Hurts Marriage (克夫)"
            modifier = 0.6
            
        final_score = base * modifier
        return {'score': max(0, final_score), 'reason': reason}
