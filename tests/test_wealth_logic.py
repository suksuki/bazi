
import pytest
from core.flux import FluxEngine
from core.meaning import MeaningEngine

def test_wealth_logic_ledger():
    # 1. Mock Flux Data
    # Simulate: DM=Wood, Fire(Tool), Metal(7K), Earth(Wealth)
    # This structure tests Tool vs Source vs Container roles.
    
    # We will mock the 'flux_data' structure that MeaningEngine expects.
    # It needs: 'particle_states' with 'id', 'char', 'type', 'amp'.
    
    flux_data = {
        'particle_states': [
            # Day: Jia Wood (DM)
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40.0},
            
            # Month: Shen Metal (QiSha - Source) - Changed from You to Shen
            {'id': 'month_branch', 'char': '申', 'type': 'branch', 'amp': 80.0},
            
            # Year: Ding Fire (ShangGuan - Tool)
            {'id': 'year_stem', 'char': '丁', 'type': 'stem', 'amp': 30.0},
            
            # Hour: Chou Earth (Wealth Tomb - Container)
            {'id': 'hour_branch', 'char': '丑', 'type': 'branch', 'amp': 60.0},
            
            # Leak: Yi Wood (JieCai)
            {'id': 'month_stem', 'char': '乙', 'type': 'stem', 'amp': 20.0},
        ],
        'log': [],
        'spectrum': {}
    }
    
    # 2. Mock Chart (MeaningEngine needs DM stem)
    chart = {
        'day': {'stem': '甲'}
    }
    
    # 3. Instantiate Engine
    engine = MeaningEngine(chart, flux_data)
    
    # Manually trigger god map build (usually done in init but let's verify)
    # The engine builds god map based on Flux Data particles.
    assert engine.god_map['day_stem'] == 'BiJian' # Self
    assert engine.god_map['month_branch'] == 'QiSha' # Shen Metal (Yang) kills Jia Wood (Yang) = QiSha
    assert engine.god_map['year_stem'] == 'ShangGuan' # Wood births Fire
    assert engine.god_map['hour_branch'] == 'ZhengCai' # Wood controls Earth 
    assert engine.god_map['month_stem'] == 'JieCai' # Wood same Wood diff polarity
    
    # 4. Run Logic Analysis
    report = engine.analyze_wealth_logic()
    
    # 5. Verify Report Structure
    assert 'ledger' in report
    assert 'path_info' in report
    assert 'conclusion' in report
    
    # Verify ledger has entries
    ledger = report['ledger']
    assert len(ledger) > 0
    
    # Verify each entry has required fields
    for entry in ledger:
        assert 'role' in entry
        assert 'god' in entry
        assert 'label' in entry
        assert 'value_str' in entry
        assert 'color' in entry
        assert 'desc' in entry
    
    # Verify path info has required fields
    assert 'pattern' in report['path_info']
    assert 'process' in report['path_info']
    
    # Verify conclusion has required fields
    assert 'level' in report['conclusion']
    assert 'risk' in report['conclusion']
    
    print("Logic Trace Test Passed!")
