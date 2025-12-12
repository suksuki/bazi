
import pytest
from learning.text_cleaner import TextCleaner
from core.rule_injector import RuleInjector

def test_text_cleaner_phrases():
    # Test garbage removal
    raw = "大家好，我是张老师。点赞关注不迷路。这个八字是甲木日主。"
    cleaned = TextCleaner.clean(raw)
    assert "点赞" not in cleaned
    assert "关注" not in cleaned
    assert "甲木日主" in cleaned
    # "大家好" might be in stop phrases
    assert "大家好" not in cleaned

def test_text_cleaner_correction():
    # Test term correction
    raw = "他的八字里有四火和深若的问题。才星很旺。"
    cleaned = TextCleaner.clean(raw)
    assert "巳火" in cleaned # Fixed 四火
    assert "身弱" in cleaned # Fixed 深若
    assert "财星" in cleaned # Fixed 才星

def test_rule_injector_logic():
    # Mock Flux Result
    flux_result = {
        "particle_states": [
            {"id": "year_branch", "char": "寅", "amp": 50},
            {"id": "day_branch", "char": "午", "amp": 60}
        ],
        "spectrum": {"Fire": 80.0, "Wood": 40.0}
    }
    
    injector = RuleInjector(flux_result)
    
    # Mock DB Context manually for unit test (avoiding real DB dependency)
    # But injector.run() calls self.db.get_all_rules(). we need to mock db or use _evaluate directly.
    
    # Let's test _evaluate directly for unit testing logic
    ctx = injector._build_context()
    
    assert ctx['Fire'] == 80.0
    assert "寅" in ctx['chars']
    
    # Test Condition 1
    cond1 = "Fire > 50"
    assert injector._evaluate(cond1, ctx) == True
    
    # Test Condition 2
    cond2 = "'寅' in chars"
    assert injector._evaluate(cond2, ctx) == True
    
    # Test Condition 3 (FAIL)
    cond3 = "Water > 10"
    assert injector._evaluate(cond3, ctx) == False

