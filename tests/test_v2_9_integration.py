
import pytest
from core.quantum_engine import QuantumEngine

def test_flux_engine_integration_fallback():
    """
    Test Rule 14: Hybrid Computation.
    When pillar_energies are missing (all 0), QuantumEngine should invoke FluxEngine
    to calculate them, resulting in non-zero values for the particles.
    """
    # Create a mock case with a valid Bazi but missing pillar_energies in physics sources
    mock_case = {
        "id": 999,
        "bazi": ["甲辰", "丙寅", "戊子", "庚申"], # Wood/Fire/Earth/Metal combo
        "day_master": "戊",
        "wang_shuai": "身弱",
        "gender": "男",
        "physics_sources": {
            "self": {"day_root": 0},
            "pillar_energies": [0, 0, 0, 0, 0, 0, 0, 0] # Explicitly empty
        }
    }
    
    engine = QuantumEngine({})
    
    # Calculate
    # We use a mocked dynamic context to trigger the inner logic if needed, 
    # though FluxEngine runs regardless of dynamic context if pillar_energies are missing.
    result = engine.calculate_energy(mock_case, dynamic_context={"year": "甲辰", "luck": "癸卯"})
    
    # Check pillar_energies
    pe = result.get('pillar_energies', [])
    print(f"Calculated Flux Energies: {pe}")
    
    # Verify not all zeros
    # FluxEngine should produce non-zero amps for Stems/Branches present
    assert pe is not None
    assert len(pe) == 8, "Should return 8 pillar energy values"
    
    # Check that at least some values are positive (Year Stem '甲' should have energy)
    # Index 0 is Year Stem.
    assert any(x > 0 for x in pe), "FluxEngine should populate pillar energies with non-zero values"

def test_visual_narrative_event_structure():
    """
    Test Rule 13: Visual Physics.
    Narrative events must include 'animation_trigger' and correctly formatted keys.
    """
    # Test Case: Earth Alliance (Case 25 Logic)
    # Needs Earth DM + Strong Self (>6.0)
    earth_case = {
        "id": 25,
        "day_master": "戊",
        "wang_shuai": "身旺", 
        "gender": "男",
        "bazi": ["戊戌", "己未", "戊辰", "己丑"], # Full Earth
        "physics_sources": {
            "self": {
                "month_command": 4.0, 
                "day_root": 2.0, 
                "other_roots": 2.0, 
                "stem_support": 2.0
            }, # Sum = 10.0 > 6.0
            "wealth": {"base": 2.0} # Wealth to trigger the check
        }
    }
    
    # Enable the logic flag explicitly
    params = {
        "enable_mountain_alliance": True,
        "K_Clash_Robbery": 1.0 # Ensure robbery logic runs
    }
    
    engine = QuantumEngine(params)
    result = engine.calculate_energy(earth_case)
    
    events = result.get('narrative_events', [])
    print("Events:", events)
    
    # Verify Mountain Alliance Trigger
    found = False
    for e in events:
        if e['card_type'] == 'mountain_alliance' and e.get('title') == '积土成山 (Alliance)':
            found = True
            assert e.get('animation_trigger') == 'earth_assemble', "Mountain Alliance missing correct animation trigger"
            assert e.get('level') == 'legendary', "Wrong level for alliance"
            
    assert found, "Mountain Alliance event was not triggered for Earth Dominant Chart"

def test_structural_penalty_cap_event():
    """
    Test Rule 13/2.2: Penalty Cap Animation
    """
    # Create massive structural clash
    # Using 'enable_structural_clash'
    # We need to accumulate clash_score > Max (6.0)
    
    # Bazi with multiple clashes:
    # Zi-Wu (5.0) + Zi-Wu (5.0) = 10.0 > 6.0
    clash_case = {
        "id": 997,
        "day_master": "甲",
        "wang_shuai": "身弱",
        "gender": "男",
        "bazi": ["甲子", "庚午", "壬子", "丙午"], # Zi-Wu x 2 pairs potentially
        "physics_sources": {
            "self": {"base": 1.0},
            "wealth": {"base": 1.0}
        }
    }
    
    params = {
        "enable_structural_clash": True,
        "Clash_Penalty_Weight": 5.0,
        "Max_Structural_Penalty": 4.0 # Lower cap to ensure we hit it with 5.0
    }
    
    engine = QuantumEngine(params)
    result = engine.calculate_energy(clash_case)
    
    events = result.get('narrative_events', [])
    
    found_cap = False
    for e in events:
        if e['card_type'] == 'penalty_cap':
            found_cap = True
            assert e.get('animation_trigger') == 'shield_ripple'
            print("Penalty Cap Event:", e)
            
    assert found_cap, "Penalty Cap event should trigger when structural penalty exceeds max"
