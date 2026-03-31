
import pytest
from unittest.mock import MagicMock, patch
from services.simulation_service import SimulationService
from datetime import datetime

class TestSimulationServiceV2:
    
    @pytest.fixture
    def service(self):
        return SimulationService()

    @patch('services.simulation_service.BaziProfile')
    @patch('services.simulation_service.ProfileManager')
    def test_run_multi_year_real_world_scan(self, MockProfileManager, MockBaziProfile, service):
        # Setup Mock Profile Data
        mock_pm = MockProfileManager.return_value
        mock_pm.get_all.return_value = [
            {'year': 1990, 'month': 1, 'day': 1, 'hour': 12, 'minute': 0, 'gender': '男', 'name': 'TestUser', 'city': 'Beijing'}
        ]
        
        # Setup Mock BaziProfile
        mock_bp = MockBaziProfile.return_value
        mock_bp.pillars = {'year': ('庚', '午'), 'month': ('丙', '子'), 'day': ('甲', '寅'), 'hour': ('庚', '午')}
        mock_bp.get_luck_pillar_at.return_value = ('壬', '申')
        mock_bp.get_year_pillar.return_value = ('甲', '辰')
        
        # Mock run_deep_specialized_scan to return a hit
        with patch.object(service, 'run_deep_specialized_scan') as mock_deep_scan:
            mock_deep_scan.side_effect = lambda *args, **kwargs: [{
                'stress': 2.5,
                'label': 'High Energy',
                'topic_name': 'Test Topic',
                'six_pillars': ['甲子', '乙丑', '丙寅', '丁卯', '戊辰', '己巳']
            }]
            
            # Execute
            results = service.run_multi_year_real_world_scan(
                profile_data={'year': 1990, 'month': 1, 'day': 1, 'hour': 12, 'gender': '男'},
                start_year=2024,
                end_year=2025,
                topic_ids=['TEST_TOPIC']
            )
            
            # Verify
            assert len(results) == 2 # 2024 and 2025
            assert results[0]['target_year'] == 2024
            assert results[1]['target_year'] == 2025
            assert results[0]['topic_name'] == 'Test Topic'

    def test_run_full_pipeline_scan(self, service):
        # We need to mock the engine's generator to avoid infinite loops or massive generation
        with patch.object(service.engine, 'generate_all_bazi') as mock_gen:
            # Mock generator yielding a few charts
            # Chart format: [('Stem', 'Branch'), ...] x4
            mock_chart = [('甲', '子'), ('乙', '丑'), ('丙', '寅'), ('丁', '卯')]
            mock_gen.return_value = iter([mock_chart] * 10)
            
            # Mock PatternScout deep audit if it was used, but here we mocked the logic inside run_full_pipeline_scan partly
            # Actually run_full_pipeline_scan uses internal logic, so we just run it
            
            res = service.run_full_pipeline_scan(track_id="SHANG_GUAN_SHANG_JIN")
            
            assert res['total'] > 0
            assert 'samples' in res
            assert 'year_sai_matrix' in res
            assert 'element_clusters' in res

    def test_placeholder_methods(self, service):
        # Ensure all placeholders are callable and return dicts (as expected by UI)
        assert isinstance(service.run_v43_live_fire_audit(), dict)
        assert isinstance(service.run_v43_penetration_audit(), dict)
        assert isinstance(service.run_v435_yangren_monopole(), dict)
        assert isinstance(service.run_v45_gxyg_audit(), dict)
