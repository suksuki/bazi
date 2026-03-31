import pytest
import datetime
import pandas as pd
from services.simulation_service import SimulationService
from services.report_generator_service import ReportGeneratorService
from core.unified_engine import UnifiedEngine
from core.bazi_profile import BaziProfile
from unittest.mock import MagicMock

@pytest.fixture
def engine():
    return UnifiedEngine()

@pytest.fixture
def jack_ma_profile():
    return BaziProfile(datetime.datetime(1964, 9, 10, 12, 0), 1)

@pytest.fixture
def simulation_service():
    return SimulationService()

@pytest.fixture
def report_service():
    return ReportGeneratorService()

class TestSimulationService:
    def test_run_timeline(self, simulation_service, engine, jack_ma_profile):
        user_input = {
            'date': datetime.date(1964, 9, 10),
            'time': 12,
            'gender': '男',
            'city': 'Hangzhou'
        }
        case_data = {
            'bazi': ['甲辰', '癸酉', '壬戌', '壬辰'],
            'day_master': '壬',
            'gender': 1,
            'city': 'Hangzhou'
        }
        
        df, handovers = simulation_service.run_timeline(
            engine=engine,
            profile=jack_ma_profile,
            user_input=user_input,
            case_data=case_data,
            start_year=2020,
            duration=12,
            era_multipliers={}
        )
        
        assert len(df) == 12
        assert 'year' in df.columns
        assert 'score' in df.columns
        assert df.iloc[0]['year'] == 2020
        assert df.iloc[-1]['year'] == 2031

    def test_cache_hits(self, simulation_service, engine, jack_ma_profile):
        user_input = {'date': '1964-09-10', 'time': 12, 'gender': 1, 'city': 'HZ'}
        case_data = {'bazi': ['甲辰', '癸酉', '壬戌', '壬辰'], 'day_master': '壬'}
        
        # Reset cache
        simulation_service._timeline_cache = {}
        simulation_service._cache_stats = {'hits': 0, 'misses': 0}
        
        # First run (miss)
        simulation_service.run_timeline(engine, jack_ma_profile, user_input, case_data, 2020, 5, {})
        stats = simulation_service.get_cache_stats()
        assert stats['misses'] == 1
        
        # Second run (hit)
        simulation_service.run_timeline(engine, jack_ma_profile, user_input, case_data, 2020, 5, {})
        stats = simulation_service.get_cache_stats()
        assert stats['hits'] == 1

class TestReportGeneratorService:
    def test_generate_semantic_report_basic(self, report_service):
        # Mocking complex result objects
        pfa_result = MagicMock()
        pfa_result.friction_index = 25
        pfa_result.conflicting_patterns = []
        
        soa_result = MagicMock()
        soa_result.stability_score = 0.8
        soa_result.optimal_elements = {'wood': 0.5, 'fire': 0.2}
        
        mca_result = MagicMock()
        
        profile_data = {'name': 'Tester'}
        force_vectors = {'wealth': 45, 'career': 60, 'relationship': 30}
        
        report = report_service.generate_semantic_report(
            profile_data=profile_data,
            pfa_result=pfa_result,
            soa_result=soa_result,
            mca_result=mca_result,
            force_vectors=force_vectors,
            year=2024,
            use_llm=False
        )
        
        assert 'core_conflict' in report
        assert 'persona' in report
        assert 'wealth_prediction' in report
        assert 'prescription' in report
        assert 'Tester' in report['persona']
