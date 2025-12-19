"""
量子验证控制器 (Quantum Lab Controller)
MVC Controller Layer - 负责量子验证（旺衰判定）的业务逻辑

严格遵循MVC架构原则：
- View层（quantum_lab.py）只负责UI展示和用户交互
- Controller层封装所有算法逻辑，协调Engine和Model
- Engine层负责核心计算
"""

import logging
import copy
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path

from core.engine_graph import GraphNetworkEngine
from core.engine_v88 import EngineV88 as QuantumEngine
from core.bazi_profile import VirtualBaziProfile, BaziProfile
from core.config_schema import DEFAULT_FULL_ALGO_PARAMS
from core.models.config_model import ConfigModel
from ui.utils.mcp_context_injection import inject_mcp_context, calculate_year_pillar

logger = logging.getLogger(__name__)


class QuantumLabController:
    """
    量子验证控制器
    
    职责：
    - 封装旺衰判定相关的算法逻辑
    - 协调Engine和Model的调用
    - 处理MCP上下文注入
    - 提供统一的数据接口给View层
    """
    
    def __init__(self, config: Optional[Dict] = None, config_model: Optional[ConfigModel] = None):
        """
        初始化控制器
        
        Args:
            config: 算法配置参数（如果为None，从ConfigModel加载）
            config_model: 配置Model（如果为None，创建新的实例）
        """
        self._engine: Optional[GraphNetworkEngine] = None
        self._quantum_engine: Optional[QuantumEngine] = None
        self.config_model = config_model or ConfigModel()
        
        # 如果提供了config，使用它；否则从Model加载
        if config is not None:
            self._config = copy.deepcopy(config)
        else:
            self._config = self.config_model.load_config()
        
        logger.info("QuantumLabController initialized")
    
    @property
    def engine(self) -> GraphNetworkEngine:
        """懒加载GraphNetworkEngine（用于旺衰判定）"""
        if self._engine is None:
            # 配置已在__init__中从ConfigModel加载
            self._engine = GraphNetworkEngine(config=self._config)
            logger.debug("GraphNetworkEngine initialized")
        
        return self._engine
    
    @property
    def quantum_engine(self) -> QuantumEngine:
        """懒加载QuantumEngine（用于兼容旧代码）"""
        if self._quantum_engine is None:
            self._quantum_engine = QuantumEngine()
            logger.debug("QuantumEngine initialized")
        
        return self._quantum_engine
    
    def _merge_config(self, base_config: Dict, user_config: Dict):
        """深度合并配置"""
        for key, value in user_config.items():
            if key in base_config and isinstance(base_config[key], dict) and isinstance(value, dict):
                self._merge_config(base_config[key], value)
            else:
                base_config[key] = value
    
    def update_config(self, config_updates: Dict, save_to_file: bool = False):
        """
        更新算法配置
        
        Args:
            config_updates: 配置更新字典（会被深度合并到当前配置）
            save_to_file: 是否保存到配置文件（默认False）
        """
        self._merge_config(self._config, config_updates)
        
        # 如果engine已初始化，需要重新初始化以应用新配置
        if self._engine is not None:
            self._engine = GraphNetworkEngine(config=self._config)
            logger.info("GraphNetworkEngine reinitialized with new config")
        
        # 如果指定保存到文件，通过Model保存
        if save_to_file:
            self.config_model.save_config(self._config, merge=True)
            logger.info("Configuration saved to file")
    
    def create_profile_from_case(self, case: Dict, luck_pillar: str, mcp_context: Optional[Dict] = None) -> VirtualBaziProfile:
        """
        从案例创建VirtualBaziProfile
        
        Args:
            case: 案例数据字典
            luck_pillar: 大运干支
            mcp_context: MCP上下文信息（可选，用于后续计算，不传递给VirtualBaziProfile）
        
        Returns:
            VirtualBaziProfile对象
        
        注意: VirtualBaziProfile 不接受 mcp_context 参数，MCP上下文信息应该在调用Engine计算时使用
        """
        bazi_list = case.get('bazi', ['', '', '', ''])
        pillars = {
            'year': bazi_list[0],
            'month': bazi_list[1],
            'day': bazi_list[2],
            'hour': bazi_list[3] if len(bazi_list) > 3 else ''
        }
        dm = case.get('day_master')
        gender = 1 if case.get('gender') == '男' else 0
        
        # VirtualBaziProfile 不接受 mcp_context 参数
        # MCP上下文信息应该在调用Engine的calculate_strength_score等方法时使用
        return VirtualBaziProfile(
            pillars=pillars,
            static_luck=luck_pillar,
            day_master=dm,
            gender=gender
        )
    
    def inject_mcp_context(self, case: Dict, selected_year: Optional[int] = None) -> Dict:
        """
        注入MCP上下文信息
        
        Args:
            case: 案例数据
            selected_year: 用户选择的年份
        
        Returns:
            包含MCP上下文的案例数据
        """
        return inject_mcp_context(case, selected_year)
    
    def get_luck_pillar(self, case: Dict, target_year: int, mcp_context: Optional[Dict] = None) -> str:
        """
        获取大运（优先级：MCP上下文 -> timeline -> VirtualBaziProfile自动反推）
        
        Args:
            case: 案例数据
            target_year: 目标年份
            mcp_context: MCP上下文信息
        
        Returns:
            大运干支字符串
        """
        # 1. 优先从MCP上下文获取
        if mcp_context:
            luck_pillar = mcp_context.get('luck_pillar')
            if luck_pillar and luck_pillar != "未知":
                logger.debug(f"✅ 从MCP上下文获取大运: {luck_pillar}")
                return luck_pillar
        
        # 2. 从timeline获取
        timeline = case.get('timeline', [])
        for event in timeline:
            if event.get('year') == target_year or event.get('dayun'):
                dayun = event.get('dayun')
                if dayun and dayun != "未知":
                    logger.debug(f"✅ 从timeline获取大运: {dayun}")
                    return dayun
        
        # 3. 使用VirtualBaziProfile自动反推
        try:
            temp_profile = self.create_profile_from_case(case, "未知", mcp_context=mcp_context)
            derived_luck = temp_profile.get_luck_pillar_at(target_year)
            
            if derived_luck and derived_luck != "未知大运" and derived_luck != "未知":
                logger.debug(f"✅ VirtualBaziProfile自动反推大运: {derived_luck}")
                return derived_luck
        except Exception as e:
            logger.warning(f"⚠️ VirtualBaziProfile反推大运失败: {e}", exc_info=True)
        
        return "未知"
    
    def calculate_strength_score(
        self,
        case: Dict,
        luck_pillar: str,
        year_pillar: str,
        geo_context: Optional[Dict] = None,
        era_context: Optional[Dict] = None,
        mcp_context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        计算旺衰分数和标签
        
        Args:
            case: 案例数据
            luck_pillar: 大运干支
            year_pillar: 流年干支
            geo_context: 地理上下文（city, longitude, latitude）
            era_context: 元运上下文（element, period）
            mcp_context: MCP上下文信息
        
        Returns:
            包含strength_score、strength_label等字段的字典
        """
        bazi_list = case.get('bazi', ['', '', '', ''])
        day_master = case.get('day_master')
        gender = case.get('gender', '男')
        
        # 创建profile
        profile = self.create_profile_from_case(case, luck_pillar, mcp_context=mcp_context)
        
        # 准备geo和era上下文
        geo = geo_context or {}
        era = era_context or {}
        
        # 调用Engine计算旺衰
        result = self.engine.calculate_strength_score(
            day_master=day_master,
            bazi=bazi_list,
            luck_pillar=luck_pillar,
            year_pillar=year_pillar,
            geo_context={
                'city': geo.get('city', 'Unknown'),
                'longitude': geo.get('longitude', 0.0),
                'latitude': geo.get('latitude', 0.0),
            },
            era_context={
                'element': era.get('element', 'Fire'),
                'period': era.get('period', 'Period 9 (Fire)'),
            }
        )
        
        return result
    
    def calculate_year_pillar(self, year: int) -> str:
        """
        计算流年干支
        
        Args:
            year: 年份
        
        Returns:
            流年干支字符串
        """
        return calculate_year_pillar(year)
    
    def evaluate_wang_shuai(self, day_master: str, bazi: List[str]) -> Tuple[str, float]:
        """
        评估旺衰（使用GraphNetworkEngine的V10.0非线性算法）
        
        Args:
            day_master: 日主
            bazi: 八字列表
        
        Returns:
            (旺衰标签, 旺衰分数) 元组
        """
        # 使用GraphNetworkEngine（V10.0非线性算法）
        # 初始化引擎（如果尚未初始化）
        engine = self.engine
        
        # 设置八字和日主
        engine.bazi = bazi
        engine.day_master_element = None  # 让引擎自动识别
        
        # 初始化节点
        engine.initialize_nodes(bazi, day_master)
        
        # 构建邻接矩阵
        engine.build_adjacency_matrix()
        
        # 能量传播
        engine.propagate(max_iterations=10)
        
        # 计算旺衰分数（使用V10.0非线性算法）
        result = engine.calculate_strength_score(day_master)
        
        return (result['strength_label'], result['strength_score'])
    
    def calculate_chart(self, birth_info: Dict) -> Dict:
        """
        计算八字排盘（使用QuantumEngine）
        
        Args:
            birth_info: 出生信息字典
        
        Returns:
            排盘结果字典
        """
        return self.quantum_engine.calculate_chart(birth_info)
    
    def calculate_year_context(self, profile: VirtualBaziProfile, year: int):
        """
        计算年份上下文（使用QuantumEngine）
        
        Args:
            profile: VirtualBaziProfile对象
            year: 年份
        
        Returns:
            年份上下文对象
        """
        from core.context import DestinyContext
        return self.quantum_engine.calculate_year_context(profile, year)
    
    def calculate_energy(self, case_data: Dict, dyn_ctx: Dict) -> Dict:
        """
        计算能量（使用QuantumEngine或GraphNetworkEngine）
        
        Args:
            case_data: 案例数据
            dyn_ctx: 动态上下文（包含year, dayun等）
        
        Returns:
            能量计算结果字典，包含graph_data（如果使用GraphNetworkEngine）
        """
        # [V12.1] 修复：优先使用GraphNetworkEngine以获取graph_data
        # 如果需要在网络拓扑可视化中显示，必须使用GraphNetworkEngine
        bazi_list = case_data.get('bazi', ['', '', '', ''])
        day_master = case_data.get('day_master')
        luck_pillar = dyn_ctx.get('dayun') or dyn_ctx.get('luck', '')
        
        # 处理year_pillar：可能是整数年份或干支字符串
        year_value = dyn_ctx.get('year', '')
        if isinstance(year_value, int):
            # 如果是整数年份，转换为干支
            from ui.utils.mcp_context_injection import calculate_year_pillar
            year_pillar = calculate_year_pillar(year_value)
        else:
            year_pillar = year_value or ''
        
        # 使用GraphNetworkEngine计算
        engine = self.engine
        engine.initialize_nodes(bazi_list, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
        engine.build_adjacency_matrix()
        engine.propagate(max_iterations=10)
        
        # 构建graph_data用于可视化
        nodes = []
        for i, node in enumerate(engine.nodes):
            nodes.append({
                'id': i,
                'char': node.char,
                'type': node.node_type,
                'element': node.element,
                'pillar_idx': node.pillar_idx
            })
        
        # 获取邻接矩阵
        adjacency_matrix = engine.adjacency_matrix.tolist() if hasattr(engine, 'adjacency_matrix') else []
        
        # 获取初始和最终能量
        initial_energy = [node.initial_energy for node in engine.nodes]
        final_energy = [node.current_energy for node in engine.nodes]
        
        # 计算旺衰分数
        strength_result = engine.calculate_strength_score(day_master)
        
        # 返回包含graph_data的结果
        result = {
            'graph_data': {
                'nodes': nodes,
                'adjacency_matrix': adjacency_matrix,
                'initial_energy': initial_energy,
                'final_energy': final_energy
            },
            'strength_score': strength_result.get('strength_score', 0.0),
            'strength_label': strength_result.get('strength_label', 'Balanced'),
            'dm_element': engine.day_master_element or engine.STEM_ELEMENTS.get(day_master, 'earth')
        }
        
        return result
    
    def calculate_wealth_with_v12(
        self,
        case: Dict,
        luck_pillar: str,
        year_pillar: str,
        gender: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        [V12.0] 使用V12.0财富引擎计算财富势能
        
        Args:
            case: 案例数据
            luck_pillar: 大运干支
            year_pillar: 流年干支
            gender: 性别（如果为None，从case中获取）
        
        Returns:
            包含wealth_potential、flow_vector、capacity_vector、volatility_sigma的字典
        """
        from core.wealth_engine import calculate_wealth_potential
        
        bazi_list = case.get('bazi', ['', '', '', ''])
        day_master = case.get('day_master')
        gender_str = gender or case.get('gender', '男')
        
        # 初始化引擎
        engine = self.engine
        engine.initialize_nodes(bazi_list, day_master, luck_pillar=luck_pillar, year_pillar=year_pillar)
        engine.build_adjacency_matrix()
        engine.propagate(max_iterations=10)
        
        # 获取身强类型
        strength_result = engine.calculate_strength_score(day_master)
        strength_type = strength_result.get('strength_label', 'Balanced')
        
        # 计算财富势能
        wealth_data = calculate_wealth_potential(
            engine=engine,
            bazi=bazi_list,
            day_master=day_master,
            gender=gender_str,
            year_pillar=year_pillar,
            luck_pillar=luck_pillar,
            strength_type=strength_type
        )
        
        return wealth_data
    
    def simulate_wealth_timeline(
        self,
        case: Dict,
        lifespan: int = 100
    ) -> List[Dict[str, Any]]:
        """
        [V12.0] 使用V12.0时间序列模拟器生成0-100岁财富曲线
        
        Args:
            case: 案例数据
            lifespan: 模拟年限（默认100岁）
        
        Returns:
            每年财富数据列表
        """
        from core.wealth_engine import simulate_life_wealth
        
        bazi_list = case.get('bazi', ['', '', '', ''])
        day_master = case.get('day_master')
        gender = case.get('gender', '男')
        
        # 从birth_date提取出生年份
        birth_date = case.get('birth_date', '')
        if isinstance(birth_date, str) and len(birth_date) >= 4:
            try:
                birth_year = int(birth_date[:4])
            except:
                birth_year = 2000  # 默认值
        elif isinstance(birth_date, dict):
            birth_year = birth_date.get('year', 2000)
        else:
            birth_year = 2000
        
        # 执行模拟
        timeline = simulate_life_wealth(
            bazi=bazi_list,
            day_master=day_master,
            gender=gender,
            birth_year=birth_year,
            lifespan=lifespan,
            config=self._config
        )
        
        return timeline

