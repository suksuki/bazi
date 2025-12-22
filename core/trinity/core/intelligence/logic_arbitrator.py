
"""
Quantum Trinity V2.0: Logic Arbitrator
======================================
High-precision Bazi rule matching and geometric interaction arbitration.
"""

from typing import List, Dict, Optional, Any, Set
import numpy as np
from ..nexus.definitions import BaziParticleNexus, ArbitrationNexus, PhysicsConstants
from ..physics.wave_laws import WaveState, WaveLaws

class LogicArbitrator:
    """The 'Brain' that identifies structural locks and geometric overlaps."""

    @staticmethod
    def match_interactions(pillars: List[str], day_master: str) -> List[Dict[str, Any]]:
        """
        Identify active combinations, clashes, and structural locks.
        """
        stems = [p[0] for p in pillars if p]
        branches = [p[1] for p in pillars if len(p) > 1]
        branch_set = set(branches)
        interactions = []

        # Find DM relations
        dm_elem, _, _ = BaziParticleNexus.STEMS.get(day_master, ("Earth", "", 0))
        output_elem = PhysicsConstants.GENERATION[dm_elem]
        control_elem = None
        for k, v in PhysicsConstants.CONTROL.items():
            if v == dm_elem: control_elem = k
            
        # Detect Oppose (Phase 28)
        # Check if output and control elements both have representatives in stems or pillars
        has_output = any(BaziParticleNexus.STEMS[s][0] == output_elem for s in stems if s in BaziParticleNexus.STEMS)
        has_control = any(BaziParticleNexus.STEMS[s][0] == control_elem for s in stems if s in BaziParticleNexus.STEMS)
        
        if has_output and has_control:
             # Estimated energy check: if output heavily outweighs control, don't trigger oppose-annihilation
             # Since we don't have the waves here, we'll let it pass for now but 
             # the ResonanceEngine will see the low sync isn't as destructive if amplitudes are mismatched.
             # Actually, let's keep it but ensure the q-value is low.
             dyn = ArbitrationNexus.DYNAMICS["OPPOSE"]
             interactions.append({
                 "id": "PH28_01", "type": "OPPOSE", "name": f"Shang Guan vs Zheng Guan ({output_elem}-{control_elem})",
                 "target_element": control_elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                 "priority": ArbitrationNexus.PRIORITY["OPPOSE"], "branches": set()
             })

        # 1. San Hui (Three Seasonal Meeting) - Priority 1
        for trio, elem in ArbitrationNexus.SAN_HUI.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HUI"]
                interactions.append({
                    "id": "A1", "type": "SAN_HUI", "name": f"Seasonal Meeting ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HUI"], "branches": set(trio)
                })

        # 2. San He (Three Harmony) - Priority 2
        for trio, elem in ArbitrationNexus.SAN_HE.items():
            if trio.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["SAN_HE"]
                interactions.append({
                    "id": "A2", "type": "SAN_HE", "name": f"Three Harmony ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["SAN_HE"], "branches": set(trio)
                })

        # 3. Liu He (Six Combinations) - Priority 3
        for pair, elem in ArbitrationNexus.LIU_HE.items():
            if pair.issubset(branch_set):
                dyn = ArbitrationNexus.DYNAMICS["LIU_HE"]
                interactions.append({
                    "id": "A3", "type": "LIU_HE", "name": f"Six Combination ({elem})",
                    "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                    "priority": ArbitrationNexus.PRIORITY["LIU_HE"], "branches": set(pair)
                })

        # 4. Clashes (Chong) - Priority 4
        chong_map = ArbitrationNexus.CLASH_MAP
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                b1, b2 = branches[i], branches[j]
                if chong_map.get(b1) == b2:
                    dyn = ArbitrationNexus.DYNAMICS["CLASH"]
                    elem1 = BaziParticleNexus.BRANCHES[b1][0]
                    interactions.append({
                        "id": "B1", "type": "CLASH", "name": f"Clash ({b1}-{b2})",
                        "target_element": elem1, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                        "priority": ArbitrationNexus.PRIORITY["CLASH"], "branches": {b1, b2}
                    })

        # 5. Resonance (Identical Branches) - Priority 5
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if branches[i] == branches[j]:
                    b = branches[i]
                    elem = BaziParticleNexus.BRANCHES[b][0]
                    dyn = ArbitrationNexus.DYNAMICS["RESONANCE"]
                    interactions.append({
                        "id": "R1", "type": "RESONANCE", "name": f"Resonance ({b})",
                        "target_element": elem, "q": dyn['q'], "phi": dyn['phi'], "lock": dyn['lock'],
                        "priority": ArbitrationNexus.PRIORITY["RESONANCE"], "branches": {b}
                    })

        # 6. Arbitration: Sort and dedup
        # In V2, we keep all but tag priority
        interactions.sort(key=lambda x: x['priority'])
        
        return interactions

    @staticmethod
    def initialize_field(pillars: List[str], day_master: str) -> Dict[str, WaveState]:
        """
        Transforms Bazi characters into their initial physics WaveStates.
        """
        waves = {e: WaveState(1e-6, PhysicsConstants.ELEMENT_PHASES[e]) for e in PhysicsConstants.ELEMENT_PHASES}
        
        pillar_names = ['year', 'month', 'day', 'hour', 'luck', 'annual']
        
        # Phase 28: Clash Damping logic
        branches = [p[1] for p in pillars if len(p) > 1]
        clash_map = ArbitrationNexus.CLASH_MAP
        clashed_indices = set()
        for i in range(len(branches)):
            for j in range(i + 1, len(branches)):
                if clash_map.get(branches[i]) == branches[j]:
                    clashed_indices.add(i)
                    clashed_indices.add(j)

        for idx, p in enumerate(pillars):
            if not p: continue
            name = pillar_names[idx] if idx < len(pillar_names) else 'unknown'
            w_prio = PhysicsConstants.PILLAR_WEIGHTS.get(name, 1.0)
            
            # Stem Contribution
            s_char = p[0]
            if s_char in BaziParticleNexus.STEMS:
                elem, _, _ = BaziParticleNexus.STEMS[s_char]
                amp = PhysicsConstants.BASE_SCORE * w_prio
                # Damping if pillar is in a clash
                if idx in clashed_indices: amp *= 0.5
                source = WaveState(amp, PhysicsConstants.ELEMENT_PHASES[elem])
                waves[elem] = WaveState.from_complex(waves[elem].to_complex() + source.to_complex())
            
            # Branch Contribution
            b_char = p[1] if len(p) > 1 else ''
            if b_char in BaziParticleNexus.BRANCHES:
                _, _, hidden = BaziParticleNexus.BRANCHES[b_char]
                base_b_amp = PhysicsConstants.BASE_SCORE * w_prio * 1.5 
                if idx in clashed_indices: base_b_amp *= 0.3 # Heavier damping for branches
                
                for s_hidden, weight in hidden:
                    h_elem, _, _ = BaziParticleNexus.STEMS.get(s_hidden, ("Earth", "", 0))
                    h_amp = base_b_amp * (weight / 10.0)
                    h_source = WaveState(h_amp, PhysicsConstants.ELEMENT_PHASES[h_elem])
                    waves[h_elem] = WaveState.from_complex(waves[h_elem].to_complex() + h_source.to_complex())
                    
        return {e: WaveLaws.apply_saturation(w) for e, w in waves.items()}
