import unittest
from unittest.mock import MagicMock, patch
from core.trajectory import AdvancedTrajectoryEngine
import datetime

class TestTrajectoryEngine(unittest.TestCase):
    
    def setUp(self):
        # Synthetic Chart and Luck Cycles
        self.chart = "甲子 乙丑 丙寅 丁卯"
        self.luck_cycles = [
            {'start_year': 1990, 'end_year': 1999, 'gan_zhi': '戊辰'},
            {'start_year': 2000, 'end_year': 2009, 'gan_zhi': '己巳'},
        ]
        self.start_year = 1990
        
    @patch('core.wuxing_engine.WuXingEngine')
    @patch('core.trajectory.FluxEngine') 
    @patch('core.quantum.QuantumSimulator')
    def test_run_monte_carlo_backbone(self, MockQuantum, MockFlux, MockWuXing):
        # Init Engine under patches
        engine = AdvancedTrajectoryEngine(self.chart, self.luck_cycles, self.start_year)

        # Setup Mocks
        mock_wx = MockWuXing.return_value
        mock_wx.calculate_strength.return_value = {'scores': {'Wood': 50}}
        
        mock_flux_inst = MockFlux.return_value
        mock_flux_inst.calculate_flux.return_value = {'TenGod': {'entropy': 1.0}}
        
        mock_q_inst = MockQuantum.return_value
        # simulate return: {Aspect: {Expected: 50, ...}}
        mock_q_inst.simulate.return_value = {
            '财富 (Wealth)': {'Expected_Value': 60, 'Uncertainty': 10},
            '事业 (Career)': {'Expected_Value': 65, 'Uncertainty': 10}
        }
        
        # Test Granularity: Year
        # Should run from 1990 to 1992 (Age 0, 1, 2)
        timeline = engine.run_monte_carlo(end_age=2, granularity="year", n_simulations=5)
        
        self.assertEqual(len(timeline), 3) # Age 0, 1, 2
        self.assertEqual(timeline[0]['year'], 1990)
        self.assertEqual(timeline[1]['year'], 1991)
        
        # Verify Backbone Calls
        self.assertEqual(mock_flux_inst.calculate_flux.call_count, 3)

    @patch('core.wuxing_engine.WuXingEngine')
    @patch('core.trajectory.FluxEngine') 
    @patch('core.quantum.QuantumSimulator')
    def test_run_monte_carlo_month(self, MockQuantum, MockFlux, MockWuXing):
        # Init Engine under patches
        engine = AdvancedTrajectoryEngine(self.chart, self.luck_cycles, self.start_year)

        # Setup Mocks
        mock_flux_inst = MockFlux.return_value
        mock_flux_inst.calculate_flux.return_value = {'TenGod': {'entropy': 1.0}}
        
        mock_q_inst = MockQuantum.return_value
        mock_q_inst.simulate.return_value = {
            '财富 (Wealth)': {'Expected_Value': 60, 'Uncertainty': 10},
            '事业 (Career)': {'Expected_Value': 65, 'Uncertainty': 10}
        }
        
        # Test Granularity: Month
        # 1 Year (1990) -> 12 steps
        timeline = engine.run_monte_carlo(end_age=0, granularity="month", n_simulations=2)
        
        # Check integrity
        self.assertGreaterEqual(len(timeline), 12)
        self.assertEqual(timeline[0]['year'], 1990)
