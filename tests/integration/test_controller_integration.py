"""
V9.5 MVC Controller Integration Tests
======================================
Validates the BaziController layer functionality for P1/P2/P3 View components.
"""

import pytest
import datetime
from controllers.bazi_controller import BaziController


class TestControllerInitialization:
    """Test Controller instantiation and basic setup."""
    
    def test_controller_version(self):
        """Controller should report correct MVC version."""
        ctrl = BaziController()
        assert "MVC" in ctrl.VERSION
        
    def test_lazy_initialization(self):
        """Controller should have None engines before set_user_input."""
        ctrl = BaziController()
        assert ctrl._quantum_engine is None
        assert ctrl._flux_engine is None
        assert ctrl._profile is None


class TestUserInputAPI:
    """Test User Input handling."""
    
    def test_set_user_input_male(self):
        """Set user input with male gender."""
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Test Male",
            gender="男",
            date_obj=datetime.date(1990, 6, 15),
            time_int=12,
            city="Beijing"
        )
        assert ctrl.get_gender_idx() == 1
        assert ctrl._city == "Beijing"
        
    def test_set_user_input_female(self):
        """Set user input with female gender."""
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Test Female",
            gender="女",
            date_obj=datetime.date(1985, 3, 20),
            time_int=8,
            city="Shanghai"
        )
        assert ctrl.get_gender_idx() == 0
        
    def test_engines_initialized_after_input(self):
        """Engines should initialize after set_user_input."""
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Test",
            gender="男",
            date_obj=datetime.date(1980, 1, 1),
            time_int=0,
            city="Beijing"
        )
        assert ctrl._quantum_engine is not None
        assert ctrl._flux_engine is not None
        assert ctrl._profile is not None


class TestChartAndLuckAPI:
    """Test chart and luck cycle retrieval."""
    
    @pytest.fixture
    def initialized_controller(self):
        """Pre-initialized controller fixture."""
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Jack Ma",
            gender="男",
            date_obj=datetime.date(1964, 9, 10),
            time_int=8,
            city="Hangzhou"
        )
        return ctrl
        
    def test_get_chart(self, initialized_controller):
        """Get chart should return non-empty dict."""
        chart = initialized_controller.get_chart()
        assert isinstance(chart, dict)
        assert "year" in chart or "day" in chart
        
    def test_get_luck_cycles(self, initialized_controller):
        """Get luck cycles should return list."""
        cycles = initialized_controller.get_luck_cycles()
        assert isinstance(cycles, list)
        
    def test_get_dynamic_luck_pillar(self, initialized_controller):
        """Get dynamic luck pillar for specific year."""
        pillar = initialized_controller.get_dynamic_luck_pillar(2024)
        assert isinstance(pillar, str)


class TestTimelineSimulation:
    """Test timeline simulation (P1 core feature)."""
    
    @pytest.fixture
    def controller(self):
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Test Case",
            gender="男",
            date_obj=datetime.date(1964, 9, 10),
            time_int=12,
            city="Hangzhou"
        )
        return ctrl
        
    def test_run_timeline_simulation(self, controller):
        """Timeline simulation should return DataFrame and handovers."""
        df, handovers = controller.run_timeline_simulation(2020, 12)
        
        assert len(df) == 12
        assert "year" in df.columns
        assert "career" in df.columns
        assert "wealth" in df.columns
        assert "relationship" in df.columns
        
    def test_handover_detection(self, controller):
        """Handover years should be detected."""
        df, handovers = controller.run_timeline_simulation(2020, 20)
        # At least one handover should be detected in 20 years
        # (May or may not exist depending on birth date)
        assert isinstance(handovers, list)


class TestGeoComparisonAPI:
    """Test GEO comparison (P2/P3 core feature)."""
    
    @pytest.fixture
    def controller(self):
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Geo Test",
            gender="女",
            date_obj=datetime.date(1975, 11, 25),
            time_int=18,
            city="Singapore"
        )
        return ctrl
        
    def test_get_baseline_trajectory(self, controller):
        """Baseline trajectory (no GEO) should have correct columns."""
        df = controller.get_baseline_trajectory(2024, 12)
        
        assert len(df) == 12
        assert "baseline_career" in df.columns
        assert "baseline_wealth" in df.columns
        assert "baseline_relationship" in df.columns
        
    def test_get_geo_trajectory(self, controller):
        """GEO trajectory should have correct columns."""
        df = controller.get_geo_trajectory("Singapore", 2024, 12)
        
        assert len(df) == 12
        assert "geo_career" in df.columns
        assert "geo_wealth" in df.columns
        assert "geo_relationship" in df.columns
        
    def test_get_geo_comparison(self, controller):
        """GEO comparison should merge both trajectories."""
        combined_df, geo_mods = controller.get_geo_comparison("Singapore", 2024, 12)
        
        assert len(combined_df) == 12
        
        # Should have both baseline and geo columns
        assert "baseline_career" in combined_df.columns
        assert "geo_career" in combined_df.columns


class TestFluxEngineAPI:
    """Test Flux Engine integration."""
    
    @pytest.fixture
    def controller(self):
        ctrl = BaziController()
        ctrl.set_user_input(
            name="Flux Test",
            gender="男",
            date_obj=datetime.date(1990, 5, 5),
            time_int=5,
            city="Beijing"
        )
        return ctrl
        
    def test_get_flux_data(self, controller):
        """Flux data should return energy state dict."""
        flux_data = controller.get_flux_data()
        assert isinstance(flux_data, dict)
        
    def test_get_wang_shuai_str(self, controller):
        """Wang Shuai string calculation."""
        flux_data = controller.get_flux_data()
        ws_str = controller.get_wang_shuai_str(flux_data)
        assert ws_str in ["身旺", "身弱", "假从/极弱"]


# Run all tests
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
