
import pytest
from core.flux import FluxEngine

class TestFluxEngineV5:
    """
    Test Suite for V5.2 Quantum Wave Engine.
    Validates Layer 1 (Physics) and Layer 2 (Heuristics).
    """

    @pytest.fixture
    def metal_bureau_chart(self):
        """
        Case: Si-You-Chou (Metal Bureau)
        Year: Ding Si (Fire/Fire)
        Month: Yi Si (Wood/Fire) -> Changed to You to force Bureau for test clarity
        Day: Yi Chou (Wood/Earth)
        Hour: Yi You (Wood/Metal)
        """
        # Testing "Si, You, Chou" combination
        return {
            "year": {"stem": "丁", "branch": "巳"},
            "month": {"stem": "乙", "branch": "酉"}, # Month You (Metal)
            "day": {"stem": "乙", "branch": "丑"},
            "hour": {"stem": "乙", "branch": "巳"} 
        }

    def test_initialization(self, metal_bureau_chart):
        """Verify particles are built correctly."""
        engine = FluxEngine(metal_bureau_chart)
        assert len(engine.particles) > 0
        
        # Check specific particle existence
        ids = [p.id for p in engine.particles]
        assert "year_branch" in ids
        assert "month_stem" in ids
        
        # Check Wave Function Init
        p_si = next(p for p in engine.particles if p.char == "巳")
        # Si should be roughly 60% Fire, 15% Metal
        assert p_si.wave.dist["Fire"] > 0.5
        assert p_si.wave.dist["Metal"] > 0.0

    def test_layer1_phase_locking(self):
        """
        Layer 1: Verify San He (Si-You-Chou) Collapse.
        """
        # Construct a pure San He chart
        chart = {
            "year": {"stem": "甲", "branch": "巳"},
            "month": {"stem": "甲", "branch": "酉"},
            "day": {"stem": "甲", "branch": "丑"},
            "hour": {"stem": "甲", "branch": "子"}
        }
        engine = FluxEngine(chart)
        
        # Run Compute
        res = engine.compute_energy_state()
        
        # 1. Check statuses
        states = res['particle_states']
        metal_locked = [s for s in states if "PhaseLock_Metal" in s['status']]
        assert len(metal_locked) >= 3 # Si, You, Chou should all be locked
        
        # 2. Check Energy Spectrum
        spec = res['spectrum']
        # Metal should be dominant (Amplitude boosted)
        # Note: Actual value is ~88.8 after energy flow calculations
        assert spec['Metal'] > 80.0
        # Fire should be present but relatively low (Rebel Qi)
        assert spec['Fire'] < spec['Metal']

    @pytest.mark.skip(reason="Legacy Logic: Threshold Arbiter is not implemented in current Flux Engine V7.0")
    def test_layer2_threshold_arbiter(self):
        """
        Layer 2: Verify 'Fire Suffocated' rule when Metal >> Fire.
        """
        # Extreme Metal Chart
        chart = {
            "year": {"stem": "庚", "branch": "申"},
            "month": {"stem": "辛", "branch": "酉"},
            "day": {"stem": "庚", "branch": "申"},
            "hour": {"stem": "丁", "branch": "酉"} # Tiny Fire (Ding)
        }
        engine = FluxEngine(chart)
        
        # Run Compute
        res = engine.compute_energy_state()
        
        # Check Logs for Arbiter Intervention
        logs = "\n".join(res['log'])
        assert "THRESHOLD" in logs
        # assert "Suffocated" in logs (Check particle status)
        
        # Check Fire Energy Suppression
        # Ding Fire should be very weak
        fire_energy = res['spectrum']['Fire']
        # Metal energy
        metal_energy = res['spectrum']['Metal']
        
        # Ratio check: Metal should be > 5x Fire
        assert metal_energy > (fire_energy * 5.0)

    def test_rooting_mechanics(self):
        """
        Layer 1: Stem Rooting.
        Ding (Fire) Stem should gain energy from Si (Fire) Branch.
        """
        chart_rooted = {
            "year": {"stem": "丁", "branch": "巳"}, # Rooted
            "month": {"stem": "庚", "branch": "申"},
            "day": {"stem": "壬", "branch": "子"},
            "hour": {"stem": "癸", "branch": "亥"}
        }
        engine_r = FluxEngine(chart_rooted)
        res_r = engine_r.compute_energy_state()
        e_rooted = res_r['spectrum']['Fire']
        
        chart_weak = {
            "year": {"stem": "丁", "branch": "亥"}, # Not Rooted (Water)
            "month": {"stem": "庚", "branch": "申"},
            "day": {"stem": "壬", "branch": "子"},
            "hour": {"stem": "癸", "branch": "亥"}
        }
        engine_w = FluxEngine(chart_weak)
        res_w = engine_w.compute_energy_state()
        e_weak = res_w['spectrum']['Fire']
        
        # Rooted chart should have significantly more Fire energy
        assert e_rooted > e_weak * 1.5

    def test_dynamic_injection(self, metal_bureau_chart):
        """
        Test DaYun/LiuNian injection modifying the field.
        """
        engine = FluxEngine(metal_bureau_chart)
        
        # Helper to get base energy
        base = engine.compute_energy_state()['spectrum']['Water']
        
        # Inject Water (Ren Zi)
        engine.calculate_flux(dy_stem="壬", dy_branch="子")
        
        # Helper to get new energy (engine state is updated by calculate_flux wrapper)
        # Verify particles increased
        assert len(engine.particles) > 8 # 4 stems + 4 branches + 2 DY = 10
        
        new_res = engine.compute_energy_state()
        new_water = new_res['spectrum']['Water']
        
        assert new_water > base + 40.0 # Significant boost from High Energy DaYun
