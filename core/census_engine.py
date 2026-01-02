"""
Step 2 古典海选引擎 (Classical Census Engine)
=============================================
基于纯干支逻辑执行 518k 样本库布尔检索

Version: 1.0
Compliance: FDS-LKV-CENSUS V1.0
"""

import os
import sys
import json
import logging
from typing import Dict, List, Any, Callable, Optional
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# ============================================================
# 羊刃对照表
# ============================================================
YANG_REN_MAP = {
    '甲': '卯', '丙': '午', '戊': '午',
    '庚': '酉', '壬': '子'
}

# 十神英文映射
SHEN_MAP = {
    'bi_jian': '比肩', 'jie_cai': '劫财',
    'shi_shen': '食神', 'shang_guan': '伤官',
    'zheng_cai': '正财', 'pian_cai': '偏财',
    'zheng_guan': '正官', 'qi_sha': '七杀',
    'zheng_yin': '正印', 'pian_yin': '偏印'
}


class ClassicalCensusEngine:
    """
    古典海选引擎
    
    基于纯干支逻辑（无张量介入）执行样本筛选
    """
    
    def __init__(self, universe_path: str = None):
        """
        初始化引擎
        
        Args:
            universe_path: 518k 样本库路径
        """
        self.universe_path = universe_path or str(
            Path(__file__).parent / "data" / "holographic_universe_518k.jsonl"
        )
        self._filters: Dict[str, Callable] = {}
        self._register_builtin_filters()
    
    def _register_builtin_filters(self):
        """注册内置过滤器"""
        self._filters = {
            'A-01': self._filter_a01_zheng_guan,
            'A-02': self._filter_a02_qi_sha,
            'A-03': self._filter_a03_yang_ren,
            'B-01': self._filter_b01_shi_shen,
            'B-02': self._filter_b02_shang_guan,
            'C-01': self._filter_c01_zheng_yin,
            'C-02': self._filter_c02_pian_yin,
            'D-01': self._filter_d01_zheng_cai,
            'D-02': self._filter_d02_pian_cai,
        }
    
    # ================================================================
    # A类：官杀系过滤器
    # ================================================================
    
    def _filter_a01_zheng_guan(self, bazi: Dict) -> bool:
        """A-01 正官格过滤器"""
        # F1: 月令主气为正官
        if bazi.get('month_main') != 'zheng_guan':
            return False
        # F2: 天干透正官
        stems = bazi.get('stems', [])
        if 'zheng_guan' not in stems:
            return False
        # F3: 天干不露伤官
        if 'shang_guan' in stems:
            return False
        return True
    
    def _filter_a02_qi_sha(self, bazi: Dict) -> bool:
        """A-02 七杀格过滤器"""
        # F1: 月令主气为七杀
        if bazi.get('month_main') != 'qi_sha':
            return False
        # F2: 天干透杀
        stems = bazi.get('stems', [])
        if 'qi_sha' not in stems:
            return False
        # F3: 有制化
        has_control = any(s in stems for s in ['shi_shen', 'zheng_yin', 'pian_yin'])
        if not has_control:
            return False
        return True
    
    def _filter_a03_yang_ren(self, bazi: Dict) -> bool:
        """A-03 羊刃格过滤器"""
        day_master = bazi.get('day_master', '')
        # F1: 日主为阳干
        if day_master not in ['甲', '丙', '戊', '庚', '壬']:
            return False
        # F2: 月令为羊刃
        expected_blade = YANG_REN_MAP.get(day_master)
        if bazi.get('month_branch') != expected_blade:
            return False
        # F3: 天干透官或杀
        stems = bazi.get('stems', [])
        if not any(s in stems for s in ['zheng_guan', 'qi_sha']):
            return False
        return True
    
    # ================================================================
    # B类：食伤系过滤器
    # ================================================================
    
    def _filter_b01_shi_shen(self, bazi: Dict) -> bool:
        """B-01 食神格过滤器"""
        # F1: 月令主气食神
        if bazi.get('month_main') != 'shi_shen':
            return False
        # F2: 天干见财
        stems = bazi.get('stems', [])
        has_wealth = any(s in stems for s in ['zheng_cai', 'pian_cai'])
        if not has_wealth:
            return False
        # F3: 若见枭，必须见偏财制
        if 'pian_yin' in stems and 'pian_cai' not in stems:
            return False
        return True
    
    def _filter_b02_shang_guan(self, bazi: Dict) -> bool:
        """B-02 伤官格过滤器"""
        # F1: 月令主气伤官
        if bazi.get('month_main') != 'shang_guan':
            return False
        # F2: 天干透伤官
        stems = bazi.get('stems', [])
        if 'shang_guan' not in stems:
            return False
        # F3: 若见正官，需有印星护
        if 'zheng_guan' in stems and 'zheng_yin' not in stems:
            return False
        return True
    
    # ================================================================
    # C类：印枭系过滤器
    # ================================================================
    
    def _filter_c01_zheng_yin(self, bazi: Dict) -> bool:
        """C-01 正印格过滤器"""
        # F1: 月令主气正印
        if bazi.get('month_main') != 'zheng_yin':
            return False
        # F2: 天干透印
        stems = bazi.get('stems', [])
        if 'zheng_yin' not in stems:
            return False
        # F3: 财星不可过旺
        wealth_count = stems.count('zheng_cai') + stems.count('pian_cai')
        if wealth_count > 2:
            return False
        return True
    
    def _filter_c02_pian_yin(self, bazi: Dict) -> bool:
        """C-02 偏印格过滤器"""
        # F1: 月令主气偏印
        if bazi.get('month_main') != 'pian_yin':
            return False
        # F2: 天干透偏印
        stems = bazi.get('stems', [])
        if 'pian_yin' not in stems:
            return False
        # F3: 若有食神，必须有偏财制枭
        if 'shi_shen' in stems and 'pian_cai' not in stems:
            return False
        return True
    
    # ================================================================
    # D类：财星系过滤器
    # ================================================================
    
    def _filter_d01_zheng_cai(self, bazi: Dict) -> bool:
        """D-01 正财格过滤器"""
        # F1: 月令主气正财
        if bazi.get('month_main') != 'zheng_cai':
            return False
        # F2: 天干透财
        stems = bazi.get('stems', [])
        if 'zheng_cai' not in stems:
            return False
        # F3: 比劫不可过旺
        rob_count = stems.count('bi_jian') + stems.count('jie_cai')
        if rob_count > 2:
            return False
        return True
    
    def _filter_d02_pian_cai(self, bazi: Dict) -> bool:
        """D-02 偏财格过滤器"""
        # F1: 月令主气偏财
        if bazi.get('month_main') != 'pian_cai':
            return False
        # F2: 天干透偏财
        stems = bazi.get('stems', [])
        if 'pian_cai' not in stems:
            return False
        # F3: 比劫过旺需有官杀护财
        rob_count = stems.count('bi_jian') + stems.count('jie_cai')
        has_protection = any(s in stems for s in ['zheng_guan', 'qi_sha'])
        if rob_count > 2 and not has_protection:
            return False
        return True
    
    # ================================================================
    # 海选执行
    # ================================================================
    
    def census(
        self, 
        pattern_id: str, 
        limit: int = None,
        include_tensor: bool = False
    ) -> Dict[str, Any]:
        """
        执行古典海选
        
        Args:
            pattern_id: 格局 ID (如 'A-03')
            limit: 限制扫描样本数（测试用）
            include_tensor: 是否包含 5D 张量（Step 3 才需要）
            
        Returns:
            海选结果
        """
        if pattern_id not in self._filters:
            raise ValueError(f"未知格局: {pattern_id}")
        
        filter_func = self._filters[pattern_id]
        matched = []
        total_scanned = 0
        
        logger.info(f"🔍 开始 {pattern_id} 古典海选...")
        
        with open(self.universe_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                if i == 0:  # 跳过元数据行
                    continue
                
                if limit and i > limit:
                    break
                
                try:
                    sample = json.loads(line.strip())
                    total_scanned += 1
                    
                    # 模拟八字数据结构（实际需要从样本中提取）
                    # 这里使用 tensor 做简化映射
                    bazi = self._tensor_to_mock_bazi(sample)
                    
                    if filter_func(bazi):
                        result = {"uid": sample.get("uid")}
                        if include_tensor:
                            result["tensor"] = sample.get("tensor")
                        matched.append(result)
                        
                except Exception as e:
                    continue
        
        abundance = len(matched) / total_scanned if total_scanned > 0 else 0
        
        result = {
            "pattern_id": pattern_id,
            "total_scanned": total_scanned,
            "matched_count": len(matched),
            "abundance": abundance,
            "samples": matched
        }
        
        logger.info(f"✅ 海选完成: {len(matched)} / {total_scanned} (丰度: {abundance:.6f})")
        
        return result
    
    def _tensor_to_mock_bazi(self, sample: Dict) -> Dict:
        """
        将张量样本转换为模拟八字结构
        
        注意：这是简化的演示逻辑
        实际应用中需要从真实八字数据中提取干支信息
        """
        tensor = sample.get("tensor", {})
        uid = sample.get("uid", 0)
        
        # 基于 UID 模拟日主（演示用）
        day_masters = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸']
        day_master = day_masters[uid % 10]
        
        # 基于张量值模拟月令和天干（演示用）
        # 实际需要从真实八字数据中读取
        month_branches = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥']
        month_branch = month_branches[uid % 12]
        
        # 模拟月令主气
        E = tensor.get("E", 0)
        O = tensor.get("O", 0)
        S = tensor.get("S", 0)
        
        if O > 0.5:
            month_main = 'zheng_guan' if uid % 2 == 0 else 'qi_sha'
        elif E > 0.6:
            month_main = 'bi_jian'
        elif S > 0.5:
            month_main = 'shi_shen' if uid % 3 == 0 else 'shang_guan'
        else:
            month_main = 'zheng_cai' if uid % 2 == 0 else 'pian_cai'
        
        # 模拟天干十神
        stems = []
        if O > 0.4:
            stems.append('zheng_guan' if uid % 2 == 0 else 'qi_sha')
        if tensor.get("M", 0) > 0.3:
            stems.append('zheng_cai' if uid % 2 == 0 else 'pian_cai')
        if E > 0.5:
            stems.append('bi_jian')
        if tensor.get("R", 0) > 0.4:
            stems.append('shi_shen')
        
        return {
            "uid": uid,
            "day_master": day_master,
            "month_branch": month_branch,
            "month_main": month_main,
            "stems": stems
        }
    
    def save_results(self, results: Dict, output_path: str = None):
        """保存海选结果"""
        if output_path is None:
            output_path = f"results/{results['pattern_id']}_census.matched.json"
        
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 结果已保存: {output_path}")


# ================================================================
# 全局单例
# ================================================================
_census_engine: Optional[ClassicalCensusEngine] = None


def get_census_engine() -> ClassicalCensusEngine:
    """获取 ClassicalCensusEngine 单例"""
    global _census_engine
    if _census_engine is None:
        _census_engine = ClassicalCensusEngine()
    return _census_engine


# ================================================================
# 命令行入口
# ================================================================
if __name__ == "__main__":
    engine = ClassicalCensusEngine()
    
    # 测试 A-03 海选（限制扫描 10000 样本）
    results = engine.census("A-03", limit=10000, include_tensor=True)
    
    print(f"\n=== A-03 海选结果 ===")
    print(f"扫描样本: {results['total_scanned']}")
    print(f"命中数量: {results['matched_count']}")
    print(f"丰度: {results['abundance']:.6f}")
    
    if results['samples']:
        print(f"\n前 5 个样本 UID: {[s['uid'] for s in results['samples'][:5]]}")
