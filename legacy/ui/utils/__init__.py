"""
UI工具模块 (UI Utilities)
========================

包含各种UI辅助工具，如MCP上下文注入、配置快照管理等。

作者: Antigravity Team
版本: V10.0
"""

import sys
import os
from pathlib import Path

# 为了兼容性，导入旧版本的utils.py中的函数
# 检查是否存在ui/utils.py文件
_utils_file = Path(__file__).parent.parent / "utils.py"
if _utils_file.exists():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ui.utils_file", _utils_file)
    utils_file_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(utils_file_module)
    
    # 重新导出函数
    load_css = utils_file_module.load_css
    init_session_state = utils_file_module.init_session_state
else:
    # 如果utils.py不存在，定义默认实现
    import streamlit as st
    
    def load_css():
        """Injects custom CSS from assets/style.css"""
        css_path = Path(__file__).parent.parent.parent / "assets" / "style.css"
        if css_path.exists():
            with open(css_path, 'r', encoding='utf-8') as f:
                st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    
    def init_session_state(keys_defaults):
        """Helper to initialize session state keys."""
        for k, v in keys_defaults.items():
            if k not in st.session_state:
                st.session_state[k] = v

# 导出常用模块
from .mcp_context_injection import inject_mcp_context, calculate_year_pillar

__all__ = [
    'inject_mcp_context', 
    'calculate_year_pillar',
    'load_css',
    'init_session_state'
]

