
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from .wave_mechanics import WaveState
from .physics_engine import ParticleDefinitions
from .entanglement_engine import EntanglementEngine

class StructuralReorganizer:
    """
    Phase 27: Structural Reorganization (Strong Vibration Suppression).
    Implements the 'Greedy for Combine, Forget the Clash' (贪合忘冲) priority logic.
    Provides automated reorganization recommendations to stabilize violent systems.
    """

    @staticmethod
    def find_suppression_particles(
        bazi: List[str],
        conflicts: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Scans for particles that can lock conflicting nodes and suppress clashes.
        """
        solutions = []
        
        # Branch-wise combine rules
        SIX_HARMONY = {
            "子": "丑", "丑": "子", "寅": "亥", "亥": "寅",
            "卯": "戌", "戌": "卯", "辰": "酉", "酉": "辰",
            "巳": "申", "申": "巳", "午": "未", "未": "午"
        }

        # Triple Harmony (San-He) - Needs two partners to complete
        TRIPLE_HARMONY = {
            "申": ["子", "辰"], "子": ["申", "辰"], "辰": ["申", "子"], # Water
            "亥": ["卯", "未"], "卯": ["亥", "未"], "未": ["亥", "卯"], # Wood
            "寅": ["午", "戌"], "午": ["寅", "戌"], "戌": ["寅", "午"], # Fire
            "巳": ["酉", "丑"], "酉": ["巳", "丑"], "丑": ["巳", "酉"]  # Metal
        }
        
        # Directional Meeting (San-Hui)
        DIRECTIONAL = {
            "亥": ["子", "丑"], "子": ["亥", "丑"], "丑": ["亥", "子"], # North/Water
            "寅": ["卯", "辰"], "卯": ["寅", "辰"], "辰": ["寅", "卯"], # East/Wood
            "巳": ["午", "未"], "午": ["巳", "未"], "未": ["巳", "午"], # South/Fire
            "申": ["酉", "戌"], "酉": ["申", "戌"], "戌": ["申", "酉"]  # West/Metal
        }
        
        # Conflict format: {"nodes": (i, j), "impact": impact}
        for conflict in conflicts:
            idx1, idx2 = conflict['nodes']
            p1 = bazi[idx1][1] if len(bazi[idx1]) > 1 else ''
            p2 = bazi[idx2][1] if len(bazi[idx2]) > 1 else ''
            
            # 1. Check Six-Harmony (Priority 1: Direct Lock)
            for branch in [p1, p2]:
                c = SIX_HARMONY.get(branch)
                if c:
                    solutions.append({
                        "target_node": branch,
                        "remedy_branch": c,
                        "type": "Six-Harmony Lock (六合锁定)",
                        "priority": conflict['impact'] * 1.5
                    })
            
            # 2. Check Triple Harmony (Priority 2: Field Resonance)
            for branch in [p1, p2]:
                partners = TRIPLE_HARMONY.get(branch)
                if partners:
                    for p in partners:
                        solutions.append({
                            "target_node": branch,
                            "remedy_branch": p,
                            "type": "Triple-Harmony Buffer (三合导流)",
                            "priority": conflict['impact'] * 1.2
                        })
            
            # 3. Check Directional (Priority 3: Area Damping)
            for branch in [p1, p2]:
                partners = DIRECTIONAL.get(branch)
                if partners:
                    for p in partners:
                        solutions.append({
                            "target_node": branch,
                            "remedy_branch": p,
                            "type": "Directional Meeting Damping (三会抑制)",
                            "priority": conflict['impact'] * 1.0
                        })
                
        # Sort by impact priority
        solutions.sort(key=lambda x: x['priority'], reverse=True)
        return solutions

    @staticmethod
    def simulate_suppression(
        original_breakdown: Dict[str, Any],
        locked_nodes: List[int]
    ) -> Dict[str, Any]:
        """
        Recalculates the breakdown status assuming certain nodes are 'LOCKED'.
        """
        # In reality, the QuantumEngine would re-run with 'Locked' logic.
        # Here we simulate the damping.
        
        damping_factor = 0.15 # 85% reduction in clash energy
        
        new_thermal = original_breakdown['thermal_release']
        for _ in locked_nodes:
            new_thermal *= damping_factor
            
        new_fragmentation = new_thermal / 25.0 # matches threshold in quantum_engine
        survived = new_thermal < 25.0
        
        return {
            "status": "REORGANIZED" if survived else "CRITICAL",
            "thermal_release": new_thermal,
            "fragmentation_index": new_fragmentation,
            "survived": survived,
            "suppression_efficiency": (original_breakdown['thermal_release'] - new_thermal) / max(original_breakdown['thermal_release'], 1e-6)
        }
