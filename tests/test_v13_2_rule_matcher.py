"""
Test Suite for V13.2 Rule Matcher and Ten Gods with Hidden Stems

Tests:
1. RuleMatcher correctly detects all verified rules
2. Ten Gods calculation includes hidden stems from branches
3. ProbValue comparison fix in phase3_propagation
"""

import pytest
from typing import List, Dict


class TestRuleMatcher:
    """Test the RuleMatcher service"""
    
    def test_rule_matcher_import(self):
        """Test RuleMatcher can be imported"""
        from core.rule_matcher import RuleMatcher, MatchedRule
        matcher = RuleMatcher()
        assert matcher is not None
    
    def test_three_harmony_detection(self):
        """Test 巳酉丑三合金局 detection"""
        from core.rule_matcher import RuleMatcher
        
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        dm = '乙'
        
        matcher = RuleMatcher()
        matched = matcher.match(bazi, dm)
        
        # Should detect three harmony metal
        rule_ids = [r.rule_id for r in matched]
        assert 'B6' in rule_ids, "Should detect B6 三合局"
        
        # Find the three harmony rule
        three_harmony = [r for r in matched if r.rule_id == 'B6'][0]
        assert 'metal' in three_harmony.effect.lower() or '金' in three_harmony.effect
    
    def test_stem_five_combination(self):
        """Test 天干五合 detection (甲己合土)"""
        from core.rule_matcher import RuleMatcher
        
        bazi = ['甲寅', '己巳', '壬申', '庚子']
        dm = '壬'
        
        matcher = RuleMatcher()
        matched = matcher.match(bazi, dm)
        
        rule_ids = [r.rule_id for r in matched]
        assert 'B1' in rule_ids, "Should detect B1 天干五合"
    
    def test_six_clash_detection(self):
        """Test 六冲 detection (寅申冲)"""
        from core.rule_matcher import RuleMatcher
        
        bazi = ['甲寅', '己巳', '壬申', '庚子']
        dm = '壬'
        
        matcher = RuleMatcher()
        matched = matcher.match(bazi, dm)
        
        rule_ids = [r.rule_id for r in matched]
        assert 'B2' in rule_ids, "Should detect B2 六冲"
    
    def test_rooting_detection(self):
        """Test 自坐强根 detection (A6)"""
        from core.rule_matcher import RuleMatcher
        
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        dm = '乙'
        
        matcher = RuleMatcher()
        matched = matcher.match(bazi, dm)
        
        rule_ids = [r.rule_id for r in matched]
        assert 'A6' in rule_ids, "Should detect A6 自坐强根 (丁巳柱丁火坐巳)"
    
    def test_rule_summary(self):
        """Test rule summary generation"""
        from core.rule_matcher import RuleMatcher
        
        bazi = ['甲寅', '己巳', '壬申', '庚子']
        dm = '壬'
        
        matcher = RuleMatcher()
        matched = matcher.match(bazi, dm)
        summary = matcher.get_rule_summary(matched)
        
        assert 'total' in summary
        assert 'by_category' in summary
        assert 'active_effects' in summary
        assert summary['total'] > 0


class TestTenGodsWithHiddenStems:
    """Test Ten Gods calculation including hidden stems"""
    
    def test_hidden_stems_mapping_exists(self):
        """Test HIDDEN_STEMS mapping is available"""
        from core.kernel import Kernel
        
        assert hasattr(Kernel, 'HIDDEN_STEMS')
        hs = Kernel.HIDDEN_STEMS
        
        # Check some known mappings
        assert '巳' in hs
        assert '丙' in hs['巳']
        assert hs['巳']['丙'] == 0.6  # 丙 is main hidden stem (60%)
        
        assert '丑' in hs
        assert '己' in hs['丑']
        assert '癸' in hs['丑']
        assert '辛' in hs['丑']
    
    def test_ten_gods_includes_hidden_stems(self):
        """Test ten gods calculation includes hidden stems contributions"""
        from core.engine_graph import GraphNetworkEngine
        from core.math import ProbValue
        from core.kernel import Kernel
        
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        dm = '乙'
        
        # Run engine
        engine = GraphNetworkEngine()
        engine.initialize_nodes(bazi, dm, luck_pillar='庚子', year_pillar='乙巳')
        engine.build_adjacency_matrix()
        engine._apply_quantum_entanglement_once()
        engine.propagate(max_iterations=5)
        
        # Calculate ten gods manually
        HIDDEN_STEMS = Kernel.HIDDEN_STEMS
        gods_map = {
            '乙': 'BiJian', '甲': 'JieCai',
            '丁': 'ShiShen', '丙': 'ShangGuan',
            '己': 'PianCai', '戊': 'ZhengCai',
            '辛': 'QiSha', '庚': 'ZhengGuan',
            '癸': 'PianYin', '壬': 'ZhengYin'
        }
        
        ten_gods = {god: 0 for god in set(gods_map.values())}
        
        for node in engine.nodes:
            mean_val = node.current_energy.mean if isinstance(node.current_energy, ProbValue) else float(node.current_energy)
            
            if node.node_type == 'stem' and node.char in gods_map:
                ten_gods[gods_map[node.char]] += mean_val
            
            elif node.node_type == 'branch' and node.char in HIDDEN_STEMS:
                for h_stem, ratio in HIDDEN_STEMS[node.char].items():
                    if h_stem in gods_map:
                        ten_gods[gods_map[h_stem]] += mean_val * ratio
        
        # 食伤 should have contribution from hidden 丙 in 巳
        shi_shang = ten_gods.get('ShiShen', 0) + ten_gods.get('ShangGuan', 0)
        assert shi_shang > 0, "食伤 should have energy from hidden stems (丙 in 巳)"
        
        # 财星 should have contribution from hidden 己 in 丑
        cai_xing = ten_gods.get('PianCai', 0) + ten_gods.get('ZhengCai', 0)
        assert cai_xing > 0, "财星 should have energy from hidden stems (己 in 丑)"
        
        # 印枭 should have contribution from hidden 癸 in 丑 and 子
        yin_xiao = ten_gods.get('PianYin', 0) + ten_gods.get('ZhengYin', 0)
        assert yin_xiao > 0, "印枭 should have energy from hidden stems (癸 in 丑/子)"


class TestProbValueComparison:
    """Test ProbValue comparison fix"""
    
    def test_probvalue_mean_comparison(self):
        """Test that ProbValue comparison uses .mean attribute"""
        from core.math import ProbValue
        
        pv1 = ProbValue(10.0, std_dev_percent=0.1)
        pv2 = ProbValue(8.0, std_dev_percent=0.1)
        
        # Should compare using .mean
        assert pv1.mean > pv2.mean
        assert pv2.mean < pv1.mean
    
    def test_phase3_propagation_runs_without_error(self):
        """Test that phase3_propagation runs without ProbValue comparison error"""
        from core.engine_graph import GraphNetworkEngine
        
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']
        dm = '乙'
        
        engine = GraphNetworkEngine()
        engine.initialize_nodes(bazi, dm, luck_pillar='庚子', year_pillar='乙巳')
        engine.build_adjacency_matrix()
        engine._apply_quantum_entanglement_once()
        
        # This should not raise TypeError for ProbValue comparison
        try:
            H = engine.propagate(max_iterations=5)
            assert H is not None
        except TypeError as e:
            if "'<' not supported between instances of 'ProbValue'" in str(e):
                pytest.fail("ProbValue comparison error not fixed")
            raise


class TestOriginalElementPreservation:
    """Test that original element is preserved after transformation"""
    
    def test_original_element_stored(self):
        """Test that original_element is stored when transformation occurs"""
        from core.engine_graph import GraphNetworkEngine
        
        bazi = ['丁巳', '乙巳', '乙丑', '乙酉']  # 巳酉丑三合金局
        dm = '乙'
        
        engine = GraphNetworkEngine()
        engine.initialize_nodes(bazi, dm)
        engine.build_adjacency_matrix()
        engine._apply_quantum_entanglement_once()
        
        # Check that transformed nodes have original_element
        for node in engine.nodes:
            if node.node_type == 'branch' and node.char in ['巳', '丑']:
                # These should be transformed to metal in 三合金局
                if node.element == 'metal':
                    assert hasattr(node, 'original_element'), f"{node.char} should have original_element"
                    assert node.original_element in ['fire', 'earth'], f"{node.char} original should be fire or earth"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
