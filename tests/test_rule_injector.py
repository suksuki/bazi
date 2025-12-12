
import pytest
from core.rule_injector import RuleInjector

def test_branch_contains_patterns():
    """Test branch character matching with AND/OR logic"""
    flux_result = {
        'particle_states': [
            {'id': 'year_branch', 'char': '巳', 'type': 'branch', 'amp': 50},
            {'id': 'month_branch', 'char': '酉', 'type': 'branch', 'amp': 60},
            {'id': 'day_branch', 'char': '丑', 'type': 'branch', 'amp': 55},
        ],
        'spectrum': {'Metal': 120.0, 'Fire': 40.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    # Test AND logic
    assert injector._evaluate_natural_language("Branches contains Si and You", ctx) == True
    assert injector._evaluate_natural_language("Branches contains Si and Yin", ctx) == False
    
    # Test OR logic (implicit)
    assert injector._evaluate_natural_language("Branches contains Si", ctx) == True
    assert injector._evaluate_natural_language("Branches contains Yin", ctx) == False
    
    # Test explicit OR
    assert injector._evaluate_natural_language("Branches contains Yin or Si", ctx) == True
    
    print("✅ Branch contains tests passed!")

def test_chinese_conditions():
    """Test Chinese condition matching (中文条件匹配)"""
    flux_result = {
        'particle_states': [
            {'id': 'year_branch', 'char': '巳', 'type': 'branch', 'amp': 50},
            {'id': 'month_branch', 'char': '酉', 'type': 'branch', 'amp': 60},
            {'id': 'day_branch', 'char': '丑', 'type': 'branch', 'amp': 55},
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40},
        ],
        'spectrum': {'Metal': 120.0, 'Fire': 40.0, 'Wood': 80.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    # Test Chinese branch conditions
    assert injector._evaluate_natural_language("地支 包含 巳 和 酉", ctx) == True
    assert injector._evaluate_natural_language("地支 包含 巳, 酉, 丑", ctx) == True
    assert injector._evaluate_natural_language("地支 包含 寅", ctx) == False
    
    # Test Chinese stem conditions
    assert injector._evaluate_natural_language("天干 包含 甲", ctx) == True
    assert injector._evaluate_natural_language("天干 包含 庚", ctx) == False
    
    # Test Chinese quality descriptors
    # Metal = 120 > 80, so it's strong
    assert injector._evaluate_natural_language("金 很强", ctx) == True
    
    print("✅ Chinese conditions tests passed!")

def test_stem_contains_patterns():
    """Test stem character matching"""
    flux_result = {
        'particle_states': [
            {'id': 'year_stem', 'char': '甲', 'type': 'stem', 'amp': 30},
            {'id': 'month_stem', 'char': '丙', 'type': 'stem', 'amp': 40},
            {'id': 'day_stem', 'char': '乙', 'type': 'stem', 'amp': 35},
        ],
        'spectrum': {'Wood': 80.0, 'Fire': 60.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    assert injector._evaluate_natural_language("Stems contains Jia", ctx) == True
    assert injector._evaluate_natural_language("Stems contains Geng", ctx) == False
    # OR logic test
    assert injector._evaluate_natural_language("Stems contains Jia or Geng", ctx) == True
    
    print("✅ Stem contains tests passed!")

def test_element_comparisons():
    """Test element energy comparisons"""
    flux_result = {
        'particle_states': [],
        'spectrum': {'Wood': 120.0, 'Fire': 45.0, 'Metal': 30.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    assert injector._evaluate_natural_language("Wood > 100", ctx) == True
    assert injector._evaluate_natural_language("Wood > 150", ctx) == False
    assert injector._evaluate_natural_language("Fire < 50", ctx) == True
    assert injector._evaluate_natural_language("Metal < 20", ctx) == False
    
    print("✅ Element comparison tests passed!")

def test_day_master_checks():
    """Test Day Master element and character checks"""
    flux_result = {
        'particle_states': [
            {'id': 'day_stem', 'char': '甲', 'type': 'stem', 'amp': 40},
        ],
        'spectrum': {'Wood': 100.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    # Day Master element check
    assert injector._evaluate_natural_language("Day Master is Wood", ctx) == True
    assert injector._evaluate_natural_language("Day Master is Fire", ctx) == False
    
    # Day Master specific stem check
    assert injector._evaluate_natural_language("Day Master is Jia", ctx) == True
    assert injector._evaluate_natural_language("Day Master is Yi", ctx) == False
    
    print("✅ Day Master tests passed!")

def test_quality_descriptors():
    """Test quality-based conditions (strong/weak/good)"""
    flux_result = {
        'particle_states': [],
        'spectrum': {'Fire': 90.0, 'Water': 20.0, 'Wood': 100.0, 'Metal': 80.0, 'Earth': 50.0}
    }
    
    injector = RuleInjector(flux_result)
    ctx = injector._build_context()
    
    # Strong check
    assert injector._evaluate_natural_language("Fire is strong", ctx) == True
    assert injector._evaluate_natural_language("Water is strong", ctx) == False
    
    # Weak check
    assert injector._evaluate_natural_language("Water is weak", ctx) == True
    assert injector._evaluate_natural_language("Fire is weak", ctx) == False
    
    # Good/excellent check (total energy > 200)
    assert injector._evaluate_natural_language("Life condition is good", ctx) == True
    
    print("✅ Quality descriptor tests passed!")

def test_integration_with_db_format():
    """Test full integration with database rule format"""
    flux_result = {
        'particle_states': [
            {'id': 'year_branch', 'char': '巳', 'type': 'branch', 'amp': 50},
            {'id': 'month_branch', 'char': '酉', 'type': 'branch', 'amp': 60},
            {'id': 'day_branch', 'char': '丑', 'type': 'branch', 'amp': 55},
        ],
        'spectrum': {'Metal': 120.0, 'Fire': 40.0}
    }
    
    injector = RuleInjector(flux_result)
    
    # This will actually query the database
    # If there are 992 rules, some should match
    active_rules = injector.run()
    
    print(f"✅ Integration test: Found {len(active_rules)} matching rules from database")
    
    # Display first few matches if any
    for i, rule in enumerate(active_rules[:3]):
        print(f"  {i+1}. {rule['name']} (来源: {rule['source']})")

if __name__ == "__main__":
    test_branch_contains_patterns()
    test_chinese_conditions()
    test_stem_contains_patterns()
    test_element_comparisons()
    test_day_master_checks()
    test_quality_descriptors()
    test_integration_with_db_format()
    print("\n🎉 All RuleInjector tests passed!")

