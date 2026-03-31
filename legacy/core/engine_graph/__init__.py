"""
图网络引擎模块
==============

Antigravity Graph Network Engine (Physics-Initialized GNN)

基于图神经网络的八字算法引擎，严格遵循"物理初始化图网络"模型。

架构说明：
- Phase 1: Node Initialization (节点初始化) - 应用所有基础物理规则
- Phase 2: Adjacency Matrix Construction (邻接矩阵构建) - 将生克制化转化为矩阵权重
- Phase 3: Propagation (传播迭代) - 模拟动态做功与传导

版本: V10.0-Graph
"""

# 向后兼容：从原文件导入主类（暂时）
# 后续重构完成后，将从新模块导入
# 注意：使用 importlib 避免循环导入（因为 core.engine_graph 既是包又是文件）
import importlib.util
from pathlib import Path

# 从原文件导入主类
spec = importlib.util.spec_from_file_location(
    "engine_graph_original",
    Path(__file__).parent.parent / "engine_graph.py"
)
engine_graph_original = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine_graph_original)

GraphNetworkEngine = engine_graph_original.GraphNetworkEngine

# 从新模块导入 GraphNode 和常量
from core.engine_graph.graph_node import GraphNode
from core.engine_graph.constants import TWELVE_LIFE_STAGES, LIFE_STAGE_COEFFICIENTS

__all__ = [
    'GraphNetworkEngine',
    'GraphNode',
    'TWELVE_LIFE_STAGES',
    'LIFE_STAGE_COEFFICIENTS',
]

