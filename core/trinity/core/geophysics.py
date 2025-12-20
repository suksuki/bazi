
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional

@dataclass
class GeoFactor:
    name: str # City Name or Region
    latitude: float
    longitude: float # Not used for element boost yet, maybe for Time Zone
    description: str

@dataclass
class RemediationResult:
    success: bool
    location: str
    original_energy: float
    boosted_energy: float
    k_geo: float
    description: str

class GeoPhysics:
    """
    Phase 19: Quantum Remediation Engine.
    Calculates K_geo spatial modifiers to boost elemental energy.
    """
    
    # Elemental Affinities by Latitude/Direction
    # North (Water), South (Fire), East (Wood), West (Metal), Center/all (Earth)
    # Simplified Logic:
    # Latitude > 30 (North) -> Water ++
    # Latitude < 0 (South/Equator) -> Fire ++
    # This is a rigorous simplification for the sandbox.
    
    # Let's use a "Directional Vector" model relative to a center point (e.g. Kaifeng/Central China ~34N, 114E)
    # But user asked for "Global Cities". 
    # Let's implement a standard "Five Element Direction" mapping.
    
    # 0 = Center. North = +Y, South = -Y, East = +X, West = -X.
    # We will map (lat, lon) to Elemental Boosts.
    
    @staticmethod
    def calculate_k_geo(element: str, lat: float) -> float:
        """
        Calculates the Geophysics Coefficient K_geo.
        Base = 1.0. Max Boost = 1.5 (+50%).
        """
        element = element.lower()
        k = 1.0
        
        # Fire: Boosted by Heat (Low Latitude / Equator / South)
        # Assume "South" means moving towards Equator or Southern Hemisphere?
        # In Feng Shui, "South" is purely direction. 
        # Let's map Latitude to "Fire-Water Axis".
        
        # 45N = Cold (Water). 0N = Hot (Fire). -45S = Cold (Water)? Or South implies -Y direction?
        # Let's interpret "South" as "Hot/Fire". 
        # High Lat (abs) -> Water. Low Lat -> Fire.
        
        abs_lat = abs(lat)
        
        if element == 'fire':
            # Closer to Equator (0) = Hotter
            # Boost = 1.0 + (1 - lat/90) * 0.5?
            # Let's align with user's "South = Fire" for Northern Hemisphere context.
            # 20N (Hainan) is Fire. 50N (Heilongjiang) is Water.
            if abs_lat < 25.0: # Tropics
                k = 1.4 # High Fire
            elif abs_lat < 35.0: # Subtropics
                k = 1.2
            else: # Temperate/Polar
                k = 0.9 # Weak Fire
                
        elif element == 'water':
            # Colder = Water
            if abs_lat > 45.0:
                k = 1.4
            elif abs_lat > 35.0:
                k = 1.2
            else:
                k = 0.8
                
        elif element == 'wood':
            # East? Or Rainforests (Low Lat)?
            # Let's stick to Direction if possible, but lat is easier.
            # Let's assume Wood thrives in "Warm+Wet" (Subtropics).
            if 15.0 < abs_lat < 35.0:
                k = 1.3
            else:
                k = 1.0
                
        elif element == 'metal':
            # West. Hard to map to Lat alone.
            # Let's use a default for now unless we add Longitude.
            k = 1.0
            
        elif element == 'earth':
            # Center. 
            k = 1.1 # Earth is everywhere
            
        return k

    @staticmethod
    def find_haven(
        target_element: str, 
        current_energy: float, 
        required_energy: float
    ) -> List[RemediationResult]:
        """
        Search for locations that boost current_energy > required_energy.
        """
        # Virtual Database of Cities
        cities = [
            GeoFactor("Hainan (South)", 19.0, 109.0, "Tropical Fire Haven"),
            GeoFactor("Kaifeng (Center)", 34.0, 114.0, "Central Earth"),
            GeoFactor("Beijing (North)", 40.0, 116.0, "Northern Water"),
            GeoFactor("Siberia (Extreme North)", 60.0, 100.0, "Arctic Water Core"),
            GeoFactor("Singapore (Equator)", 1.0, 103.0, "Pure Yang Fire"),
            GeoFactor("Changsha (South-Central)", 28.0, 112.0, "Fire/Wood Hub")
        ]
        
        results = []
        for city in cities:
            k = GeoPhysics.calculate_k_geo(target_element, city.latitude)
            boosted = current_energy * k
            
            if boosted > required_energy:
                desc = f"✅ HAVEN FOUND: {city.name}. K_geo={k:.2f}. Energy {current_energy:.2f} -> {boosted:.2f} (> {required_energy:.2f})"
                results.append(RemediationResult(
                    success=True, location=city.name, 
                    original_energy=current_energy, boosted_energy=boosted, 
                    k_geo=k, description=desc
                ))
            else:
                # Keep tracking close calls?
                pass
                
        return sorted(results, key=lambda x: x.boosted_energy, reverse=True)

    @staticmethod
    def remediate_extreme_case(case_id: str, breakdown: Dict) -> List[RemediationResult]:
        """
        Specialized remediation for Phase 19 Extreme Batch cases.
        Strategies:
        1. Entropy Tax Reduction: Find a Haven that neutralizes the 'Missing Element' or supports the 'Victim'.
        2. Case 010 (Fire Weak, Water Strong): Need Heavy Fire (South).
        3. Case 003 (Jealousy - 4 Ding vs 1 Ren): Need Wood to bridge or Metal to arbitrate?
           - 4 Ding (Fire) vs 1 Ren (Water). Fire > Water. Water evaporates.
           - Needs Metal (Source of Water) to support Ren? Or Earth to exhaust Fire?
           - Jealousy Damping -> Need to reduce simple Competition.
        """
        results = []
        
        if case_id == 'CASE_FUSION_EXT_010_PHASE_SHIFT_COLLAPSE':
            # Analysis: Fire (Year) is crushed by Water (Month). Entropy Tax is high.
            # Strategy: Boost Fire to restore balance.
            current_e = breakdown.get('Year (Wu-Gui)', 4.5)
            # Find Haven for Fire
            res = GeoPhysics.find_haven("fire", current_e, 7.0) # Aim for > 7.0
            for r in res:
                r.description = f"🔥 Case 010 CURE: Boost Wu-Gui to withstand Water Field. {r.description}"
            results.extend(res)
            
        elif case_id == 'CASE_FUSION_EXT_003_N4_CHAOS':
            # Analysis: 4 Ding (Fire) competing for 1 Ren (Water).
            # If we boost Water (Ren), it might withstand the competition better?
            # Or assume the issue is "Ren Evaporation".
            current_e = 5.0 # Mock Ren energy
            res = GeoPhysics.find_haven("water", current_e, 8.0)
            for r in res:
                r.description = f"💧 Case 003 CURE: Strengthen Ren (Water) to handle 4 rivals. {r.description}"
            results.extend(res)
            
        return sorted(results, key=lambda x: x.boosted_energy, reverse=True)

    @staticmethod
    def auto_search_all_elements(
        current_energy: float, 
        required_energy: float
    ) -> List[RemediationResult]:
        """
        Exhaustive search across all elements.
        """
        all_results = []
        for elem in ['fire', 'water', 'wood', 'metal', 'earth']:
            havens = GeoPhysics.find_haven(elem, current_energy, required_energy)
            all_results.extend(havens)
        return sorted(all_results, key=lambda x: x.boosted_energy, reverse=True)

    @staticmethod
    def simulate_su_dongpo_rescue():
        """
        Attempt to rescue Su Dongpo (1079) via Migration.
        Dual Strategy Test:
        1. South (Fire Boost) -> Control Metal, Bridge Flow.
        2. North (Water Boost) -> Produce Wood, Strengthen Day Master.
        """
        print("--- Operation: RESURRECT SU DONGPO (1079) ---")
        
        current_energy = 5.1
        required_energy = 7.0 
        
        print(f"Current Vitality: {current_energy}")
        print(f"Required Threshold: {required_energy}")
        print("Initiating Global Exhaustion Search (All Elements)...")
        
        havens = GeoPhysics.auto_search_all_elements(current_energy, required_energy)
        
        if not havens:
            print("❌ No Haven Found. Doom is inevitable.")
        else:
            print(f"🔍 Found {len(havens)} Viable Spacetime Coordinates:")
            for h in havens:
                print(f"[{h.location}] Target: {h.description} -> Energy {h.boosted_energy:.2f} (K={h.k_geo})")
            
            best = havens[0]
            print(f"\n🚀 OPTIMAL STRATEGY: Migrate to {best.location}.")
            print(f"Legacy Result: {best.description}")

if __name__ == "__main__":
    GeoPhysics.simulate_su_dongpo_rescue()
