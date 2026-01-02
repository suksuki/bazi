"""
FDS-LKV 综合测试套件 (Integration Test Suite)
=============================================
测试所有 LKV 相关模块的功能完整性

模块覆盖:
- VaultManager
- ComplianceRouter
- ProtocolChecker
- LogicCompiler
- CensusEngine
- CensusCache
- QGAVV Generator
"""

import pytest
import sys
import os
import logging

# 添加项目根目录
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================
# VaultManager 测试
# ============================================================

class TestVaultManager:
    """VaultManager 测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.vault_manager import VaultManager, get_vault_manager
        assert VaultManager is not None
        assert get_vault_manager is not None
    
    def test_singleton(self):
        """测试单例模式"""
        from core.vault_manager import get_vault_manager
        v1 = get_vault_manager()
        v2 = get_vault_manager()
        assert v1 is v2
    
    def test_get_stats(self):
        """测试获取统计"""
        from core.vault_manager import get_vault_manager
        vault = get_vault_manager()
        stats = vault.get_vault_stats()
        assert "semantic_count" in stats
        assert "singularity_count" in stats
        assert stats["semantic_count"] >= 0
        assert stats["singularity_count"] >= 0


# ============================================================
# ProtocolChecker 测试
# ============================================================

class TestProtocolChecker:
    """ProtocolChecker 测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.protocol_checker import ProtocolChecker, get_protocol_checker, LOGIC_PROTOCOLS
        assert ProtocolChecker is not None
        assert LOGIC_PROTOCOLS is not None
        assert len(LOGIC_PROTOCOLS) >= 9  # A-01 到 D-02
    
    def test_check_bazi_passed(self):
        """测试八字检查 - 通过"""
        from core.protocol_checker import get_protocol_checker
        checker = get_protocol_checker()
        
        bazi = {
            'day_master': '甲',
            'month_branch': '卯',
            'month_main': 'bi_jian',
            'stems': ['qi_sha', 'zheng_cai']
        }
        
        result = checker.check_bazi(bazi, 'A-03')
        assert result["passed"] == True
        assert result["mandatory_passed"] == True
    
    def test_check_bazi_failed(self):
        """测试八字检查 - 未通过"""
        from core.protocol_checker import get_protocol_checker
        checker = get_protocol_checker()
        
        bazi = {
            'day_master': '乙',  # 阴干，不符合羊刃
            'month_branch': '卯',
            'month_main': 'bi_jian',
            'stems': ['qi_sha']
        }
        
        result = checker.check_bazi(bazi, 'A-03')
        assert result["passed"] == False
    
    def test_dual_match(self):
        """测试双重比对"""
        from core.protocol_checker import get_protocol_checker
        checker = get_protocol_checker()
        
        bazi = {
            'day_master': '甲',
            'month_branch': '卯',
            'month_main': 'bi_jian',
            'stems': ['qi_sha']
        }
        
        result = checker.dual_match(bazi, 'A-03', mahalanobis_distance=1.5)
        assert result["conclusion"] == "STANDARD_MATCH"
        assert result["verdict"] == "标准成格"
    
    def test_generate_audit_report(self):
        """测试审计报告生成"""
        from core.protocol_checker import get_protocol_checker
        checker = get_protocol_checker()
        
        bazi = {'day_master': '甲', 'month_branch': '卯', 'month_main': 'bi_jian', 'stems': ['qi_sha']}
        dual_result = checker.dual_match(bazi, 'A-03', mahalanobis_distance=1.5)
        
        report = checker.generate_audit_report(dual_result)
        assert "古典逻辑审计报告" in report
        assert "A-03" in report


# ============================================================
# LogicCompiler 测试
# ============================================================

class TestLogicCompiler:
    """LogicCompiler 测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.logic_compiler import LogicCompiler, KnowledgeDrivenCensus
        assert LogicCompiler is not None
        assert KnowledgeDrivenCensus is not None
    
    def test_compile(self):
        """测试协议编译"""
        from core.logic_compiler import LogicCompiler
        compiler = LogicCompiler()
        
        filter_func = compiler.compile('A-03')
        assert callable(filter_func)
        assert filter_func.__name__ == "filter_A-03"
    
    def test_get_protocol_sql(self):
        """测试 SQL 生成"""
        from core.logic_compiler import LogicCompiler
        compiler = LogicCompiler()
        
        sql = compiler.get_protocol_sql('A-03')
        assert "SELECT" in sql
        assert "A-03" in sql
        assert "is_yang_stem" in sql


# ============================================================
# CensusEngine 测试
# ============================================================

class TestCensusEngine:
    """CensusEngine 测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.census_engine import ClassicalCensusEngine, get_census_engine
        assert ClassicalCensusEngine is not None
    
    def test_filter_registration(self):
        """测试过滤器注册"""
        from core.census_engine import ClassicalCensusEngine
        engine = ClassicalCensusEngine()
        
        assert 'A-01' in engine._filters
        assert 'A-03' in engine._filters
        assert 'B-01' in engine._filters
        assert 'D-02' in engine._filters


# ============================================================
# CensusCache 测试
# ============================================================

class TestCensusCache:
    """CensusCache 测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.census_cache import CensusCache, FastPredictor
        assert CensusCache is not None
        assert FastPredictor is not None
    
    def test_cache_result(self):
        """测试缓存结果"""
        from core.census_cache import CensusCache
        cache = CensusCache()
        
        samples = [
            {"uid": 1, "tensor": {"E": 0.5, "O": 0.4, "M": 0.3, "S": 0.4, "R": 0.3}},
            {"uid": 2, "tensor": {"E": 0.6, "O": 0.5, "M": 0.4, "S": 0.5, "R": 0.4}}
        ]
        
        result = cache.cache_census_result("TEST-01", samples, {"name": "测试格局"})
        assert result["cached"] == True
        assert result["sample_count"] == 2
    
    def test_fingerprint_match(self):
        """测试指纹匹配"""
        from core.census_cache import CensusCache
        cache = CensusCache()
        
        # 先缓存一个格局
        samples = [{"uid": i, "tensor": {"E": 0.5, "O": 0.4, "M": 0.3, "S": 0.4, "R": 0.3}} for i in range(10)]
        cache.cache_census_result("TEST-02", samples, {"name": "测试"})
        
        # 测试匹配
        matches = cache.fingerprint_match([0.5, 0.4, 0.3, 0.4, 0.3], top_k=3)
        assert len(matches) > 0
    
    def test_fast_predictor_path(self):
        """测试 FastPredictor 路径策略"""
        from core.census_cache import FastPredictor
        
        predictor = FastPredictor()
        assert predictor.GREEN_THRESHOLD == 2.0
        assert predictor.YELLOW_THRESHOLD == 3.5


# ============================================================
# QGAVV Generator 测试
# ============================================================

class TestQGAVVGenerator:
    """QGAVV 报告生成器测试"""
    
    def test_import(self):
        """测试模块导入"""
        from core.qgavv_generator import QGAVV_ReportGenerator, get_report_generator
        assert QGAVV_ReportGenerator is not None
    
    def test_generate_report(self):
        """测试报告生成"""
        from core.qgavv_generator import get_report_generator
        generator = get_report_generator()
        
        report = generator.generate_report(
            pattern_id='A-03',
            tensor_5d=[0.5, 0.4, 0.3, 0.4, 0.3],
            metrics={
                'mahalanobis_distance': 1.5,
                'cosine_similarity': 0.9,
                'confidence': 0.85,
                'conclusion': 'STANDARD_MATCH'
            }
        )
        
        assert "QGA-VV" in report
        assert "A-03" in report
        assert "物理态" in report


# ============================================================
# 运行测试
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
