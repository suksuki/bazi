from typing import List, Dict, Any, Optional
from core.engine_v88 import EngineV88
from core.processors.geo import GeoProcessor
from core.processors.era import EraProcessor
from core.schemas.ui_protocol import AnalysisResponse

class EngineV90(EngineV88):
    """
    Antigravity V9.0 Engine (Heaven & Earth)
    
    Inherits V8.8 Core Physics.
    Adds:
    - Layer 0: Geographic Correction (GeoProcessor)
    - Layer 4: Era/Zeitgeist Correction (EraProcessor)
    """
    
    VERSION = "9.0.0-HeavenEarth"

    def __init__(self):
        super().__init__()
        # Initialize new processors
        self.geo = GeoProcessor()
        self.era = EraProcessor()
        # print(f"🚀 {self.VERSION} Loaded with Geo & Era Modules.")

    def analyze(self, bazi: List[str], day_master: str, 
                city: str = "Unknown", year: int = 2024,
                latitude: Optional[float] = None) -> AnalysisResponse:
        """
        V9.0 Analysis Entry Point.
        
        Args:
            bazi: 4 pillars
            day_master: DM char
            city: City name for Option C lookup
            year: Current year for Era calculation
            latitude: Optional latitude override for Option B
        """
        messages = [f"[{self.VERSION}] Starting analysis..."]
        
        # === 1. Calculate Base V8.8 Physics ===
        # We need to access the internal steps of V8.8 but inject modifiers.
        # Since V8.8.analyze() is a pipeline, we might need to be clever.
        # Option: Run parts of the pipeline manually.
        
        # Step 1: Base Physics (Layer 1) & Seasonal (Layer 2)
        # We can reuse the V8.8 processors directly.
        
        dm_element = self.physics._get_element_stem(day_master)
        context = {
            'bazi': bazi,
            'day_master': day_master,
            'dm_element': dm_element,
            'month_branch': bazi[1][1] if len(bazi) > 1 else ''
        }
        
        # Run Physics Layer
        physics_result = self.physics.process(context)
        raw_energy = physics_result['raw_energy']
        
        # === V9.0 Layer 0: Applying Geo Modifiers ===
        # Determine location input (City name or Lat)
        loc_input = latitude if latitude is not None else city
        geo_mods = self.geo.process(loc_input)
        
        if geo_mods:
            mod_desc = geo_mods.get('desc', 'GeoMod')
            messages.append(f"[Geo] Applying {mod_desc}")
            for elem, mult in geo_mods.items():
                if elem in raw_energy and isinstance(mult, (int, float)):
                    old_score = raw_energy[elem]
                    raw_energy[elem] *= mult
                    # messages.append(f"  - {elem}: {old_score:.1f} -> {raw_energy[elem]:.1f} (x{mult})")
        
        # === V9.0 Layer 4: Applying Era Modifiers ===
        era_res = self.era.process(year)
        if era_res:
            era_elem = era_res.get('era_element')
            era_mods = era_res.get('modifiers', {})
            desc = era_res.get('desc', '')
            messages.append(f"[Era] Period {era_res.get('period')} ({desc})")
            
            for elem, mult in era_mods.items():
                if elem in raw_energy:
                    raw_energy[elem] *= mult
                    
        # ... Continue with V8.8 Pipeline (Seasonal, Phase, Judge) ...
        # We need to re-inject the modified raw_energy into the pipeline flow
        
        # Seasonal
        seasonal_result = self.seasonal.process(context)
        
        # Combine Scores (Simplified logic from V8.8 analyze)
        # Recalculate base score from modified energy
        resource_element = None
        from core.processors.physics import GENERATION
        for mother, child in GENERATION.items():
            if child == dm_element:
                resource_element = mother
                break
        
        e_self = raw_energy.get(dm_element, 0)
        e_resource = raw_energy.get(resource_element, 0) if resource_element else 0
        base_score = e_self + e_resource
        
        # Add Seasonal Bonuses
        base_score += seasonal_result['in_command_bonus']
        base_score += seasonal_result['resource_month_bonus']
        
        # Phase Change
        # Note: We should pass the MODIFIED energy to PhaseProcessor if it uses it.
        # But PhaseProcessor currently uses context['month_branch'] mainly.
        # If we update PhaseProcessor later to check effective strength, we should pass `raw_energy`.
        # For now, let's inject raw_energy into context for future proofing.
        context['raw_energy_snapshot'] = raw_energy
        phase_result = self.phase_change.process(context)
        resource_efficiency = phase_result['resource_efficiency']
        
        # Judge
        judge_context = {
            'base_score': base_score,
            'in_command_bonus': seasonal_result['in_command_bonus'],
            'resource_month_bonus': seasonal_result['resource_month_bonus'],
            'resource_efficiency': resource_efficiency,
            'is_in_command': seasonal_result['is_in_command'],
            'is_resource_month': seasonal_result['is_resource_month']
        }
        judgment = self.judge.process(judge_context)
        
        messages.append(f"[Judge] Verdict: {judgment['verdict']} (Score: {judgment['final_score']:.1f})")

        return self._build_response(
            judgment=judgment,
            phase_result=phase_result,
            raw_energy=raw_energy,
            messages=messages
        )
